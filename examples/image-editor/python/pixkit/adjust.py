"""Tonal adjustments implemented as 256-entry lookup tables (LUTs).

A LUT turns any per-value adjustment into one array index per pixel channel,
however expensive the formula that built it.
"""

from typing import Callable, Sequence

import numpy as np


def build_lut(fn: Callable[[np.ndarray], np.ndarray]) -> np.ndarray:
    """Evaluate fn on 0..1 for all 256 input levels; return a uint8 table."""
    x = np.arange(256, dtype=np.float32) / 255.0
    return np.clip(np.rint(fn(x) * 255.0), 0, 255).astype(np.uint8)


def apply_lut(img_u8: np.ndarray, lut: np.ndarray) -> np.ndarray:
    """Apply a LUT to the RGB channels of a uint8 image; alpha is untouched."""
    out = img_u8.copy()
    out[..., :3] = lut[img_u8[..., :3]]
    return out


def levels_lut(
    black: int = 0, white: int = 255, gamma: float = 1.0, out_black: int = 0, out_white: int = 255
) -> np.ndarray:
    """Photoshop-style Levels: map [black, white] to [out_black, out_white] with a midtone gamma.

    gamma > 1 brightens midtones (like moving Photoshop's grey slider left).
    """
    if not 0 <= black < white <= 255:
        raise ValueError("need 0 <= black < white <= 255")
    if gamma <= 0:
        raise ValueError("gamma must be > 0")

    def fn(x):
        t = np.clip((x * 255.0 - black) / (white - black), 0.0, 1.0) ** (1.0 / gamma)
        return (out_black + t * (out_white - out_black)) / 255.0

    return build_lut(fn)


def curves_lut(points: Sequence[tuple[int, int]]) -> np.ndarray:
    """Curves through control points (input, output) in 0..255, linearly interpolated.

    Photoshop draws a smooth spline through the points; linear interpolation keeps
    this reference simple and is exact at the control points.
    """
    pts = sorted(points)
    xs = np.array([p[0] for p in pts], np.float32)
    ys = np.array([p[1] for p in pts], np.float32)
    if len(pts) < 2 or np.any(np.diff(xs) <= 0):
        raise ValueError("need at least two points with distinct inputs")
    return build_lut(lambda x: np.interp(x * 255.0, xs, ys) / 255.0)


def invert_lut() -> np.ndarray:
    return build_lut(lambda x: 1.0 - x)
