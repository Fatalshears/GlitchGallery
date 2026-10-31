import assert from "node:assert/strict";
import { test } from "node:test";
import {
  distanceToSegment, elementBounds, hitTest, newElement, pointInPolygon, rotate, updateElement,
} from "../src/index.ts";

const close = (a: number, b: number, eps = 1e-9) => assert.ok(Math.abs(a - b) < eps, `${a} != ${b}`);
const seq = () => { let i = 0; return () => (++i % 97) / 97; }; // deterministic "random"

test("distance to segment clamps to the endpoints", () => {
  close(distanceToSegment({ x: 5, y: 3 }, { x: 0, y: 0 }, { x: 10, y: 0 }), 3);
  close(distanceToSegment({ x: -3, y: 4 }, { x: 0, y: 0 }, { x: 10, y: 0 }), 5); // beyond a
  close(distanceToSegment({ x: 2, y: 2 }, { x: 1, y: 1 }, { x: 1, y: 1 }), Math.SQRT2); // degenerate
});

test("point in polygon handles concave shapes", () => {
  const L = [{ x: 0, y: 0 }, { x: 10, y: 0 }, { x: 10, y: 4 }, { x: 4, y: 4 }, { x: 4, y: 10 }, { x: 0, y: 10 }];
  assert.equal(pointInPolygon({ x: 2, y: 8 }, L), true);
  assert.equal(pointInPolygon({ x: 8, y: 8 }, L), false); // in the notch
  assert.equal(pointInPolygon({ x: 8, y: 2 }, L), true);
});

test("rotate by 90 degrees", () => {
  const p = rotate({ x: 10, y: 0 }, { x: 0, y: 0 }, Math.PI / 2);
  close(p.x, 0); close(p.y, 10);
});

test("rectangle hit test uses tolerance and undoes rotation", () => {
  const r = newElement({ id: "r", type: "rectangle", x: 0, y: 0, width: 100, height: 20 }, seq());
  assert.equal(hitTest(r, { x: 50, y: 10 }), true);
  assert.equal(hitTest(r, { x: 50, y: 23 }, 4), true);
  assert.equal(hitTest(r, { x: 50, y: 30 }, 4), false);
  const turned = updateElement(r, { angle: Math.PI / 2 }, seq()); // now 20 wide, 100 tall around (50, 10)
  assert.equal(hitTest(turned, { x: 50, y: 50 }, 0), true);
  assert.equal(hitTest(turned, { x: 90, y: 10 }, 0), false);
  const b = elementBounds(turned);
  close(b.minX, 40); close(b.maxX, 60); close(b.minY, -40); close(b.maxY, 60);
});

test("ellipse, line and closed freedraw hit tests", () => {
  const e = newElement({ id: "e", type: "ellipse", x: 0, y: 0, width: 100, height: 50 }, seq());
  assert.equal(hitTest(e, { x: 50, y: 25 }), true);
  assert.equal(hitTest(e, { x: 2, y: 2 }, 0), false); // corner of the box is outside the ellipse
  const line = newElement({ id: "l", type: "line", x: 10, y: 10, points: [{ x: 0, y: 0 }, { x: 100, y: 0 }] }, seq());
  assert.equal(hitTest(line, { x: 60, y: 13 }, 4), true);
  assert.equal(hitTest(line, { x: 60, y: 20 }, 4), false);
  const loop = newElement({
    id: "f", type: "freedraw", x: 0, y: 0,
    points: [{ x: 0, y: 0 }, { x: 40, y: 0 }, { x: 40, y: 40 }, { x: 0, y: 40 }, { x: 0, y: 1 }],
  }, seq());
  assert.equal(hitTest(loop, { x: 20, y: 20 }, 2), true); // inside the closed stroke
});

test("updates return new objects with a bumped version", () => {
  const a = newElement({ id: "a", type: "rectangle", x: 0, y: 0 }, seq());
  const b = updateElement(a, { x: 5 }, seq());
  assert.equal(a.x, 0);
  assert.equal(b.x, 5);
  assert.equal(b.version, a.version + 1);
  assert.equal(hitTest(updateElement(a, { isDeleted: true, width: 10, height: 10 }), { x: 1, y: 1 }), false);
});
