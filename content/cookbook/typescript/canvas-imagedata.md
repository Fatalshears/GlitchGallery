---
title: Canvas ImageData and Pixel Editing in the Browser
type: cookbook
tags: [cookbook, typescript, browser, graphics]
aliases: [ImageData, getImageData, putImageData, Uint8ClampedArray, OffscreenCanvas]
versions: "Modern browsers (Chrome, Firefox, Safari); Node.js 22.18+ for the self-test"
status: draft
levels: [2]
---

Concepts: [[raster-images-and-pixel-formats]] · [[alpha-compositing]] · [[flood-fill]] · [[layers-and-blend-modes]].

Browser editors (Photopea, Photoshop on the web, Figma) edit pixels either through the 2D canvas API, WebGL/WebGPU, or WebAssembly modules working on the same RGBA byte layout.

## API map

| Need | API |
|---|---|
| Read pixels | `ctx.getImageData(x, y, w, h)` → `ImageData { width, height, data: Uint8ClampedArray }` |
| Write pixels | `ctx.putImageData(imageData, x, y)` (ignores compositing and globalAlpha) |
| Composite with a blend mode | `ctx.globalCompositeOperation = "multiply"`, then `drawImage` |
| Layers | one `OffscreenCanvas` per layer, drawn in order |
| Work off the main thread | `OffscreenCanvas` + Web Worker; transfer `ImageData.data.buffer` |
| Pen input | `pointermove` with `event.pressure`, `event.getCoalescedEvents()` |

Layout: `data[(y * width + x) * 4 + c]`, RGBA, 8-bit, **straight** (not premultiplied) alpha, no row padding. Writes clamp to 0–255 and round to nearest.

## Recipes

> [!mwe] Invert the selected rectangle
> - **Used for:** The read–modify–write loop on canvas pixels.
> - **Input:** A `<canvas id="c">` already showing an image; rectangle 50,50 to 250,200.
> - **Expected output:** That rectangle shows inverted colours; alpha unchanged.
>
> ```ts
> const ctx = (document.getElementById("c") as HTMLCanvasElement).getContext("2d", { willReadFrequently: true })!;
> const img = ctx.getImageData(50, 50, 200, 150);
> const d = img.data;
> for (let i = 0; i < d.length; i += 4) {
>   d[i] = 255 - d[i]; d[i + 1] = 255 - d[i + 1]; d[i + 2] = 255 - d[i + 2];
> }
> ctx.putImageData(img, 50, 50);
> ```

> [!tested] Blend modes and paint bucket — `examples/image-editor/typescript/imagedata-ops.ts`
> - **Used for:** Multiply and Screen blends and a scanline flood fill on `ImageData`-style arrays; runs in Node for testing.
> - **Input:** None for the self-test (it builds small images in memory).
> - **Expected output:** `imagedata-ops: all checks passed`.
>
> ```bash
> node examples/image-editor/typescript/imagedata-ops.ts
> ```

## Gotchas

- `getImageData` on a canvas that drew a **cross-origin image** without CORS throws `SecurityError` (tainted canvas). Serve images with `Access-Control-Allow-Origin` and set `img.crossOrigin = "anonymous"`.
- `putImageData` bypasses `globalAlpha` and `globalCompositeOperation`; draw an intermediate canvas with `drawImage` to composite.
- Canvas stores premultiplied colour internally on most browsers, so `put` then `get` of semi-transparent pixels may not round-trip exactly.
- Reading pixels from a GPU-backed canvas is slow; pass `{ willReadFrequently: true }` when you read often.
- `devicePixelRatio`: a 300 CSS-px canvas on a 2× display needs a 600-px backing store for sharp output.

## References

- MDN, *Pixel manipulation with canvas* — https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial/Pixel_manipulation_with_canvas
- MDN, `OffscreenCanvas` — https://developer.mozilla.org/en-US/docs/Web/API/OffscreenCanvas
- MDN, CORS-enabled images — https://developer.mozilla.org/en-US/docs/Web/HTML/How_to/CORS_enabled_image
