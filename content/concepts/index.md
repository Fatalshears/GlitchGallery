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
  subgraph Graphics
    RI[Raster images]
    CG[Colour and gamma]
    AC[Alpha compositing]
    CK[Convolution]
    LUT[Lookup tables]
    TI[Tiled processing]
  end
  subgraph Patterns["Patterns and structures"]
    CP[Command pattern]
    COW[Copy-on-write]
    FF[Flood fill]
  end
  RI --> AC & CK & LUT
  CG --> LUT
  CK --> TI
  TI --> WP
  CP --> COW
  TI --> COW
  subgraph Collaboration["Vector and collaboration"]
    VS[Scene model]
    CT[Coordinate transforms]
    HT[Hit testing]
    SX[Spatial index]
    FI[Fractional indexing]
    CF[Conflict resolution]
    WSK[WebSockets]
    E2E[End-to-end encryption]
  end
  CT --> HT --> SX
  VS --> CF
  FI --> CF
  WSK --> CF
  E2E --> WSK
  RB --> WSK
  subgraph Robotics["Control, safety and testing"]
    PIDN[PID]
    MPCN[MPC]
    KFN[Kalman filter]
    FRL[Fixed-rate loops]
    CANN[CAN bus]
    PSM[Pub/sub messaging]
    RBUF[Ring buffer]
    FS[Functional safety]
    RRT[Record and replay]
    ML[On-device inference]
  end
  FRL --> PIDN & MPCN & KFN
  KFN --> MPCN
  RBUF --> PSM --> RRT
  CANN --> FS
  FSM --> FS
  PC --> PSM
```

| Domain | Concepts |
|---|---|
| Networking | [[http-range-requests]] · [[http-conditional-requests]] · [[parallel-tcp-throughput]] · [[websockets]] · [[can-bus]] |
| Concurrency | [[worker-pool]] · [[producer-consumer-queue]] · [[async-io-event-loop]] |
| Algorithms | [[token-bucket]] · [[retry-with-exponential-backoff]] · [[flood-fill]] · [[seeded-pseudorandom-numbers]] · [[fractional-indexing]] · [[debounce-and-throttle]] |
| Data structures | [[priority-queue]] · [[spatial-index]] · [[ring-buffer]] |
| Storage | [[random-access-file-io]] · [[atomic-writes-and-crash-safety]] |
| Security | [[cryptographic-hash-functions]] · [[end-to-end-encryption]] |
| Distributed systems | [[conflict-resolution]] |
| Control and estimation | [[pid-controller]] · [[model-predictive-control]] · [[kalman-filter]] · [[fixed-rate-control-loops]] |
| Safety | [[functional-safety]] |
| Testing | [[record-and-replay-testing]] |
| Machine learning | [[on-device-ml-inference]] |
| Graphics | [[raster-images-and-pixel-formats]] · [[color-spaces-and-gamma]] · [[alpha-compositing]] · [[convolution-and-kernels]] · [[lookup-tables]] · [[tiled-image-processing]] · [[vector-graphics-and-scene-model]] · [[coordinate-transforms]] · [[hit-testing]] |
| Architecture & patterns | [[finite-state-machine]] · [[browser-extension-native-messaging]] · [[command-pattern]] · [[copy-on-write]] · [[publish-subscribe-messaging]] |

Planned domains with the next slices: databases (indexing, transactions, multi-tenancy), caching (HTTP caching, eviction policies, consistent hashing), search (inverted index, ranking). See [[roadmap]].
