"""Pixel representation helpers.

Convention used throughout pixkit: an image is a float32 NumPy array of shape
(height, width, 4) holding *straight* (non-premultiplied) RGBA in [0, 1], with
RGB in the sRGB-encoded space, as Photoshop does for 8-bit RGB documents.
"""

import numpy as np


def to_float(img_u8: np.ndarray) -> np.ndarray:
    """uint8 [0, 255] -> float32 [0, 1]. Adds an opaque alpha channel to RGB input."""
    img = img_u8.astype(np.float32) / 255.0
    if img.ndim == 2:
        img = np.stack([img, img, img], axis=-1)
    if img.shape[-1] == 3:
        img = np.concatenate([img, np.ones(img.shape[:2] + (1,), np.float32)], axis=-1)
    return img


def to_u8(img: np.ndarray) -> np.ndarray:
    """float [0, 1] -> uint8 with rounding (not truncation) and clipping."""
    return np.clip(np.rint(img * 255.0), 0, 255).astype(np.uint8)


def srgb_to_linear(c: np.ndarray) -> np.ndarray:
    """IEC 61966-2-1 sRGB decoding: encoded value -> linear light."""
    c = np.asarray(c, np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).astype(np.float32)


def linear_to_srgb(c: np.ndarray) -> np.ndarray:
    c = np.clip(np.asarray(c, np.float32), 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055).astype(np.float32)


def premultiply(img: np.ndarray) -> np.ndarray:
    out = img.copy()
    out[..., :3] *= img[..., 3:4]
    return out


def unpremultiply(img: np.ndarray) -> np.ndarray:
    out = img.copy()
    a = img[..., 3:4]
    with np.errstate(divide="ignore", invalid="ignore"):
        out[..., :3] = np.where(a > 0, img[..., :3] / a, 0.0)
    return out


def solid(height: int, width: int, rgba=(0.0, 0.0, 0.0, 0.0)) -> np.ndarray:
    """A new image filled with one colour (transparent by default)."""
    return np.broadcast_to(np.asarray(rgba, np.float32), (height, width, 4)).copy()
