// Rate-limit chatty events: pointer moves for cursor broadcast (throttle) and
// autosave after the user stops editing (debounce).

/** Call fn at most once per `ms`; the last call in a burst is still delivered (trailing edge). */
export function throttle<A extends unknown[]>(fn: (...args: A) => void, ms: number) {
  let last = -Infinity;
  let timer: ReturnType<typeof setTimeout> | undefined;
  let pending: A | undefined;
  return (...args: A) => {
    const now = Date.now();
    if (now - last >= ms) {
      // A new leading call supersedes any pending trailing one; otherwise the stale value
      // would be delivered after this newer one and (for cursors) jump backwards.
      clearTimeout(timer);
      timer = undefined;
      pending = undefined;
      last = now;
      fn(...args);
    } else {
      pending = args;
      timer ??= setTimeout(() => {
        timer = undefined;
        last = Date.now();
        fn(...pending!);
      }, ms - (now - last));
    }
  };
}

/** Call fn once, `ms` after the last call in a burst. */
export function debounce<A extends unknown[]>(fn: (...args: A) => void, ms: number) {
  let timer: ReturnType<typeof setTimeout> | undefined;
  return (...args: A) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}
