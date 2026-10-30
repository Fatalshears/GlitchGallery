// Minimal segmented downloader in C++17 with libcurl.
// Build: g++ -std=c++17 -O2 segmented_download.cpp -lcurl -pthread -o segdl
// Run:   ./segdl <url> <dest> [connections]
//
// Scope: probe, parallel Range requests (one easy handle per thread), positional
// writes with pwrite(2). POSIX only (pwrite); on Windows use WriteFile + OVERLAPPED
// offsets. No resume state or rate limit - see the Python reference implementation.

#include <curl/curl.h>
#include <fcntl.h>
#include <unistd.h>

#include <algorithm>
#include <chrono>
#include <cstdio>
#include <exception>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

struct Segment {
  curl_off_t start, end;  // inclusive
  curl_off_t offset;      // next byte to write
  int fd;
};

// libcurl calls this for every received chunk; returning less than size*nmemb aborts.
static size_t on_data(char* data, size_t size, size_t nmemb, void* user) {
  auto* seg = static_cast<Segment*>(user);
  size_t n = size * nmemb;
  if (seg->offset + static_cast<curl_off_t>(n) > seg->end + 1) return 0;  // server overran
  ssize_t w = pwrite(seg->fd, data, n, seg->offset);
  if (w != static_cast<ssize_t>(n)) return 0;
  seg->offset += n;
  return n;
}

static void fetch_segment(const std::string& url, Segment* seg) {
  for (int attempt = 0; attempt < 5; ++attempt) {
    CURL* h = curl_easy_init();  // easy handles must not be shared across threads
    std::string range = std::to_string(seg->offset) + "-" + std::to_string(seg->end);
    curl_easy_setopt(h, CURLOPT_URL, url.c_str());
    curl_easy_setopt(h, CURLOPT_RANGE, range.c_str());
    curl_easy_setopt(h, CURLOPT_FOLLOWLOCATION, 1L);
    curl_easy_setopt(h, CURLOPT_FAILONERROR, 1L);
    curl_easy_setopt(h, CURLOPT_LOW_SPEED_LIMIT, 1L);  // abort if < 1 B/s ...
    curl_easy_setopt(h, CURLOPT_LOW_SPEED_TIME, 30L);  // ... for 30 seconds
    curl_easy_setopt(h, CURLOPT_WRITEFUNCTION, on_data);
    curl_easy_setopt(h, CURLOPT_WRITEDATA, seg);
    CURLcode rc = curl_easy_perform(h);
    long status = 0;
    curl_easy_getinfo(h, CURLINFO_RESPONSE_CODE, &status);
    curl_easy_cleanup(h);
    if (rc == CURLE_OK && status == 206 && seg->offset == seg->end + 1) return;
    if (rc == CURLE_OK && status != 206) throw std::runtime_error("server ignored Range");
    std::this_thread::sleep_for(std::chrono::milliseconds(250 << attempt));
  }
  throw std::runtime_error("segment failed after retries");
}

static curl_off_t probe_size(const std::string& url) {
  CURL* h = curl_easy_init();
  curl_easy_setopt(h, CURLOPT_URL, url.c_str());
  curl_easy_setopt(h, CURLOPT_NOBODY, 1L);  // HEAD request
  curl_easy_setopt(h, CURLOPT_FOLLOWLOCATION, 1L);
  curl_off_t len = -1;
  if (curl_easy_perform(h) == CURLE_OK)
    curl_easy_getinfo(h, CURLINFO_CONTENT_LENGTH_DOWNLOAD_T, &len);
  curl_easy_cleanup(h);
  return len;
}

int main(int argc, char** argv) {
  if (argc < 3) {
    std::fprintf(stderr, "usage: %s <url> <dest> [connections]\n", argv[0]);
    return 2;
  }
  std::string url = argv[1], dest = argv[2], part = dest + ".part";
  int conns = argc > 3 ? std::stoi(argv[3]) : 4;

  curl_global_init(CURL_GLOBAL_DEFAULT);  // once, before any thread starts
  curl_off_t total = probe_size(url);
  if (total <= 0) {
    std::fprintf(stderr, "unknown size; this example requires Content-Length\n");
    return 1;
  }

  int fd = open(part.c_str(), O_CREAT | O_TRUNC | O_WRONLY, 0644);
  if (fd < 0 || ftruncate(fd, total) != 0) {
    std::perror("open/ftruncate");
    return 1;
  }

  std::vector<Segment> segs;
  curl_off_t size = (total + conns - 1) / conns;
  for (curl_off_t s = 0; s < total; s += size)
    segs.push_back({s, std::min(s + size, total) - 1, s, fd});

  std::vector<std::thread> workers;
  std::vector<std::exception_ptr> errors(segs.size());
  for (size_t i = 0; i < segs.size(); ++i)
    workers.emplace_back([&, i] {
      try {
        fetch_segment(url, &segs[i]);
      } catch (...) {
        errors[i] = std::current_exception();
      }
    });
  for (auto& t : workers) t.join();

  for (auto& e : errors)
    if (e) {
      try {
        std::rethrow_exception(e);
      } catch (const std::exception& ex) {
        std::fprintf(stderr, "error: %s\n", ex.what());
        return 1;
      }
    }

  fsync(fd);
  close(fd);
  std::rename(part.c_str(), dest.c_str());
  curl_global_cleanup();
  std::puts("done");
  return 0;
}
