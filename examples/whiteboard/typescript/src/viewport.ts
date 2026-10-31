// Infinite canvas: map between screen pixels and scene coordinates.
//   screen = (scene + scroll) * zoom        scene = screen / zoom - scroll

import type { Point } from "./geometry.ts";

export interface Viewport {
  readonly scrollX: number;
  readonly scrollY: number;
  readonly zoom: number;
}

export const MIN_ZOOM = 0.1;
export const MAX_ZOOM = 30;

export const sceneToScreen = (p: Point, v: Viewport): Point => ({
  x: (p.x + v.scrollX) * v.zoom,
  y: (p.y + v.scrollY) * v.zoom,
});

export const screenToScene = (p: Point, v: Viewport): Point => ({
  x: p.x / v.zoom - v.scrollX,
  y: p.y / v.zoom - v.scrollY,
});

/** Pan by a screen-space delta (e.g. a drag of dx, dy pixels). */
export const pan = (v: Viewport, dx: number, dy: number): Viewport => ({
  ...v,
  scrollX: v.scrollX + dx / v.zoom,
  scrollY: v.scrollY + dy / v.zoom,
});

/** Zoom by `factor` keeping the scene point under the cursor fixed on screen. */
export function zoomAt(v: Viewport, cursor: Point, factor: number): Viewport {
  const zoom = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, v.zoom * factor));
  const anchor = screenToScene(cursor, v);
  // Solve (anchor + scroll') * zoom = cursor for scroll'.
  return { zoom, scrollX: cursor.x / zoom - anchor.x, scrollY: cursor.y / zoom - anchor.y };
}

/** Scene-space rectangle currently visible in a screen of width × height pixels. */
export function visibleScene(v: Viewport, width: number, height: number) {
  const a = screenToScene({ x: 0, y: 0 }, v);
  const b = screenToScene({ x: width, y: height }, v);
  return { minX: a.x, minY: a.y, maxX: b.x, maxY: b.y };
}
