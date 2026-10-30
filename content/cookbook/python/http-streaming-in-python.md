---
title: HTTP Streaming in Python (urllib and httpx)
type: cookbook
tags: [cookbook, python, http]
aliases: [python download file streaming, urllib range request, httpx stream]
versions: "Python 3.10+, httpx 0.27+"
status: draft
levels: [2]
---

Concepts behind this page: [[http-range-requests]] · [[http-conditional-requests]] · [[retry-with-exponential-backoff]].

## Choosing a client

| Library | Install | Strengths | Weaknesses |
|---|---|---|---|
| `urllib.request` | standard library | no dependencies, always available | verbose; raises `HTTPError` for 4xx/5xx; no HTTP/2; no connection pooling |
| `requests` | `pip install requests` | the classic, huge ecosystem | sync only; no HTTP/2 |
| `httpx` | `pip install httpx` | sync **and** async, HTTP/2 (`httpx[http2]`), connection pooling, timeouts by default | extra dependency |
| `aiohttp` | `pip install aiohttp` | mature async client + server | async only |

Rule of thumb: standard library for tools that must run anywhere; `httpx` for applications.

## Recipes

> [!mwe] Stream a file to disk with urllib (constant memory)
> ```python
> import shutil, urllib.request
>
> req = urllib.request.Request("https://www.rfc-editor.org/rfc/rfc9110.txt",
>                              headers={"User-Agent": "learn/1.0"})
> with urllib.request.urlopen(req, timeout=30) as resp, open("rfc9110.txt", "wb") as out:
>     shutil.copyfileobj(resp, out, length=64 * 1024)
> ```

> [!mwe] Range request and status handling with urllib
> ```python
> import urllib.error, urllib.request
>
> req = urllib.request.Request(url, headers={"Range": "bytes=0-0"})
> try:
>     with urllib.request.urlopen(req, timeout=30) as resp:
>         print(resp.status, resp.headers.get("Content-Range"), resp.headers.get("ETag"))
> except urllib.error.HTTPError as e:      # 4xx/5xx arrive as exceptions in urllib
>     print("HTTP error", e.code, e.headers.get("Content-Range"))
> except urllib.error.URLError as e:       # DNS failure, refused connection, TLS error
>     print("network error", e.reason)
> ```

> [!mwe] Resume a partial file with httpx
> ```python
> import os, httpx
>
> def resume(url: str, path: str, etag: str | None = None) -> None:
>     have = os.path.getsize(path) if os.path.exists(path) else 0
>     headers = {"Range": f"bytes={have}-", "Accept-Encoding": "identity"}
>     if etag:
>         headers["If-Range"] = etag
>     with httpx.stream("GET", url, headers=headers, timeout=30, follow_redirects=True) as r:
>         r.raise_for_status()
>         mode = "ab" if r.status_code == 206 else "wb"   # 200 = file changed or no ranges
>         with open(path, mode) as f:
>             for chunk in r.iter_bytes(64 * 1024):
>                 f.write(chunk)
> ```
> A complete resume needs a check that the existing file is not already complete (server answers 416) — see the tested reference.

> [!tested] Full reference — `examples/download-manager/python/minidm/downloader.py`
> Probe with retries, segmented range requests with `If-Range`, `206` and `Content-Range` validation, premature EOF detection.

## Gotchas

- **Timeouts:** `urllib` waits forever unless you pass `timeout=`; `httpx` defaults to 5 s, which is too short for slow first bytes on big files — set it explicitly.
- **Redirects:** `urllib` follows them automatically; `httpx` does not unless `follow_redirects=True`.
- **Compression:** `httpx`/`requests` send `Accept-Encoding: gzip, deflate` and transparently decode; byte ranges then refer to compressed bytes. Send `Accept-Encoding: identity` for downloads.
- **`resp.read()` without a size** loads the whole body into memory.
- **Premature EOF:** if the server closes early, `urllib` raises `http.client.IncompleteRead`; `httpx` raises `httpx.RemoteProtocolError`. Treat both as transient.
- **Connection reuse:** create one `httpx.Client` and reuse it; a new client per request repeats TCP + TLS handshakes.

## Testing

Run against a local server you control, not the internet: [[testing-network-code-locally]].

## References

- `urllib.request` — https://docs.python.org/3/library/urllib.request.html
- httpx — https://www.python-httpx.org/ (streaming: `/quickstart/#streaming-responses`, timeouts: `/advanced/timeouts/`)
- requests — https://requests.readthedocs.io/
