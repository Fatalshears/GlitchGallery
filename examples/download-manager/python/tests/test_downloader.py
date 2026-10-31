import hashlib
import os
import threading

import pytest

from minidm import Downloader, DownloadError, IntegrityError, Options

BODY = os.urandom(1_000_003)  # odd size so segments are uneven


def fast_opts(**kw) -> Options:
    base = dict(
        connections=4,
        min_segment_size=1024,
        chunk_size=8192,
        checkpoint_bytes=16384,
        backoff_base=0.01,
        backoff_cap=0.05,
        timeout=5,
    )
    base.update(kw)
    return Options(**base)


def test_segmented_download_matches_source(server, tmp_path):
    server.body = BODY
    dest = tmp_path / "out.bin"
    assert Downloader(server.url, str(dest), fast_opts()).run()
    assert dest.read_bytes() == BODY
    assert not os.path.exists(str(dest) + ".part")
    assert not os.path.exists(str(dest) + ".part.json")
    # one probe + one request per segment
    assert len([r for r in server.range_log if r and r != "bytes=0-0"]) == 4


def test_falls_back_to_single_stream_without_range_support(server, tmp_path):
    server.body, server.support_ranges = BODY, False
    dest = tmp_path / "out.bin"
    assert Downloader(server.url, str(dest), fast_opts()).run()
    assert dest.read_bytes() == BODY


def test_truncated_single_stream_is_retried_not_accepted(server, tmp_path):
    # No range support: the only way to survive a cut connection is to notice the short body.
    server.body, server.support_ranges = BODY, False
    server.drop_after, server.drops = 50_000, 3  # cuts the probe and the first two downloads
    dest = tmp_path / "out.bin"
    assert Downloader(server.url, str(dest), fast_opts()).run()
    assert dest.read_bytes() == BODY  # used to be a silently truncated 50 000-byte file


def test_dropped_connections_are_retried_and_resumed(server, tmp_path):
    server.body = BODY
    server.drop_after, server.drops = 50_000, 3
    dest = tmp_path / "out.bin"
    assert Downloader(server.url, str(dest), fast_opts()).run()
    assert dest.read_bytes() == BODY
    # A retried request must start after the bytes already received.
    starts = [int(r[6:].split("-")[0]) for r in server.range_log if r and r != "bytes=0-0"]
    assert len(starts) > 4 and len(set(starts)) == len(starts)


def test_transient_503_is_retried(server, tmp_path):
    server.body = BODY
    server.fail_status, server.fail_times = 503, 2
    dest = tmp_path / "out.bin"
    assert Downloader(server.url, str(dest), fast_opts()).run()
    assert dest.read_bytes() == BODY


def test_permanent_404_fails_fast(server, tmp_path):
    server.body = BODY
    server.fail_status, server.fail_times = 404, 99
    with pytest.raises(DownloadError):
        Downloader(server.url, str(tmp_path / "out.bin"), fast_opts()).run()


def test_pause_then_resume_fetches_only_missing_bytes(server, tmp_path):
    server.body = BODY
    dest = tmp_path / "out.bin"
    stop = threading.Event()

    def pause_midway(done, total):
        if done > len(BODY) // 3:
            stop.set()

    opts = fast_opts(rate_limit=2_000_000)
    first = Downloader(server.url, str(dest), opts, stop_event=stop, on_progress=pause_midway)
    assert first.run() is False
    assert os.path.exists(str(dest) + ".part.json")
    log_len = len(server.range_log)

    assert Downloader(server.url, str(dest), fast_opts()).run()
    assert dest.read_bytes() == BODY
    resumed = server.range_log[log_len:]
    assert "bytes=0-0" not in resumed  # no re-probe: state came from the sidecar
    assert all(not r.startswith("bytes=0-") for r in resumed)


def test_changed_remote_file_restarts_from_scratch(server, tmp_path):
    server.body = BODY
    dest = tmp_path / "out.bin"
    stop = threading.Event()
    first = Downloader(
        server.url,
        str(dest),
        fast_opts(rate_limit=2_000_000),
        stop_event=stop,
        on_progress=lambda d, t: d > 200_000 and stop.set(),
    )
    assert first.run() is False

    new_body = os.urandom(500_000)
    server.body, server.etag = new_body, '"v2"'
    assert Downloader(server.url, str(dest), fast_opts()).run()
    assert dest.read_bytes() == new_body


def test_checksum_verified(server, tmp_path):
    server.body = BODY
    good = hashlib.sha256(BODY).hexdigest()
    dest = tmp_path / "ok.bin"
    assert Downloader(server.url, str(dest), fast_opts(expected_sha256=good)).run()

    bad = tmp_path / "bad.bin"
    with pytest.raises(IntegrityError):
        Downloader(server.url, str(bad), fast_opts(expected_sha256="0" * 64)).run()
    assert not bad.exists() and not os.path.exists(str(bad) + ".part")
