import { useEffect, useRef } from "react";

/**
 * Calls `tick` every `intervalMs` until it returns true (finished) or the
 * component goes away. A tick that throws stops the polling and reports it.
 */
export function usePolling(
  active: boolean,
  tick: () => Promise<boolean>,
  onError: (error: unknown) => void,
  intervalMs = 1500,
): void {
  const latest = useRef({ tick, onError });
  latest.current = { tick, onError };

  useEffect(() => {
    if (!active) return;

    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;

    const run = async () => {
      try {
        const done = await latest.current.tick();

        if (!cancelled && !done) timer = setTimeout(run, intervalMs);
      } catch (error) {
        if (!cancelled) latest.current.onError(error);
      }
    };

    timer = setTimeout(run, intervalMs);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [active, intervalMs]);
}
