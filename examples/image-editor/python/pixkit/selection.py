"""Selections as masks: shapes, magic wand (flood fill), feathering, combination."""

from collections import deque

import numpy as np

from .filters import convolve_separable, gaussian_kernel


def rect_mask(height: int, width: int, x0: int, y0: int, x1: int, y1: int) -> np.ndarray:
    """Pixels with x0 <= x < x1 and y0 <= y < y1 are selected (1.0)."""
    m = np.zeros((height, width), np.float32)
    m[max(0, y0) : min(height, y1), max(0, x0) : min(width, x1)] = 1.0
    return m


def ellipse_mask(height: int, width: int, cx: float, cy: float, rx: float, ry: float) -> np.ndarray:
    """Ellipse with a 1-pixel anti-aliased edge (coverage estimated from the distance)."""
    ys, xs = np.mgrid[0:height, 0:width].astype(np.float32) + 0.5  # pixel centres
    d = np.sqrt(((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2)
    return np.clip((1 - d) * min(rx, ry) + 0.5, 0, 1).astype(np.float32)


def magic_wand(
    img: np.ndarray, x: int, y: int, tolerance: int = 32, contiguous: bool = True, connectivity: int = 4
) -> np.ndarray:
    """Select pixels whose colour is within `tolerance` (0-255 scale, max channel difference)
    of the seed pixel; with `contiguous`, only those connected to the seed (flood fill)."""
    h, w = img.shape[:2]
    seed = img[y, x, :3]
    match = np.abs(img[..., :3] - seed).max(axis=-1) * 255.0 <= tolerance + 1e-4
    if not contiguous:
        return match.astype(np.float32)

    steps = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if connectivity == 8:
        steps += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    selected = np.zeros((h, w), bool)
    selected[y, x] = True
    queue = deque([(y, x)])
    while queue:  # breadth-first flood fill
        cy, cx = queue.popleft()
        for dy, dx in steps:
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < h and 0 <= nx < w and match[ny, nx] and not selected[ny, nx]:
                selected[ny, nx] = True
                queue.append((ny, nx))
    return selected.astype(np.float32)


def feather(mask: np.ndarray, radius: float) -> np.ndarray:
    """Soften a mask's edge; Photoshop's feather radius ≈ Gaussian sigma here."""
    if radius <= 0:
        return mask.copy()
    return np.clip(convolve_separable(mask, gaussian_kernel(radius), "zero"), 0, 1)


def combine(a: np.ndarray, b: np.ndarray, op: str) -> np.ndarray:
    """Selection arithmetic: 'add' (Shift), 'subtract' (Alt/Option), 'intersect' (both)."""
    if op == "add":
        return np.maximum(a, b)
    if op == "subtract":
        return np.clip(a - b, 0, 1)
    if op == "intersect":
        return np.minimum(a, b)
    raise ValueError(op)
