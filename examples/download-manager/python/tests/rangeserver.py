"""Local HTTP server with controllable Range behaviour and fault injection.

No pytest dependency, so smoke tests in other languages can reuse it.
"""

import re
import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler



@dataclass
class ServerConfig:
    body: bytes = b""
    etag: str = '"v1"'
    support_ranges: bool = True
    # Close the connection after sending this many body bytes, `drops` times.
    drop_after: int | None = None
    drops: int = 0
    fail_status: int | None = None  # answer this status `fail_times` times
    fail_times: int = 0
    range_log: list[str | None] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)


def make_handler(cfg: ServerConfig):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args):  # keep test output clean
            pass

        def do_HEAD(self):
            self.send_response(200)
            self.send_header("Content-Length", str(len(cfg.body)))
            self.send_header("ETag", cfg.etag)
            if cfg.support_ranges:
                self.send_header("Accept-Ranges", "bytes")
            self.end_headers()

        def do_GET(self):
            rng = self.headers.get("Range")
            with cfg.lock:
                cfg.range_log.append(rng)
                if cfg.fail_times > 0:
                    cfg.fail_times -= 1
                    self.send_response(cfg.fail_status)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                drop = cfg.drop_after if cfg.drops > 0 else None
                if drop is not None:
                    cfg.drops -= 1

            body, total = cfg.body, len(cfg.body)
            if_range = self.headers.get("If-Range")
            use_range = cfg.support_ranges and rng and (if_range in (None, cfg.etag))

            if use_range:
                m = re.fullmatch(r"bytes=(\d+)-(\d*)", rng)
                start = int(m.group(1))
                end = int(m.group(2)) if m.group(2) else total - 1
                if start >= total:
                    self.send_response(416)
                    self.send_header("Content-Range", f"bytes */{total}")
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                end = min(end, total - 1)
                payload = body[start : end + 1]
                self.send_response(206)
                self.send_header("Content-Range", f"bytes {start}-{end}/{total}")
            else:
                payload = body
                self.send_response(200)

            self.send_header("Content-Length", str(len(payload)))
            self.send_header("ETag", cfg.etag)
            if cfg.support_ranges:
                self.send_header("Accept-Ranges", "bytes")
            self.end_headers()
            if drop is not None:
                self.wfile.write(payload[:drop])
                self.wfile.flush()
                self.close_connection = True
                return
            self.wfile.write(payload)

    return Handler
