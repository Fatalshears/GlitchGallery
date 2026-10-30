"""Crash-safe persistence of download progress (the `.part.json` sidecar)."""

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field


@dataclass
class Segment:
    start: int
    end: int  # inclusive
    done: int = 0  # bytes already written from `start`

    @property
    def remaining(self) -> int:
        return self.end - self.start + 1 - self.done

    @property
    def next_offset(self) -> int:
        return self.start + self.done


@dataclass
class DownloadState:
    url: str
    total: int | None
    etag: str | None = None
    last_modified: str | None = None
    segments: list[Segment] = field(default_factory=list)

    @property
    def downloaded(self) -> int:
        return sum(s.done for s in self.segments)

    @property
    def complete(self) -> bool:
        return bool(self.segments) and all(s.remaining == 0 for s in self.segments)

    def validator(self) -> str | None:
        """Value for `If-Range`: a strong ETag is preferred over a date."""
        if self.etag and not self.etag.startswith("W/"):
            return self.etag
        return self.last_modified


def atomic_write_json(path: str, data: dict) -> None:
    """Write JSON so readers see either the old file or the new one, never half.

    Pattern: write temp file in the same directory -> flush -> fsync -> rename.
    `os.replace` is atomic on POSIX when source and target are on the same
    filesystem; on Windows (MoveFileExW) it is atomic in practice on NTFS.
    """
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def save_state(path: str, state: DownloadState) -> None:
    atomic_write_json(path, asdict(state))


def load_state(path: str) -> DownloadState | None:
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except FileNotFoundError:
        return None
    except (json.JSONDecodeError, OSError):
        return None  # corrupt sidecar: treat as fresh download
    raw["segments"] = [Segment(**s) for s in raw.get("segments", [])]
    return DownloadState(**raw)
