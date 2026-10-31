import assert from "node:assert/strict";
import { test } from "node:test";
import { GridIndex, mulberry32, pan, sceneToScreen, screenToScene, sketchyLine, visibleScene, zoomAt } from "../src/index.ts";

const close = (a: number, b: number, eps = 1e-9) => assert.ok(Math.abs(a - b) < eps, `${a} != ${b}`);

test("screen and scene coordinates round-trip", () => {
  const v = { scrollX: -120, scrollY: 35, zoom: 1.75 };
  const p = { x: 412, y: 233 };
  const back = sceneToScreen(screenToScene(p, v), v);
  close(back.x, p.x); close(back.y, p.y);
});

test("zoomAt keeps the point under the cursor fixed", () => {
  const v = { scrollX: 10, scrollY: -20, zoom: 1 };
  const cursor = { x: 300, y: 200 };
  const before = screenToScene(cursor, v);
  const z = zoomAt(v, cursor, 2.5);
  const after = screenToScene(cursor, z);
  close(z.zoom, 2.5); close(after.x, before.x); close(after.y, before.y);
  assert.equal(zoomAt(v, cursor, 1000).zoom, 30); // clamped to MAX_ZOOM
});

test("pan moves by screen pixels at any zoom", () => {
  const v = pan({ scrollX: 0, scrollY: 0, zoom: 2 }, 100, 0);
  close(sceneToScreen({ x: 0, y: 0 }, v).x, 100);
  const r = visibleScene({ scrollX: 0, scrollY: 0, zoom: 2 }, 800, 600);
  assert.deepEqual(r, { minX: 0, minY: 0, maxX: 400, maxY: 300 });
});

test("seeded random is reproducible and in [0, 1)", () => {
  const a = mulberry32(42), b = mulberry32(42), c = mulberry32(43);
  const xs = Array.from({ length: 1000 }, a);
  assert.deepEqual(xs.slice(0, 5), Array.from({ length: 5 }, b));
  assert.notEqual(xs[0], c());
  assert.ok(xs.every((x) => x >= 0 && x < 1));
  const mean = xs.reduce((s, x) => s + x, 0) / xs.length;
  assert.ok(Math.abs(mean - 0.5) < 0.05);
});

test("sketchy line: fixed endpoints, same seed same wobble", () => {
  const a = { x: 0, y: 0 }, b = { x: 200, y: 0 };
  const l1 = sketchyLine(a, b, 7), l2 = sketchyLine(a, b, 7), l3 = sketchyLine(a, b, 8);
  assert.deepEqual(l1, l2);
  assert.notDeepEqual(l1, l3);
  assert.deepEqual(l1[0], a); assert.deepEqual(l1.at(-1), b);
  assert.ok(l1.some((p) => p.y !== 0) && l1.every((p) => Math.abs(p.y) <= 2));
});

test("grid index matches brute force", () => {
  const rand = mulberry32(1);
  const idx = new GridIndex(64);
  const boxes = new Map<string, { minX: number; minY: number; maxX: number; maxY: number }>();
  for (let i = 0; i < 300; i++) {
    const x = rand() * 2000 - 1000, y = rand() * 2000 - 1000;
    const b = { minX: x, minY: y, maxX: x + rand() * 300, maxY: y + rand() * 300 };
    boxes.set(`e${i}`, b); idx.insert(`e${i}`, b);
  }
  for (let i = 0; i < 100; i += 3) { idx.remove(`e${i}`); boxes.delete(`e${i}`); }
  for (let q = 0; q < 50; q++) {
    const x = rand() * 2000 - 1000, y = rand() * 2000 - 1000;
    const box = { minX: x, minY: y, maxX: x + 150, maxY: y + 150 };
    const expected = [...boxes].filter(([, b]) => b.minX <= box.maxX && b.maxX >= box.minX && b.minY <= box.maxY && b.maxY >= box.minY).map(([id]) => id).sort();
    assert.deepEqual([...idx.query(box)].sort(), expected);
  }
  assert.equal(idx.size, boxes.size);
});
