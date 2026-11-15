# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

TxnWeave is a graphing web app for retail security agents to visualize suspicious activity and long-running fraud cases (built with gift card fraud in mind). Users enter store/transaction data and see it rendered as a graph to spot patterns.

The repo is at an early "hello world" stage: most files under `apps/` and `docs/` exist as empty placeholders that sketch the intended architecture. Only the API's `/api/hello` endpoint and the web app's call to it are implemented.

## Working style

The author uses Claude Code in manual-approval mode and reviews all generated code to make sure they understand it. Keep changes small and explainable, and don't run git commands (branching, committing) unless the user explicitly asks.

## Commands

The full stack runs via Docker Compose from the repo root:

```bash
docker compose up --build      # api on 127.0.0.1:8000, web on 127.0.0.1:5173
```

API (`apps/api`, Python ≥3.12, FastAPI, setuptools src-layout):

```bash
pip install -e .
uvicorn txnweave_api.main:app --reload --port 8000
```

Web (`apps/web`, React 19 + Vite 6 + TypeScript):

```bash
npm install
npm run dev       # vite dev server on 0.0.0.0:5173
npm run build     # tsc --noEmit && vite build
```

No test runner (pytest / vitest) or linter is configured yet, even though test files exist as placeholders (`apps/api/src/tests/`, `apps/web/src/tests/`). `.github/workflows/ci.yml` is empty.

## File structure

```
TxnWeave-Repo/
├── compose.yaml                 # api + web services, ports bound to 127.0.0.1
├── .github/workflows/ci.yml     # CI (empty)
├── data/examples/sample-graph.json
├── docs/
│   ├── architecture/overview.md
│   └── development/             # local-setup.md, vpn-connection.md
└── apps/
    ├── api/                     # FastAPI backend (Python ≥3.12)
    │   ├── Dockerfile
    │   ├── pyproject.toml
    │   └── src/
    │       ├── txnweave_api/
    │       │   ├── main.py      # FastAPI app + /api/hello
    │       │   ├── config.py    # settings
    │       │   ├── routes/      # graphs.py — HTTP endpoints
    │       │   ├── services/    # graph_service.py — graph logic
    │       │   ├── schemas/     # graph.py — Pydantic models
    │       │   └── db/          # database.py, models.py
    │       └── tests/           # conftest.py, test_graphs.py, test_graph_service.py
    └── web/                     # React 19 + Vite + TypeScript frontend
        ├── Dockerfile
        ├── index.html
        ├── package.json
        ├── tsconfig.json
        ├── vite.config.ts       # /api proxy → http://api:8000
        └── src/
            ├── main.tsx, App.tsx
            ├── api/graphApi.ts  # backend fetch calls
            ├── pages/           # HomePage, GraphPage
            ├── components/      # GraphCanvas, GraphToolbar, NodeEditor, EdgeEditor, PropertyPanel
            ├── graph/           # cytoscapeConfig.ts, graphMapper.ts
            ├── types/graph.ts
            ├── styles/global.css
            └── tests/           # GraphCanvas.test.tsx, graphMapper.test.tsx
```

## Architecture

- **apps/api** — FastAPI app in `src/txnweave_api/main.py`. Planned layering (currently empty files): `routes/` (HTTP endpoints) → `services/` (graph logic) → `db/` (database + models), with Pydantic `schemas/` and `config.py`. All endpoints are prefixed `/api`.
- **apps/web** — React SPA. `src/api/graphApi.ts` holds fetch calls to the backend using relative `/api/...` URLs. Planned pieces: `pages/` (HomePage, GraphPage), `components/` (graph canvas, toolbar, node/edge editors, property panel), and `src/graph/` (`cytoscapeConfig.ts`, `graphMapper.ts`), which suggests Cytoscape.js for rendering (not yet a dependency).
- **Frontend → backend wiring:** the Vite dev server proxies `/api` to `http://api:8000`, which is the Compose service hostname. Running the web app outside Compose needs that proxy target changed (e.g. to `http://localhost:8000`).
- `data/examples/sample-graph.json` is intended as sample graph input (currently empty).

## Gotchas

- Compose binds ports to `127.0.0.1` only. Remote access to the author's hosted instance goes through a VPN (`docs/development/vpn-connection.md`, not yet written).
