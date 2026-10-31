"""CAN frames and DBC-style signal packing.

A CAN frame carries an 11-bit (or 29-bit) id and 0-8 data bytes (CAN FD: up to 64).
A DBC file describes where each signal lives inside those bytes. This module
implements the two common layouts, Intel (little-endian) and Motorola
(big-endian), with scale/offset and two's-complement signed values.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Frame:
    address: int
    data: bytes
    bus: int = 0


@dataclass(frozen=True)
class Signal:
    name: str
    start_bit: int  # DBC start bit: LSB for Intel, MSB for Motorola (DBC "sawtooth" numbering)
    size: int
    little_endian: bool = True
    signed: bool = False
    factor: float = 1.0
    offset: float = 0.0

    def bit_positions(self) -> list[int]:
        """Absolute bit indices (byte*8 + bit-in-byte), most significant bit first."""
        if self.little_endian:
            return [self.start_bit + i for i in reversed(range(self.size))]
        positions, bit = [], self.start_bit
        for _ in range(self.size):
            positions.append(bit)
            # Motorola: move toward the LSB inside the byte, then to bit 7 of the next byte
            bit = bit - 1 if bit % 8 else bit + 15
        return positions


def decode(sig: Signal, data: bytes) -> float:
    raw = 0
    for pos in sig.bit_positions():
        raw = (raw << 1) | ((data[pos // 8] >> (pos % 8)) & 1)
    if sig.signed and raw & (1 << (sig.size - 1)):
        raw -= 1 << sig.size
    return raw * sig.factor + sig.offset


def encode(sig: Signal, value: float, data: bytearray) -> None:
    """Write a physical value into data in place (rounded, range-checked)."""
    raw = round((value - sig.offset) / sig.factor)
    lo, hi = (-(1 << (sig.size - 1)), (1 << (sig.size - 1)) - 1) if sig.signed else (0, (1 << sig.size) - 1)
    if not lo <= raw <= hi:
        raise ValueError(f"{sig.name}={value} out of range for {sig.size}-bit signal")
    raw &= (1 << sig.size) - 1
    for i, pos in enumerate(reversed(sig.bit_positions())):  # LSB first
        byte, bit = divmod(pos, 8)
        data[byte] = (data[byte] & ~(1 << bit)) | (((raw >> i) & 1) << bit)


def checksum_sum(data: bytes, length: int) -> int:
    """Simple additive checksum over the first length-1 bytes (one common OEM scheme)."""
    return (sum(data[: length - 1]) + length) & 0xFF


@dataclass
class CounterChecker:
    """Detect dropped, repeated or stale frames via a rolling counter (0..modulo-1)."""

    modulo: int = 16
    last: int | None = None
    errors: int = 0

    def check(self, counter: int) -> bool:
        ok = self.last is None or counter == (self.last + 1) % self.modulo
        if not ok:
            self.errors += 1
        self.last = counter
        return ok
