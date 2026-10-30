// Minimal segmented downloader for Node.js >= 22 (built-in fetch, no dependencies).
// Run: node segmented-download.ts <url> <dest> [connections]
// Node 22.18+ strips TypeScript types natively; older 22.x needs --experimental-strip-types.
//
// Scope: parallel Range requests + positional writes + retry. No pause/resume state,
// no rate limit - see the Python reference implementation for those.

import { open, rename } from "node:fs/promises";

type Range = { start: number; end: number }; // inclusive

async function probe(url: string): Promise<{ total: number; ranges: boolean }> {
  const res = await fetch(url, { headers: { Range: "bytes=0-0" } });
  await res.body?.cancel(); // we only need headers
  if (res.status === 206) {
    const total = Number(res.headers.get("content-range")?.split("/")[1]);
    return { total, ranges: Number.isFinite(total) };
  }
  if (!res.ok) throw new Error(`probe failed: HTTP ${res.status}`);
  return { total: Number(res.headers.get("content-length") ?? NaN), ranges: false };
}

function split(total: number, parts: number): Range[] {
  const size = Math.ceil(total / parts);
  const out: Range[] = [];
  for (let s = 0; s < total; s += size) out.push({ start: s, end: Math.min(s + size, total) - 1 });
  return out;
}

async function fetchRange(url: string, r: Range, file: Awaited<ReturnType<typeof open>>) {
  let offset = r.start;
  for (let attempt = 0; ; attempt++) {
    try {
      const res = await fetch(url, { headers: { Range: `bytes=${offset}-${r.end}` } });
      if (res.status !== 206) throw new Error(`expected 206, got ${res.status}`);
      // Response body is a web ReadableStream<Uint8Array>; iterate chunk by chunk.
      for await (const chunk of res.body as unknown as AsyncIterable<Uint8Array>) {
        await file.write(chunk, 0, chunk.length, offset); // positional write: no shared cursor
        offset += chunk.length;
      }
      if (offset !== r.end + 1) throw new Error("connection closed early");
      return;
    } catch (err) {
      if (attempt >= 4) throw err;
      const delay = Math.random() * Math.min(10_000, 250 * 2 ** attempt); // full jitter
      await new Promise((ok) => setTimeout(ok, delay));
    }
  }
}

export async function download(url: string, dest: string, connections = 4) {
  const { total, ranges } = await probe(url);
  const part = `${dest}.part`;
  const file = await open(part, "w");
  try {
    if (ranges && total > 0) {
      await file.truncate(total);
      await Promise.all(split(total, connections).map((r) => fetchRange(url, r, file)));
    } else {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      let pos = 0;
      for await (const chunk of res.body as unknown as AsyncIterable<Uint8Array>) {
        await file.write(chunk, 0, chunk.length, pos);
        pos += chunk.length;
      }
    }
    await file.sync();
  } finally {
    await file.close();
  }
  await rename(part, dest);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const [url, dest, n] = process.argv.slice(2);
  if (!url || !dest) {
    console.error("usage: node segmented-download.ts <url> <dest> [connections]");
    process.exit(2);
  }
  await download(url, dest, Number(n ?? 4));
  console.log("done");
}
