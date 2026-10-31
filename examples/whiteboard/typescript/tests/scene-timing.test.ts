import assert from "node:assert/strict";
import { mock, test } from "node:test";
import { Scene, debounce, keyBetween, newElement, throttle, updateElement } from "../src/index.ts";

function sample(): Scene {
  const s = new Scene();
  s.put(newElement({ id: "back", type: "rectangle", x: 0, y: 0, width: 200, height: 200, index: "F" }));
  s.put(newElement({ id: "front", type: "ellipse", x: 50, y: 50, width: 100, height: 100, index: "V" }));
  s.put(newElement({ id: "far", type: "rectangle", x: 5000, y: 5000, width: 10, height: 10, index: "k" }));
  return s;
}

test("hit returns the topmost element; deleted elements are skipped", () => {
  const s = sample();
  assert.equal(s.hit({ x: 100, y: 100 })!.id, "front");
  assert.equal(s.hit({ x: 10, y: 10 })!.id, "back");
  assert.equal(s.hit({ x: 1000, y: 1000 }), undefined);
  s.put(updateElement(s.get("front")!, { isDeleted: true }));
  assert.equal(s.hit({ x: 100, y: 100 })!.id, "back");
  assert.deepEqual(s.elements.map((e) => e.id), ["back", "far"]);
});

test("box selection takes only fully contained elements", () => {
  const ids = sample().selectInBox({ minX: 40, minY: 40, maxX: 160, maxY: 160 }).map((e) => e.id);
  assert.deepEqual(ids, ["front"]);
});

test("new elements go on top", () => {
  const s = sample();
  const k = s.topIndex();
  assert.ok(k > "k");
  assert.ok(keyBetween("F", "V") > "F");
});

test("JSON round trip and validation", () => {
  const s = sample();
  const copy = Scene.fromJSON(s.toJSON());
  assert.deepEqual(copy.elements, s.elements);
  assert.throws(() => Scene.fromJSON('{"type":"other"}'), /not a sketchkit file/);
  assert.throws(() => Scene.fromJSON('{"type":"sketchkit","version":99,"elements":[]}'), /unsupported/);
});

test("SVG export is deterministic and hand-drawn", () => {
  const s = sample();
  const svg = s.toSVG();
  assert.equal(svg, s.toSVG()); // same seeds → identical output
  assert.match(svg, /^<svg xmlns="http:\/\/www\.w3\.org\/2000\/svg"/);
  assert.equal((svg.match(/<path /g) ?? []).length, 2);
  assert.equal((svg.match(/<ellipse /g) ?? []).length, 1);
});

test("applyRemote reports changed ids", () => {
  const a = sample(), b = sample();
  // b is a copy of a's data so both start identical
  for (const el of a.all.values()) b.put(el);
  const moved = updateElement(a.get("far")!, { x: 0 });
  a.put(moved);
  assert.deepEqual(b.applyRemote([...a.all.values()]), ["far"]);
  assert.equal(b.hit({ x: 5, y: 5005 })!.id, "far");
  assert.equal(b.hit({ x: 5005, y: 5005 }), undefined); // spatial index updated
});

test("throttle: first call immediately, then at most one per interval, trailing call kept", () => {
  mock.timers.enable({ apis: ["setTimeout", "Date"] });
  try {
    const calls: number[] = [];
    const t = throttle((n: number) => calls.push(n), 100);
    t(1); t(2); t(3);
    assert.deepEqual(calls, [1]);
    mock.timers.tick(100);
    assert.deepEqual(calls, [1, 3]); // latest pending value delivered
    mock.timers.tick(50); t(4);
    assert.deepEqual(calls, [1, 3]);
    mock.timers.tick(50);
    assert.deepEqual(calls, [1, 3, 4]);
  } finally {
    mock.timers.reset();
  }
});

test("debounce: one call after the burst ends", () => {
  mock.timers.enable({ apis: ["setTimeout"] });
  try {
    const calls: string[] = [];
    const d = debounce((s: string) => calls.push(s), 300);
    d("a"); mock.timers.tick(200); d("b"); mock.timers.tick(200);
    assert.deepEqual(calls, []);
    mock.timers.tick(100);
    assert.deepEqual(calls, ["b"]);
  } finally {
    mock.timers.reset();
  }
});
