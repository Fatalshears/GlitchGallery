---
title: Implementation Cookbook
type: hub
---

Language-specific, **version-specific** recipes: which API, which library, which flags, which pitfalls. Durable explanations stay on the [[concepts/index|concept pages]]; when a library changes, only the cookbook page changes.

Language preference across the wiki: **Python → TypeScript → C++**, as long as the language fits the problem; otherwise the language industry commonly uses for it.

| Language | Page | Concepts covered |
|---|---|---|
| Python | [[http-streaming-in-python]] | [[http-range-requests]], [[http-conditional-requests]] |
| Python | [[python-threads-and-asyncio]] | [[worker-pool]], [[async-io-event-loop]] |
| Python | [[file-hashing-in-python]] | [[cryptographic-hash-functions]] |
| Python | [[testing-network-code-locally]] | fault injection for any network concept |
| TypeScript | [[node-fetch-and-file-handles]] | [[http-range-requests]], [[random-access-file-io]] |
| C++ | [[libcurl-easy-interface]] | [[http-range-requests]], [[worker-pool]] |
| Python | [[numpy-image-processing]] | [[raster-images-and-pixel-formats]], [[convolution-and-kernels]], [[lookup-tables]], [[alpha-compositing]] |
| TypeScript | [[canvas-imagedata]] | [[raster-images-and-pixel-formats]], [[flood-fill]], [[layers-and-blend-modes]] |
| C++ | [[image-processing-in-cpp]] | [[convolution-and-kernels]], [[command-pattern]], [[worker-pool]] |

## Runnable examples

Code under [`examples/`](https://github.com/Fatalshears/GlitchGallery/tree/main/examples) is executed in CI:

- `examples/download-manager/python` — **tested reference** (pytest, 20 tests).
- `examples/download-manager/typescript`, `examples/download-manager/cpp` — **minimal working examples**, smoke-tested against the same fault-injecting server.
- `examples/image-editor/python` — **tested reference** image-editing engine `pixkit` (pytest, 42 tests).
- `examples/image-editor/cpp`, `examples/image-editor/typescript` — blur cross-checked against `pixkit`, undo stack, blend modes and flood fill, run by `examples/image-editor/smoke_test.sh`.
