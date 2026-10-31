#!/usr/bin/env bash
# Build and run the C++ and TypeScript examples; cross-check the C++ blur against
# the Python reference. Requires python3 + numpy, g++, node >= 22.18.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

echo "== C++ undo stack"
g++ -std=c++17 -O2 "$here/cpp/undo_stack.cpp" -o "$work/undo_stack"
"$work/undo_stack"

echo "== C++ blur vs Python reference"
g++ -std=c++17 -O2 "$here/cpp/gaussian_blur.cpp" -pthread -o "$work/gaussian_blur"
PYTHONPATH="$here/python" python3 - "$work" <<'PY'
import sys, numpy as np
from pixkit import gaussian_blur, to_float, to_u8
work = sys.argv[1]
rng = np.random.default_rng(1)
src = rng.integers(0, 256, (37, 53, 3), dtype=np.uint8)
with open(f"{work}/in.ppm", "wb") as f:
    f.write(b"P6\n53 37\n255\n" + src.tobytes())
np.save(f"{work}/expected.npy", to_u8(gaussian_blur(to_float(src), 2.0))[..., :3])
PY
"$work/gaussian_blur" "$work/in.ppm" "$work/out.ppm" 2.0 4
PYTHONPATH="$here/python" python3 - "$work" <<'PY'
import sys, numpy as np
work = sys.argv[1]
raw = open(f"{work}/out.ppm", "rb").read()
got = np.frombuffer(raw[len(b"P6\n53 37\n255\n"):], np.uint8).reshape(37, 53, 3)
diff = np.abs(got.astype(int) - np.load(f"{work}/expected.npy").astype(int)).max()
print("max difference vs Python:", diff)
assert diff <= 1, "C++ and Python blur disagree"
PY

echo "== TypeScript ImageData ops"
node "$here/typescript/imagedata-ops.ts"
echo "smoke tests passed"
