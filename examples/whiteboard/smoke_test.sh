#!/usr/bin/env bash
# Run sketchkit's tests, then a two-client encrypted collaboration demo through the relay.
# Requires Node.js >= 22.18 and network access to the npm registry (for ws, typescript and type packages).
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'kill "${relay_pid:-}" 2>/dev/null || true; rm -rf "$work"' EXIT

echo "== unit tests"
(cd "$here/typescript" && node --test 2>&1 | grep -E "^# (pass|fail)")

echo "== relay + two clients"
cp -r "$here/typescript/." "$work/"
(cd "$work" && npm install --no-save --no-audit --no-fund --loglevel=error ws@8 @types/ws typescript@5 @types/node@22 >/dev/null)
echo "== strict type check (node only strips types; it never checks them)"
(cd "$work" && npx tsc -p . && echo "tsc: no type errors")
port=$((20000 + RANDOM % 20000))
node "$work/relay/relay-server.ts" "$port" > "$work/relay.log" 2>&1 &
relay_pid=$!
for _ in $(seq 50); do grep -q listening "$work/relay.log" 2>/dev/null && break; sleep 0.1; done
node "$work/relay/collab-demo.ts" "ws://localhost:$port"
echo "smoke tests passed"
