---
title: Glossary
type: meta
tags: [meta, glossary]
---

Terms are the keys to searching on your own. Each entry links to the page that explains it.

| Term | Short meaning | Page |
|---|---|---|
| 206 Partial Content | HTTP success status for a range response | [[http-range-requests]] |
| 304 Not Modified | cached copy is still valid | [[http-conditional-requests]] |
| 416 Range Not Satisfiable | requested range is outside the file | [[http-range-requests]] |
| Accept-Ranges | header advertising range support | [[http-range-requests]] |
| Alpha | per-pixel opacity / coverage | [[alpha-compositing]] |
| Atomic rename | replace a file in one indivisible step | [[atomic-writes-and-crash-safety]] |
| Backpressure | slowing producers when consumers lag | [[producer-consumer-queue]] |
| Bandwidth-delay product (BDP) | bandwidth × RTT; data in flight to fill a link | [[parallel-tcp-throughput]] |
| Binary heap | array-backed tree giving O(log n) priority operations | [[priority-queue]] |
| Blend mode | function combining backdrop and source colours | [[layers-and-blend-modes]] |
| Checkpoint | persisted progress record | [[pause-and-resume]] |
| Command pattern | each edit as an object with do/undo | [[command-pattern]] |
| Congestion window (cwnd) | TCP sender's limit on unacknowledged data | [[parallel-tcp-throughput]] |
| Content-Range | header saying which bytes a response holds | [[http-range-requests]] |
| Convolution | weighted sum of neighbours via a kernel | [[convolution-and-kernels]] |
| Copy-on-write | share data, copy only the part being changed | [[copy-on-write]] |
| Dab | one imprint of a brush tip | [[brush-painting]] |
| Digest | output of a hash function | [[cryptographic-hash-functions]] |
| ETag | opaque version identifier of a resource | [[http-conditional-requests]] |
| Event loop | single-threaded scheduler for async I/O | [[async-io-event-loop]] |
| Exponential backoff | doubling wait after each failure | [[retry-with-exponential-backoff]] |
| Feather | soften a selection edge | [[selections-and-masks]] |
| Flood fill | select the connected region around a seed | [[flood-fill]] |
| fsync | force cached file data to stable storage | [[atomic-writes-and-crash-safety]] |
| Future / promise | handle to a value available later | [[worker-pool]] |
| Gamma encoding | non-linear storage of brightness values | [[color-spaces-and-gamma]] |
| GIL | CPython lock letting one thread run bytecode at a time | [[python-threads-and-asyncio]] |
| Halo | extra border read around a tile | [[tiled-image-processing]] |
| Idempotent | safe to repeat with the same effect | [[retry-with-exponential-backoff]] |
| If-Range | "send the range only if the version still matches" | [[http-conditional-requests]] |
| Jitter | randomness added to retry delays | [[retry-with-exponential-backoff]] |
| Kernel | weight matrix of a filter | [[convolution-and-kernels]] |
| LUT | lookup table replacing a per-value function | [[lookup-tables]] |
| Mask | per-pixel 0–1 weight limiting an edit | [[selections-and-masks]] |
| Native messaging | browser-managed JSON channel to a local program | [[browser-extension-native-messaging]] |
| Premultiplied alpha | colour stored already multiplied by alpha | [[alpha-compositing]] |
| pwrite | write at an explicit file offset | [[random-access-file-io]] |
| Range request | HTTP request for part of a resource | [[http-range-requests]] |
| Segment | byte range handled by one worker | [[segmented-download]] |
| Semaphore | counter limiting concurrent access | [[python-threads-and-asyncio]] |
| Separable filter | 2-D kernel done as two 1-D passes | [[convolution-and-kernels]] |
| Source over | the default compositing operator | [[alpha-compositing]] |
| Sparse file | file with unallocated holes | [[random-access-file-io]] |
| sRGB | the standard colour space of the web and most images | [[color-spaces-and-gamma]] |
| State machine | named states + allowed transitions | [[finite-state-machine]] |
| Stride | bytes from one image row to the next | [[raster-images-and-pixel-formats]] |
| Strong vs weak validator | byte-exact vs semantically-equal version tag | [[http-conditional-requests]] |
| Thundering herd | many clients retrying in sync | [[retry-with-exponential-backoff]] |
| Tile | fixed-size block of a large image | [[tiled-image-processing]] |
| Token bucket | rate limiter allowing bursts up to a capacity | [[token-bucket]] |
| Tolerance | allowed colour difference in a magic-wand selection | [[selections-and-masks]] |
| Transient error | failure likely to succeed on retry | [[retry-with-exponential-backoff]] |
| Work stealing | idle worker takes part of a busy one's work | [[segmented-download]] |
| Worker pool | fixed set of workers executing queued jobs | [[worker-pool]] |
