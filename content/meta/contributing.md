---
title: Contributing and Page Standard
type: meta
tags: [meta]
---

This page defines how pages are written so that the wiki stays consistent and interconnected.

## Repository layout

```
content/              wiki pages (Markdown, Obsidian-flavoured)
  products/           Product Encyclopedia
  features/           Feature & Component Library
  concepts/<domain>/  Technical Knowledge (networking, concurrency, storage, ...)
  cookbook/<lang>/    Implementation Cookbook (python, typescript, cpp, ...)
  blueprints/         Project Blueprints
  field-notes/        Troubleshooting write-ups
  meta/               How-to, glossary, roadmap, this page
examples/             Runnable code referenced by [!tested] callouts (CI-tested)
site/                 Quartz config, layout and theme (Everforest)
scripts/build-site.sh Builds the site with a pinned Quartz version
```

Preview locally (Node.js ≥ 22, Git):

- **Used for:** Previewing the wiki locally while you edit.
- **Input:** Node.js 22+ and Git installed; run from the repository root.
- **Expected output:** The site served at http://localhost:8080, rebuilt when files in `content/` change.

```bash
scripts/build-site.sh --serve
```

## Linking rules

- Link with wikilinks by file name: `[[http-range-requests]]` or `[[http-range-requests|range requests]]`. File names must be unique across the wiki.
- **Link downward explicitly**: product → features → concepts → cookbook. Upward links (concept → products that use it) appear automatically in **Backlinks**; add them in prose only when the context helps.
- A concept used by two products must live in one concept page, never be duplicated in product pages.
- Planned pages may be linked before they exist; list them in the [[roadmap]].

## Front matter

- **Used for:** The metadata block at the top of every page.
- **Input:** Fill in the values for your page.
- **Expected output:** Quartz uses `title`, `tags` and `aliases` for the page title, tag pages and search; the other fields are for readers and future tooling.

```yaml
---
title: HTTP Range Requests        # human title
type: concept                      # product | feature | concept | cookbook | blueprint | field-note | hub | meta
domain: networking                 # concepts only
tags: [http, networking]
aliases: [byte serving, partial content]   # alternative names; also improves search
status: draft                      # stub | draft | reviewed
levels: [1, 2, 3]                  # competency levels this page covers
versions: "Python 3.10+"           # cookbook only: versions the code was checked against
---
```

## The standard knowledge page

Concept and feature pages use these sections, in this order. Omit a section only if it truly does not apply.

1. **Problem and purpose** — the pain, in plain words.
2. **Core concepts and terminology** — terms in bold, plus a *Search keywords* line.
3. **How it works** — at least one diagram (Mermaid).
4. **Related features and components** — links up and sideways.
5. **Required technical knowledge** — prerequisites, linked.
6. **Implementation techniques and APIs** — technology-agnostic first, then per language.
7. **Minimal working examples** — labelled callouts (see below).
8. **Error handling and edge cases**
9. **Testing and debugging**
10. **Limitations and engineering trade-offs**
11. **Competency checklist** — `[!level1]`, `[!level2]`, `[!level3]` callouts.
12. **Related knowledge and references** — authoritative sources first (RFCs, official docs, man pages).

Product pages instead use: Purpose → Users and pain points → Core features → Workflows → Feature decomposition → Architecture sketch → Build-it-yourself path → References.

Cookbook pages are version-specific: state versions in front matter, keep durable explanations on the concept page and only API detail here.

## Code example labels

- **Used for:** The three ways to label a code example.
- **Input:** Pick the label that matches how far the code has been verified, then add Used for / Input / Expected output lines and the code.
- **Expected output:** A coloured callout box with the matching icon on the rendered page.

```markdown
> [!pseudocode] Title
> conceptual; not runnable

> [!mwe] Title (Python 3.10+)
> runs as shown; minimal error handling

> [!tested] Title
> lives in examples/, covered by CI; link to the file
```

Every code example — whatever its label — starts with three lines so a reader knows what it does before reading it:

```markdown
> [!mwe] Parse `Content-Range` (Python 3.10+)
> - **Used for:** reading which bytes a 206 response contains.
> - **Input:** a `Content-Range` header value, e.g. `"bytes 0-99/1234"`.
> - **Expected output:** `(0, 99, 1234)`; `ValueError` for units other than `bytes`.
>
> ```python
> ...
> ```
```

State concrete values in **Expected output** (a printed line, a return value, a file that appears, an error type) so the reader can check their run against it.

Language choice: prefer **Python**, then **TypeScript**, then **C++**, as long as the language fits the problem. Where none fits, use what industry commonly uses for that problem (e.g. SQL for databases, Go for some infrastructure, Swift/Kotlin for mobile) and say why.

## Diagrams

Use Mermaid (`flowchart`, `sequenceDiagram`, `stateDiagram-v2`, `classDiagram`, `erDiagram`). Every concept page should have at least one. Prefer diagrams that show a mechanism (who sends what, in which order) over decorative boxes.

## Field notes

A field note records one real failure: symptoms, root cause, fix, diagnostic checklist, references. Link it to the concepts involved so it shows up in their backlinks.
