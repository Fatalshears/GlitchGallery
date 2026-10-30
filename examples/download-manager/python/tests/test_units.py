import os

import pytest

from minidm import TokenBucket, split_ranges
from minidm.ranges import parse_content_range
from minidm.state import DownloadState, Segment, load_state, save_state


@pytest.mark.parametrize("total,parts", [(1, 1), (10, 3), (1000, 8), (7, 7), (5, 10)])
def test_split_ranges_covers_every_byte_once(total, parts):
    ranges = split_ranges(total, parts)
    covered = [b for s, e in ranges for b in range(s, e + 1)]
    assert covered == list(range(total))
    assert len(ranges) <= parts


def test_split_ranges_respects_min_size():
    assert split_ranges(100, 8, min_size=40) == [(0, 49), (50, 99)]
    assert split_ranges(10, 4, min_size=1000) == [(0, 9)]


def test_split_ranges_empty_and_invalid():
    assert split_ranges(0, 4) == []
    with pytest.raises(ValueError):
        split_ranges(10, 0)


def test_parse_content_range():
    assert parse_content_range("bytes 0-99/1234") == (0, 99, 1234)
    assert parse_content_range("bytes 5-9/*") == (5, 9, None)
    with pytest.raises(ValueError):
        parse_content_range("items 0-1/2")


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.slept = 0.0

    def time(self):
        return self.now

    def sleep(self, s):
        self.slept += s
        self.now += s


def test_token_bucket_burst_then_throttle():
    clk = FakeClock()
    bucket = TokenBucket(rate=100, capacity=100, clock=clk.time, sleep=clk.sleep)
    bucket.consume(100)  # full burst, no wait
    assert clk.slept == 0
    bucket.consume(50)  # needs 0.5 s of refill
    assert clk.slept == pytest.approx(0.5)


def test_token_bucket_request_larger_than_capacity():
    clk = FakeClock()
    bucket = TokenBucket(rate=10, capacity=10, clock=clk.time, sleep=clk.sleep)
    bucket.consume(35)  # 10 burst + 25 at 10/s
    assert clk.slept == pytest.approx(2.5)


def test_state_roundtrip_and_corrupt_file(tmp_path):
    path = tmp_path / "f.part.json"
    st = DownloadState("http://x", 10, '"e"', None, [Segment(0, 4, 2), Segment(5, 9)])
    save_state(str(path), st)
    loaded = load_state(str(path))
    assert loaded == st
    assert loaded.downloaded == 2 and not loaded.complete
    assert [p for p in os.listdir(tmp_path) if p.startswith(".tmp-")] == []

    path.write_text("{not json")
    assert load_state(str(path)) is None


def test_weak_etag_is_not_used_for_if_range():
    assert DownloadState("u", 1, 'W/"x"', "Tue, 01 Oct 2026 00:00:00 GMT").validator() == (
        "Tue, 01 Oct 2026 00:00:00 GMT"
    )
