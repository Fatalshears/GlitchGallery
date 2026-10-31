import random

import pytest

from drivekit.can import CounterChecker, Signal, checksum_sum, decode, encode


def test_intel_little_endian_known_bytes():
    # 16-bit unsigned at bit 0: bytes 0x34 0x12 -> 0x1234
    assert decode(Signal("s", 0, 16), bytes([0x34, 0x12, 0, 0])) == 0x1234
    # 12-bit at bit 4 spanning bytes: value 0xABC
    data = bytearray(8)
    encode(Signal("s", 4, 12), 0xABC, data)
    assert data[:2] == bytes([0xC0, 0xAB])


def test_motorola_big_endian_known_bytes():
    # DBC Motorola: start bit = MSB. 16-bit signal starting at bit 7 of byte 0 -> bytes 0x12 0x34
    assert decode(Signal("s", 7, 16, little_endian=False), bytes([0x12, 0x34, 0, 0])) == 0x1234
    # 12-bit Motorola starting at bit 3 of byte 0: low nibble of byte 0, all of byte 1
    data = bytearray(8)
    encode(Signal("s", 3, 12, little_endian=False), 0xABC, data)
    assert data[:2] == bytes([0x0A, 0xBC])


def test_scale_offset_and_signed():
    speed = Signal("speed", 0, 16, factor=0.01, offset=-50.0)
    data = bytearray(8)
    encode(speed, 27.78, data)
    assert decode(speed, bytes(data)) == pytest.approx(27.78, abs=0.005)
    torque = Signal("torque", 8, 11, signed=True)
    encode(torque, -1023, data)
    assert decode(torque, bytes(data)) == -1023
    with pytest.raises(ValueError):
        encode(torque, 1024, data)  # 11-bit signed range is -1024..1023


@pytest.mark.parametrize("little", [True, False])
def test_roundtrip_random_signals(little):
    rng = random.Random(1)
    for _ in range(500):
        size = rng.randint(1, 32)
        sig = Signal("x", rng.randint(0, 63), size, little_endian=little, signed=rng.random() < 0.5)
        if not all(0 <= p < 64 for p in sig.bit_positions()):
            continue  # signal would run past the 8-byte frame
        lo, hi = (-(1 << (size - 1)), (1 << (size - 1)) - 1) if sig.signed else (0, (1 << size) - 1)
        value = rng.randint(lo, hi)
        data = bytearray(rng.randbytes(8))
        before = bytes(data)
        encode(sig, value, data)
        assert decode(sig, bytes(data)) == value
        touched = set(sig.bit_positions())
        for pos in range(64):  # bits outside the signal are untouched
            if pos not in touched:
                assert (data[pos // 8] >> (pos % 8)) & 1 == (before[pos // 8] >> (pos % 8)) & 1


def test_checksum_and_counter():
    assert checksum_sum(bytes([1, 2, 3, 0]), 4) == (1 + 2 + 3 + 4)
    c = CounterChecker(modulo=4)
    assert [c.check(v) for v in [0, 1, 2, 3, 0, 2, 3, 3]] == [True, True, True, True, True, False, True, False]
    assert c.errors == 2
