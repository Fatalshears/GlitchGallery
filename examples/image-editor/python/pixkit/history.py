"""Undo/redo with the command pattern.

Each edit is an object that knows how to apply and revert itself. Pixel edits
store only the rectangle they touch (before and after), not the whole image.
"""

from abc import ABC, abstractmethod
from typing import Callable

import numpy as np

from .layers import Document, Layer

BBox = tuple[int, int, int, int]  # (y0, y1, x0, x1), end-exclusive


class Command(ABC):
    label = "edit"

    @abstractmethod
    def do(self, doc: Document) -> None: ...

    @abstractmethod
    def undo(self, doc: Document) -> None: ...

    @property
    def nbytes(self) -> int:
        return 0


class PixelEdit(Command):
    """Apply fn to a rectangular patch of one layer."""

    def __init__(self, layer: int, bbox: BBox, fn: Callable[[np.ndarray], np.ndarray], label: str = "pixels"):
        self.layer, self.bbox, self.fn, self.label = layer, bbox, fn, label
        self.before: np.ndarray | None = None
        self.after: np.ndarray | None = None

    def _view(self, doc: Document) -> np.ndarray:
        y0, y1, x0, x1 = self.bbox
        return doc.layers[self.layer].pixels[y0:y1, x0:x1]

    def do(self, doc: Document) -> None:
        view = self._view(doc)
        if self.after is None:  # first run: compute; redo: replay the stored result
            self.before = view.copy()
            self.after = np.asarray(self.fn(view.copy()), np.float32)
        view[...] = self.after

    def undo(self, doc: Document) -> None:
        self._view(doc)[...] = self.before

    @property
    def nbytes(self) -> int:
        return sum(a.nbytes for a in (self.before, self.after) if a is not None)


class SetLayerProps(Command):
    """Change layer properties such as opacity, blend, visible, name."""

    def __init__(self, layer: int, **changes):
        self.layer, self.changes, self.old = layer, changes, {}
        self.label = "layer " + ", ".join(changes)

    def do(self, doc: Document) -> None:
        target = doc.layers[self.layer]
        self.old = {k: getattr(target, k) for k in self.changes}
        for k, v in self.changes.items():
            setattr(target, k, v)

    def undo(self, doc: Document) -> None:
        for k, v in self.old.items():
            setattr(doc.layers[self.layer], k, v)


class AddLayer(Command):
    def __init__(self, layer: Layer, index: int | None = None):
        self.new, self.index, self.label = layer, index, f"add {layer.name}"

    def do(self, doc: Document) -> None:
        self.index = len(doc.layers) if self.index is None else self.index
        doc.layers.insert(self.index, self.new)

    def undo(self, doc: Document) -> None:
        del doc.layers[self.index]

    @property
    def nbytes(self) -> int:
        return self.new.pixels.nbytes


class History:
    """Linear undo history with a step limit (Photoshop's default is 50 history states)."""

    def __init__(self, doc: Document, limit: int = 50):
        self.doc, self.limit = doc, limit
        self.undo_stack: list[Command] = []
        self.redo_stack: list[Command] = []

    def execute(self, cmd: Command) -> None:
        cmd.do(self.doc)
        self.undo_stack.append(cmd)
        self.redo_stack.clear()  # a new edit after undo discards the redo branch
        while len(self.undo_stack) > self.limit:
            self.undo_stack.pop(0)

    def undo(self) -> bool:
        if not self.undo_stack:
            return False
        cmd = self.undo_stack.pop()
        cmd.undo(self.doc)
        self.redo_stack.append(cmd)
        return True

    def redo(self) -> bool:
        if not self.redo_stack:
            return False
        cmd = self.redo_stack.pop()
        cmd.do(self.doc)
        self.undo_stack.append(cmd)
        return True

    @property
    def nbytes(self) -> int:
        return sum(c.nbytes for c in self.undo_stack + self.redo_stack)
