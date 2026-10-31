---
title: Canvas 2D Drawing, Transforms and Input
type: cookbook
tags: [cookbook, typescript, browser, graphics]
aliases: [canvas 2d, devicePixelRatio, pointer events, offscreen canvas cache, render loop]
versions: "Modern browsers (Chrome, Firefox, Safari), TypeScript 5.x"
status: draft
levels: [2]
---

Concepts: [[coordinate-transforms]] · [[vector-graphics-and-scene-model]] · [[hit-testing]] · [[debounce-and-throttle]].

This is the drawing layer of a whiteboard: a crisp canvas on high-DPI screens, a render loop that only redraws when needed, pointer input converted to scene coordinates, and per-element caching.

## API map

| Need | API |
|---|---|
| Context | `canvas.getContext("2d")` |
| Viewport transform | `ctx.setTransform(a, b, c, d, e, f)`, `ctx.save()/restore()`, `translate/rotate/scale` |
| Shapes | `beginPath`, `moveTo`, `lineTo`, `quadraticCurveTo`, `ellipse`, `stroke`, `fill`, `Path2D` |
| Crisp on Retina | backing size = CSS size × `devicePixelRatio` |
| Redraw scheduling | `requestAnimationFrame` |
| Input | `pointerdown/move/up`, `setPointerCapture`, `e.pressure`, `getCoalescedEvents()` |
| Caching | `OffscreenCanvas` or a hidden `<canvas>`, `drawImage` |
| Export | `canvas.toBlob("image/png")`, `OffscreenCanvas.convertToBlob()` |

## Recipes

> [!mwe] High-DPI canvas with a render-on-demand loop
> - **Used for:** A sharp canvas that redraws only after something changed.
> - **Input:** A `<canvas id="board">` sized by CSS; a `draw(ctx)` function that paints the scene in scene units; a `view` viewport object.
> - **Expected output:** Lines are crisp on 2× displays; `invalidate()` called many times in one frame causes exactly one redraw.
>
> ```ts
> const canvas = document.getElementById("board") as HTMLCanvasElement;
> const ctx = canvas.getContext("2d")!;
>
> function resize() {
>   const dpr = window.devicePixelRatio || 1;
>   canvas.width = Math.round(canvas.clientWidth * dpr);     // backing store in device pixels
>   canvas.height = Math.round(canvas.clientHeight * dpr);
>   invalidate();
> }
>
> let scheduled = false;
> function invalidate() {
>   if (scheduled) return;
>   scheduled = true;
>   requestAnimationFrame(() => {
>     scheduled = false;
>     const dpr = window.devicePixelRatio || 1;
>     ctx.setTransform(1, 0, 0, 1, 0, 0);
>     ctx.clearRect(0, 0, canvas.width, canvas.height);
>     const z = view.zoom * dpr;
>     ctx.setTransform(z, 0, 0, z, view.scrollX * z, view.scrollY * z);   // scene units from here on
>     draw(ctx);
>   });
> }
> new ResizeObserver(resize).observe(canvas);
> ```

> [!mwe] Drag to draw a rectangle, in scene coordinates
> - **Used for:** Turning pointer input into a new element.
> - **Input:** The canvas above, `view`, a `scene` with `put`, and `newElement`/`updateElement` from sketchkit.
> - **Expected output:** Dragging creates a rectangle whose corners follow the pointer at any zoom; releasing finishes it; the pointer keeps being tracked outside the canvas.
>
> ```ts
> import { newElement, updateElement } from "./src/elements.ts";
> import { screenToScene } from "./src/viewport.ts";
>
> let drawing: ReturnType<typeof newElement> | null = null;
> let start = { x: 0, y: 0 };
> canvas.addEventListener("pointerdown", (e) => {
>   canvas.setPointerCapture(e.pointerId);
>   start = screenToScene({ x: e.offsetX, y: e.offsetY }, view);
>   drawing = newElement({ id: crypto.randomUUID(), type: "rectangle", x: start.x, y: start.y, index: scene.topIndex() });
>   scene.put(drawing);
> });
> canvas.addEventListener("pointermove", (e) => {
>   if (!drawing) return;
>   const p = screenToScene({ x: e.offsetX, y: e.offsetY }, view);
>   drawing = updateElement(drawing, {
>     x: Math.min(start.x, p.x), y: Math.min(start.y, p.y),       // normalize negative drags
>     width: Math.abs(p.x - start.x), height: Math.abs(p.y - start.y),
>   });
>   scene.put(drawing);
>   invalidate();
> });
> canvas.addEventListener("pointerup", () => { drawing = null; });
> ```

> [!mwe] Per-element bitmap cache
> - **Used for:** Avoiding re-generating sketchy strokes on every pan or zoom frame.
> - **Input:** An element `el` with `id` and `version`, and a function `paint(ctx, el)` that draws it at the origin.
> - **Expected output:** `paint` runs once per element version; later frames reuse the cached bitmap through `drawImage`.
>
> ```ts
> const cache = new Map<string, { version: number; bmp: OffscreenCanvas }>();
> function drawCached(ctx: CanvasRenderingContext2D, el: Element, pad = 4) {
>   let c = cache.get(el.id);
>   if (!c || c.version !== el.version) {
>     const bmp = new OffscreenCanvas(Math.ceil(el.width + 2 * pad), Math.ceil(el.height + 2 * pad));
>     const g = bmp.getContext("2d")!;
>     g.translate(pad - el.x, pad - el.y);
>     paint(g, el);
>     cache.set(el.id, (c = { version: el.version, bmp }));
>   }
>   ctx.drawImage(c.bmp, el.x - pad, el.y - pad);
> }
> ```
> The cache is in scene units, so it blurs at high zoom; real editors re-render at the current zoom level when it changes a lot.

## Gotchas

- Forgetting `devicePixelRatio` makes everything blurry on Retina/HiDPI screens.
- `offsetX/offsetY` are relative to the canvas element's padding box; use `getBoundingClientRect()` if the canvas has borders or CSS transforms.
- Line widths are scaled by the transform — a 1-unit line at zoom 10 is 10 px wide; divide by zoom for constant-width UI strokes (selection outlines).
- Clearing with `clearRect` under a transform clears the wrong area — reset the transform first (as above).
- Very large canvases fail silently (browser limits around 16 384 px per side or 268 M pixels); keep the canvas the size of the viewport.

## References

- MDN, *Canvas tutorial* — https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial
- MDN, *Optimizing canvas* — https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial/Optimizing_canvas
- MDN, `Window.devicePixelRatio` — https://developer.mozilla.org/en-US/docs/Web/API/Window/devicePixelRatio
