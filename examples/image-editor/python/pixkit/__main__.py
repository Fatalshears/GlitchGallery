"""CLI: python -m pixkit IN OUT [--levels B,W,G] [--blur SIGMA] [--sharpen SIGMA,AMOUNT]

Operations run in the order given above. Needs Pillow for reading and writing files.
"""

import argparse
import sys

from .adjust import apply_lut, levels_lut
from .color import to_float, to_u8
from .filters import gaussian_blur, unsharp_mask
from .io import load_image, save_image


def main() -> int:
    p = argparse.ArgumentParser(prog="pixkit")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--levels", help="black,white,gamma e.g. 10,245,1.2")
    p.add_argument("--blur", type=float, help="Gaussian sigma in pixels")
    p.add_argument("--sharpen", help="sigma,amount e.g. 1.0,0.8")
    a = p.parse_args()

    img = load_image(a.input)
    if a.levels:
        b, w, g = a.levels.split(",")
        img = to_float(apply_lut(to_u8(img), levels_lut(int(b), int(w), float(g))))
    if a.blur:
        img = gaussian_blur(img, a.blur)
    if a.sharpen:
        s, amt = a.sharpen.split(",")
        img = unsharp_mask(img, float(s), float(amt))
    save_image(a.output, img)
    print(f"wrote {a.output} ({img.shape[1]}x{img.shape[0]})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
