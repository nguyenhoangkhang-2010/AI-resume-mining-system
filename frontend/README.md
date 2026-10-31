# Interface

A small React + TypeScript app over the API: upload a CV and watch it being read
(with how far to trust the result), create jobs and see the candidates ranked for
them, search candidates in plain language, and see which CVs need a person.

It has two modes, the same screens in both:

| Mode | Command | Needs |
|---|---|---|
| Live | `npm run dev` | the API running; the dev server proxies `/api` to `http://127.0.0.1:8000` (set `VITE_API_TARGET` for another address) |
| Recorded demo | `npm run dev:demo` | nothing: answers recorded from the real API on synthetic data replay in the browser |

```bash
npm install
npm run dev:demo        # try it without the models, a database or a key
npm run dev             # against a running API; enter the API key in the bar at the top
```

In live mode the page asks for the API address (empty means the same origin) and
the API key; the key is kept in `sessionStorage` only, so it is gone when the tab
closes. If the page and the API are on different origins, add the page's origin to
`CORS_ORIGINS` on the API.

## Look

Warm paper-like neutrals with one green accent, light and dark following the system
setting. Titles use Fraunces, text Geist and numbers Geist Mono; all three are
installed from npm (`@fontsource-variable/*`) and bundled, so the page makes no request
to a font service. Colours, type and spacing are the tokens at the top of `src/styles.css`.

## How it is wired to the backend

- **Types come from the API.** `scripts/export_openapi.py` writes the API's
  OpenAPI description to `openapi.json`; `npm run gen:api` turns it into
  `src/api/schema.d.ts`. A change to a response shape becomes a type error here
  (`npx tsc -b` runs in CI), and a Python test fails when `openapi.json` is stale.
  After changing the API: `python -m scripts.export_openapi` then `npm run gen:api`.
- **One interface, two backends.** The screens only use the `Api` interface
  (`src/api/types.ts`). `live.ts` implements it with `fetch`; `demo.ts` replays
  `src/demo/fixtures.json`, which `python -m scripts.make_demo_fixtures` records by
  running the real API in-process on synthetic data (real models, FAISS index and CV
  pipeline; only MongoDB is faked). The fixtures hold no real person and no contact details.
- **Errors say what to do.** 401 and 403 tell the user about the key, 429 shows the
  `Retry-After` time, an unreachable API says so, and the status bar polls `/ready`.

## Checks

```bash
npx tsc -b       # types, including those generated from the API
npm test         # unit and flow tests (vitest, jsdom)
npm run build    # live build; build:demo is the static recorded demo
```

The recorded demo is a static site (`npm run build:demo`, output in `dist/`).
`.github/workflows/demo.yml` publishes it to GitHub Pages once Pages is enabled
for the repository (Settings, Pages, Source: GitHub Actions).

## What it does not do

No log in beyond the API key, no editing of candidates, no charts. It shows
what the API returns and says plainly where a result may be wrong; it is not a
recruiting product.
