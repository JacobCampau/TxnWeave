# Backend: Build Plan

- **Status:** Agreed (from `backend-graphing-design.md` v3, "Implementation guidance"). Updated 2026-11-17 (user decisions): steps tagged by wave (P1), and new steps for importance (BD27, BD28), settings (BD29 to BD31, BD33) and rename (BD32). Updated 2026-11-23: step 9 adds the BD34 marker rejection. Updated 2026-11-24: step 13, saved node positions (BD35 to BD37).
- **Scope:** Where every backend file lives and what it contains, dependencies to add, the Compose change for the database volume, and the suggested order of small, reviewable steps for building the backend across all backend feature docs.
- **Master plan:** [../master-plan.md](../master-plan.md)
- **Related:** [data-model.md](data-model.md), [persistence.md](persistence.md), [api.md](api.md), [relationship-resolution.md](relationship-resolution.md), [graph-output.md](graph-output.md), [csv-save-load.md](csv-save-load.md), [node-positions.md](node-positions.md)

## Where code lives (`apps/api/src/txnweave_api/`)
| File | Contents |
|---|---|
| `config.py` | `DB_PATH` from `TXNWEAVE_DB_PATH`, `MAX_IMPORT_BYTES = 5_000_000`. Plain `os.environ` |
| `db/database.py` | engine, session factory, foreign-key pragma listener, `init_db()`, the `get_session` dependency |
| `db/models.py` | ORM classes for the 10 tables (including `investigation_settings`, BD30, and `node_positions`, BD35) |
| `schemas/common.py` | Shared value types |
| `schemas/documents.py` | `PaymentIn/Out`, `*In`, `*Out`, `DocumentIn`, `DocumentOut`, `DocumentRef`, `ImportanceIn` (BD28) |
| `schemas/investigation.py` | `InvestigationCreate`, `InvestigationUpdate`, `InvestigationOut` |
| `schemas/settings.py` | `NodeColorToken`, `EdgeColorToken`, `NodeShape`, `TypeStyle`, `InvestigationSettingsIn/Out`, `DEFAULT_SETTINGS` (BD29) |
| `schemas/graph.py` | `GraphOut`, `NodeData`, `EdgeData`, `CyNode` (with optional `position`, 4.5), `CyEdge` |
| `schemas/layout.py` | `NodeId`, `Position`, `LayoutIn` (BD36) |
| `schemas/imports.py` | `ImportReport`, `ImportProblem` |
| `services/keys.py` | `transaction_key(doc) -> tuple[str, str, str, str]`, `TxnRef` (known components), `matches(ref, candidate) -> bool`. Small and pure, with its own tests |
| `services/document_service.py` | create, update, delete, set importance, duplicate-key check, ORM ↔ schema conversion, titles |
| `services/relationship_service.py` | **pure** `resolve(investigation_id, docs) -> Resolution(placeholders, links, referenced_by)` |
| `services/graph_service.py` | **pure** `build_graph(resolution, docs, positions) -> GraphOut`, including node and edge `important` (4.3, 4.4) and node `position` (4.5) |
| `services/layout_service.py` | get, replace and upsert positions, delete one, promotion carry-over (8.1 to 8.6) |
| `services/investigation_service.py` | Investigation CRUD, rename rules (BD32), `updated_at` bump, unsaved-changes flag |
| `services/settings_service.py` | get with defaults, replace with the distinctness check, reset (BD29 to BD31) |
| `services/money.py` | `parse_money_cell(text) -> int` (cents, using `Decimal`), `format_money_cell(cents) -> str`, and `card_view(payment_amount_cents) -> int`, the **only** place the BD25 sign flip is written (3.14) |
| `services/csv_service.py` | export and import, including the `important` column and the `settings` section (BD33) |
| `routes/investigations.py`, `routes/documents.py`, `routes/graphs.py`, `routes/imports.py`, `routes/settings.py`, `routes/layout.py` | Thin routers. `main.py` calls `include_router(..., prefix="/api")` and runs `init_db()` in the lifespan |
| `tests/` | `test_keys.py`, `test_relationship_service.py`, `test_graph_service.py`, `test_money.py`, `test_documents_api.py`, `test_settings.py`, `test_layout.py` |

## Dependencies to add
`sqlalchemy>=2.0,<3`, `python-multipart`. Dev-only: `pytest`, `httpx`.

## Compose
Add a named volume `txnweave-data:/data` to the `api` service, and set `TXNWEAVE_DB_PATH=/data/txnweave.db`.

## Suggested order (small, reviewable steps)
Each step is tagged with its wave (P1) and the requirements it serves.

| # | Wave | Step | FRs |
|---|---|---|---|
| 1 | Wave 1 | `config.py`, `db/database.py`, the Investigation model and routes (create, list, get, rename per BD32, delete), pytest setup | FR-01 |
| 2 | Wave 1 | Shared value types (including signed `AmountCents`), and Transaction end to end (model, payments, service, routes) with the composite duplicate check. The `documents.important` column is added here so the table never changes later; it stays `false` until step 11 | FR-03, FR-07, FR-12 |
| 3 | Wave 1 | Gift Card (with history), Online Order and Misc, one type per change | FR-04 to FR-07, FR-12 |
| 4 | Wave 1 | `services/keys.py` with tests for the matching table in 3.3 | FR-08 |
| 5 | Wave 1 | `relationship_service.resolve`: exact, ambiguous and zero-match references, the placeholder pass (3.5), prefill, merging, determinism. Table-driven tests | FR-08 |
| 6 | Wave 1 | Placeholders and `referenced_by` in the document endpoints, and the 409 rules | FR-07, FR-08, FR-09 |
| 7 | Wave 1 | `graph_service` and `GET /graph`. Fill `data/examples/sample-graph.json` with a real response | FR-02 |
| 8 | Wave 1 | The rest of `services/money.py` (cell parsing and formatting), then the CSV export with `has_unsaved_changes`. (`card_view` is needed earlier, in step 5, for placeholder prefill) | FR-11 |
| 9 | Wave 1 | CSV import with `dry_run` and the report. The marker check runs first and rejects markerless files with 422 `not_a_txnweave_file` (BD34). This also delivers FR-19 (Wave 2) and FR-22 (Future) early | FR-11, FR-19, FR-22 |
| 10 | Wave 1 | Hardening: the 422 `input` stripping handler and a log review. **No FR behind it** (sensitive data, see [traceability](../project/traceability.md)) | — |
| 11 | Wave 2 | Importance: `important` in `*In` / `*Out`, the BD28 `PATCH`, graph 4.3 and 4.4, and the CSV `important` column (BD33a) | FR-14, FR-15, UC06, UC07 |
| 12 | Wave 2 | Settings: the `investigation_settings` model, `settings_service`, `routes/settings.py` (BD29 to BD31), and the CSV `settings` section (BD33b, 5.9) | FR-13, UC08 |
| 13 | Wave 2 | Saved node positions ([node-positions](node-positions.md)): (a) the `NodePosition` model, `schemas/layout.py`, `layout_service` get/replace/upsert, `routes/layout.py` (PUT, PATCH), and `build_graph(..., positions)` (4.5), with `test_layout.py` and new `test_graph_service.py` cases. (b) Delete a document's position on DELETE (8.5). (c) Promotion carry-over in `document_service` (BD37, 8.6), with tests for a Gift Card placeholder, an unknown-store Transaction placeholder, and a PUT that keeps the document's own position | FR-10, FR-18 (weak) |
| — | Future | IAM (FR-23, FR-24, FR-26), FR-25 gift card history view, FR-27 AI analysis, open follow-ups F10, F13 to F15, and F22 (positions in the CSV) | — |

## Acceptance criteria
- [ ] `keys`, `relationship_service`, `graph_service` and `money` have unit tests that run without a database.
- [ ] Every Wave 1 step is complete before the assignment's Wave 1 milestone, and each Wave 2 step has at least been started (P1).
