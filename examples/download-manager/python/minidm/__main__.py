"""CLI: python -m minidm URL DEST [-c 8] [--limit 500000] [--sha256 HEX]

Ctrl+C pauses; running the same command again resumes.
"""

import argparse
import sys
import threading

from .downloader import Downloader, DownloadError, Options


def main() -> int:
    p = argparse.ArgumentParser(prog="minidm")
    p.add_argument("url")
    p.add_argument("dest")
    p.add_argument("-c", "--connections", type=int, default=4)
    p.add_argument("--limit", type=float, help="bytes per second")
    p.add_argument("--sha256")
    args = p.parse_args()

    stop = threading.Event()

    def progress(done: int, total: int | None) -> None:
        pct = f"{done * 100 / total:5.1f}%" if total else f"{done} B"
        print(f"\r{pct}", end="", file=sys.stderr, flush=True)

    dl = Downloader(
        args.url,
        args.dest,
        Options(connections=args.connections, rate_limit=args.limit, expected_sha256=args.sha256),
        stop_event=stop,
        on_progress=progress,
    )
    try:
        done = dl.run()
    except KeyboardInterrupt:
        stop.set()
        print("\npaused - run again to resume", file=sys.stderr)
        return 130
    except DownloadError as e:
        print(f"\nerror: {e}", file=sys.stderr)
        return 1
    print("\ndone" if done else "\npaused", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
