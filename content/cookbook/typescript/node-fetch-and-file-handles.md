---
title: Node.js fetch, Streams and File Handles
type: cookbook
tags: [cookbook, typescript, nodejs, http]
aliases: [node fetch range request, FileHandle write position, node download file]
versions: "Node.js 22.18+ (native TypeScript type stripping); fetch is stable since Node 21"
status: draft
levels: [2]
---

Concepts: [[http-range-requests]] · [[random-access-file-io]] · [[async-io-event-loop]] · [[worker-pool]].

## API map

| Need | API |
|---|---|
| HTTP request | global `fetch(url, { headers, signal })` (Undici under the hood) |
| Read body incrementally | `for await (const chunk of res.body)` (web `ReadableStream`) |
| Cancel | `AbortController` → `signal`; `res.body?.cancel()` to drop an unwanted body |
| Open file | `fs.promises.open(path, "w" \| "r+")` → `FileHandle` |
| Positional write | `fh.write(buffer, 0, buffer.length, position)` |
| Preallocate / flush | `fh.truncate(n)`, `fh.sync()` |
| Atomic rename | `fs.promises.rename(tmp, final)` |
| Run in parallel | `Promise.all` / `Promise.allSettled` |

## Recipes

> [!mwe] Stream a download to disk with backpressure
> ```ts
> import { createWriteStream } from "node:fs";
> import { Readable } from "node:stream";
> import { pipeline } from "node:stream/promises";
>
> const res = await fetch("https://www.rfc-editor.org/rfc/rfc9110.txt");
> if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);
> await pipeline(Readable.fromWeb(res.body as any), createWriteStream("rfc9110.txt"));
> ```
> `pipeline` handles backpressure and closes both streams on error.

> [!mwe] Timeout and cancel
> ```ts
> const res = await fetch(url, { signal: AbortSignal.timeout(30_000) });  // aborts with TimeoutError
> ```

> [!mwe] Segmented download — `examples/download-manager/typescript/segmented-download.ts`
> Probe with `Range: bytes=0-0`, `Promise.all` over ranges, `FileHandle.write(chunk, 0, len, offset)`, jittered retry. Smoke-tested against the fault-injecting Python server by `examples/download-manager/smoke_test.sh`.

## Gotchas

- `fetch` **does not throw** on 4xx/5xx — check `res.ok` / `res.status`. It throws `TypeError: fetch failed` on network errors (inspect `err.cause`).
- An unread body keeps the connection busy; call `res.body?.cancel()` when you only need headers.
- Undici transparently decompresses `Content-Encoding: gzip`; set `Accept-Encoding: identity` for byte-exact range downloads.
- Undici limits connections per origin through its global dispatcher; for many parallel ranges to one host, configure `new Agent({ connections: N })` from the `undici` package.
- `fh.write` with a `position` is a positional write; without it, writes go to the current offset — do not mix them.
- Running `.ts` directly needs Node 22.18+ (or 23.6+); type-only syntax works, but `enum` and parameter properties need `--experimental-transform-types` or a build step (`tsc`, `tsx`).

## References

- Node.js `fetch` — https://nodejs.org/api/globals.html#fetch
- `FileHandle` — https://nodejs.org/api/fs.html#class-filehandle
- Node.js TypeScript support — https://nodejs.org/api/typescript.html
- Undici — https://undici.nodejs.org/
