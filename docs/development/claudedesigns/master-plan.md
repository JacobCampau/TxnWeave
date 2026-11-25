# TxnWeave Master Plan

- **Status:** Agreed (reorganized from `backend-graphing-design.md` v3 and `page-and-ui-layout.md` v2, 2026-11-17; no content changes). Updated 2026-11-17 with the user's course-requirement decisions: P1, P2, BD27 here; BD28 to BD33 and D26 to D33 in feature docs ([history](design-history.md)). Updated 2026-11-23 to follow the activity diagrams: G4 narrowed; BD34 and D34 to D37 in feature docs. Updated 2026-11-24: `@types/cytoscape` dropped from the tech stack (`cytoscape` ≥3.35 ships its own types). Updated 2026-11-24 (user decision): node positions are saved on the server (D8 amended; BD35 to BD37 in the new [backend/node-positions.md](backend/node-positions.md); D38, UI-36 to UI-38). Updated 2026-11-24 (user-approved implementation plan): the CSV column layout is now in [backend/csv-save-load.md](backend/csv-save-load.md) 5.10, so it is no longer "still to come".
- **Source plans:** `docs/development/initial-plans.md`, `docs/development/CS420_Project_Discovery and Specification.pdf`, `docs/development/CS420_Project_Concept.pdf` (unread, F19)
- **History:** [design-history.md](design-history.md) holds the original version metadata, changelogs and follow-ups.

Read this file first. It holds what every feature doc assumes. Then load only the feature docs you need from the [index](#index).

## Purpose and users
TxnWeave is a graphing web app for retail security agents. It helps them visualize suspicious activity and long-running fraud cases, built with gift card fraud in mind. Agents enter store and transaction data as **documents** (Transaction, Gift Card, Online Order, Misc) through validated forms, and the backend works out every relationship between them and returns a graph. Unlike draw.io, users never draw nodes or connections themselves. Agents work at desktops.

There are two main pages:
- the **Investigation page**, which shows the auto-generated graph;
- the **Documents page**, where agents create, edit, search and filter the documents that become nodes.

A third page, the **Investigation settings page** (D26), changes the color and shape of each document type and deletes the investigation.

The project is also a CS 420 (HCI) course project. Where its pieces are:
- **Background** (problem, stakeholders, persona, interview findings, quality goals, risks): [project/context.md](project/context.md).
- **Course requirements:** functional requirements FR-01 to FR-27 and use cases UC01 to UC10, with their coverage, in [project/requirements.md](project/requirements.md).
- **Design-to-requirement map:** every design element mapped to an FR or UC (P2) in [project/traceability.md](project/traceability.md).
- **Build order:** the waves in P1.

Follow-ups that are still open (F7 to F10, F12 to F15, F19 to F22) don't change any agreed decision.

## Goals
**Backend**
- G1. One API produces the full Cytoscape element list for an investigation. The frontend never decides which nodes are connected.
- G2. Missing, partial, one-sided or ambiguous references never cause an error. They show up as incomplete nodes and edges.
- G3. Investigation data survives a browser crash or reload without the user doing anything (the plan's "saved occasionally").
- G4. The backend supports CSV export and import with a validity marker. A file without the marker is rejected (BD34). A file with the marker loads best-effort: bad rows are reported and skipped.
- G5. Every piece is small enough to review on its own: pure-function relationship resolution, thin routes, one service per concern.

**UI**
- An agent can start, resume, or load an investigation immediately on opening the app.
- An agent can create and edit Transaction, Gift Card, Online Order and Misc documents through validated forms.
- An agent can view the resulting graph, explore it (pan, zoom, drag, inspect a node, with every node's position kept across reloads), and export it as a PNG in landscape or portrait.
- Incomplete nodes are always visible and easy to find on both pages.
- The UI uses only the five palette colors, with WCAG-compliant black or white text.

## Project-wide non-goals / out of scope
Feature-specific non-goals live in their feature docs. These apply everywhere:
- Login, IAM and per-user ownership of investigations. A slot is reserved in the top bar for a future user menu. An IAM design is still to come.
- Concurrent edits: last write wins (BD23, [persistence](backend/persistence.md)).
- Undo (anywhere in the app). Saving unsaved form drafts in the browser (BD22).
- Mobile layout (desktop only, minimum width 1280px, D21).
- Database migrations and encryption at rest: see [persistence](backend/persistence.md) non-goals.
- Path finding, path highlighting and named paths. FR-15 and UC07 are met by importance instead (BD27).
- Searching on the graph. Document search is on the Documents page (D33).
- AI analysis of the graph (FR-27): future work. A forked build that runs only on the user's machine could keep the data local. No design yet.

## Cross-cutting principles
1. **Incomplete, never an error.** Missing or uncertain data becomes an incomplete node or edge, never an error status (G2). See [relationship-resolution](backend/relationship-resolution.md).
2. **Backend owns structure, frontend owns presentation** (G1, B12). Nodes, placeholders, matching, edges, status, classes, masking and titles are backend work. Labels, styles, layout and PNG export are frontend work. The backend only stores and returns the node positions the frontend saves (BD35). Exact split: [graph-output](backend/graph-output.md).
3. **Card numbers are sensitive** (B13, D10). Full numbers appear only in request/response bodies for documents, the PropertyPanel and the form.
4. **Every color comes from the five-color palette, text is black or white** (D19). See [color-system](ui/color-system.md).
5. **Small, reviewable steps.** The author reviews all code in manual-approval mode. Keep changes small and explainable (G5).
6. **Proportionate.** Early-stage, single-user, localhost or VPN only. Prefer the simplest approach.

## Cross-cutting decisions
These decisions affect several feature docs, so they live here. Feature docs refer to them by ID.

| # | Decision | Rationale | Alternatives considered |
|---|---|---|---|
| P1 | **Implementation waves** replace the course PDF's requirement levels. **Wave 1:** every Level 1 requirement (FR-01 to FR-12) is fully implemented. **Wave 2:** every Level 2 requirement (FR-13 to FR-21) is at least started. **Future:** everything else (Level 3 FR-22 to FR-27, open follow-ups, IAM), after the assignment is submitted. Every build step in [backend](backend/build-plan.md) and [ui](ui/build-plan.md) build plans is tagged with its wave | User decision. The PDF's "shown in prototype, but not fully implemented" was ambiguous (former F17) | Keep the PDF levels |
| P2 | **Every design element traces to at least one FR or UC ID** from the course PDF. The map is [project/traceability.md](project/traceability.md). Elements with no FR behind them are listed there explicitly, not given made-up FRs | User decision. Keeps scope tied to the stated requirements (RK-4) | No traceability |
| BD27 | **Importance.** A saved document has a stored boolean `important` (default `false`). **Edges are never marked directly:** an edge is important exactly when **both** of its end nodes are important. This is worked out on every graph read, so un-marking either node makes the edge stop being important automatically. **Placeholders can't be marked** because they aren't stored (B4). They are always `important: false`, and a promoted document starts unmarked. FR-15 (paths) and UC07 (named paths) are met by this: mark the nodes along a path, and the edges between them highlight | User decision (former F5, F16). Edges have no stored identity, and their IDs change when a CSV is imported, so a node flag is the only mark that survives export and import | Stored edge flags; named paths; path finding |
| B6 | Every ID-like number (transaction, order, gift card, store, register) is a **digits-only string**, never an integer. The maximum lengths are 8, 8, 24, 3 and 3. Matching is on the exact string as typed: leading zeros matter, and nothing is padded | INT overflows at 24 digits and drops leading zeros. This settles D25 (maximum length only, no exact length) | Exact lengths; left-padding before matching |
| B7 | Money is **integer cents** (`amount_cents`), with a magnitude cap of $99,999.99. Payment and history amounts are **signed**, from -9,999,999 to 9,999,999. The activation amount is **0 to 9,999,999** (BD25). What the sign means depends on whose point of view the amount is recorded from (BD25) | Floating point can't hold amounts like 0.10 exactly. The user said returns are frequent | `REAL`/float; non-negative only |
| B8 | Dates are ISO `YYYY-MM-DD` in the API and the database. Times are `HH:MM` 24-hour strings (`00:00` to `23:59`). The frontend converts its `MM-DD-YYYY` input to ISO. The CSV uses `MM-DD-YYYY` | ISO dates sort correctly as text, and Pydantic's `date` type validates them | `MM-DD-YYYY` everywhere |
| B13 | **Full gift card numbers never appear in a URL path, query string, graph payload, element ID, title, import message or log line.** The graph sends only a masked `display_key` (`…1234`). Placeholder IDs are hashes | Uvicorn's access log records URLs, and graph data ends up in PNG exports. Follows D10 | — |
| B15 | API JSON uses **snake_case** field names | Pydantic's default, no alias configuration | camelCase through aliases |
| BD25 | **Amount sign convention.** Every amount is recorded from the point of view of the document that holds it. **Transaction / Online Order / Misc payment rows (transaction view):** positive = the customer paid with this tender, negative = money returned to this tender. **Gift Card activation and history amounts (card view):** positive = value went **onto** the card (activation, reload, return credited to the card), negative = value spent **from** the card. **Whenever the backend relates the two, the sign flips: card amount = −(payment amount).** This applies to placeholder prefill (3.7), any amount shown on or computed for an edge, and any future amount comparison or check (3.14). **Activation amounts must be at least 0**, because an activation always puts value onto the card. A zero activation is allowed | User decision (v3): "a return on a gift card should show negative on the transaction but positive in the gift card". Spends being negative in card view follows from the same flip | Spends recorded as positive in history (would need a second rule for loads, and would break the single flip) |

## Glossary
| Term | Meaning |
|---|---|
| Investigation | One case. Every document belongs to exactly one investigation (B3). Has an optional name (D4) |
| Investigation page | Route `/`. Shows the auto-generated graph |
| Documents page | Route `/documents`. List plus form where agents create and edit documents |
| Document | A saved Transaction, Gift Card, Online Order or Misc record. Each document is one graph node |
| Node / edge | A graph element. Nodes are documents or placeholders. Edges are derived from reference fields, never drawn by users |
| Reference | A field in one document that points at another (activation, history entry, payment card number, Misc transaction/order number). Rules R1 to R6 |
| Incomplete node / placeholder | A node for something that is referenced but has no document yet. Derived on every read, never stored (B4). Status `incomplete` |
| Incomplete edge | An edge with a placeholder at either end, or from an ambiguous match (B5, BD15). Drawn dashed |
| Promotion | Saving a real document that matches a placeholder, which replaces it automatically |
| Natural key / key tuple | A document's identity within an investigation. Transaction: `(transaction_number, date, store_number, register_number)`. Gift Card: card number. Online Order: order number. Misc: none (B14) |
| Exact / ambiguous match | A reference that matches one candidate is `exact`. One that matches two or more links to each, `ambiguous` (BD3) |
| Transaction view / card view | The two points of view for amounts (BD25) |
| Edge kinds | `activated`, `used_in`, `related` (BD6) |
| `title` | Backend-built display title for a document (BD24) |
| `display_key` | The masked short key shown on a graph node |
| Autosave | The server-side SQLite database. Every successful save commits immediately (B2) |
| Unsaved changes | Changed since the last CSV export (B16) |
| Validity marker | First CSV row `TXNWEAVE_SAVE,format_version,1` (BD12) |
| `ref` / `parent_ref` | Export-local CSV row references (BD10) |
| Investigation settings page | Route `/settings`. Per-investigation color and shape for each document type, the important-edge color, reset to defaults, and Delete investigation (D26 to D29) |
| Important node / important edge | A document marked important (BD27). An edge is important when both of its end nodes are |
| Wave 1 / Wave 2 / Future | Implementation waves (P1) |
| Palette tokens | ink #131313, slate #394249, mist #D2CDCB, rose #D26D6F, crimson #C11E20 |

## Tech stack
| Layer | Choice |
|---|---|
| Backend | Python ≥3.12, FastAPI, Pydantic, SQLAlchemy 2.0 typed ORM, SQLite file (B1). `python-multipart` for uploads. Dev: `pytest`, `httpx` |
| Frontend | React 19, Vite 6, TypeScript, `react-router-dom`, `cytoscape` (≥3.35, bundles its own TypeScript types, so no `@types/cytoscape`) |
| Runtime | Docker Compose, ports bound to 127.0.0.1. Remote access to the hosted instance is through a VPN. The Vite dev server proxies `/api` to `http://api:8000` |

## Architecture
- **Backend layering** (`apps/api/src/txnweave_api/`): thin `routes/` → `services/` (logic; relationship resolution and graph building are pure functions) → `db/` (engine, ORM models). Pydantic models in `schemas/`, settings in `config.py`. All endpoints are prefixed `/api`. Full file map: [backend/build-plan.md](backend/build-plan.md).
- **Frontend** (`apps/web/src/`): `pages/` (InvestigationPage, DocumentsPage, SettingsPage), `components/`, `graph/` (`cytoscapeConfig.ts`, `graphMapper.ts`), `styles/` (`palette.ts`, `global.css`), `api/graphApi.ts` with relative `/api/...` URLs. Full component list in the UI docs, order in [ui/build-plan.md](ui/build-plan.md).
- **Data flow:** form → `POST/PUT /documents` (commits immediately) → `GET /graph` returns Cytoscape elements → `graphMapper.ts` adds labels → Cytoscape renders.

## Conventions
- **Decision IDs** are kept from the original docs so cross-references stay valid: `G1`–`G5` backend goals; `P1`, `P2` project decisions; `B1`–`B17` and `BD1`–`BD37` backend decisions (there is no BD20); `D1`–`D38` UI decisions; `R1`–`R6` reference rules; behavior numbers `1.x`–`8.x` are the backend behavior sections (`8.x` is node positions); UI behaviors are `UI-1` to `UI-38`; `F1` to `F22` follow-ups (all in [design-history.md](design-history.md)). Course-document IDs are kept exactly as the PDF writes them: `FR-01` to `FR-27`, `UC01` to `UC10`. Project-level IDs from the course pass: `S1`, `S2` success criteria, `NQ-1` to `NQ-8` quality goals, `RK-1` to `RK-6` risks, `S-1` suggestion.
- Each decision is written out in full in exactly one doc. Other docs cite the ID.
- Forms and CSV show dates as `MM-DD-YYYY`. The API and database use ISO (B8).
- Negative amounts are displayed as `-$25.00`.
- Use the user's terms consistently: "Investigation page", "Documents page", "incomplete node".

## Index
| Doc | What it covers |
|---|---|
| [backend/data-model.md](backend/data-model.md) | Value types, the four document types, payments, history entries, keys, titles, Pydantic schema split, plan inconsistencies |
| [backend/persistence.md](backend/persistence.md) | SQLite file, SQLAlchemy models, tables, indexes, uniqueness check, autosave, retention, concurrency |
| [backend/api.md](backend/api.md) | Endpoint table, error body, investigation and document behavior, `InvestigationOut`, JSON examples, sensitive-data handling |
| [backend/relationship-resolution.md](backend/relationship-resolution.md) | Reference rules R1–R6, matching, ambiguity, placeholders, prefill, promotion, edge merging, `referenced_by`, money flip |
| [backend/graph-output.md](backend/graph-output.md) | `GET /graph`, `GraphOut`, node/edge data fields, classes, frontend vs backend split |
| [backend/csv-save-load.md](backend/csv-save-load.md) | CSV export and import: marker, sections, cell rules, parsing, dry run, `ImportReport` |
| [backend/node-positions.md](backend/node-positions.md) | Saved node positions: `node_positions` table, `PUT`/`PATCH .../layout`, delete cleanup, promotion carry-over (BD35 to BD37, 8.x) |
| [backend/build-plan.md](backend/build-plan.md) | Backend file map, dependencies, Compose volume, build order |
| [ui/color-system.md](ui/color-system.md) | Palette tokens, contrast tables, per-element color usage, transparency rule |
| [ui/app-shell.md](ui/app-shell.md) | Routes, TopBar, StartDialog and the start flow (Starting An Investigation diagram), unsaved-changes prompts, Save/Load, banners, toasts, keyboard, width |
| [ui/investigation-page.md](ui/investigation-page.md) | Graph canvas, node/edge styles, layout, saved positions and new-node placement, toolbar, PropertyPanel, PNG export |
| [ui/documents-page.md](ui/documents-page.md) | Document list, per-type forms, inputs, validation, repeatable rows, delete |
| [ui/settings-page.md](ui/settings-page.md) | Investigation settings page: per-type color and shape, important-edge color, reset to defaults, Delete investigation |
| [ui/build-plan.md](ui/build-plan.md) | Frontend dependencies and build order, tagged by wave |
| [project/context.md](project/context.md) | Draft. Problem statement, stakeholders, persona, interview findings, success criteria, quality goals (NQ), risks (RK), similar systems, waves |
| [project/requirements.md](project/requirements.md) | FR-01 to FR-27 and UC01 to UC10 with coverage status, wave, and terminology mapping |
| [project/traceability.md](project/traceability.md) | Every decision, behavior and component mapped to FR or UC IDs (P2), plus the untraced list |
| [design-history.md](design-history.md) | Original statuses, changelogs, follow-ups F1 to F22 (closed and open), and the note on the kept historical docs |
| `backend-graphing-design.md`, `page-and-ui-layout.md` | **Historical records, kept on purpose and superseded.** Don't implement from them. Exempt from the 250-line limit ([history](design-history.md)) |

Still to come: an IAM design.
