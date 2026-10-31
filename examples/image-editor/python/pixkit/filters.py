"""Convolution filters: blur, sharpen, and general kernels."""

import math

import numpy as np

from .color import premultiply, unpremultiply

_EDGE_MODES = {"clamp": "edge", "reflect": "reflect", "wrap": "wrap", "zero": "constant"}


def gaussian_kernel(sigma: float) -> np.ndarray:
    """Normalized 1-D Gaussian with radius ceil(3*sigma) (covers 99.7 % of the weight)."""
    if sigma <= 0:
        raise ValueError("sigma must be > 0")
    r = max(1, math.ceil(3 * sigma))
    x = np.arange(-r, r + 1, dtype=np.float32)
    k = np.exp(-(x * x) / (2 * sigma * sigma))
    return (k / k.sum()).astype(np.float32)


def box_kernel(radius: int) -> np.ndarray:
    n = 2 * radius + 1
    return np.full(n, 1.0 / n, np.float32)


def convolve1d(img: np.ndarray, kernel: np.ndarray, axis: int, edge: str = "clamp") -> np.ndarray:
    """Convolve along one axis (0 = vertical, 1 = horizontal) with a symmetric odd kernel."""
    r = len(kernel) // 2
    pad = [(0, 0)] * img.ndim
    pad[axis] = (r, r)
    padded = np.pad(img, pad, mode=_EDGE_MODES[edge])
    out = np.zeros_like(img, dtype=np.float32)
    n = img.shape[axis]
    for i, w in enumerate(kernel):
        sl = [slice(None)] * img.ndim
        sl[axis] = slice(i, i + n)
        out += w * padded[tuple(sl)]
    return out


def convolve_separable(img: np.ndarray, kernel: np.ndarray, edge: str = "clamp") -> np.ndarray:
    """2-D convolution with kernel ⊗ kernel as two 1-D passes: O(k) instead of O(k²) per pixel."""
    return convolve1d(convolve1d(img, kernel, 0, edge), kernel, 1, edge)


def convolve2d(img: np.ndarray, kernel: np.ndarray, edge: str = "clamp") -> np.ndarray:
    """General (non-separable) 2-D convolution, e.g. sharpen or edge-detect kernels."""
    kh, kw = kernel.shape
    ry, rx = kh // 2, kw // 2
    pad = [(ry, ry), (rx, rx)] + [(0, 0)] * (img.ndim - 2)
    padded = np.pad(img, pad, mode=_EDGE_MODES[edge])
    h, w = img.shape[:2]
    out = np.zeros_like(img, dtype=np.float32)
    flipped = kernel[::-1, ::-1]  # true convolution, not correlation
    for dy in range(kh):
        for dx in range(kw):
            out += flipped[dy, dx] * padded[dy : dy + h, dx : dx + w]
    return out


def _blur_rgba(img: np.ndarray, kernel: np.ndarray, edge: str) -> np.ndarray:
    # Blur premultiplied colour, or transparent pixels (often black) bleed dark fringes.
    if img.shape[-1] == 4:
        return np.clip(unpremultiply(convolve_separable(premultiply(img), kernel, edge)), 0, 1)
    return np.clip(convolve_separable(img, kernel, edge), 0, 1)


def gaussian_blur(img: np.ndarray, sigma: float, edge: str = "clamp") -> np.ndarray:
    return _blur_rgba(img, gaussian_kernel(sigma), edge)


def box_blur(img: np.ndarray, radius: int, edge: str = "clamp") -> np.ndarray:
    return _blur_rgba(img, box_kernel(radius), edge)


def unsharp_mask(img: np.ndarray, sigma: float, amount: float = 1.0, threshold: float = 0.0) -> np.ndarray:
    """Sharpen: add back `amount` × (image − blurred) where the difference exceeds `threshold`."""
    blurred = gaussian_blur(img, sigma)
    out = img.copy()
    diff = img[..., :3] - blurred[..., :3]
    keep = np.abs(diff) >= threshold
    out[..., :3] = np.clip(img[..., :3] + amount * diff * keep, 0, 1)
    return out
