"""Blend modes and source-over compositing (W3C Compositing and Blending Level 1)."""

from typing import Callable

import numpy as np

BlendFn = Callable[[np.ndarray, np.ndarray], np.ndarray]


def _screen(cb, cs):
    return cb + cs - cb * cs


def _hard_light(cb, cs):
    return np.where(cs <= 0.5, cb * 2 * cs, _screen(cb, 2 * cs - 1))


def _color_dodge(cb, cs):
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(cb == 0, 0.0, np.where(cs >= 1, 1.0, np.minimum(1.0, cb / (1 - cs))))


def _color_burn(cb, cs):
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(cb == 1, 1.0, np.where(cs <= 0, 0.0, 1 - np.minimum(1.0, (1 - cb) / cs)))


# B(Cb, Cs): backdrop colour Cb, source colour Cs, both straight RGB in [0, 1].
BLEND_MODES: dict[str, BlendFn] = {
    "normal": lambda cb, cs: cs,
    "multiply": lambda cb, cs: cb * cs,
    "screen": _screen,
    "overlay": lambda cb, cs: _hard_light(cs, cb),
    "darken": np.minimum,
    "lighten": np.maximum,
    "color-dodge": _color_dodge,
    "color-burn": _color_burn,
    "hard-light": _hard_light,
    "difference": lambda cb, cs: np.abs(cb - cs),
    "linear-dodge": lambda cb, cs: np.minimum(1.0, cb + cs),
}


def composite(
    backdrop: np.ndarray,
    source: np.ndarray,
    mode: str = "normal",
    opacity: float = 1.0,
    mask: np.ndarray | None = None,
) -> np.ndarray:
    """Blend `source` onto `backdrop` (both straight RGBA) and composite with source-over.

        co = as·(1−ab)·Cs + as·ab·B(Cb, Cs) + (1−as)·ab·Cb
        ao = as + ab·(1−as)
        C  = co / ao
    """
    if mode not in BLEND_MODES:
        raise ValueError(f"unknown blend mode {mode!r}; choose from {sorted(BLEND_MODES)}")
    cb, ab = backdrop[..., :3], backdrop[..., 3:4]
    cs, a_s = source[..., :3], source[..., 3:4] * opacity
    if mask is not None:
        a_s = a_s * mask[..., None]
    b = BLEND_MODES[mode](cb, cs)
    co = a_s * (1 - ab) * cs + a_s * ab * b + (1 - a_s) * ab * cb
    ao = a_s + ab * (1 - a_s)
    out = np.empty_like(backdrop, dtype=np.float32)
    with np.errstate(divide="ignore", invalid="ignore"):
        out[..., :3] = np.where(ao > 0, co / ao, 0.0)
    out[..., 3:4] = ao
    return np.clip(out, 0, 1)
