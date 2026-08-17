import { useCallback, useEffect, useRef, useState } from "react";

export interface AsyncState<T> {
  data: T | null;
  error: Error | null;
  loading: boolean;
}

export interface UseAsyncOptions {
  initialData?: null;
}

export interface UseAsyncResult<T, Args extends unknown[]> extends AsyncState<T> {
  execute: (...args: Args) => Promise<T | undefined>;
  reset: () => void;
}

export function useAsync<T, Args extends unknown[] = []>(
  asyncFunction: (...args: Args) => Promise<T>,
  options: UseAsyncOptions = {},
): UseAsyncResult<T, Args> {
  const { initialData = null } = options;

  const [state, setState] = useState<AsyncState<T>>({
    data: initialData,
    error: null,
    loading: false,
  });

  const mountedRef = useRef(true);

  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const execute = useCallback(
    async (...args: Args): Promise<T | undefined> => {
      setState((current) => ({
        ...current,
        loading: true,
        error: null,
      }));

      try {
        const data = await asyncFunction(...args);

        if (!mountedRef.current) {
          return data;
        }

        setState({
          data,
          error: null,
          loading: false,
        });

        return data;
      } catch (error) {
        if (!mountedRef.current) {
          return undefined;
        }

        const normalizedError =
          error instanceof Error
            ? error
            : new Error(String(error));

        setState({
          data: null,
          error: normalizedError,
          loading: false,
        });

        return undefined;
      }
    },
    [asyncFunction],
  );

  const reset = useCallback(() => {
    if (!mountedRef.current) {
      return;
    }

    setState({
      data: initialData,
      error: null,
      loading: false,
    });
  }, [initialData]);

  return {
    ...state,
    execute,
    reset,
  };
}