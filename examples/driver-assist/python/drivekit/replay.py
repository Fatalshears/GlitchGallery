"""Record/replay testing ("process replay"): feed logged inputs through a
process, compare its outputs with a stored reference, report differences.
"""

import json
from typing import Callable, Iterable

Process = Callable[[dict], dict]


def run(process_factory: Callable[[], Process], inputs: Iterable[dict]) -> list[dict]:
    process = process_factory()  # fresh state for every replay: results must not depend on history
    return [process(msg) for msg in inputs]


def save_jsonl(path: str, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")


def load_jsonl(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def compare(reference: list[dict], new: list[dict], tolerance: float = 1e-6) -> list[str]:
    """Human-readable differences; empty list means the behaviour is unchanged."""
    diffs = []
    if len(reference) != len(new):
        diffs.append(f"length {len(reference)} -> {len(new)}")
    for i, (a, b) in enumerate(zip(reference, new)):
        for key in sorted(set(a) | set(b)):
            va, vb = a.get(key), b.get(key)
            if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
                if abs(va - vb) > tolerance:
                    diffs.append(f"frame {i} {key}: {va} -> {vb}")
            elif va != vb:
                diffs.append(f"frame {i} {key}: {va!r} -> {vb!r}")
    return diffs
