import { createContext, useContext, useMemo, useRef, useState, type ReactNode } from "react";

import { demoApi } from "../api/demo";
import { liveApi, type ConnectionSettings } from "../api/live";
import type { Api } from "../api/types";

const STORAGE_KEY = "resume-mining-connection";

function load(): ConnectionSettings {
  try {
    // sessionStorage: the key is a secret and should not outlive the tab.
    const stored = JSON.parse(sessionStorage.getItem(STORAGE_KEY) ?? "null");

    if (stored && typeof stored.baseUrl === "string" && typeof stored.apiKey === "string") return stored;
  } catch {
    // unreadable storage: start empty
  }

  return { baseUrl: "", apiKey: "" };
}

interface Connection {
  api: Api;
  settings: ConnectionSettings;
  update: (next: ConnectionSettings) => void;
}

const ConnectionContext = createContext<Connection | null>(null);

export function ConnectionProvider({ children, forceDemo }: { children: ReactNode; forceDemo?: boolean }) {
  const [settings, setSettings] = useState<ConnectionSettings>(load);
  const current = useRef(settings);
  current.current = settings;

  const value = useMemo<Connection>(
    () => ({
      // The recorded demo has no server; the live client reads the settings at call time.
      api: forceDemo ?? import.meta.env.MODE === "demo" ? demoApi() : liveApi(() => current.current),
      settings,
      update: (next) => {
        setSettings(next);

        try {
          sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next));
        } catch {
          // storage unavailable: the settings still apply for this page
        }
      },
    }),
    [settings, forceDemo],
  );

  return <ConnectionContext.Provider value={value}>{children}</ConnectionContext.Provider>;
}

export function useConnection(): Connection {
  const value = useContext(ConnectionContext);

  if (!value) throw new Error("useConnection needs a ConnectionProvider");

  return value;
}
