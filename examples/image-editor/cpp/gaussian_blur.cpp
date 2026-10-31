// Separable Gaussian blur of a binary PPM (P6) image, multithreaded by rows.
// Build: g++ -std=c++17 -O2 gaussian_blur.cpp -pthread -o gaussian_blur
// Run:   ./gaussian_blur in.ppm out.ppm 2.0 [threads]
//
// Same algorithm as pixkit.gaussian_blur for opaque images: kernel radius
// ceil(3*sigma), clamp-to-edge borders, float accumulation, round to nearest.

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

struct Image {
  int w = 0, h = 0;
  std::vector<float> px;  // RGB, row-major, values 0..255
  float& at(int x, int y, int c) { return px[(static_cast<size_t>(y) * w + x) * 3 + c]; }
};

static Image read_ppm(const std::string& path) {
  std::ifstream f(path, std::ios::binary);
  std::string magic;
  int maxval = 0;
  Image img;
  f >> magic >> img.w >> img.h >> maxval;
  if (!f || magic != "P6" || maxval != 255) throw std::runtime_error("need an 8-bit binary P6 PPM");
  f.get();  // the single whitespace byte after the header
  std::vector<uint8_t> raw(static_cast<size_t>(img.w) * img.h * 3);
  f.read(reinterpret_cast<char*>(raw.data()), raw.size());
  if (!f) throw std::runtime_error("truncated PPM");
  img.px.assign(raw.begin(), raw.end());
  return img;
}

static void write_ppm(const std::string& path, const Image& img) {
  std::ofstream f(path, std::ios::binary);
  f << "P6\n" << img.w << " " << img.h << "\n255\n";
  for (float v : img.px) f.put(static_cast<char>(std::clamp(std::lround(v), 0L, 255L)));
}

static std::vector<float> gaussian_kernel(double sigma) {
  int r = std::max(1, static_cast<int>(std::ceil(3 * sigma)));
  std::vector<float> k(2 * r + 1);
  double sum = 0;
  for (int i = -r; i <= r; ++i) sum += k[i + r] = static_cast<float>(std::exp(-(i * i) / (2 * sigma * sigma)));
  for (float& v : k) v = static_cast<float>(v / sum);
  return k;
}

// One 1-D pass. horizontal=true reads neighbours along x. Rows are split across threads;
// each thread writes only its own rows of `dst`, so no locking is needed.
static void pass(Image& src, Image& dst, const std::vector<float>& k, bool horizontal, int threads) {
  int r = static_cast<int>(k.size() / 2);
  auto rows = [&](int y0, int y1) {
    for (int y = y0; y < y1; ++y)
      for (int x = 0; x < src.w; ++x)
        for (int c = 0; c < 3; ++c) {
          float acc = 0;
          for (int i = -r; i <= r; ++i) {
            int sx = horizontal ? std::clamp(x + i, 0, src.w - 1) : x;  // clamp-to-edge border
            int sy = horizontal ? y : std::clamp(y + i, 0, src.h - 1);
            acc += k[i + r] * src.at(sx, sy, c);
          }
          dst.at(x, y, c) = acc;
        }
  };
  std::vector<std::thread> pool;
  int band = (src.h + threads - 1) / threads;
  for (int y0 = 0; y0 < src.h; y0 += band) pool.emplace_back(rows, y0, std::min(src.h, y0 + band));
  for (auto& t : pool) t.join();
}

int main(int argc, char** argv) {
  if (argc < 4) {
    std::fprintf(stderr, "usage: %s in.ppm out.ppm sigma [threads]\n", argv[0]);
    return 2;
  }
  try {
    Image img = read_ppm(argv[1]);
    int threads = argc > 4 ? std::stoi(argv[4]) : static_cast<int>(std::max(1u, std::thread::hardware_concurrency()));
    auto k = gaussian_kernel(std::stod(argv[3]));
    Image tmp = img;
    pass(img, tmp, k, /*horizontal=*/false, threads);  // vertical first, matching pixkit
    pass(tmp, img, k, /*horizontal=*/true, threads);
    write_ppm(argv[2], img);
    std::printf("blurred %dx%d with %zu-tap kernel on %d threads\n", img.w, img.h, k.size(), threads);
  } catch (const std::exception& e) {
    std::fprintf(stderr, "error: %s\n", e.what());
    return 1;
  }
}
