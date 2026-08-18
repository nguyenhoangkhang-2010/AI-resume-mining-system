import { useMemo, useState } from "react";

import type { Settings } from "../types/settings";


interface UseSettingsResult {
  loading: boolean;
  error: Error | null;
  settings: Settings | null;
}


export function useSettings(): UseSettingsResult {
  const [settings] =
    useState<Settings | null>(null);

  const [loading] =
    useState(false);

  const [error] =
    useState<Error | null>(null);


  return useMemo(
    () => ({
      loading,
      error,
      settings,
    }),
    [
      loading,
      error,
      settings,
    ],
  );
}