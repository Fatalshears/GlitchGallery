"""Segmented, resumable HTTP downloader (standard library only).

Flow:  probe -> plan segments -> preallocate .part -> N workers fetch ranges
       -> checkpoint progress to .part.json -> verify -> rename to final name.
"""

import hashlib
import http.client
import os
import random
import threading
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Callable

from .ranges import parse_content_range, split_ranges
from .ratelimit import TokenBucket
from .state import DownloadState, Segment, load_state, save_state


class DownloadError(Exception):
    pass


class ResourceChanged(DownloadError):
    """Remote file changed (or stopped honouring ranges) since we started."""


class IntegrityError(DownloadError):
    pass


TRANSIENT_HTTP = {408, 425, 429, 500, 502, 503, 504}
TRANSIENT_EXC = (urllib.error.URLError, http.client.HTTPException, ConnectionError, TimeoutError)


@dataclass
class Options:
    connections: int = 4
    min_segment_size: int = 256 * 1024
    chunk_size: int = 64 * 1024
    checkpoint_bytes: int = 1024 * 1024
    max_retries: int = 5
    backoff_base: float = 0.5
    backoff_cap: float = 30.0
    timeout: float = 30.0
    rate_limit: float | None = None  # bytes per second, shared by all workers
    expected_sha256: str | None = None
    headers: dict[str, str] = field(default_factory=dict)


@dataclass
class ProbeResult:
    total: int | None
    accepts_ranges: bool
    etag: str | None
    last_modified: str | None


def backoff_delay(attempt: int, base: float, cap: float) -> float:
    """Exponential backoff with full jitter: uniform(0, min(cap, base * 2^attempt))."""
    return random.uniform(0, min(cap, base * (2**attempt)))


class Downloader:
    def __init__(
        self,
        url: str,
        dest: str,
        options: Options | None = None,
        stop_event: threading.Event | None = None,
        on_progress: Callable[[int, int | None], None] | None = None,
    ):
        self.url = url
        self.dest = dest
        self.opts = options or Options()
        self.stop = stop_event or threading.Event()
        self.on_progress = on_progress
        self.part_path = dest + ".part"
        self.state_path = dest + ".part.json"
        self.bucket = TokenBucket(self.opts.rate_limit) if self.opts.rate_limit else None
        self._lock = threading.Lock()
        self._downloaded = 0
        self.state: DownloadState | None = None

    # ── public ──

    def run(self) -> bool:
        """Download to `dest`. Returns True when complete, False when paused.

        Calling `run()` again after a pause (or crash) resumes from the sidecar.
        """
        try:
            return self._run_once()
        except ResourceChanged:
            self._discard()
            return self._run_once()

    # ── orchestration ──

    def _run_once(self) -> bool:
        state = load_state(self.state_path)
        if state and (state.url != self.url or not os.path.exists(self.part_path)):
            state = None

        if state is None:
            info = self.probe()
            if not (info.accepts_ranges and info.total):
                return self._single_stream()
            state = DownloadState(
                url=self.url,
                total=info.total,
                etag=info.etag,
                last_modified=info.last_modified,
                segments=[
                    Segment(s, e)
                    for s, e in split_ranges(
                        info.total, self.opts.connections, self.opts.min_segment_size
                    )
                ],
            )
            with open(self.part_path, "wb") as f:
                f.truncate(info.total)  # sparse preallocation on most filesystems
            save_state(self.state_path, state)

        self.state = state
        self._downloaded = state.downloaded
        pending = [s for s in state.segments if s.remaining > 0]
        if pending:
            with ThreadPoolExecutor(max_workers=len(pending)) as pool:
                futures = [pool.submit(self._fetch_segment, s) for s in pending]
                errors = [f.exception() for f in futures if f.exception()]
            if errors:
                # Prefer ResourceChanged so run() can restart from scratch.
                raise next((e for e in errors if isinstance(e, ResourceChanged)), errors[0])

        if not state.complete:
            return False  # paused; progress is in the sidecar
        self._finalize()
        return True

    def probe(self) -> ProbeResult:
        """Ask for byte 0 only; a 206 answer proves the server supports ranges."""
        req = self._request({"Range": "bytes=0-0"})
        attempt = 0
        while True:
            try:
                with urllib.request.urlopen(req, timeout=self.opts.timeout) as resp:
                    etag = resp.headers.get("ETag")
                    modified = resp.headers.get("Last-Modified")
                    if resp.status == 206:
                        _, _, total = parse_content_range(resp.headers["Content-Range"])
                        return ProbeResult(total, total is not None, etag, modified)
                    length = resp.headers.get("Content-Length")
                    return ProbeResult(int(length) if length else None, False, etag, modified)
            except urllib.error.HTTPError as e:
                if e.code == 416:  # e.g. empty file; fall back to a plain GET
                    return ProbeResult(None, False, None, None)
                if e.code not in TRANSIENT_HTTP:
                    raise DownloadError(f"probe failed: HTTP {e.code}") from e
                attempt = self._retry_or_raise(attempt, e)
            except TRANSIENT_EXC as e:
                attempt = self._retry_or_raise(attempt, e)

    # ── workers ──

    def _fetch_segment(self, seg: Segment) -> None:
        attempt = 0
        while seg.remaining > 0 and not self.stop.is_set():
            try:
                self._stream_range(seg)
                attempt = 0
            except urllib.error.HTTPError as e:
                if e.code == 416:
                    raise ResourceChanged("range not satisfiable; file shrank?") from e
                if e.code not in TRANSIENT_HTTP:
                    raise DownloadError(f"HTTP {e.code} for {seg}") from e
                attempt = self._retry_or_raise(attempt, e)
            except ResourceChanged:
                raise
            except TRANSIENT_EXC as e:
                attempt = self._retry_or_raise(attempt, e)

    def _retry_or_raise(self, attempt: int, err: Exception) -> int:
        attempt += 1
        if attempt > self.opts.max_retries:
            raise DownloadError(f"giving up after {self.opts.max_retries} retries") from err
        # Event.wait doubles as an interruptible sleep: pause wakes us at once.
        self.stop.wait(backoff_delay(attempt, self.opts.backoff_base, self.opts.backoff_cap))
        return attempt

    def _stream_range(self, seg: Segment) -> None:
        headers = {"Range": f"bytes={seg.next_offset}-{seg.end}"}
        validator = self.state.validator()
        if validator:
            # If the file changed, the server answers 200 with the full body
            # instead of 206 - we detect that below.
            headers["If-Range"] = validator
        req = self._request(headers)
        with urllib.request.urlopen(req, timeout=self.opts.timeout) as resp:
            if resp.status != 206:
                raise ResourceChanged(f"expected 206, got {resp.status}")
            start, _, _ = parse_content_range(resp.headers["Content-Range"])
            if start != seg.next_offset:
                raise ResourceChanged(f"server returned range at {start}")

            offset, pending = seg.next_offset, 0
            with open(self.part_path, "r+b") as f:
                f.seek(offset)
                try:
                    while offset <= seg.end and not self.stop.is_set():
                        chunk = resp.read(min(self.opts.chunk_size, seg.end - offset + 1))
                        if not chunk:
                            raise ConnectionError("connection closed before range end")
                        if self.bucket:
                            self.bucket.consume(len(chunk))
                        f.write(chunk)
                        offset += len(chunk)
                        pending += len(chunk)
                        self._report(len(chunk))
                        if pending >= self.opts.checkpoint_bytes:
                            self._commit(f, seg, pending)
                            pending = 0
                finally:
                    if pending:
                        self._commit(f, seg, pending)

    def _commit(self, f, seg: Segment, n: int) -> None:
        """Make bytes durable first, then record them. Never the other way round."""
        f.flush()
        os.fsync(f.fileno())
        with self._lock:
            seg.done += n
            save_state(self.state_path, self.state)

    def _single_stream(self) -> bool:
        """Fallback for servers without range support: no parallelism, no resume."""
        attempt = 0
        while True:
            if self.stop.is_set():
                return False
            try:
                self._downloaded = 0
                with urllib.request.urlopen(self._request({}), timeout=self.opts.timeout) as resp:
                    expected = resp.headers.get("Content-Length")
                    written = 0
                    with open(self.part_path, "wb") as f:
                        while chunk := resp.read(self.opts.chunk_size):
                            if self.stop.is_set():
                                return False
                            if self.bucket:
                                self.bucket.consume(len(chunk))
                            f.write(chunk)
                            written += len(chunk)
                            self._report(len(chunk))
                        f.flush()
                        os.fsync(f.fileno())
                    # http.client's read(amt) returns b"" at a premature EOF instead of raising,
                    # so a cut connection looks like a finished body. Compare with Content-Length.
                    if expected is not None and written != int(expected):
                        raise ConnectionError(f"connection closed after {written} of {expected} bytes")
                break
            except urllib.error.HTTPError as e:
                if e.code not in TRANSIENT_HTTP:
                    raise DownloadError(f"HTTP {e.code}") from e
                attempt = self._retry_or_raise(attempt, e)
            except TRANSIENT_EXC as e:
                attempt = self._retry_or_raise(attempt, e)
        self._finalize()
        return True

    # ── helpers ──

    def _finalize(self) -> None:
        if self.opts.expected_sha256:
            actual = sha256_file(self.part_path)
            if actual != self.opts.expected_sha256.lower():
                self._discard()
                raise IntegrityError(f"sha256 mismatch: {actual}")
        os.replace(self.part_path, self.dest)
        if os.path.exists(self.state_path):
            os.unlink(self.state_path)

    def _discard(self) -> None:
        for p in (self.part_path, self.state_path):
            if os.path.exists(p):
                os.unlink(p)

    def _request(self, extra: dict[str, str]) -> urllib.request.Request:
        headers = {"User-Agent": "minidm/0.1", **self.opts.headers, **extra}
        return urllib.request.Request(self.url, headers=headers)

    def _report(self, n: int) -> None:
        with self._lock:
            self._downloaded += n
            done = self._downloaded
        if self.on_progress:
            self.on_progress(done, self.state.total if self.state else None)


def sha256_file(path: str, block: int = 1024 * 1024) -> str:
    """Hash a file in fixed-size blocks so memory stays constant for any file size."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while data := f.read(block):
            h.update(data)
    return h.hexdigest()
