"""Process large images in tiles, in parallel.

NumPy releases the GIL inside array operations, so a thread pool gives real
parallelism here. Neighbourhood filters need a halo (overlap) of at least the
kernel radius around each tile, or tile seams appear.
"""

from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterator

import numpy as np


def iter_tiles(height: int, width: int, tile: int) -> Iterator[tuple[int, int, int, int]]:
    for y0 in range(0, height, tile):
        for x0 in range(0, width, tile):
            yield y0, min(y0 + tile, height), x0, min(x0 + tile, width)


def apply_tiled(img: np.ndarray, fn: Callable[[np.ndarray], np.ndarray], tile: int = 256,
                halo: int = 0, workers: int | None = None) -> np.ndarray:
    """Run fn on each tile plus `halo` pixels of context, keep only the tile's own pixels."""
    h, w = img.shape[:2]
    out = np.empty_like(img, dtype=np.float32)

    def work(t):
        y0, y1, x0, x1 = t
        ey0, ey1 = max(0, y0 - halo), min(h, y1 + halo)
        ex0, ex1 = max(0, x0 - halo), min(w, x1 + halo)
        result = fn(img[ey0:ey1, ex0:ex1])
        out[y0:y1, x0:x1] = result[y0 - ey0 : y1 - ey0, x0 - ex0 : x1 - ex0]

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(work, iter_tiles(h, w, tile)))  # list() re-raises worker exceptions
    return out
