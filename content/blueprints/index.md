---
title: Project Blueprints
type: hub
---

A blueprint turns knowledge into a buildable project: ordered milestones, the concepts to study before each one, acceptance tests, and a reference implementation to compare against afterwards.

| Blueprint | Product inspiration | Skills exercised | Reference |
|---|---|---|---|
| [[build-a-download-manager]] | [[internet-download-manager\|IDM]] | HTTP, concurrency, file I/O, crash safety, rate limiting, testing | `examples/download-manager/python` (tested) |

## How to use a blueprint

```mermaid
flowchart LR
  A[Read milestone goal] --> B[Study linked concepts<br/>to Level 1] --> C[Write acceptance tests first] --> D[Implement until tests pass] --> E[Compare with reference] --> F[Note differences<br/>and why] --> A
```

Planned: *build a caching reverse proxy* (Cloudflare slice), *build a mini search engine* (Google Search slice). See [[roadmap]].
