#!/usr/bin/env python3
"""Check wiki pages against the page standard in content/meta/contributing.md.

Run: python3 scripts/check_wiki.py   (exit code 1 if any page breaks a rule)
"""
import collections
import glob
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..", "content")
STANDARD = [
    "## Problem and purpose", "## Core concepts and terminology", "## How it works",
    "## Related features and components", "## Required technical knowledge",
    "## Implementation techniques and APIs", "## Error handling and edge cases",
    "## Testing and debugging", "## Limitations and engineering trade-offs",
    "## Competency checklist", "## References",
]
REQUIRED_SECTIONS = {
    "concept": STANDARD,
    "feature": STANDARD,
    "product": ["## Purpose", "## Users and pain points", "## Core features", "## Feature decomposition",
                "## Architecture sketch", "## Build it yourself", "## References"],
    "cookbook": ["## References"],
    "blueprint": ["## Milestone map", "## Reference implementation", "## Self-assessment"],
}
# Fenced blocks that are sample output or diagrams-as-text, not code examples.
NO_DESCRIPTION_NEEDED = {"field-notes/claude-code-model-access-litellm.md"}


def strip_code(text: str) -> str:
    text = re.sub(r"^(> )?```.*?^(> )?```", "", text, flags=re.S | re.M)
    return re.sub(r"`[^`\n]*`", "", text)


def main() -> int:
    pages = {}
    for path in glob.glob(f"{ROOT}/**/*.md", recursive=True):
        text = open(path, encoding="utf-8").read()
        fm = re.match(r"---\n(.*?)\n---\n", text, re.S)
        meta = dict(re.findall(r"^(\w[\w-]*):\s*(.*)$", fm.group(1), re.M)) if fm else {}
        pages[os.path.relpath(path, ROOT)] = (meta, text)
    slugs = {os.path.splitext(os.path.basename(p))[0] for p in pages}
    paths = {os.path.splitext(p)[0] for p in pages}
    inbound = collections.Counter()
    problems = []

    for page, (meta, text) in sorted(pages.items()):
        kind = meta.get("type")
        if not kind:
            problems.append(f"{page}: front matter has no 'type'")
            continue
        needed = ["title"]
        if kind in REQUIRED_SECTIONS:
            needed += ["tags", "status"]
        if kind in ("concept", "feature"):
            needed += ["levels"]
        if kind == "cookbook":
            needed += ["versions"]
        problems += [f"{page}: front matter missing '{k}'" for k in needed if k not in meta]
        problems += [f"{page}: missing section {h!r}" for h in REQUIRED_SECTIONS.get(kind, []) if h not in text]
        if kind in ("concept", "feature"):
            if "*Search keywords:*" not in text:
                problems.append(f"{page}: no '*Search keywords:*' line")
            if "```mermaid" not in text:
                problems.append(f"{page}: no diagram")
            for level in re.findall(r"\d", meta.get("levels", "")):
                if f"[!level{level}]" not in text:
                    problems.append(f"{page}: levels lists {level} but has no [!level{level}] callout")

        for target in re.findall(r"\[\[([^\]|#\\]+)", strip_code(text)):
            target = target.strip()
            if target in slugs or target in paths:
                inbound[target.split("/")[-1]] += 1
            else:
                problems.append(f"{page}: link to missing page [[{target}]]")

        lines = text.splitlines()
        inside = False
        for i, line in enumerate(lines):
            m = re.match(r"^(> )?```(\S*)\s*$", line)
            if not m:
                continue
            if inside:
                inside = False
                continue
            inside = True
            if m.group(2) == "mermaid" or page in NO_DESCRIPTION_NEEDED or page.endswith("contributing.md"):
                continue
            if not any("**Used for:**" in x for x in lines[max(0, i - 6):i]):
                problems.append(f"{page}:{i + 1}: code example without Used for / Input / Expected output")

    for page, (meta, _) in pages.items():
        slug = os.path.splitext(os.path.basename(page))[0]
        if slug != "index" and meta.get("type") != "hub" and inbound[slug] == 0:
            problems.append(f"{page}: orphan page (nothing links to it)")

    for p in problems:
        print(p)
    print(f"checked {len(pages)} pages, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
