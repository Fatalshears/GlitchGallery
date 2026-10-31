---
title: Image Processing with NumPy and Pillow
type: cookbook
tags: [cookbook, python, graphics, numpy]
aliases: [numpy image, pillow numpy, vectorized image processing]
versions: "Python 3.10+, NumPy 1.24+ (tested with 2.x), Pillow 10+"
status: draft
levels: [2]
---

Concepts: [[raster-images-and-pixel-formats]] · [[alpha-compositing]] · [[convolution-and-kernels]] · [[lookup-tables]] · [[tiled-image-processing]].

## API map

| Need | API |
|---|---|
| Read / write files | `Image.open(p).convert("RGBA")`, `np.asarray(im)`, `Image.fromarray(arr, "RGBA").save(p)` |
| Convert type | `arr.astype(np.float32) / 255`, `np.clip(np.rint(f * 255), 0, 255).astype(np.uint8)` |
| Per-pixel maths | broadcasting: `img[..., :3] * img[..., 3:4]` |
| Conditional | `np.where(cond, a, b)` |
| Lookup table | fancy indexing `lut[img_u8]` |
| Neighbourhood | slicing shifted views of a padded array; `np.pad(mode="edge"/"reflect")` |
| Coordinates | `ys, xs = np.mgrid[0:h, 0:w]` |
| Histogram | `np.bincount(channel.ravel(), minlength=256)` |
| Parallel | `ThreadPoolExecutor` over tiles (NumPy releases the GIL in big operations) |

## Recipes

> [!mwe] Load, brighten through a LUT, save
> - **Used for:** The complete file-to-file loop with the fastest per-value operation.
> - **Input:** `in.png` (any mode; converted to RGBA).
> - **Expected output:** `out.png` with midtones brightened (gamma 0.8) and alpha unchanged.
>
> ```python
> import numpy as np
> from PIL import Image
>
> img = np.asarray(Image.open("in.png").convert("RGBA")).copy()   # copy: asarray may be read-only
> lut = np.clip(np.rint(255 * (np.arange(256) / 255) ** 0.8), 0, 255).astype(np.uint8)
> img[..., :3] = lut[img[..., :3]]
> Image.fromarray(img, "RGBA").save("out.png")
> ```

> [!mwe] Vectorized compositing (Multiply blend, opaque images)
> - **Used for:** Replacing a per-pixel Python loop with one array expression.
> - **Input:** Two float32 `(H, W, 3)` arrays `a`, `b` in [0, 1] with the same shape.
> - **Expected output:** `(H, W, 3)` array `a * b`; runs about 100× faster than a nested Python loop on a 1-megapixel image.
>
> ```python
> out = a * b                                       # vectorized
> # equivalent slow loop:
> # for y in range(h):
> #     for x in range(w):
> #         out[y, x] = a[y, x] * b[y, x]
> ```

> [!mwe] 3×3 neighbourhood with shifted slices
> - **Used for:** Writing a neighbourhood filter without any Python loop over pixels.
> - **Input:** A float32 `(H, W)` or `(H, W, C)` array `img`.
> - **Expected output:** `out`, the 3×3 mean of every pixel, same shape, edges clamped.
>
> ```python
> p = np.pad(img, [(1, 1), (1, 1)] + [(0, 0)] * (img.ndim - 2), mode="edge")
> h, w = img.shape[:2]
> out = sum(p[dy:dy + h, dx:dx + w] for dy in range(3) for dx in range(3)) / 9
> ```

> [!tested] Full reference — `examples/image-editor/python/pixkit`
> - **Used for:** Running every recipe on this page together as a tested library and command-line tool.
> - **Input:** For the CLI: an input image path, an output path, and options.
> - **Expected output:** `42 passed` from pytest; the CLI prints `wrote out.png (WxH)`.
>
> ```bash
> cd examples/image-editor/python
> python -m pip install numpy pytest Pillow
> python -m pytest -q
> python -m pixkit in.png out.png --levels 10,245,1.2 --blur 1.5 --sharpen 1.0,0.8
> ```

## Gotchas

- **Integer overflow:** `uint8` arithmetic wraps silently (`np.uint8(200) + np.uint8(100) == 44`). Convert to float or `int16` first.
- **`[y, x]` indexing**, while Pillow and most APIs use `(x, y)`; shape is `(height, width, channels)`.
- `np.asarray(pil_image)` can return a **read-only** array; `.copy()` before writing.
- Views vs copies: slicing returns a view — writing to it changes the original (useful for in-place region edits, dangerous by accident).
- `float64` is NumPy's default; use `float32` explicitly to halve memory.
- Pillow's `Image.fromarray` needs `uint8` for 8-bit modes; floats raise or produce garbage.

## References

- NumPy, *Broadcasting* — https://numpy.org/doc/stable/user/basics.broadcasting.html
- Pillow, *Image module* — https://pillow.readthedocs.io/en/stable/reference/Image.html
- scikit-image (higher-level algorithms on NumPy arrays) — https://scikit-image.org/
