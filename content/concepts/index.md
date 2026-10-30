---
title: Technical Knowledge
type: hub
---

Technology-agnostic concepts: what a technique is, why it works, its trade-offs. Language-specific API detail lives in the [[cookbook/index|Cookbook]]; each concept page links to it.

```mermaid
flowchart LR
  subgraph Networking
    RR[HTTP range requests]
    CR[Conditional requests]
    TCP[Parallel TCP throughput]
  end
  subgraph Concurrency
    WP[Worker pool]
    PC[Producer-consumer queue]
    AIO[Async I/O]
  end
  subgraph Algorithms
    TB[Token bucket]
    RB[Retry + backoff]
  end
  subgraph "Data structures"
    PQ[Priority queue]
  end
  subgraph Storage
    RA[Random-access file I/O]
    AW[Atomic writes]
  end
  subgraph Security
    H[Hash functions]
  end
  subgraph Architecture
    FSM[State machine]
    NM[Native messaging]
  end
  RR --> CR
  WP --> PC
  AIO --> PC
  RA --> AW
  RB --> TB
```

| Domain | Concepts |
|---|---|
| Networking | [[http-range-requests]] · [[http-conditional-requests]] · [[parallel-tcp-throughput]] |
| Concurrency | [[worker-pool]] · [[producer-consumer-queue]] · [[async-io-event-loop]] |
| Algorithms | [[token-bucket]] · [[retry-with-exponential-backoff]] |
| Data structures | [[priority-queue]] |
| Storage | [[random-access-file-io]] · [[atomic-writes-and-crash-safety]] |
| Security | [[cryptographic-hash-functions]] |
| Architecture & patterns | [[finite-state-machine]] · [[browser-extension-native-messaging]] |

Planned domains with the next slices: databases (indexing, transactions, multi-tenancy), caching (HTTP caching, eviction policies, consistent hashing), search (inverted index, ranking), graphics (raster images, convolution, command pattern). See [[roadmap]].
