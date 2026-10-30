#!/usr/bin/env bash
# Smoke-test the TypeScript and C++ minimal examples against a local Range-capable
# server (the same one the Python tests use). Requires node >= 22.18, g++, libcurl dev.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'kill "${srv_pid:-}" 2>/dev/null || true; rm -rf "$work"' EXIT

head -c 3000017 /dev/urandom > "$work/src.bin"

python3 -c "
import sys
sys.path.insert(0, '$here/python/tests')
from conftest import ServerConfig, make_handler
from http.server import ThreadingHTTPServer
cfg = ServerConfig(body=open('$work/src.bin','rb').read())
cfg.drop_after, cfg.drops = 100_000, 2
s = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(cfg))
open('$work/port','w').write(str(s.server_address[1]))
s.serve_forever()
" &
srv_pid=$!
for _ in $(seq 50); do [ -s "$work/port" ] && break; sleep 0.1; done
url="http://127.0.0.1:$(cat "$work/port")/file.bin"

echo "== TypeScript"
node "$here/typescript/segmented-download.ts" "$url" "$work/ts.bin" 4
cmp "$work/src.bin" "$work/ts.bin"

echo "== C++"
g++ -std=c++17 -O2 "$here/cpp/segmented_download.cpp" -lcurl -pthread -o "$work/segdl"
"$work/segdl" "$url" "$work/cpp.bin" 4
cmp "$work/src.bin" "$work/cpp.bin"

echo "smoke tests passed"
