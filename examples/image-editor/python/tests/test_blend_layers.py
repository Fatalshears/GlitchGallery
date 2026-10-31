import numpy as np
import pytest

from pixkit import BLEND_MODES, Document, composite, solid


def px(r, g, b, a=1.0):
    return np.array([[[r, g, b, a]]], np.float32)


@pytest.mark.parametrize(
    "mode,cb,cs,expected",
    [
        ("normal", 0.2, 0.7, 0.7),
        ("multiply", 0.5, 0.5, 0.25),
        ("multiply", 0.6, 1.0, 0.6),  # white is neutral for multiply
        ("screen", 0.5, 0.5, 0.75),
        ("screen", 0.6, 0.0, 0.6),  # black is neutral for screen
        ("overlay", 0.25, 0.5, 0.25),  # 50 % grey is neutral for overlay
        ("overlay", 0.25, 0.8, 0.4),  # cb <= .5: 2*cb*cs
        ("darken", 0.3, 0.6, 0.3),
        ("lighten", 0.3, 0.6, 0.6),
        ("difference", 0.3, 0.8, 0.5),
        ("color-dodge", 0.5, 0.5, 1.0),
        ("color-burn", 0.5, 0.5, 0.0),
        ("linear-dodge", 0.7, 0.6, 1.0),
    ],
)
def test_blend_modes_opaque(mode, cb, cs, expected):
    out = composite(px(cb, cb, cb), px(cs, cs, cs), mode)
    assert out[0, 0, 0] == pytest.approx(expected, abs=1e-6) and out[0, 0, 3] == 1


def test_opacity_and_mask_mix_linearly():
    out = composite(px(0, 0, 0), px(1, 1, 1), opacity=0.5)
    assert out[0, 0, 0] == pytest.approx(0.5)
    out = composite(px(0, 0, 0), px(1, 1, 1), mask=np.array([[0.25]], np.float32))
    assert out[0, 0, 0] == pytest.approx(0.25)


def test_source_over_with_transparency():
    assert np.allclose(composite(px(0.2, 0.4, 0.6), px(1, 1, 1, 0.0)), px(0.2, 0.4, 0.6))
    assert np.allclose(composite(px(0, 0, 0, 0.0), px(0.9, 0.1, 0.1, 0.5)), px(0.9, 0.1, 0.1, 0.5))
    out = composite(px(0, 0, 1, 0.5), px(1, 0, 0, 0.5))  # two half-transparent layers
    assert out[0, 0, 3] == pytest.approx(0.75)
    assert out[0, 0, :3] == pytest.approx([2 / 3, 0, 1 / 3], abs=1e-6)


def test_blend_mode_ignored_where_backdrop_is_transparent():
    # multiply over nothing shows the source unchanged
    assert np.allclose(composite(px(0, 0, 0, 0), px(0.8, 0.5, 0.2), "multiply"), px(0.8, 0.5, 0.2))


def test_unknown_mode():
    with pytest.raises(ValueError):
        composite(px(0, 0, 0), px(1, 1, 1), "nope")
    assert len(BLEND_MODES) >= 10


def test_document_flatten_order_visibility_mask():
    doc = Document(2, 1)
    doc.new_layer("bg", (1, 1, 1, 1))
    top = doc.new_layer("red", (1, 0, 0, 1))
    assert np.allclose(doc.flatten()[0, 0], [1, 0, 0, 1])
    top.visible = False
    assert np.allclose(doc.flatten()[0, 0], [1, 1, 1, 1])
    top.visible, top.mask = True, np.array([[1.0, 0.0]], np.float32)
    flat = doc.flatten()
    assert np.allclose(flat[0, 0], [1, 0, 0, 1]) and np.allclose(flat[0, 1], [1, 1, 1, 1])
    top.blend, top.mask = "multiply", None
    assert np.allclose(doc.flatten()[0, 0], [1, 0, 0, 1])  # red × white = red
    assert np.allclose(Document(3, 2).flatten(), solid(2, 3))
