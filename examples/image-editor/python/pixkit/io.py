"""Load/save via Pillow (optional dependency: pip install Pillow)."""

import numpy as np

from .color import to_float, to_u8


def load_image(path: str) -> np.ndarray:
    from PIL import Image

    with Image.open(path) as im:
        return to_float(np.asarray(im.convert("RGBA")))


def save_image(path: str, img: np.ndarray) -> None:
    from PIL import Image

    Image.fromarray(to_u8(img), "RGBA").save(path)
