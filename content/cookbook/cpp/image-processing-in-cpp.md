---
title: Image Processing in C++
type: cookbook
tags: [cookbook, cpp, graphics, performance]
aliases: [C++ image buffer, stb_image, PPM, std::thread image, C++ pixel loop]
versions: "C++17 (g++ 9+, clang 10+, MSVC 2019+)"
status: draft
levels: [2, 3]
---

Concepts: [[raster-images-and-pixel-formats]] · [[convolution-and-kernels]] · [[worker-pool]] · [[command-pattern]] · [[copy-on-write]].

Why C++ for this domain: predictable memory layout, no garbage-collector pauses during interactive painting, SIMD intrinsics, direct GPU APIs, and code that can also be compiled to WebAssembly (as Photoshop on the web does).

## Libraries

| Need | Common choice |
|---|---|
| Read/write PNG, JPEG | `stb_image.h` / `stb_image_write.h` (single header), libpng, libjpeg-turbo |
| Everything image | OpenCV (`cv::Mat`; `cv::imread` returns **BGR** order), OpenImageIO, VIPS |
| Fast pipelines | Halide, Intel IPP, Apple vImage |
| Threads | `std::thread`, `std::async`, C++17 parallel algorithms, TBB, OpenMP |
| No dependencies at all | PPM/PGM (header + raw bytes), used in the examples here |

## Recipes

> [!tested] Separable blur on threads — `examples/image-editor/cpp/gaussian_blur.cpp`
> - **Used for:** A complete, dependency-free filter: read PPM, blur in two passes split across threads, write PPM.
> - **Input:** `in.ppm` (binary P6, 8-bit), sigma, optional thread count.
> - **Expected output:** `out.ppm` and `blurred WxH with N-tap kernel on T threads`; CI compares it with the Python reference (max difference 0).
>
> ```bash
> g++ -std=c++17 -O2 examples/image-editor/cpp/gaussian_blur.cpp -pthread -o gaussian_blur
> ./gaussian_blur in.ppm out.ppm 2.0 4
> # make a test PPM from any image: python -c "from PIL import Image; Image.open('a.png').convert('RGB').save('in.ppm')"
> ```

> [!mwe] Image struct with explicit stride
> - **Used for:** A minimal buffer type whose indexing cannot silently go wrong.
> - **Input:** Width, height, channels; pixel coordinates.
> - **Expected output:** A reference to the channel byte at `(x, y, c)`; out-of-range access fails an `assert` in debug builds.
>
> ```cpp
> #include <cassert>
> #include <cstdint>
> #include <vector>
> struct Image8 {
>   int w, h, ch;
>   size_t stride;                 // bytes per row; >= w * ch
>   std::vector<uint8_t> data;
>   Image8(int w_, int h_, int ch_) : w(w_), h(h_), ch(ch_), stride(size_t(w_) * ch_), data(stride * h_) {}
>   uint8_t& at(int x, int y, int c) {
>     assert(x >= 0 && x < w && y >= 0 && y < h && c >= 0 && c < ch);
>     return data[size_t(y) * stride + size_t(x) * ch + c];
>   }
> };
> ```

> [!tested] Command-pattern undo — `examples/image-editor/cpp/undo_stack.cpp`
> - **Used for:** Region-snapshot undo/redo with `std::unique_ptr` ownership.
> - **Input:** None (self-checking).
> - **Expected output:** `undo_stack: all checks passed`.
>
> ```bash
> g++ -std=c++17 -O2 examples/image-editor/cpp/undo_stack.cpp -o undo_stack && ./undo_stack
> ```

## Gotchas

- Index with `size_t`: `y * w * 4` overflows `int` on images above ~536 megapixels.
- Loop order: iterate `y` outer, `x` inner — row-major memory, cache-friendly.
- Float → byte: `std::lround` plus clamp; a plain cast truncates and wraps negatives.
- Threads writing **disjoint row bands** need no locks; threads writing the same buffer region race.
- `-O2` matters: debug builds of pixel loops can be 10–50× slower.
- OpenCV's `imread` returns BGR; convert with `cv::cvtColor(m, m, cv::COLOR_BGR2RGB)`.

## References

- stb single-file libraries — https://github.com/nothings/stb
- cppreference, `std::thread` — https://en.cppreference.com/w/cpp/thread/thread
- Netpbm PPM format — https://netpbm.sourceforge.net/doc/ppm.html
- Halide — https://halide-lang.org/
