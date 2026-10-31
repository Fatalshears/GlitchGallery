// Seeded pseudo-random numbers and the "hand-drawn" line built from them.

import type { Point } from "./geometry.ts";

/** mulberry32: tiny, fast 32-bit PRNG. Same seed → same sequence on every machine. */
export function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * A sketchy line: the straight segment a–b with its midpoints nudged sideways.
 * The wobble comes from `seed`, so every client and every redraw draws the same
 * strokes — without a seed the shape would shimmer on each frame.
 */
export function sketchyLine(a: Point, b: Point, seed: number, roughness = 1, segments = 4): Point[] {
  const rand = mulberry32(seed);
  const len = Math.hypot(b.x - a.x, b.y - a.y);
  const nx = len ? -(b.y - a.y) / len : 0; // unit normal
  const ny = len ? (b.x - a.x) / len : 0;
  const amp = roughness * Math.min(2, len / 50); // short lines wobble less
  const pts: Point[] = [];
  for (let i = 0; i <= segments; i++) {
    const t = i / segments;
    const off = i === 0 || i === segments ? 0 : (rand() * 2 - 1) * amp;
    pts.push({ x: a.x + (b.x - a.x) * t + nx * off, y: a.y + (b.y - a.y) * t + ny * off });
  }
  return pts;
}
