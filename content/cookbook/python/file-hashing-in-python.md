---
title: File Hashing in Python
type: cookbook
tags: [cookbook, python, security]
aliases: [hashlib, sha256 file python, file_digest]
versions: "Python 3.10+ (file_digest needs 3.11+)"
status: draft
levels: [2]
---

Concepts: [[cryptographic-hash-functions]] · [[file-integrity-verification]].

## Recipes

> [!mwe] Streaming SHA-256, any Python 3
> ```python
> import hashlib
>
> def sha256_file(path: str, block: int = 1024 * 1024) -> str:
>     h = hashlib.sha256()
>     with open(path, "rb") as f:
>         while data := f.read(block):
>             h.update(data)
>     return h.hexdigest()
> ```

> [!mwe] Python 3.11+ one-liner
> ```python
> import hashlib
> with open("ubuntu.iso", "rb") as f:
>     digest = hashlib.file_digest(f, "sha256").hexdigest()
> ```

> [!mwe] Verify against a `SHA256SUMS` file
> ```python
> def expected_from_sums(sums_path: str, filename: str) -> str:
>     with open(sums_path, encoding="utf-8") as f:
>         for line in f:
>             digest, _, name = line.strip().partition(" ")
>             if name.lstrip(" *") == filename:      # "*" marks binary mode in sha256sum output
>                 return digest.lower()
>     raise KeyError(filename)
>
> assert sha256_file("ubuntu.iso") == expected_from_sums("SHA256SUMS", "ubuntu.iso")
> ```

> [!tested] Reference — `minidm.sha256_file` and `Options(expected_sha256=...)`; test `test_checksum_verified`.

## Gotchas

- Open files in **binary** mode (`"rb"`); text mode changes line endings on Windows.
- `hashlib.md5()` may raise in FIPS-enabled environments; pass `usedforsecurity=False` (3.9+) when you only need a non-security checksum.
- Known answer: `hashlib.sha256(b"").hexdigest()` → `e3b0c442…7852b855`.
- Block size 64 KiB–1 MiB is a good range; tiny blocks waste time in Python call overhead.

## References

- `hashlib` — https://docs.python.org/3/library/hashlib.html
- `sha256sum` output format — https://www.gnu.org/software/coreutils/manual/html_node/md5sum-invocation.html
