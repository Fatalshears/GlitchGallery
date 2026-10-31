// Merge remote element updates into local state (last-writer-wins per element).
//
// Every element carries a `version` that its editor increments on each change.
// For each id, keep the copy with the higher version; on a tie (two users edited
// the same version concurrently), keep the lower `versionNonce`. Both clients apply
// the same rule to the same pair, so they converge on the same result without a server
// deciding. Deletions are tombstones (isDeleted: true) so they win the same way.

import type { Element } from "./elements.ts";

export function winner(a: Element, b: Element): Element {
  if (a.version !== b.version) return a.version > b.version ? a : b;
  if (a.versionNonce !== b.versionNonce) return a.versionNonce < b.versionNonce ? a : b;
  return a; // identical update seen twice
}

export interface ReconcileOptions {
  /** Id of the element the local user is dragging/typing into right now: keep local copy. */
  editingId?: string;
}

export function reconcile(
  local: ReadonlyMap<string, Element>,
  remote: Iterable<Element>,
  opts: ReconcileOptions = {},
): Map<string, Element> {
  const out = new Map(local);
  for (const r of remote) {
    const l = out.get(r.id);
    if (!l) out.set(r.id, r);
    else if (r.id === opts.editingId) continue; // don't yank an element out from under the cursor
    else out.set(r.id, winner(l, r));
  }
  return out;
}
