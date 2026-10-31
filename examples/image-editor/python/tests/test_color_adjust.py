import numpy as np
import pytest

from pixkit import apply_lut, curves_lut, invert_lut, levels_lut, linear_to_srgb, srgb_to_linear, to_float, to_u8
from pixkit.color import premultiply, unpremultiply


def test_srgb_known_values_and_roundtrip():
    assert float(srgb_to_linear(0.5)) == pytest.approx(0.21404, abs=1e-4)
    assert float(linear_to_srgb(0.18)) == pytest.approx(0.46135, abs=1e-4)  # 18 % grey
    x = np.linspace(0, 1, 256, dtype=np.float32)
    assert np.allclose(linear_to_srgb(srgb_to_linear(x)), x, atol=1e-5)


def test_u8_float_roundtrip_and_alpha_added():
    rgb = np.arange(256, dtype=np.uint8).reshape(16, 16, 1).repeat(3, axis=2)
    f = to_float(rgb)
    assert f.shape == (16, 16, 4) and np.all(f[..., 3] == 1)
    assert np.array_equal(to_u8(f)[..., :3], rgb)


def test_premultiply_roundtrip_and_transparent_pixel():
    img = np.array([[[1.0, 0.5, 0.0, 0.5], [0.3, 0.3, 0.3, 0.0]]], np.float32)
    back = unpremultiply(premultiply(img))
    assert np.allclose(back[0, 0], img[0, 0])
    assert np.all(back[0, 1, :3] == 0)  # colour of a fully transparent pixel is undefined -> 0


def test_levels_identity_and_endpoints():
    assert np.array_equal(levels_lut(), np.arange(256, dtype=np.uint8))
    lut = levels_lut(black=50, white=200)
    assert lut[0] == 0 and lut[50] == 0 and lut[200] == 255 and lut[255] == 255
    assert lut[125] == 128  # (125-50)/150*255 = 127.5 -> rounds to 128
    assert levels_lut(gamma=2.0)[128] > 128  # gamma > 1 brightens midtones
    with pytest.raises(ValueError):
        levels_lut(black=200, white=100)


def test_curves_hit_control_points_and_invert():
    lut = curves_lut([(0, 0), (64, 128), (255, 255)])
    assert lut[64] == 128 and lut[0] == 0 and lut[255] == 255
    assert np.all(np.diff(lut.astype(int)) >= 0)  # monotonic for increasing points
    assert invert_lut()[0] == 255 and invert_lut()[255] == 0


def test_apply_lut_leaves_alpha():
    img = np.array([[[10, 20, 30, 40]]], np.uint8)
    out = apply_lut(img, invert_lut())
    assert out.tolist() == [[[245, 235, 225, 40]]]
