#!/usr/bin/env bash
# Build the C++ examples, run the ring buffer, and cross-check the C++ safety
# checker against the Python one on a random event stream. Needs g++ and python3.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

echo "== C++ SPSC ring buffer (2 threads)"
g++ -std=c++17 -O2 -Wall -Wextra -pthread "$here/cpp/spsc_ring.cpp" -o "$work/spsc_ring"
echo "== same ring buffer under ThreadSanitizer (fails on any data race)"
g++ -std=c++17 -O1 -g -fsanitize=thread -pthread "$here/cpp/spsc_ring.cpp" -o "$work/spsc_ring_tsan"
TSAN_OPTIONS=halt_on_error=1 "$work/spsc_ring_tsan"
"$work/spsc_ring"
echo "== same ring buffer under ThreadSanitizer (fails on any data race)"
g++ -std=c++17 -O1 -g -fsanitize=thread -pthread "$here/cpp/spsc_ring.cpp" -o "$work/spsc_ring_tsan"
TSAN_OPTIONS=halt_on_error=1 "$work/spsc_ring_tsan"

echo "== C++ vs Python safety checker"
g++ -std=c++17 -O2 -Wall -Wextra "$here/cpp/safety_replay.cpp" -o "$work/safety_replay"
PYTHONPATH="$here/python" python3 - "$work" <<'PY'
import random, sys
from drivekit.safety import SafetyChecker
work = sys.argv[1]
rng = random.Random(7)
events, expected, s = [], [], SafetyChecker()
for _ in range(50000):
    r = rng.random()
    if r < 0.01:
        v = rng.random() < 0.3; events.append(f"brake {int(v)}"); s.on_brake(v)
    elif r < 0.03:
        v = rng.random() < 0.8; events.append(f"cruise {int(v)}"); s.on_cruise(v)
    else:
        # mostly small steps from the last torque, sometimes wild jumps
        t = s.last_torque + rng.randint(-30, 30) if rng.random() < 0.9 else rng.randint(-1600, 1600)
        events.append(f"steer {t}"); expected.append(str(int(s.allow_steer(t))))
open(f"{work}/events.txt", "w").write("\n".join(events) + "\n")
open(f"{work}/expected.txt", "w").write("\n".join(expected) + "\n")
print(f"{len(events)} events, {expected.count('1')} commands allowed, {expected.count('0')} blocked")
PY
"$work/safety_replay" < "$work/events.txt" > "$work/actual.txt"
cmp "$work/expected.txt" "$work/actual.txt" && echo "C++ and Python agree on every decision"
echo "smoke tests passed"
