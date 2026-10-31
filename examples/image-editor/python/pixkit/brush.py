"""Brush strokes: evenly spaced dabs of a round tip along a path."""

import math
from typing import Sequence

import numpy as np

from .blend import composite

Point = tuple[float, float]  # (x, y) in pixels


def spaced_points(points: Sequence[Point], spacing: float) -> list[Point]:
    """Points every `spacing` pixels along the polyline, carrying leftover distance
    across segments so dab density does not depend on how the mouse events were sampled."""
    if spacing <= 0:
        raise ValueError("spacing must be > 0")
    out = [tuple(points[0])]
    to_next = spacing
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        pos = 0.0
        while seg - pos >= to_next:
            pos += to_next
            t = pos / seg
            out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
            to_next = spacing
        to_next -= seg - pos
    return out


def dab_alpha(dist: np.ndarray, radius: float, hardness: float) -> np.ndarray:
    """Coverage of a round tip at distance `dist` from its centre.
    hardness 1: solid disc with a 1-pixel anti-aliased edge; lower: smooth falloff."""
    if hardness >= 1:
        return np.clip(radius - dist + 0.5, 0, 1)
    inner = radius * hardness
    t = np.clip((dist - inner) / (radius - inner), 0, 1)
    return 1 - t * t * (3 - 2 * t)  # 1 - smoothstep


def stroke_bbox(points: Sequence[Point], diameter: float, height: int, width: int):
    """Rectangle (y0, y1, x0, x1) a stroke can touch — needed before painting to snapshot for undo."""
    r = diameter / 2 + 1
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    y0, y1 = max(0, math.floor(min(ys) - r)), min(height, math.ceil(max(ys) + r))
    x0, x1 = max(0, math.floor(min(xs) - r)), min(width, math.ceil(max(xs) + r))
    return y0, y1, x0, x1


def stroke_coverage(points: Sequence[Point], diameter: float, height: int, width: int,
                    hardness: float = 1.0, spacing: float = 0.25) -> np.ndarray:
    """Coverage mask of a whole stroke: the maximum of all dabs, so overlapping dabs within
    one stroke never exceed the stroke's opacity (Photoshop's Opacity vs Flow distinction)."""
    radius = diameter / 2
    cov = np.zeros((height, width), np.float32)
    for cx, cy in spaced_points(points, max(1.0, spacing * diameter)):
        y0, y1 = max(0, int(cy - radius - 1)), min(height, int(cy + radius + 2))
        x0, x1 = max(0, int(cx - radius - 1)), min(width, int(cx + radius + 2))
        if y0 >= y1 or x0 >= x1:
            continue
        ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float32) + 0.5
        a = dab_alpha(np.hypot(xs - cx, ys - cy), radius, hardness)
        np.maximum(cov[y0:y1, x0:x1], a, out=cov[y0:y1, x0:x1])
    return cov


def paint_stroke(pixels: np.ndarray, points: Sequence[Point], color, diameter: float,
                 hardness: float = 1.0, opacity: float = 1.0, spacing: float = 0.25) -> np.ndarray:
    """Return a copy of `pixels` with the stroke composited on top (normal mode)."""
    h, w = pixels.shape[:2]
    cov = stroke_coverage(points, diameter, h, w, hardness, spacing)
    src = np.zeros_like(pixels)
    src[..., :3] = np.asarray(color, np.float32)[:3]
    src[..., 3] = cov * opacity
    return composite(pixels, src)
