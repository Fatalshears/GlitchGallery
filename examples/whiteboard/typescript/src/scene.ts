// The scene: element store + spatial index + z-order, and JSON/SVG export.

import { type Element, elementBounds, hitTest, outline, parseElement } from "./elements.ts";
import { byIndex, keyBetween } from "./fractional.ts";
import { type Box, type Point, boxContains } from "./geometry.ts";
import { sketchyLine } from "./random.ts";
import { reconcile } from "./reconcile.ts";
import { GridIndex } from "./spatial.ts";

export const FILE_TYPE = "sketchkit";
export const FILE_VERSION = 1;

export class Scene {
  private els = new Map<string, Element>();
  private index = new GridIndex(256);

  get elements(): Element[] {
    return [...this.els.values()].filter((e) => !e.isDeleted).sort(byIndex);
  }

  /** All elements including tombstones — what you send to collaborators. */
  get all(): ReadonlyMap<string, Element> {
    return this.els;
  }

  get(id: string): Element | undefined {
    return this.els.get(id);
  }

  /** Key that places a new element above everything else. */
  topIndex(): string {
    const top = [...this.els.values()].sort(byIndex).at(-1);
    return keyBetween(top?.index ?? null, null);
  }

  put(el: Element): void {
    this.els.set(el.id, el);
    if (el.isDeleted) this.index.remove(el.id);
    else this.index.insert(el.id, elementBounds(el));
  }

  /**
   * Apply collaborators' elements with last-writer-wins; returns ids that changed.
   * Remote data is untrusted: malformed elements are skipped, valid ones still apply.
   */
  applyRemote(remote: readonly unknown[], editingId?: string): string[] {
    const valid: Element[] = [];
    for (const raw of remote) {
      try {
        valid.push(parseElement(raw));
      } catch {
        // ignore: a buggy or malicious peer must not crash or corrupt this client
      }
    }
    const merged = reconcile(this.els, valid, { editingId });
    const changed: string[] = [];
    for (const [id, el] of merged) {
      if (this.els.get(id) !== el) {
        this.put(el);
        changed.push(id);
      }
    }
    return changed;
  }

  /** Topmost element under p, using the grid to avoid testing every element. */
  hit(p: Point, tolerance = 4): Element | undefined {
    const box = { minX: p.x - tolerance, minY: p.y - tolerance, maxX: p.x + tolerance, maxY: p.y + tolerance };
    const candidates = [...this.index.query(box)].map((id) => this.els.get(id)!).sort(byIndex);
    for (let i = candidates.length - 1; i >= 0; i--) if (hitTest(candidates[i], p, tolerance)) return candidates[i];
    return undefined;
  }

  /** Box selection: elements entirely inside the dragged rectangle. */
  selectInBox(box: Box): Element[] {
    return [...this.index.query(box)]
      .map((id) => this.els.get(id)!)
      .filter((e) => boxContains(box, elementBounds(e)))
      .sort(byIndex);
  }

  toJSON(): string {
    return JSON.stringify({ type: FILE_TYPE, version: FILE_VERSION, elements: this.elements }, null, 2);
  }

  static fromJSON(text: string): Scene {
    const data = JSON.parse(text);
    if (data?.type !== FILE_TYPE) throw new Error("not a sketchkit file");
    if (typeof data.version !== "number" || data.version > FILE_VERSION)
      throw new Error(`unsupported file version ${data.version}`);
    if (!Array.isArray(data.elements)) throw new Error("missing elements array");
    const scene = new Scene();
    for (const [i, raw] of (data.elements as unknown[]).entries()) {
      try {
        scene.put(parseElement(raw));
      } catch (err) {
        throw new Error(`element ${i}: ${(err as Error).message}`);
      }
    }
    return scene;
  }

  /** Hand-drawn SVG: every edge drawn with the element's seeded wobble. */
  toSVG(padding = 10): string {
    const els = this.elements;
    if (els.length === 0) return `<svg xmlns="http://www.w3.org/2000/svg" width="0" height="0"/>`;
    const bounds = els.map(elementBounds);
    const minX = Math.min(...bounds.map((b) => b.minX)) - padding;
    const minY = Math.min(...bounds.map((b) => b.minY)) - padding;
    const w = Math.max(...bounds.map((b) => b.maxX)) + padding - minX;
    const h = Math.max(...bounds.map((b) => b.maxY)) + padding - minY;
    const fmt = (n: number) => +n.toFixed(2);
    const paths = els.map((el) => {
      const pts = outline(el);
      const closed = el.type === "rectangle" || el.type === "ellipse";
      const edges = closed ? pts.map((p, i) => [p, pts[(i + 1) % pts.length]]) : pts.slice(1).map((p, i) => [pts[i], p]);
      const d = edges
        .map(([a, b], i) => sketchyLine(a, b, el.seed + i))
        .map((line) => "M" + line.map((p) => `${fmt(p.x - minX)} ${fmt(p.y - minY)}`).join(" L"))
        .join(" ");
      if (el.type !== "ellipse") return `<path d="${d}" fill="none" stroke="#1e1e1e" stroke-linecap="round"/>`;
      const cx = fmt(el.x + el.width / 2 - minX);
      const cy = fmt(el.y + el.height / 2 - minY);
      const rot = el.angle ? ` transform="rotate(${fmt((el.angle * 180) / Math.PI)} ${cx} ${cy})"` : "";
      return `<ellipse cx="${cx}" cy="${cy}" rx="${fmt(el.width / 2)}" ry="${fmt(el.height / 2)}"${rot} fill="none" stroke="#1e1e1e"/>`;
    });
    return `<svg xmlns="http://www.w3.org/2000/svg" width="${fmt(w)}" height="${fmt(h)}" viewBox="0 0 ${fmt(w)} ${fmt(h)}">${paths.join("")}</svg>`;
  }
}
