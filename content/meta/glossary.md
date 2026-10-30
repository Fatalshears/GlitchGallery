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
| Atomic rename | replace a file in one indivisible step | [[atomic-writes-and-crash-safety]] |
| Backpressure | slowing producers when consumers lag | [[producer-consumer-queue]] |
| Bandwidth-delay product (BDP) | bandwidth × RTT; data in flight to fill a link | [[parallel-tcp-throughput]] |
| Binary heap | array-backed tree giving O(log n) priority operations | [[priority-queue]] |
| Checkpoint | persisted progress record | [[pause-and-resume]] |
| Content-Range | header saying which bytes a response holds | [[http-range-requests]] |
| Congestion window (cwnd) | TCP sender's limit on unacknowledged data | [[parallel-tcp-throughput]] |
| Digest | output of a hash function | [[cryptographic-hash-functions]] |
| ETag | opaque version identifier of a resource | [[http-conditional-requests]] |
| Event loop | single-threaded scheduler for async I/O | [[async-io-event-loop]] |
| Exponential backoff | doubling wait after each failure | [[retry-with-exponential-backoff]] |
| fsync | force cached file data to stable storage | [[atomic-writes-and-crash-safety]] |
| Future / promise | handle to a value available later | [[worker-pool]] |
| GIL | CPython lock letting one thread run bytecode at a time | [[python-threads-and-asyncio]] |
| Idempotent | safe to repeat with the same effect | [[retry-with-exponential-backoff]] |
| If-Range | "send the range only if the version still matches" | [[http-conditional-requests]] |
| Jitter | randomness added to retry delays | [[retry-with-exponential-backoff]] |
| Native messaging | browser-managed JSON channel to a local program | [[browser-extension-native-messaging]] |
| pwrite | write at an explicit file offset | [[random-access-file-io]] |
| Range request | HTTP request for part of a resource | [[http-range-requests]] |
| Segment | byte range handled by one worker | [[segmented-download]] |
| Semaphore | counter limiting concurrent access | [[python-threads-and-asyncio]] |
| Sparse file | file with unallocated holes | [[random-access-file-io]] |
| State machine | named states + allowed transitions | [[finite-state-machine]] |
| Strong vs weak validator | byte-exact vs semantically-equal version tag | [[http-conditional-requests]] |
| Thundering herd | many clients retrying in sync | [[retry-with-exponential-backoff]] |
| Token bucket | rate limiter allowing bursts up to a capacity | [[token-bucket]] |
| Transient error | failure likely to succeed on retry | [[retry-with-exponential-backoff]] |
| Work stealing | idle worker takes part of a busy one's work | [[segmented-download]] |
| Worker pool | fixed set of workers executing queued jobs | [[worker-pool]] |
