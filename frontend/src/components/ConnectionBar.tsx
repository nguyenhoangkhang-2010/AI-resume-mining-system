import { useEffect, useState } from "react";

import { useConnection } from "../app/context";
import type { Readiness } from "../api/types";
import { Icon } from "./ui";

type State = { kind: "checking" } | { kind: "ready"; info: Readiness } | { kind: "down"; message: string };

function describe(state: State): { tone: "good" | "warn" | "bad"; text: string } {
  if (state.kind === "checking") return { tone: "warn", text: "Checking…" };
  if (state.kind === "down") return { tone: "bad", text: "API unreachable" };

  return state.info.status === "ready"
    ? { tone: "good", text: "API ready" }
    : { tone: "warn", text: "API starting (models loading)" };
}

/** Where the API is, the key to use with it, and whether it is ready. */
export function ConnectionBar() {
  const { api, settings, update } = useConnection();
  const [state, setState] = useState<State>({ kind: "checking" });
  const [baseUrl, setBaseUrl] = useState(settings.baseUrl);
  const [apiKey, setApiKey] = useState(settings.apiKey);
  // Open until a key has been given, since nothing works without one.
  const [open, setOpen] = useState(!settings.apiKey);

  useEffect(() => {
    let cancelled = false;

    const check = () =>
      api
        .ready()
        .then((info) => !cancelled && setState({ kind: "ready", info }))
        .catch((error: Error) => !cancelled && setState({ kind: "down", message: error.message }));

    check();
    const timer = setInterval(check, 5000);

    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [api]);

  const { tone, text } = describe(state);

  if (api.mode === "demo") {
    return (
      <div className="connection connection-demo">
        <p className="status">
          <span className="dot dot-accent" aria-hidden="true" />
          Recorded demo
        </p>
        <p className="fineprint">
          Answers recorded from the real API on synthetic data. Nothing here is a real person, and nothing you
          type is sent anywhere.
        </p>
      </div>
    );
  }

  return (
    <div className="connection">
      <button
        type="button"
        className="status status-button"
        aria-expanded={open}
        aria-controls="connection-form"
        onClick={() => setOpen(!open)}
      >
        <span className={`dot dot-${tone}`} aria-hidden="true" />
        <span>{text}</span>
        <Icon name="plug" />
      </button>

      {state.kind === "down" && <p className="fineprint">{state.message}</p>}
      {state.kind === "ready" && state.info.worker && state.info.worker !== "n/a" && (
        <p className="fineprint">Queue worker: {state.info.worker}</p>
      )}

      {open && (
        <form
          id="connection-form"
          className="connection-form"
          onSubmit={(event) => {
            event.preventDefault();
            update({ baseUrl: baseUrl.trim(), apiKey: apiKey.trim() });
          }}
        >
          <label>
            API address
            <input
              value={baseUrl}
              onChange={(event) => setBaseUrl(event.target.value)}
              placeholder="same origin"
              spellCheck={false}
            />
          </label>
          <label>
            API key
            <input
              type="password"
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
              placeholder="X-API-Key"
              autoComplete="off"
            />
          </label>
          <button type="submit" className="btn btn-small">
            Use this key
          </button>
          <p className="fineprint">Kept in this tab only; it is gone when the tab closes.</p>
        </form>
      )}
    </div>
  );
}
