# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

TxnWeave is a graphing web app for retail security agents to visualize suspicious activity and long-running fraud cases (built with gift card fraud in mind). Users enter store/transaction data and see it rendered as a graph to spot patterns.

The repo is at an early "hello world" stage: most files under `apps/` exist as empty placeholders. Only the API's `/api/hello` endpoint and the web app's call to it are implemented. The full design is agreed and lives in `docs/development/claudedesigns/` (see below). Where the placeholder files differ from the design, the design wins.

It is also a CS 420 (HCI) course project. Course requirements come from `docs/development/CS420_Project_Discovery and Specification.pdf` (FR-01 to FR-27, UC01 to UC10). `CS420_Project_Concept.pdf` has not been folded in yet, because its pages render blank (follow-up F19).

## Design documents

Start with `docs/development/claudedesigns/master-plan.md`. It holds the purpose, goals, cross-cutting decisions, glossary, tech stack, conventions and an index of every feature doc. Then load only the feature docs the task needs:

- `backend/`: data-model, persistence, api, relationship-resolution, graph-output, csv-save-load, build-plan
- `ui/`: color-system, app-shell, investigation-page, documents-page, settings-page, build-plan
- `project/`: context (problem, persona, quality goals, risks), requirements (FR/UC coverage), traceability (design element → FR/UC map)
- `design-history.md`: changelogs and follow-ups F1 to F19 (some still open)

Rules that apply when using or editing them:

- **Build in waves (P1).** Wave 1 fully implements every Level 1 requirement (FR-01 to FR-12). Wave 2 at least starts every Level 2 requirement (FR-13 to FR-21). Everything else is Future, after the assignment is submitted. Every step in `backend/build-plan.md` and `ui/build-plan.md` is tagged with its wave. Follow that order.
- **Traceability (P2).** Every design element cites at least one FR or UC ID. New design work must be added to `project/traceability.md`. Don't invent FRs.
- **Decision IDs are stable.** These include G, P, B, BD, D, R, UI-n, F, FR and UC. Each decision is written in full in exactly one doc and cited by ID elsewhere.
- **Keep each design `.md` at or under 250 lines.** Split a doc rather than exceed the limit.
- **Leave the two historical docs unchanged.** `backend-graphing-design.md` and `page-and-ui-layout.md` are superseded but kept on purpose as a record. Don't edit or split them, and don't build from them.
- **Use the project's terms:** "Investigation page", "Documents page", "Investigation settings page", "incomplete node", "document".
- **Design changes go through the `project-designer` agent.** It does not write application code.

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
│   └── development/             # local-setup.md, vpn-connection.md, initial-plans.md, CS420 PDFs
│       └── claudedesigns/       # agreed design: master-plan.md, backend/, ui/, project/, design-history.md
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

The tree above shows the placeholder files as they exist today. The design replaces some of them: the pages become `InvestigationPage` (`/`), `DocumentsPage` (`/documents`) and the Investigation settings page (`/settings`), and users never draw nodes or edges by hand. The backend works out every relationship and returns Cytoscape elements from `GET /graph`. The file maps are in `backend/build-plan.md` and `ui/build-plan.md`.

- **apps/api** — FastAPI app in `src/txnweave_api/main.py`. Planned layering (currently empty files): `routes/` (HTTP endpoints) → `services/` (graph logic) → `db/` (database + models), with Pydantic `schemas/` and `config.py`. All endpoints are prefixed `/api`.
- **apps/web** — React SPA. `src/api/graphApi.ts` holds fetch calls to the backend using relative `/api/...` URLs. Planned pieces: `pages/` (HomePage, GraphPage), `components/` (graph canvas, toolbar, node/edge editors, property panel), and `src/graph/` (`cytoscapeConfig.ts`, `graphMapper.ts`), which suggests Cytoscape.js for rendering (not yet a dependency).
- **Frontend → backend wiring:** the Vite dev server proxies `/api` to `http://api:8000`, which is the Compose service hostname. Running the web app outside Compose needs that proxy target changed (e.g. to `http://localhost:8000`).
- `data/examples/sample-graph.json` is intended as sample graph input (currently empty).

## Gotchas

- Compose binds ports to `127.0.0.1` only. Remote access to the author's hosted instance goes through a VPN (`docs/development/vpn-connection.md`, not yet written).
