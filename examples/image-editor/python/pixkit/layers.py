"""Layer stack and flattening."""

from dataclasses import dataclass, field

import numpy as np

from .blend import composite
from .color import solid


@dataclass
class Layer:
    name: str
    pixels: np.ndarray  # (H, W, 4) straight RGBA float32
    opacity: float = 1.0
    blend: str = "normal"
    visible: bool = True
    mask: np.ndarray | None = None  # (H, W) float in [0, 1]; 0 hides, 1 shows


@dataclass
class Document:
    width: int
    height: int
    layers: list[Layer] = field(default_factory=list)  # index 0 = bottom

    def new_layer(self, name: str, fill=(0.0, 0.0, 0.0, 0.0), index: int | None = None) -> Layer:
        layer = Layer(name, solid(self.height, self.width, fill))
        self.layers.insert(len(self.layers) if index is None else index, layer)
        return layer

    def flatten(self) -> np.ndarray:
        """Composite visible layers bottom to top onto a transparent canvas."""
        out = solid(self.height, self.width)
        for layer in self.layers:
            if layer.visible and layer.opacity > 0:
                out = composite(out, layer.pixels, layer.blend, layer.opacity, layer.mask)
        return out
