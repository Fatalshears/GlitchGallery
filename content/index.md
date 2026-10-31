---
title: GlitchGallery
type: hub
---

**Learn software engineering by understanding how real-world software products solve real-world problems.**

This wiki starts from products people already use, asks *what pain does this solve and how*, and follows the answer down to the algorithms, protocols, data structures and APIs you need to build it yourself — with or without an AI assistant at your side.

## The knowledge map

Every page belongs to one of five layers. Links run in both directions: a product links down to the concepts it needs, and every concept page shows (in **Backlinks**, right sidebar) which features and products use it.

```mermaid
flowchart TB
  P["Product Encyclopedia<br/><i>what users need and why</i>"]
  F["Feature & Component Library<br/><i>reusable building blocks</i>"]
  T["Technical Knowledge<br/><i>language-agnostic concepts</i>"]
  C["Implementation Cookbook<br/><i>APIs, libraries, code, tests</i>"]
  B["Project Blueprints<br/><i>step-by-step build plans</i>"]
  P -- "decomposes into" --> F
  F -- "built from" --> T
  T -- "implemented with" --> C
  B -- "sequences" --> F
  B -- "uses" --> C
```

| Layer | Start here | Answers the question |
|---|---|---|
| Product Encyclopedia | [[products/index\|Products]] | What problem does this product solve, for whom, and with which features? |
| Feature & Component Library | [[features/index\|Features]] | What does a feature consist of, and where else does it appear? |
| Technical Knowledge | [[concepts/index\|Concepts]] | Which algorithm, protocol, structure or pattern makes it work? |
| Implementation Cookbook | [[cookbook/index\|Cookbook]] | Which API, library and code do I use in Python, TypeScript or C++? |
| Project Blueprints | [[blueprints/index\|Blueprints]] | In what order do I build it, and how do I know each step works? |

Plus [[field-notes/index|Field Notes]]: short write-ups of real bugs and odd failures met in practice.

## Where to begin

1. Read [[how-to-learn|How to learn with this wiki]] — the three competency levels and how to study without an AI assistant.
2. Follow the first complete slice: **[[internet-download-manager|Internet Download Manager (IDM)]]** → [[segmented-download]] → [[http-range-requests]] → [[http-streaming-in-python]] → [[build-a-download-manager]].
3. Or the graphics slice: **[[adobe-photoshop|Adobe Photoshop]]** → [[layers-and-blend-modes]] → [[alpha-compositing]] → [[numpy-image-processing]] → [[build-a-layered-image-editor]].
4. Or the collaboration slice: **[[excalidraw|Excalidraw]]** → [[real-time-collaboration]] → [[conflict-resolution]] → [[websockets-in-typescript]] → [[build-a-collaborative-whiteboard]].
5. Or the robotics slice: **[[openpilot]]** → [[independent-safety-layer]] → [[pid-controller]] → [[control-and-estimation-in-python]] → [[build-a-driver-assist-stack]].
6. Keep the [[glossary]] open; every term there links to the page that explains it.

> [!tip] Use the graph
> The **Graph View** in the right sidebar shows the neighbourhood of the current page. Click the expand icon for the whole wiki. Concepts with many incoming links are the ones most worth mastering first.

## Coverage so far

Four products are traced end-to-end; others are queued in the [[roadmap]].

```mermaid
flowchart LR
  IDM[IDM] --> SD[Segmented download] & PR[Pause & resume] & BL[Bandwidth limiting] & Q[Queue & scheduler] & BC[Browser capture] & IV[Integrity check]
  SD --> RR[HTTP range requests] & WP[Worker pool] & TP[Parallel TCP throughput] & RA[Random-access file I/O]
  PR --> CR[Conditional requests] & AW[Atomic writes] & FSM[State machine] & RB[Retry + backoff]
  BL --> TB[Token bucket]
  Q --> PQ[Priority queue] & PC[Producer-consumer]
  BC --> NM[Native messaging]
  IV --> H[Hash functions]
  PS[Photoshop] --> LB[Layers & blend modes] & UR[Undo history] & SM[Selections] & IF[Filters] & TA[Adjustments] & BR[Brushes]
  LB --> AC[Alpha compositing] & RI[Raster images]
  UR --> CP[Command pattern] & COW[Copy-on-write]
  SM --> FF[Flood fill]
  IF --> CK[Convolution] & TI[Tiled processing]
  TA --> LUT[Lookup tables] & CG[Colour & gamma]
  BR --> AC
  TI --> WP
  EX[Excalidraw] --> IC[Infinite canvas] & HS[Hand-drawn shapes] & SEL[Selection] & RTC[Collaboration] & ESL[Encrypted links] & FIL[Files and export]
  IC --> CTR[Coordinate transforms]
  HS --> SPR[Seeded random]
  SEL --> HIT[Hit testing] & SPI[Spatial index]
  RTC --> CON[Conflict resolution] & WSO[WebSockets] & FRI[Fractional indexing] & DT[Debounce and throttle]
  ESL --> E2E[End-to-end encryption]
  FIL --> DT
  WSO --> RB
  OP[openpilot] --> ACC[Adaptive cruise] & LCN[Lane centering] & DMN[Driver monitoring] & VIN[CAN integration] & SAF[Safety layer] & LOGR[Logging and replay]
  ACC --> MPCC[MPC] & KAL[Kalman filter]
  LCN --> PIDC[PID]
  DMN --> MLI[On-device inference]
  VIN --> CANC[CAN bus]
  SAF --> FSAF[Functional safety] & FSM
  LOGR --> RRTC[Record and replay] & PSUB[Pub/sub] & RNG[Ring buffer]
```
