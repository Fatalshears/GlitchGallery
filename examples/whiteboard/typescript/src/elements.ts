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

// Default only when a field is absent; an explicit null (what JSON makes of Infinity/NaN) is an error.
const orDefault = <T>(v: unknown, d: T): unknown => (v === undefined ? d : v);

const finite = (v: unknown, name: string): number => {
  if (typeof v !== "number" || !Number.isFinite(v)) throw new Error(`${name} must be a finite number`);
  return v;
};

/**
 * Validate untrusted data (a loaded file or a collaborator's message) and return a clean Element.
 * Missing optional fields get defaults (so older files keep loading); wrong types and
 * non-finite numbers throw. Unknown element types are kept so data from newer versions survives.
 */
export function parseElement(raw: unknown): Element {
  if (typeof raw !== "object" || raw === null) throw new Error("element must be an object");
  const r = raw as Record<string, unknown>;
  if (typeof r.id !== "string" || r.id === "" || r.id.length > 128) throw new Error("id must be a non-empty string");
  if (typeof r.type !== "string") throw new Error("type must be a string");
  const rawPoints = orDefault(r.points, []);
  if (!Array.isArray(rawPoints) || rawPoints.length > 100_000) throw new Error("points must be an array");
  const points = rawPoints.map((p, i) => {
    if (typeof p !== "object" || p === null) throw new Error(`points[${i}] must be an object`);
    return { x: finite((p as Record<string, unknown>).x, `points[${i}].x`), y: finite((p as Record<string, unknown>).y, `points[${i}].y`) };
  });
  const version = orDefault(r.version, 1);
  if (typeof version !== "number" || !Number.isSafeInteger(version) || version < 1) throw new Error("version must be a positive integer");
  const isDeleted = orDefault(r.isDeleted, false);
  if (typeof isDeleted !== "boolean") throw new Error("isDeleted must be a boolean");
  const index = orDefault(r.index, "V");
  if (typeof index !== "string") throw new Error("index must be a string");
  return {
    id: r.id,
    type: r.type as ElementType,
    x: finite(r.x, "x"),
    y: finite(r.y, "y"),
    width: finite(orDefault(r.width, 0), "width"),
    height: finite(orDefault(r.height, 0), "height"),
    angle: finite(orDefault(r.angle, 0), "angle"),
    points,
    seed: finite(orDefault(r.seed, 0), "seed"),
    version,
    versionNonce: finite(orDefault(r.versionNonce, 0), "versionNonce"),
    index,
    isDeleted,
  };
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
    default:
      return false; // element type from a newer version: keep it, but it cannot be picked
  }
}
