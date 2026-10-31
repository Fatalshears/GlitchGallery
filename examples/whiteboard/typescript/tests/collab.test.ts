import assert from "node:assert/strict";
import { test } from "node:test";
import {
  type Element, decryptJSON, encryptJSON, exportKey, generateKey, importKey, keyBetween, mulberry32,
  newElement, parseShareFragment, reconcile, updateElement, winner,
} from "../src/index.ts";

test("keyBetween: always strictly between, under random insertion", () => {
  const rand = mulberry32(5);
  const keys: string[] = [keyBetween(null, null)];
  for (let i = 0; i < 2000; i++) {
    const pos = Math.floor(rand() * (keys.length + 1)); // insert before keys[pos]
    const k = keyBetween(keys[pos - 1] ?? null, keys[pos] ?? null);
    keys.splice(pos, 0, k);
  }
  for (let i = 1; i < keys.length; i++) assert.ok(keys[i - 1] < keys[i], `${keys[i - 1]} < ${keys[i]}`);
  assert.ok(Math.max(...keys.map((k) => k.length)) < 40);
  assert.throws(() => keyBetween("b", "a"));
});

test("winner: higher version, then lower nonce", () => {
  const base = newElement({ id: "x", type: "rectangle", x: 0, y: 0 });
  const v2 = { ...base, version: 2, versionNonce: 900 };
  const v2b = { ...base, version: 2, versionNonce: 100 };
  const v3 = { ...base, version: 3, versionNonce: 999 };
  assert.equal(winner(v2, v3), v3);
  assert.equal(winner(v2, v2b), v2b);
  assert.equal(winner(v2b, v2), v2b); // symmetric
});

test("deletion is a tombstone that wins like any edit", () => {
  const a = newElement({ id: "a", type: "rectangle", x: 0, y: 0 });
  const deleted = updateElement(a, { isDeleted: true });
  const merged = reconcile(new Map([["a", a]]), [deleted]);
  assert.equal(merged.get("a")!.isDeleted, true);
  const stale = reconcile(new Map([["a", deleted]]), [a]); // old copy arriving late
  assert.equal(stale.get("a")!.isDeleted, true);
});

test("the element being edited locally is not overwritten", () => {
  const a = newElement({ id: "a", type: "rectangle", x: 0, y: 0 });
  const mine = updateElement(a, { x: 50 });
  const theirs = updateElement(updateElement(a, { x: -50 }), { x: -60 });
  assert.equal(reconcile(new Map([["a", mine]]), [theirs], { editingId: "a" }).get("a")!.x, 50);
  assert.equal(reconcile(new Map([["a", mine]]), [theirs]).get("a")!.x, -60);
});

test("replicas converge whatever order updates arrive in", () => {
  const rand = mulberry32(9);
  const replicas = [new Map<string, Element>(), new Map<string, Element>(), new Map<string, Element>()];
  const log: Element[] = [];
  for (let step = 0; step < 300; step++) {
    const r = replicas[Math.floor(rand() * replicas.length)];
    const id = `e${Math.floor(rand() * 8)}`;
    const cur = r.get(id);
    const el = cur
      ? updateElement(cur, rand() < 0.15 ? { isDeleted: true } : { x: Math.round(rand() * 100) }, rand)
      : newElement({ id, type: "rectangle", x: 0, y: 0 }, rand);
    r.set(id, el);
    log.push(el);
  }
  // deliver the whole log to every replica, each in a different shuffled order
  const finals = replicas.map((r) => {
    const shuffled = [...log].sort(() => rand() - 0.5);
    return reconcile(r, shuffled);
  });
  const canon = (m: Map<string, Element>) => JSON.stringify([...m].sort(([a], [b]) => (a < b ? -1 : 1)));
  assert.equal(canon(finals[0]), canon(finals[1]));
  assert.equal(canon(finals[1]), canon(finals[2]));
});

test("AES-GCM round trip, wrong key and tampering fail", async () => {
  const key = await generateKey();
  const k = await exportKey(key);
  assert.match(k, /^[A-Za-z0-9_-]{22}$/); // 128-bit key as base64url
  const scene = { elements: [{ id: "a", x: 1 }] };
  const { iv, data } = await encryptJSON(key, scene);
  assert.deepEqual(await decryptJSON(await importKey(k), iv, data), scene);
  await assert.rejects(decryptJSON(await generateKey(), iv, data));
  data[0] ^= 1;
  await assert.rejects(decryptJSON(key, iv, data));
  const again = await encryptJSON(key, scene);
  assert.notDeepEqual(again.iv, iv); // fresh IV every message
});

test("share links keep the key in the fragment", () => {
  assert.deepEqual(parseShareFragment("#json=abc123,Zm9vYmFy-_"), { id: "abc123", key: "Zm9vYmFy-_" });
  assert.equal(parseShareFragment("#room=abc"), null);
  assert.equal(new URL("https://example.app/#json=abc,KEY").search, ""); // never part of the request
});
