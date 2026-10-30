"""Byte-range arithmetic for segmented downloads.

All ranges are inclusive on both ends, matching the HTTP `Range: bytes=a-b` syntax.
"""


def split_ranges(total: int, parts: int, min_size: int = 1) -> list[tuple[int, int]]:
    """Split [0, total) into at most `parts` contiguous inclusive ranges.

    Segments never get smaller than `min_size` bytes (except the only segment
    of a tiny file), so a 10-byte file is not split into 8 pieces.
    """
    if total < 0:
        raise ValueError("total must be >= 0")
    if parts < 1:
        raise ValueError("parts must be >= 1")
    if total == 0:
        return []

    parts = max(1, min(parts, total // max(min_size, 1)))
    base, extra = divmod(total, parts)
    ranges = []
    start = 0
    for i in range(parts):
        size = base + (1 if i < extra else 0)
        ranges.append((start, start + size - 1))
        start += size
    return ranges


def parse_content_range(value: str) -> tuple[int, int, int | None]:
    """Parse `bytes 0-99/1234` -> (0, 99, 1234). Total is None for `*`."""
    unit, _, rest = value.strip().partition(" ")
    if unit != "bytes" or "/" not in rest:
        raise ValueError(f"unsupported Content-Range: {value!r}")
    span, _, total = rest.partition("/")
    start, _, end = span.partition("-")
    return int(start), int(end), None if total == "*" else int(total)
