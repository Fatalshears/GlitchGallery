// Two clients edit the same scene concurrently through the relay and converge.
// Uses Node 22's built-in WebSocket client and the sketchkit engine.
//
// Run (with the relay running): node collab-demo.ts [ws://localhost:3002]

import { isDeepStrictEqual } from "node:util";
import {
  Scene, decryptJSON, encryptJSON, exportKey, generateKey, importKey, newElement, updateElement,
  type Element,
} from "../src/index.ts";

const url = process.argv[2] ?? "ws://localhost:3002";
const room = "demo-room-" + Math.random().toString(36).slice(2, 10);

const key = await generateKey();
const shared = await exportKey(key); // in a real app: carried in the share link's #fragment

type Client = { name: string; scene: Scene; ws: WebSocket; received: number };

async function connect(name: string): Promise<Client> {
  const k = await importKey(shared);
  const ws = new WebSocket(`${url}/?room=${room}`);
  ws.binaryType = "arraybuffer";
  const client: Client = { name, scene: new Scene(), ws, received: 0 };
  ws.onmessage = async (ev) => {
    const buf = new Uint8Array(ev.data as ArrayBuffer);
    const elements = await decryptJSON<Element[]>(k, buf.slice(0, 12), buf.slice(12)); // [iv | ciphertext]
    client.scene.applyRemote(elements);
    client.received++;
  };
  await new Promise((ok, fail) => { ws.onopen = ok; ws.onerror = fail; });
  return client;
}

async function broadcast(c: Client, elements: Element[]) {
  const { iv, data } = await encryptJSON(key, elements);
  const frame = new Uint8Array(iv.length + data.length);
  frame.set(iv); frame.set(data, iv.length);
  c.ws.send(frame);
}

const alice = await connect("alice");
const bob = await connect("bob");

// Alice draws a box; Bob receives it.
const box = newElement({ id: "box", type: "rectangle", x: 0, y: 0, width: 100, height: 60 });
alice.scene.put(box);
await broadcast(alice, [box]);
await new Promise((r) => setTimeout(r, 200));

// Both edit the same element concurrently from the same version; then Bob deletes nothing,
// Alice adds a second element. Last-writer-wins resolves the conflict identically on both.
const aliceMove = updateElement(alice.scene.get("box")!, { x: 40 });
const bobResize = updateElement(bob.scene.get("box")!, { width: 300 });
alice.scene.put(aliceMove);
bob.scene.put(bobResize);
const circle = newElement({ id: "circle", type: "ellipse", x: 200, y: 0, width: 50, height: 50, index: alice.scene.topIndex() });
alice.scene.put(circle);
await Promise.all([broadcast(alice, [aliceMove, circle]), broadcast(bob, [bobResize])]);
await new Promise((r) => setTimeout(r, 300));

const same = isDeepStrictEqual(alice.scene.elements, bob.scene.elements); // content, not key order
console.log(`alice: ${alice.scene.elements.map((e) => `${e.id}@x=${e.x},w=${e.width}`).join(" ")}`);
console.log(`bob:   ${bob.scene.elements.map((e) => `${e.id}@x=${e.x},w=${e.width}`).join(" ")}`);
console.log(same ? "converged: both clients show the same scene" : "DIVERGED");
alice.ws.close(); bob.ws.close();
process.exit(same ? 0 : 1);
