// Single-producer single-consumer lock-free ring buffer, the pattern behind
// low-latency message queues between processes or threads (openpilot's msgq
// uses shared-memory ring buffers between processes).
// Build: g++ -std=c++17 -O2 -pthread spsc_ring.cpp -o spsc_ring && ./spsc_ring
#include <array>
#include <atomic>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <optional>
#include <thread>

template <typename T, size_t N>
class SpscRing {
  static_assert((N & (N - 1)) == 0, "N must be a power of two");
  std::array<T, N> buf_{};
  alignas(64) std::atomic<size_t> head_{0};  // written by producer only
  alignas(64) std::atomic<size_t> tail_{0};  // written by consumer only

 public:
  bool push(const T& v) {
    const size_t h = head_.load(std::memory_order_relaxed);
    if (h - tail_.load(std::memory_order_acquire) == N) return false;  // full
    buf_[h & (N - 1)] = v;
    head_.store(h + 1, std::memory_order_release);  // publish the slot after writing it
    return true;
  }
  std::optional<T> pop() {
    const size_t t = tail_.load(std::memory_order_relaxed);
    if (t == head_.load(std::memory_order_acquire)) return std::nullopt;  // empty
    T v = buf_[t & (N - 1)];
    tail_.store(t + 1, std::memory_order_release);  // free the slot after reading it
    return v;
  }
};

struct CarState {
  uint64_t frame;
  float v_ego;
};

int main() {
  SpscRing<CarState, 1024> ring;
  constexpr uint64_t kMessages = 2'000'000;

  std::thread producer([&] {
    for (uint64_t i = 0; i < kMessages; ++i)
      while (!ring.push({i, static_cast<float>(i % 40)})) std::this_thread::yield();  // full: back off
  });

  uint64_t expected = 0;
  while (expected < kMessages) {
    if (auto m = ring.pop()) {
      assert(m->frame == expected && "messages must arrive complete and in order");
      assert(m->v_ego == static_cast<float>(expected % 40));
      ++expected;
    } else {
      std::this_thread::yield();
    }
  }
  producer.join();
  std::printf("spsc_ring: %llu messages delivered in order\n", static_cast<unsigned long long>(expected));
}
