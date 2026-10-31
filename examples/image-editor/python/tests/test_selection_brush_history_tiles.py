import numpy as np
import pytest

from pixkit import (
    AddLayer, Document, History, Layer, PixelEdit, SetLayerProps, apply_tiled, combine,
    ellipse_mask, feather, gaussian_blur, magic_wand, paint_stroke, rect_mask, stroke_bbox,
)
from pixkit.brush import spaced_points, stroke_coverage


def two_squares():
    # two white squares on black, separated by a black column; one square slightly off-white
    img = np.zeros((6, 9, 4), np.float32)
    img[..., 3] = 1
    img[1:5, 1:4, :3] = 1.0
    img[1:5, 5:8, :3] = 0.95
    return img


def test_magic_wand_contiguous_vs_global_and_tolerance():
    img = two_squares()
    sel = magic_wand(img, 2, 2, tolerance=32)
    assert sel.sum() == 12 and sel[2, 6] == 0  # only the left square
    assert magic_wand(img, 2, 2, tolerance=32, contiguous=False).sum() == 24  # 0.95*255 is within 32
    assert magic_wand(img, 2, 2, tolerance=5, contiguous=False).sum() == 12


def test_magic_wand_connectivity():
    img = np.zeros((3, 3, 4), np.float32)
    img[0, 0, :3] = img[1, 1, :3] = 1  # diagonal neighbours
    assert magic_wand(img, 0, 0, tolerance=0, connectivity=4).sum() == 1
    assert magic_wand(img, 0, 0, tolerance=0, connectivity=8).sum() == 2


def test_shapes_feather_combine():
    r = rect_mask(10, 10, 2, 2, 6, 6)
    assert r.sum() == 16
    e = ellipse_mask(21, 21, 10.5, 10.5, 5, 5)
    assert e[10, 10] == 1 and e[0, 0] == 0 and e.sum() == pytest.approx(np.pi * 25, rel=0.05)
    f = feather(r, 1.0)
    assert 0 < f[4, 6] < 1 and f.sum() == pytest.approx(16, rel=0.01)
    a, b = rect_mask(4, 4, 0, 0, 2, 4), rect_mask(4, 4, 1, 0, 4, 4)
    assert combine(a, b, "add").sum() == 16
    assert combine(a, b, "intersect").sum() == 4
    assert combine(a, b, "subtract").sum() == 4


def test_spaced_points_are_even_across_segments():
    pts = spaced_points([(0, 0), (3, 0), (10, 0)], 2.0)  # break at x=3 must not reset spacing
    assert [p[0] for p in pts] == pytest.approx([0, 2, 4, 6, 8, 10])


def test_stroke_opacity_caps_overlapping_dabs():
    cov = stroke_coverage([(5, 10), (35, 10)], diameter=8, height=20, width=40, spacing=0.1)
    assert cov.max() == pytest.approx(1.0) and cov[10, 20] == 1.0
    img = np.zeros((20, 40, 4), np.float32)
    img[..., 3] = 1
    out = paint_stroke(img, [(5, 10), (35, 10)], (1, 1, 1), 8, opacity=0.5, spacing=0.1)
    assert out[10, 20, 0] == pytest.approx(0.5)  # not 1.0 despite many overlapping dabs
    soft = stroke_coverage([(20, 10)], 10, 20, 40, hardness=0.0)
    assert soft[10, 20] > 0.9 and 0 < soft[10, 23] < soft[10, 21]


def test_stroke_bbox_contains_all_painted_pixels():
    pts = [(5, 5), (30, 12)]
    y0, y1, x0, x1 = stroke_bbox(pts, 6, 20, 40)
    cov = stroke_coverage(pts, 6, 20, 40)
    inside = np.zeros_like(cov, bool)
    inside[y0:y1, x0:x1] = True
    assert cov[~inside].max() == 0


def test_history_undo_redo_and_branching():
    doc = Document(8, 8)
    doc.new_layer("paint", (0, 0, 0, 1))
    original = doc.layers[0].pixels.copy()
    hist = History(doc)
    invert = PixelEdit(0, (2, 6, 2, 6), lambda p: np.concatenate([1 - p[..., :3], p[..., 3:]], -1), "invert")
    hist.execute(invert)
    edited = doc.layers[0].pixels.copy()
    assert edited[3, 3, 0] == 1 and edited[0, 0, 0] == 0
    assert invert.nbytes == 2 * 4 * 4 * 4 * 4  # before+after, 4x4 px, 4 channels, float32

    assert hist.undo() and np.array_equal(doc.layers[0].pixels, original)
    assert hist.redo() and np.array_equal(doc.layers[0].pixels, edited)

    hist.undo()
    hist.execute(SetLayerProps(0, opacity=0.5))
    assert not hist.redo_stack and not hist.redo()  # new edit discarded the redo branch
    hist.undo()
    assert doc.layers[0].opacity == 1.0


def test_history_limit_and_add_layer():
    doc = Document(2, 2)
    hist = History(doc, limit=3)
    for i in range(5):
        hist.execute(AddLayer(Layer(f"l{i}", np.zeros((2, 2, 4), np.float32))))
    assert len(doc.layers) == 5 and len(hist.undo_stack) == 3
    while hist.undo():
        pass
    assert [l.name for l in doc.layers] == ["l0", "l1"]  # the two oldest steps can no longer be undone


@pytest.mark.parametrize("tile", [7, 32, 100])
def test_tiled_blur_matches_whole_image(tile):
    rng = np.random.default_rng(0)
    img = rng.random((61, 83, 4), dtype=np.float32)
    whole = gaussian_blur(img, 2.0)
    tiled = apply_tiled(img, lambda t: gaussian_blur(t, 2.0), tile=tile, halo=6, workers=4)
    assert np.allclose(tiled, whole, atol=1e-6)
    if tile < min(img.shape[:2]):  # with a single tile there are no seams to get wrong
        seams = apply_tiled(img, lambda t: gaussian_blur(t, 2.0), tile=tile, halo=0)
        assert not np.allclose(seams, whole, atol=1e-3)  # without a halo, tile borders are wrong
