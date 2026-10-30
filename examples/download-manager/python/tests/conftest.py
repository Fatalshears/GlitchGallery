"""pytest fixture wrapping the fault-injecting server in rangeserver.py."""

import threading
from http.server import ThreadingHTTPServer

import pytest

from rangeserver import ServerConfig, make_handler


@pytest.fixture
def server():
    cfg = ServerConfig()
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(cfg))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    cfg.url = f"http://127.0.0.1:{httpd.server_address[1]}/file.bin"
    yield cfg
    httpd.shutdown()
    httpd.server_close()
