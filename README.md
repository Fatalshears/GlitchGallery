# GlitchGallery

A product-oriented software engineering knowledge base: learn how to build real software by studying how real products solve real problems — from user pain point to feature, component, concept, API and tested code.

Site: https://fatalshears.github.io/GlitchGallery/

## Layout

| Path | Contents |
|---|---|
| `content/` | Wiki pages (Markdown + wikilinks + Mermaid), rendered with Quartz 4 |
| `examples/` | Runnable code referenced by the wiki; tested in CI |
| `site/` | Quartz config, layout and Everforest theme |
| `scripts/build-site.sh` | Builds the site with a pinned Quartz version |

## Local preview

Requires Node.js 22+ and Git.

```bash
scripts/build-site.sh --serve
```

Open http://localhost:8080.

## Run the example tests

```bash
cd examples/download-manager/python && python -m pytest -q
```

```bash
examples/download-manager/smoke_test.sh
```

```bash
cd examples/image-editor/python && python -m pytest -q
```

```bash
examples/image-editor/smoke_test.sh
```

See `content/meta/contributing.md` for the page standard.
