// Minimal collaboration relay: clients join a room and every message is forwarded
// to the other clients in that room. Payloads are end-to-end encrypted, so the
// server stores nothing and cannot read scenes — it only routes bytes.
//
// Run: npm install ws@8 && node relay-server.ts [port]

import { WebSocketServer, type WebSocket } from "ws";

const port = Number(process.argv[2] ?? 3002);
const rooms = new Map<string, Set<WebSocket>>();
const wss = new WebSocketServer({ port, maxPayload: 2 * 1024 * 1024 }); // reject huge frames

wss.on("connection", (ws, req) => {
  const room = new URL(req.url ?? "/", "http://x").searchParams.get("room");
  if (!room || !/^[A-Za-z0-9_-]{8,64}$/.test(room)) {
    ws.close(1008, "invalid room"); // 1008 = policy violation
    return;
  }
  let peers = rooms.get(room);
  if (!peers) rooms.set(room, (peers = new Set()));
  peers.add(ws);

  ws.on("message", (data, isBinary) => {
    for (const peer of peers!) if (peer !== ws && peer.readyState === peer.OPEN) peer.send(data, { binary: isBinary });
  });
  ws.on("close", () => {
    peers!.delete(ws);
    if (peers!.size === 0) rooms.delete(room);
  });
});

wss.on("listening", () => console.log(`relay listening on ws://localhost:${port}`));
