---
title: Python Threads and asyncio for I/O
type: cookbook
tags: [cookbook, python, concurrency]
aliases: [ThreadPoolExecutor, asyncio TaskGroup, python concurrency]
versions: "Python 3.11+ (TaskGroup); 3.10 for the thread examples"
status: draft
levels: [2]
---

Concepts: [[worker-pool]] · [[async-io-event-loop]] · [[producer-consumer-queue]].

## API map

| Need | Threads | asyncio |
|---|---|---|
| Run N jobs, gather results | `ThreadPoolExecutor.map` / `submit` + `as_completed` | `asyncio.TaskGroup` / `asyncio.gather` |
| Limit concurrency | `max_workers` | `asyncio.Semaphore(n)` |
| Stop cooperatively | `threading.Event` | task `.cancel()` → `CancelledError` |
| Lock shared state | `threading.Lock` | `asyncio.Lock` (or no lock: single thread, no `await` inside the critical section) |
| Queue | `queue.Queue` | `asyncio.Queue` |
| Call blocking code | — | `await asyncio.to_thread(fn, *args)` |
| Timeout | `future.result(timeout=)` | `async with asyncio.timeout(10):` (3.11+) |

**GIL note:** in the default CPython build only one thread executes Python bytecode at a time, but threads release the GIL while waiting on I/O — so threads are fine for downloads. Free-threaded builds (PEP 703, 3.13+ `python3.13t`) remove the GIL but are optional.

## Recipes

> [!mwe] Thread pool with a stop flag
> ```python
> import threading, time
> from concurrent.futures import ThreadPoolExecutor
>
> stop = threading.Event()
>
> def job(i: int) -> int:
>     for _ in range(50):
>         if stop.is_set():
>             return -1                      # exit cleanly between units of work
>         time.sleep(0.01)
>     return i
>
> with ThreadPoolExecutor(max_workers=4) as pool:
>     futures = [pool.submit(job, i) for i in range(8)]
>     time.sleep(0.2); stop.set()            # e.g. user pressed Pause
> print([f.result() for f in futures])
> ```

> [!mwe] asyncio with bounded concurrency and timeouts (3.11+)
> ```python
> import asyncio
>
> sem = asyncio.Semaphore(3)
>
> async def job(i: int) -> int:
>     async with sem:
>         async with asyncio.timeout(2):
>             await asyncio.sleep(0.1 * i)
>             return i
>
> async def main() -> None:
>     async with asyncio.TaskGroup() as tg:      # if one task fails, the rest are cancelled
>         tasks = [tg.create_task(job(i)) for i in range(10)]
>     print([t.result() for t in tasks])
>
> asyncio.run(main())
> ```

> [!tested] Reference — `minidm.Downloader` uses `ThreadPoolExecutor` + `threading.Event` + `threading.Lock` for state commits.

## Gotchas

- `ThreadPoolExecutor.map` re-raises the first exception only when you iterate the results.
- `asyncio.gather` without `return_exceptions=True` leaves other tasks running after the first failure; `TaskGroup` cancels them.
- `Ctrl+C` in a thread-pool program: `KeyboardInterrupt` arrives in the main thread only; set your stop event in the handler.
- Don't call `time.sleep` or sync HTTP inside `async def` — it blocks the loop.

## References

- `concurrent.futures` — https://docs.python.org/3/library/concurrent.futures.html
- `asyncio` task groups — https://docs.python.org/3/library/asyncio-task.html#task-groups
- PEP 703 (free-threaded CPython) — https://peps.python.org/pep-0703/
