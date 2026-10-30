---
title: Roadmap
type: meta
tags: [meta]
---

The wiki grows one product slice at a time. A slice is done when the product page, its features, the concepts they need, at least one cookbook page per concept, and a blueprint exist and link to each other.

```mermaid
flowchart LR
  A["1. IDM<br/>networking, concurrency, files"]:::done --> B["2. Cloudflare<br/>proxies, caching, DNS, rate limiting"]
  B --> C["3. Google Search<br/>crawling, indexing, ranking"]
  C --> D["4. Salesforce CRM<br/>data modelling, multi-tenancy, workflows"]
  D --> E["5. Photoshop<br/>raster graphics, layers, undo/redo"]
  classDef done fill:#a7c08055,stroke:#8da101
```

The order maximizes reuse: each slice reuses concepts from the previous ones (Cloudflare reuses [[token-bucket]], [[http-conditional-requests]], [[retry-with-exponential-backoff]]).

## Planned pages

| Slice | Products | New features | New concepts |
|---|---|---|---|
| 2 | Cloudflare | CDN edge caching, DDoS protection, rate limiting, DNS, TLS termination | reverse proxy, HTTP caching (RFC 9111), consistent hashing, anycast, sliding-window counters, TLS handshake |
| 3 | Google Search | crawling, indexing, query autocomplete, ranking, spell correction | inverted index, tokenization, BM25/TF-IDF, trie, PageRank, Bloom filter, MapReduce |
| 4 | Salesforce CRM | record management, custom fields, workflow automation, reports, permissions | relational modelling, multi-tenant schema, RBAC, event-driven architecture, OLAP aggregation |
| 5 | Photoshop | layers, blend modes, selections, filters, undo history | raster images, color spaces, convolution, command pattern, memento, tiling |

## Done

- **Slice 1 — [[internet-download-manager|IDM]]**: 6 features, 14 concepts, 6 cookbook pages, 1 blueprint, tested Python reference implementation, TypeScript and C++ minimal examples.
