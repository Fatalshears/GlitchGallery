---
title: Roadmap
type: meta
tags: [meta]
---

The wiki grows one product slice at a time. A slice is done when the product page, its features, the concepts they need, at least one cookbook page per concept, and a blueprint exist and link to each other.

```mermaid
flowchart LR
  A["1. IDM<br/>networking, concurrency, files"]:::done --> E["2. Photoshop<br/>raster graphics, layers, undo/redo"]:::done
  E --> B["3. Cloudflare<br/>proxies, caching, DNS, rate limiting"]
  B --> C["4. Google Search<br/>crawling, indexing, ranking"]
  C --> D["5. Salesforce CRM<br/>data modelling, multi-tenancy, workflows"]
  classDef done fill:#a7c08055,stroke:#8da101
```

The order maximizes reuse: each slice reuses concepts from the previous ones (Cloudflare reuses [[token-bucket]], [[http-conditional-requests]], [[retry-with-exponential-backoff]]; Photoshop reused [[worker-pool]] for tiled filters).

## Planned pages

| Slice | Products | New features | New concepts |
|---|---|---|---|
| 3 | Cloudflare | CDN edge caching, DDoS protection, rate limiting, DNS, TLS termination | reverse proxy, HTTP caching (RFC 9111), consistent hashing, anycast, sliding-window counters, TLS handshake |
| 4 | Google Search | crawling, indexing, query autocomplete, ranking, spell correction | inverted index, tokenization, BM25/TF-IDF, trie, PageRank, Bloom filter, MapReduce |
| 5 | Salesforce CRM | record management, custom fields, workflow automation, reports, permissions | relational modelling, multi-tenant schema, RBAC, event-driven architecture, OLAP aggregation |

## Done

- **Slice 1 — [[internet-download-manager|IDM]]**: 6 features, 14 concepts, 6 cookbook pages, 1 blueprint, tested Python reference implementation, TypeScript and C++ minimal examples.
- **Slice 2 — [[adobe-photoshop|Photoshop]]**: 6 features, 9 concepts (graphics, flood fill, command pattern, copy-on-write), 3 cookbook pages, 1 blueprint, tested Python reference `pixkit`, C++ blur cross-checked against it, C++ undo stack, TypeScript ImageData operations. Reuses [[worker-pool]] and [[finite-state-machine]] from slice 1.
