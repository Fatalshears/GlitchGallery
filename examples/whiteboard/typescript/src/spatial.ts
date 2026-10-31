// Uniform-grid spatial index: find elements near a point or inside a box without
// testing every element. Each element is registered in every cell its bounds touch.

import type { Box } from "./geometry.ts";

export class GridIndex {
  private cells = new Map<string, Set<string>>();
  private boxes = new Map<string, Box>();
  readonly cellSize: number;
  constructor(cellSize = 256) {
    this.cellSize = cellSize;
  }

  private *keys(b: Box): Generator<string> {
    const s = this.cellSize;
    for (let cx = Math.floor(b.minX / s); cx <= Math.floor(b.maxX / s); cx++)
      for (let cy = Math.floor(b.minY / s); cy <= Math.floor(b.maxY / s); cy++) yield `${cx},${cy}`;
  }

  insert(id: string, box: Box): void {
    this.remove(id);
    this.boxes.set(id, box);
    for (const k of this.keys(box)) {
      let cell = this.cells.get(k);
      if (!cell) this.cells.set(k, (cell = new Set()));
      cell.add(id);
    }
  }

  remove(id: string): void {
    const box = this.boxes.get(id);
    if (!box) return;
    for (const k of this.keys(box)) {
      const cell = this.cells.get(k);
      cell?.delete(id);
      if (cell?.size === 0) this.cells.delete(k);
    }
    this.boxes.delete(id);
  }

  /** Candidate ids whose bounds overlap `box` (callers still run the exact hit test). */
  query(box: Box): Set<string> {
    const out = new Set<string>();
    for (const k of this.keys(box)) {
      for (const id of this.cells.get(k) ?? []) {
        const b = this.boxes.get(id)!;
        if (b.minX <= box.maxX && b.maxX >= box.minX && b.minY <= box.maxY && b.maxY >= box.minY) out.add(id);
      }
    }
    return out;
  }

  get size(): number {
    return this.boxes.size;
  }
}
