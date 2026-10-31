// Fractional indexing: z-order keys you can always insert between, so concurrent
// "bring to front" or "insert here" edits never need to renumber other elements.
// Keys are strings over a sorted alphabet compared with plain string comparison.

const DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"; // ascending in ASCII
const BASE = DIGITS.length;

const digit = (s: string, i: number): number => (i < s.length ? DIGITS.indexOf(s[i]) : 0);

/**
 * Return a key strictly between `a` and `b` (either may be null for "no bound").
 * Requires a < b. Keys never end in the smallest digit "0", which keeps room below them.
 */
export function keyBetween(a: string | null, b: string | null): string {
  const lo = a ?? "";
  if (b !== null && lo >= b) throw new Error(`keyBetween: ${a} is not < ${b}`);
  let out = "";
  for (let i = 0; ; i++) {
    const dl = digit(lo, i);
    const dh = b === null ? BASE : i < b.length ? DIGITS.indexOf(b[i]) : BASE;
    if (dh - dl > 1) {
      return out + DIGITS[Math.floor((dl + dh) / 2)];
    }
    // No room at this position: copy the lower digit and look one position deeper.
    out += DIGITS[dl];
    if (dh - dl === 1) {
      // Below b from here on; only `a` still constrains us.
      for (let j = i + 1; ; j++) {
        const d = digit(lo, j);
        if (d < BASE - 1) return out + DIGITS[Math.floor((d + BASE) / 2)];
        out += DIGITS[d];
      }
    }
  }
}

/** Sort by index, ties by id, so every client derives the same stacking order. */
export const byIndex = <T extends { index: string; id: string }>(a: T, b: T): number =>
  a.index < b.index ? -1 : a.index > b.index ? 1 : a.id < b.id ? -1 : a.id > b.id ? 1 : 0;
