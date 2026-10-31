// Scene elements: immutable records with collaboration metadata.

import { type Box, type Point, boxOfPoints, distanceToSegment, pointInPolygon, rotate } from "./geometry.ts";

export type ElementType = "rectangle" | "ellipse" | "line" | "freedraw";

export interface Element {
  readonly id: string;
  readonly type: ElementType;
  readonly x: number; // top-left of the unrotated bounding box
  readonly y: number;
  readonly width: number;
  readonly height: number;
  readonly angle: number; // radians, around the box centre
  readonly points: readonly Point[]; // line/freedraw, relative to (x, y)
  readonly seed: number; // makes the hand-drawn wobble reproducible
  readonly version: number; // incremented on every change
  readonly versionNonce: number; // random, breaks ties between concurrent edits
  readonly index: string; // fractional z-order key
  readonly isDeleted: boolean; // tombstone, so deletions sync like edits
}

export type Random = () => number;

export function newElement(
  init: Pick<Element, "id" | "type" | "x" | "y"> & Partial<Element>,
  random: Random = Math.random,
): Element {
  return {
    width: 0, height: 0, angle: 0, points: [], index: "V", isDeleted: false,
    seed: Math.floor(random() * 2 ** 31), version: 1, versionNonce: Math.floor(random() * 2 ** 31),
    ...init,
  };
}

/** Return a changed copy with version bumped — never mutate an element in place. */
export function updateElement(el: Element, changes: Partial<Element>, random: Random = Math.random): Element {
  return { ...el, ...changes, version: el.version + 1, versionNonce: Math.floor(random() * 2 ** 31) };
}

export const center = (el: Element): Point => ({ x: el.x + el.width / 2, y: el.y + el.height / 2 });

/** Corners (rectangle) or absolute points (line/freedraw) after rotation. */
export function outline(el: Element): Point[] {
  const c = center(el);
  const raw =
    el.type === "line" || el.type === "freedraw"
      ? el.points.map((p) => ({ x: el.x + p.x, y: el.y + p.y }))
      : [
          { x: el.x, y: el.y },
          { x: el.x + el.width, y: el.y },
          { x: el.x + el.width, y: el.y + el.height },
          { x: el.x, y: el.y + el.height },
        ];
  return el.angle ? raw.map((p) => rotate(p, c, el.angle)) : raw;
}

/** Axis-aligned bounds of the rotated element (used by the spatial index and box selection). */
export const elementBounds = (el: Element): Box => boxOfPoints(outline(el));

/**
 * Does a click at p (scene coordinates) hit the element? `tolerance` is in scene units —
 * divide a screen-pixel tolerance by the zoom so hit areas feel the same at every zoom.
 */
export function hitTest(el: Element, p: Point, tolerance = 4): boolean {
  if (el.isDeleted) return false;
  // Undo the element's rotation instead of rotating its geometry.
  const q = el.angle ? rotate(p, center(el), -el.angle) : p;
  switch (el.type) {
    case "rectangle":
      return (
        q.x >= el.x - tolerance && q.x <= el.x + el.width + tolerance &&
        q.y >= el.y - tolerance && q.y <= el.y + el.height + tolerance
      );
    case "ellipse": {
      const rx = el.width / 2 + tolerance;
      const ry = el.height / 2 + tolerance;
      const c = center(el);
      return ((q.x - c.x) / rx) ** 2 + ((q.y - c.y) / ry) ** 2 <= 1;
    }
    case "line":
    case "freedraw": {
      const pts = el.points.map((pt) => ({ x: el.x + pt.x, y: el.y + pt.y }));
      if (pts.length === 1) return Math.hypot(q.x - pts[0].x, q.y - pts[0].y) <= tolerance;
      for (let i = 1; i < pts.length; i++) if (distanceToSegment(q, pts[i - 1], pts[i]) <= tolerance) return true;
      // A closed freehand loop also counts as hit inside it.
      return el.type === "freedraw" && pts.length > 2 && pointInPolygon(q, pts);
    }
  }
}
