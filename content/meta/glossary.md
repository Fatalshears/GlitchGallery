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
| ACC | adaptive cruise control: speed control that keeps a gap to the car ahead | [[adaptive-cruise-control]] |
| Accept-Ranges | header advertising range support | [[http-range-requests]] |
| AES-GCM | authenticated symmetric encryption | [[end-to-end-encryption]] |
| Alpha | per-pixel opacity / coverage | [[alpha-compositing]] |
| Anti-windup | stop integrating while a controller output is saturated | [[pid-controller]] |
| ASIL | automotive safety integrity level (ISO 26262) | [[functional-safety]] |
| Atomic rename | replace a file in one indivisible step | [[atomic-writes-and-crash-safety]] |
| Backpressure | slowing producers when consumers lag | [[producer-consumer-queue]] |
| Bandwidth-delay product (BDP) | bandwidth × RTT; data in flight to fill a link | [[parallel-tcp-throughput]] |
| Binary heap | array-backed tree giving O(log n) priority operations | [[priority-queue]] |
| Blend mode | function combining backdrop and source colours | [[layers-and-blend-modes]] |
| CAN frame | id plus up to 8 (CAN FD: 64) data bytes on a vehicle bus | [[can-bus]] |
| Checkpoint | persisted progress record | [[pause-and-resume]] |
| Command pattern | each edit as an object with do/undo | [[command-pattern]] |
| Congestion window (cwnd) | TCP sender's limit on unacknowledged data | [[parallel-tcp-throughput]] |
| Content-Range | header saying which bytes a response holds | [[http-range-requests]] |
| Convergence | all replicas end in the same state | [[conflict-resolution]] |
| Convolution | weighted sum of neighbours via a kernel | [[convolution-and-kernels]] |
| Copy-on-write | share data, copy only the part being changed | [[copy-on-write]] |
| CRDT | data type whose merges always converge | [[conflict-resolution]] |
| Dab | one imprint of a brush tip | [[brush-painting]] |
| DBC file | database mapping CAN ids and bits to named signals | [[vehicle-integration]] |
| Debounce | call once after a burst of events ends | [[debounce-and-throttle]] |
| Digest | output of a hash function | [[cryptographic-hash-functions]] |
| End-to-end encryption | only the endpoints can decrypt | [[end-to-end-encryption]] |
| ETag | opaque version identifier of a resource | [[http-conditional-requests]] |
| Event loop | single-threaded scheduler for async I/O | [[async-io-event-loop]] |
| Exponential backoff | doubling wait after each failure | [[retry-with-exponential-backoff]] |
| Feather | soften a selection edge | [[selections-and-masks]] |
| Flood fill | select the connected region around a seed | [[flood-fill]] |
| Fractional index | sortable key you can always insert between | [[fractional-indexing]] |
| fsync | force cached file data to stable storage | [[atomic-writes-and-crash-safety]] |
| Future / promise | handle to a value available later | [[worker-pool]] |
| Gamma encoding | non-linear storage of brightness values | [[color-spaces-and-gamma]] |
| GIL | CPython lock letting one thread run bytecode at a time | [[python-threads-and-asyncio]] |
| Halo | extra border read around a tile | [[tiled-image-processing]] |
| Hit testing | deciding which shape a point touches | [[hit-testing]] |
| Idempotent | safe to repeat with the same effect | [[retry-with-exponential-backoff]] |
| If-Range | "send the range only if the version still matches" | [[http-conditional-requests]] |
| Jerk | rate of change of acceleration; a comfort measure | [[model-predictive-control]] |
| Jitter | randomness added to retry delays | [[retry-with-exponential-backoff]] |
| Kalman gain | weighting between prediction and measurement | [[kalman-filter]] |
| Kernel | weight matrix of a filter | [[convolution-and-kernels]] |
| Last-writer-wins (LWW) | keep the newest version, drop the other | [[conflict-resolution]] |
| Liveness | a topic arriving at its expected rate | [[publish-subscribe-messaging]] |
| LUT | lookup table replacing a per-value function | [[lookup-tables]] |
| Mask | per-pixel 0–1 weight limiting an edit | [[selections-and-masks]] |
| MPC | model predictive control: optimize ahead, apply the first step | [[model-predictive-control]] |
| Native messaging | browser-managed JSON channel to a local program | [[browser-extension-native-messaging]] |
| PID | proportional-integral-derivative feedback controller | [[pid-controller]] |
| Premultiplied alpha | colour stored already multiplied by alpha | [[alpha-compositing]] |
| PRNG | seeded, deterministic random number generator | [[seeded-pseudorandom-numbers]] |
| Process replay | rerun a component on logged inputs and diff its outputs | [[record-and-replay-testing]] |
| pwrite | write at an explicit file offset | [[random-access-file-io]] |
| Range request | HTTP request for part of a resource | [[http-range-requests]] |
| Receding horizon | re-plan every cycle with fresh measurements | [[model-predictive-control]] |
| Relay server | forwards messages between clients in a room | [[websockets]] |
| Ring buffer | fixed array used circularly; overwrites or rejects when full | [[ring-buffer]] |
| Safe state | what a system does when a fault is detected | [[functional-safety]] |
| Scene coordinates | coordinates shapes live in, independent of pan/zoom | [[coordinate-transforms]] |
| Segment | byte range handled by one worker | [[segmented-download]] |
| Semaphore | counter limiting concurrent access | [[python-threads-and-asyncio]] |
| Separable filter | 2-D kernel done as two 1-D passes | [[convolution-and-kernels]] |
| Source over | the default compositing operator | [[alpha-compositing]] |
| Sparse file | file with unallocated holes | [[random-access-file-io]] |
| Spatial index | structure for finding objects near a location | [[spatial-index]] |
| SPSC queue | single-producer single-consumer lock-free queue | [[ring-buffer]] |
| sRGB | the standard colour space of the web and most images | [[color-spaces-and-gamma]] |
| State machine | named states + allowed transitions | [[finite-state-machine]] |
| Steady-state error | error left after a controller settles | [[pid-controller]] |
| Stride | bytes from one image row to the next | [[raster-images-and-pixel-formats]] |
| Strong vs weak validator | byte-exact vs semantically-equal version tag | [[http-conditional-requests]] |
| Throttle | call at most once per interval | [[debounce-and-throttle]] |
| Thundering herd | many clients retrying in sync | [[retry-with-exponential-backoff]] |
| Tile | fixed-size block of a large image | [[tiled-image-processing]] |
| Token bucket | rate limiter allowing bursts up to a capacity | [[token-bucket]] |
| Tolerance | allowed colour difference in a magic-wand selection | [[selections-and-masks]] |
| Tombstone | deleted record kept so the deletion syncs | [[conflict-resolution]] |
| Transient error | failure likely to succeed on retry | [[retry-with-exponential-backoff]] |
| URL fragment | the part after #, never sent to servers | [[encrypted-sharing-links]] |
| Viewport | scroll and zoom mapping scene to screen | [[infinite-canvas]] |
| WebSocket | persistent two-way connection over HTTP upgrade | [[websockets]] |
| Work stealing | idle worker takes part of a busy one's work | [[segmented-download]] |
| Worker pool | fixed set of workers executing queued jobs | [[worker-pool]] |
