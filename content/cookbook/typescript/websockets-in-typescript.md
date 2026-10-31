---
title: WebSockets in TypeScript (Browser, Node and ws)
type: cookbook
tags: [cookbook, typescript, networking, real-time]
aliases: [websocket client, ws server, reconnecting websocket, binary messages]
versions: "Node.js 22.18+ (built-in WebSocket client), ws 8.x, modern browsers"
status: draft
levels: [2, 3]
---

Concepts: [[websockets]] · [[retry-with-exponential-backoff]] · [[debounce-and-throttle]] · [[conflict-resolution]].

## API map

| Need | Client (browser, Node 22+) | Server (Node, `ws` 8) |
|---|---|---|
| Connect / listen | `new WebSocket(url)` | `new WebSocketServer({ port })` |
| Events | `onopen`, `onmessage`, `onclose`, `onerror` | `wss.on("connection", (ws, req) => …)`, `ws.on("message")` |
| Send | `ws.send(stringOrArrayBuffer)` | `ws.send(data, { binary })` |
| Binary | `ws.binaryType = "arraybuffer"` | `Buffer` / `isBinary` flag |
| Back-pressure | `ws.bufferedAmount` | `ws.bufferedAmount`, `ws.send(…, cb)` |
| Limits | — | `maxPayload` |
| Close | `ws.close(1000, "bye")` | `ws.close(code, reason)`, `ws.terminate()` |

## Recipes

> [!tested] Two clients through a relay — `examples/whiteboard/typescript/relay/`
> - **Used for:** A complete room relay (`relay-server.ts`) and two Node clients that exchange encrypted scene updates (`collab-demo.ts`).
> - **Input:** None for the smoke test; manually: `npm install ws@8`, run the server with a port, then the demo with the server URL.
> - **Expected output:** `relay listening on ws://localhost:3002`; the demo prints both clients' scenes and `converged: both clients show the same scene`.
>
> ```bash
> cd examples/whiteboard/typescript && npm install --no-save ws@8
> node relay/relay-server.ts 3002 &
> node relay/collab-demo.ts ws://localhost:3002
> ```

> [!mwe] Reconnecting client with backoff, outbox and resync
> - **Used for:** Keeping a collaboration connection alive across network drops.
> - **Input:** A WebSocket URL; your `onMessage` handler; `onReconnect`, which should return your full current scene.
> - **Expected output:** Reconnect delays grow 0.5 s, 1 s, 2 s, … up to 30 s with jitter and reset after a successful connection. Messages sent while the socket is not open are queued and flushed on reconnect, followed by the full scene. Messages sent in the moment before the client notices a drop can still be lost, and a relay only forwards to peers connected at that instant — the full-scene resync (harmless to repeat, thanks to `reconcile`) is what actually guarantees convergence.
>
> ```ts
> export function connect(
>   url: string,
>   onMessage: (data: ArrayBuffer | string) => void,
>   onReconnect: () => string | ArrayBuffer,           // e.g. the encrypted full scene
> ) {
>   let ws: WebSocket | null = null;
>   let attempt = 0;
>   let connectedBefore = false;
>   const outbox: (string | ArrayBuffer)[] = [];
>
>   const open = () => {
>     ws = new WebSocket(url);
>     ws.binaryType = "arraybuffer";
>     ws.onopen = () => {
>       attempt = 0;
>       while (outbox.length) ws!.send(outbox.shift()!);
>       if (connectedBefore) ws!.send(onReconnect());    // resync: covers anything lost in the gap
>       connectedBefore = true;
>     };
>     ws.onmessage = (e) => onMessage(e.data);
>     // A failed connect attempt may fire only `error` (Node 22's built-in client) or
>     // `error` then `close` (browsers): retry from both, but only once per socket.
>     let retried = false;
>     const retry = () => {
>       if (retried) return;
>       retried = true;
>       const delay = Math.random() * Math.min(30_000, 500 * 2 ** attempt++);   // full jitter
>       setTimeout(open, delay);
>     };
>     ws.onclose = retry;
>     ws.onerror = retry;
>   };
>   open();
>
>   return {
>     send(msg: string | ArrayBuffer) {
>       if (ws?.readyState === WebSocket.OPEN) ws.send(msg);
>       else outbox.push(msg);                 // safe to resend: reconcile is idempotent
>     },
>   };
> }
> ```

> [!mwe] Typed JSON messages with a discriminated union
> - **Used for:** Distinguishing scene updates from cursor positions safely.
> - **Input:** Raw text from `onmessage`.
> - **Expected output:** `handle` calls the right branch; malformed or unknown messages are ignored instead of crashing.
>
> ```ts
> type Message =
>   | { kind: "scene-update"; elements: unknown[] }
>   | { kind: "cursor"; user: string; x: number; y: number };
>
> function handle(raw: string) {
>   let msg: Message;
>   try { msg = JSON.parse(raw); } catch { return; }
>   switch (msg.kind) {
>     case "scene-update": applyRemote(msg.elements); break;
>     case "cursor": moveCursor(msg.user, msg.x, msg.y); break;
>     default: return;                         // unknown kind from a newer client
>   }
> }
> ```

## Gotchas

- Browsers do not expose ping/pong frames to JavaScript; detect dead connections with app-level heartbeats.
- When a connection *attempt* fails, Node 22's built-in `WebSocket` fired `error` without a following `close` in our tests (browsers fire both) — a reconnect loop driven only by `onclose` stops forever.
- `ws.send` while `CONNECTING` throws `InvalidStateError` — queue instead.
- Check `bufferedAmount` before sending large or frequent messages, or memory grows when the network is slow.
- `ws://` from an `https://` page is blocked (mixed content) — use `wss://`.
- In `ws`, `message` data is a `Buffer` (or array of Buffers); check `isBinary` before decoding as text.
- Socket.IO is *not* plain WebSocket: a Socket.IO server cannot talk to a raw `WebSocket` client.

## References

- MDN, *Writing WebSocket client applications* — https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_client_applications
- `ws` documentation — https://github.com/websockets/ws/blob/master/doc/ws.md
- Node.js, `WebSocket` global — https://nodejs.org/api/globals.html#websocket
