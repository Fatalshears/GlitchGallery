---
title: libcurl Easy Interface in C++
type: cookbook
tags: [cookbook, cpp, http]
aliases: [libcurl range download, CURLOPT_RANGE, curl_easy_perform, C++ HTTP client]
versions: "C++17, libcurl 7.68+ (8.x recommended)"
status: draft
levels: [2]
---

Concepts: [[http-range-requests]] · [[worker-pool]] · [[random-access-file-io]].

C++ has no standard HTTP client; **libcurl** is the de-facto choice (also used inside Git, CMake, PHP, and countless devices). Alternatives: cpr (C++ wrapper over libcurl), Boost.Beast (async HTTP on Asio), Poco.

## Install and build

```bash
sudo apt install libcurl4-openssl-dev          # Debian/Ubuntu
brew install curl                              # macOS (system curl also ships headers in the SDK)
vcpkg install curl                             # Windows
g++ -std=c++17 -O2 main.cpp -lcurl -pthread -o main
```

CMake: `find_package(CURL REQUIRED)` and `target_link_libraries(app PRIVATE CURL::libcurl)`.

## API map

| Need | Call |
|---|---|
| Global init (once, before threads) | `curl_global_init(CURL_GLOBAL_DEFAULT)` |
| One transfer handle | `CURL* h = curl_easy_init()` … `curl_easy_cleanup(h)` |
| URL / range | `CURLOPT_URL`, `CURLOPT_RANGE` (`"0-99"`, no `bytes=` prefix) |
| Receive data | `CURLOPT_WRITEFUNCTION` + `CURLOPT_WRITEDATA` |
| HEAD request | `CURLOPT_NOBODY = 1L` |
| Redirects / fail on 4xx-5xx | `CURLOPT_FOLLOWLOCATION`, `CURLOPT_FAILONERROR` |
| Stall detection | `CURLOPT_LOW_SPEED_LIMIT` + `CURLOPT_LOW_SPEED_TIME` |
| Run | `curl_easy_perform(h)` → `CURLcode` |
| Status code / size | `curl_easy_getinfo(h, CURLINFO_RESPONSE_CODE, &long)`, `CURLINFO_CONTENT_LENGTH_DOWNLOAD_T` |
| Many transfers on one thread | multi interface: `curl_multi_add_handle`, `curl_multi_poll` |

## Recipes

> [!mwe] Fetch a byte range into a std::string
> ```cpp
> #include <curl/curl.h>
> #include <iostream>
> #include <string>
>
> static size_t sink(char* p, size_t sz, size_t n, void* user) {
>   static_cast<std::string*>(user)->append(p, sz * n);
>   return sz * n;                     // returning less aborts with CURLE_WRITE_ERROR
> }
>
> int main() {
>   curl_global_init(CURL_GLOBAL_DEFAULT);
>   CURL* h = curl_easy_init();
>   std::string body;
>   curl_easy_setopt(h, CURLOPT_URL, "https://www.rfc-editor.org/rfc/rfc9110.txt");
>   curl_easy_setopt(h, CURLOPT_RANGE, "0-99");
>   curl_easy_setopt(h, CURLOPT_WRITEFUNCTION, sink);
>   curl_easy_setopt(h, CURLOPT_WRITEDATA, &body);
>   CURLcode rc = curl_easy_perform(h);
>   long status = 0;
>   curl_easy_getinfo(h, CURLINFO_RESPONSE_CODE, &status);
>   std::cout << curl_easy_strerror(rc) << " HTTP " << status << " bytes=" << body.size() << "\n";
>   curl_easy_cleanup(h);
>   curl_global_cleanup();
> }
> ```

> [!mwe] Parallel segments — `examples/download-manager/cpp/segmented_download.cpp`
> One `std::thread` and one easy handle per segment, `pwrite` in the write callback, retry with backoff. Smoke-tested by `examples/download-manager/smoke_test.sh`.

## Gotchas

- **Easy handles are not thread-safe** — one per thread; `curl_global_init` must run before threads start.
- `CURLOPT_RANGE` takes `"start-end"` without the `bytes=` unit.
- A server ignoring the range answers 200 and libcurl happily writes the whole body — check `CURLINFO_RESPONSE_CODE`.
- Pass `long` values to `curl_easy_setopt` for numeric options (`1L`, not `1`) — it is a variadic C function.
- The write callback may be called with any chunk size, including 0 bytes for empty bodies.
- Without `CURLOPT_LOW_SPEED_*` or `CURLOPT_TIMEOUT`, a stalled transfer can hang forever.

## References

- libcurl tutorial — https://curl.se/libcurl/c/libcurl-tutorial.html
- `CURLOPT_RANGE` — https://curl.se/libcurl/c/CURLOPT_RANGE.html
- Thread safety — https://curl.se/libcurl/c/threadsafe.html
- *Everything curl* (free book) — https://everything.curl.dev/
