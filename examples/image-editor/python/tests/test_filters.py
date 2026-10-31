import numpy as np
import pytest

from pixkit import box_blur, convolve2d, gaussian_blur, gaussian_kernel, unsharp_mask
from pixkit.filters import convolve_separable


def test_gaussian_kernel_shape_and_normalized():
    k = gaussian_kernel(1.0)
    assert len(k) == 7 and k.sum() == pytest.approx(1.0) and k[3] == k.max()
    assert np.allclose(k, k[::-1])


def test_blur_of_constant_image_is_unchanged():
    img = np.full((20, 30, 4), 0.4, np.float32)
    img[..., 3] = 1
    assert np.allclose(gaussian_blur(img, 2.0), img, atol=1e-6)


def test_impulse_response_is_kernel_outer_product():
    img = np.zeros((15, 15), np.float32)
    img[7, 7] = 1
    k = gaussian_kernel(1.5)
    out = convolve_separable(img, k, "zero")
    r = len(k) // 2
    assert np.allclose(out[7 - r : 8 + r, 7 - r : 8 + r], np.outer(k, k), atol=1e-7)


def test_box_blur_known_values():
    img = np.zeros((1, 5, 4), np.float32)
    img[..., 3] = 1
    img[0, 2, :3] = 0.9
    out = box_blur(img, 1)
    assert np.allclose(out[0, :, 0], [0, 0.3, 0.3, 0.3, 0], atol=1e-6)


def test_blur_does_not_darken_edges_next_to_transparency():
    # white opaque left half, fully transparent *black* right half
    img = np.zeros((8, 8, 4), np.float32)
    img[:, :4] = [1, 1, 1, 1]
    out = gaussian_blur(img, 1.5)
    edge = out[4, 4]
    assert 0 < edge[3] < 1  # alpha is soft across the edge ...
    assert np.allclose(edge[:3], 1.0, atol=1e-5)  # ... but the colour stays white (premultiplied blur)


def test_convolve2d_flips_kernel():
    img = np.zeros((5, 5), np.float32)
    img[2, 2] = 1
    k = np.zeros((3, 3), np.float32)
    k[0, 1] = 1  # kernel with a single 1 in its top-middle cell
    out = convolve2d(img, k, "zero")
    assert out[1, 2] == 1 and out.sum() == 1  # convolving an impulse reproduces the kernel's shape
    # correlation (no flip) would have put it below instead: out[3, 2]


def test_unsharp_mask_increases_edge_contrast():
    img = np.zeros((1, 10, 4), np.float32)
    img[..., 3] = 1
    img[0, 5:, :3] = 0.5
    out = unsharp_mask(img, 1.0, amount=1.0)
    assert out[0, 5, 0] > 0.5 and out[0, 4, 0] == 0.0  # overshoot on the bright side, clipped dark side
    assert np.allclose(unsharp_mask(img, 1.0, amount=1.0, threshold=1.0), img)  # threshold skips all
