// Pixel operations on RGBA bytes, the layout of a browser canvas ImageData
// (Uint8ClampedArray, 4 bytes per pixel, row-major).
// Run the self-test: node imagedata-ops.ts   (Node.js >= 22.18)

export type RGBA = Uint8ClampedArray;

/** Multiply blend of two same-sized opaque images: result = a × b / 255. */
export function multiply(a: RGBA, b: RGBA): RGBA {
  const out = new Uint8ClampedArray(a.length);
  for (let i = 0; i < a.length; i += 4) {
    for (let c = 0; c < 3; c++) out[i + c] = (a[i + c] * b[i + c]) / 255;  // ImageData arrays round to nearest on store
    out[i + 3] = 255;
  }
  return out;
}

/** Screen blend: result = 255 − (255 − a)(255 − b) / 255. Always lightens. */
export function screen(a: RGBA, b: RGBA): RGBA {
  const out = new Uint8ClampedArray(a.length);
  for (let i = 0; i < a.length; i += 4) {
    for (let c = 0; c < 3; c++) out[i + c] = 255 - ((255 - a[i + c]) * (255 - b[i + c])) / 255;
    out[i + 3] = 255;
  }
  return out;
}

/**
 * Paint-bucket fill: replace the 4-connected region of pixels whose RGB is within
 * `tolerance` of the seed pixel. Scanline algorithm with an explicit stack, so a
 * huge region cannot overflow the call stack. Returns the number of pixels filled.
 */
export function floodFill(
  data: RGBA, width: number, height: number, x: number, y: number,
  fill: [number, number, number, number], tolerance = 0,
): number {
  const seed = (y * width + x) * 4;
  const target = [data[seed], data[seed + 1], data[seed + 2]];
  const done = new Uint8Array(width * height);
  const matches = (p: number) =>
    !done[p] &&
    Math.max(
      Math.abs(data[p * 4] - target[0]),
      Math.abs(data[p * 4 + 1] - target[1]),
      Math.abs(data[p * 4 + 2] - target[2]),
    ) <= tolerance;

  let filled = 0;
  const stack: number[] = [x, y];
  while (stack.length) {
    const sy = stack.pop()!;
    let sx = stack.pop()!;
    if (!matches(sy * width + sx)) continue;
    while (sx > 0 && matches(sy * width + sx - 1)) sx--;  // walk to the left end of the run
    let spanUp = false;
    let spanDown = false;
    for (; sx < width && matches(sy * width + sx); sx++) {
      const p = sy * width + sx;
      done[p] = 1;
      data.set(fill, p * 4);
      filled++;
      // Push one seed per contiguous run in the rows above and below.
      if (sy > 0) {
        const up = matches(p - width);
        if (up && !spanUp) stack.push(sx, sy - 1);
        spanUp = up;
      }
      if (sy < height - 1) {
        const down = matches(p + width);
        if (down && !spanDown) stack.push(sx, sy + 1);
        spanDown = down;
      }
    }
  }
  return filled;
}

// ── self-test ──
if (import.meta.url === `file://${process.argv[1]}`) {
  const px = (...v: number[]) => new Uint8ClampedArray(v);
  const assert = (ok: boolean, msg: string) => { if (!ok) throw new Error(msg); };

  assert(multiply(px(128, 255, 0, 255), px(128, 128, 255, 255)).join() === "64,128,0,255", "multiply");
  assert(screen(px(128, 0, 255, 255), px(128, 0, 0, 255)).join() === "192,0,255,255", "screen");

  // 6x4 image: white border ring with a black 4x2 hole inside, plus a separate black pixel at (5,3)
  const w = 6, h = 4;
  const img = new Uint8ClampedArray(w * h * 4).fill(255);
  for (const [x, y] of [[1, 1], [2, 1], [3, 1], [4, 1], [1, 2], [2, 2], [3, 2], [4, 2], [5, 3]]) img.set([0, 0, 0, 255], (y * w + x) * 4);
  const n = floodFill(img, w, h, 2, 1, [255, 0, 0, 255]);
  assert(n === 8, `filled ${n}, expected 8`);
  assert(img[(3 * w + 5) * 4] === 0, "unconnected pixel must stay black");
  assert(floodFill(img, w, h, 0, 0, [0, 0, 255, 255]) === 15, "white region (24 - 9 = 15 px)");
  console.log("imagedata-ops: all checks passed");
}
