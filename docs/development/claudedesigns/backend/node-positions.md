# Backend: Saved Node Positions

- **Status:** Agreed (user decisions 2026-11-24, reversing D8's "dragged positions are not saved"; see [../design-history.md](../design-history.md)).
- **Scope:** Storing every node's position on the Investigation page per investigation: the `node_positions` table, the `PUT` and `PATCH .../layout` endpoints, how positions reach the frontend through `GET /graph` (4.5), what happens to a position when a document is deleted, and how a promoted document takes over its placeholder's position. The layout itself (where new nodes go, Re-layout, the export preview) is frontend work and lives in [../ui/investigation-page.md](../ui/investigation-page.md) (D8, D38, UI-36 to UI-38).
- **Master plan:** [../master-plan.md](../master-plan.md) (B12, B13, principle 6)
- **Related:** [persistence.md](persistence.md) (tables), [api.md](api.md) (endpoint rows), [graph-output.md](graph-output.md) (4.5), [relationship-resolution.md](relationship-resolution.md) (3.6 placeholder IDs, 3.8 promotion), [csv-save-load.md](csv-save-load.md) (positions are not exported)

## Non-goals
- Computing any layout on the backend. The backend only stores and returns positions the frontend sends.
- Positions in the CSV export and import. A loaded investigation starts with the automatic layout (F22, Future).
- Saving zoom and pan (the viewport). Every page open fits the graph (UI-38).
- Cleaning up positions of placeholders that no longer exist. They are ignored when read (8.4).

## Decisions
| # | Decision | Rationale | Alternatives considered |
|---|---|---|---|
| BD35 | **Every node's position is stored on the server**, one row per `(investigation_id, node_id)` in `node_positions`. This includes incomplete nodes, keyed by their placeholder ID (3.6). Positions are **not** in the CSV and **not** an unsaved change: a position write never updates `investigations.updated_at`, so `has_unsaved_changes` (B16) and the Resume row's "Last saved" (UI-30) are unaffected | User decision: dragged nodes stay put across reloads, and no node moves on its own between loads. Leaving positions out of the CSV keeps D8's original reason (no layout data in the CSV). Counting them as unsaved would prompt for an export that can't capture them | Only dragged nodes saved; document nodes only; positions in the CSV (F22) |
| BD36 | **Two endpoints on one resource:** `PUT /investigations/{iid}/layout` **replaces** the whole map (first layout, Re-layout); `PATCH /investigations/{iid}/layout` **adds or updates** only the listed nodes (drags, new-node placement). Both take `LayoutIn` and return 204. Positions come back to the frontend as an optional `position` on each node in `GET /graph` (4.5), so there is no `GET .../layout` | One fetch for the graph and its positions. PUT gives Re-layout an atomic replace that also drops stale rows | `DELETE` then `PATCH`; one `PUT .../layout/{node_id}` per node; a separate `GET .../layout` |
| BD37 | **Promotion keeps the position.** When saving a document makes a placeholder of the same type disappear (3.8), the saved document's node takes over that placeholder's stored position. Worked out in `document_service` by comparing the placeholder IDs from `resolve()` before and after the write (8.6) | User decision: a promoted node shouldn't jump. Comparing before and after works even when the IDs differ, for example a Transaction placeholder with an unknown store (`?` in its hash) promoted by a document with a store | Match by hash (fails for unknown-store placeholders); no carry-over |

## Data model
**Table `node_positions`** (BD35):

| Column | Type | Rule |
|---|---|---|
| `investigation_id` | `INTEGER NOT NULL` | `FK→investigations.id ON DELETE CASCADE` |
| `node_id` | `TEXT NOT NULL` | A saved document ID as text (`"12"`) or a placeholder ID (`"ph-gift_card-5f4bd08dab58"`). No FK, because placeholders aren't stored (B4) |
| `x`, `y` | `REAL NOT NULL` | Cytoscape model coordinates |

Primary key `(investigation_id, node_id)`. ORM class `NodePosition` in `db/models.py`.

**Schemas** (`schemas/layout.py`):

| Name | Python | TypeScript | Rules |
|---|---|---|---|
| `NodeId` | `Annotated[str, StringConstraints(pattern=NODE_ID_PATTERN)]` | `string` | Document ID or placeholder ID (pattern below). There are no Misc placeholders (3.5) |
| `Position` | `BaseModel`: `x: float`, `y: float`, `model_config = ConfigDict(extra="forbid", allow_inf_nan=False)` | `{x: number; y: number}` | Each value finite, with `-1_000_000 <= v <= 1_000_000` |
| `LayoutIn` | `BaseModel`: `positions: dict[NodeId, Position]`, `extra="forbid"` | `{positions: Record<string, {x: number; y: number}>}` | 0 to 5,000 entries. An empty map is valid (PUT clears everything; PATCH does nothing) |

```python
NODE_ID_PATTERN = r"^([1-9][0-9]{0,18}|ph-(transaction|gift_card|online_order)-[0-9a-f]{12})$"
```

Example `LayoutIn`:
```json
{"positions": {"12": {"x": 140.5, "y": -32.0}, "ph-gift_card-5f4bd08dab58": {"x": 260.0, "y": 18.25}}}
```

## Behavior
### 8. Node positions
8.1 `PUT .../layout` deletes every `node_positions` row of the investigation and inserts the given ones, in one transaction. It commits immediately (B2) but does not touch `updated_at` (BD35).

8.2 `PATCH .../layout` inserts or updates (SQLite `INSERT ... ON CONFLICT DO UPDATE`) each listed node, in one transaction, and leaves other rows alone. Same commit and `updated_at` rule as 8.1.

8.3 Neither endpoint checks that a node ID exists in the current graph. That would mean resolving the graph on every drag. A position for a node that isn't in the graph is harmless (8.4).

8.4 `GET /graph` loads the investigation's rows once and passes them to `build_graph` (4.5). Rows whose `node_id` isn't a node in this response are ignored and stay in the table until the next `PUT`, document delete (8.5) or investigation delete.

8.5 **Deleting a document** (2.4) deletes its row (`node_id = str(doc_id)`) in the same transaction. **Deleting an investigation** removes all its rows through the cascade (1.3).

8.6 **Promotion (BD37).** On a successful POST, and on a PUT, of a document of type T (not Misc), inside the write transaction:
1. Before the write: `before = {placeholder IDs of type T}` from `resolve()` on the investigation's saved documents.
2. Do the write. After it: `after = {placeholder IDs of type T}` from `resolve()` again.
3. `gone = before − after`, ordered as in 3.12. If `gone` is empty, stop.
4. If the saved document **already has** a row (a PUT of a document the user has placed), keep its position and stop.
5. Otherwise take the **first** ID in `gone` that has a row, and give the saved document that position: insert a row for `str(doc_id)` with the same x and y, and delete the placeholder's row. Rows for any other IDs in `gone` are left alone (8.4).

Why "same type" is enough: no reference rule links a document to another document of its own type (R1 to R6), so the only way a type-T save can remove a type-T placeholder is by matching it. Resolving twice is cheap because investigations are small (B11; target in F10). The position step must never make the document write fail. If it raises, log the error type (never card numbers, 6.2), skip the carry-over, and still commit the document.

8.7 **Changed placeholder IDs.** A placeholder ID changes when the placeholder's key changes (3.6), for example when an edit gives a reference a store. The node then has no saved position and is placed as a new node (D38). The old row is ignored (8.4). Accepted by the user.

8.8 **CSV.** Export writes no positions. Import creates no rows, so the Investigation page lays out the loaded investigation from scratch (UI-38) and saves the result.

8.9 **Errors.** Unknown investigation: 404. An invalid body (bad node ID, non-finite or out-of-range value, more than 5,000 entries, extra fields): 422 with `input` stripped (BD8). Concurrent writes: last write wins (BD23).

## Interfaces
| Method | Path | Request | Response | Status codes |
|---|---|---|---|---|
| PUT | `/investigations/{iid}/layout` | `LayoutIn` | — | 204, 404, 422 |
| PATCH | `/investigations/{iid}/layout` | `LayoutIn` | — | 204, 404, 422 |

Node IDs appear only in the body, never in the URL. They contain no card numbers anyway (3.6, B13).

## Implementation guidance
- `db/models.py`: `NodePosition`. `schemas/layout.py`: `NodeId`, `Position`, `LayoutIn`.
- `services/layout_service.py`: `get_positions(session, iid) -> dict[str, tuple[float, float]]`, `replace_positions(...)`, `upsert_positions(...)`, `delete_position(session, iid, node_id)`, `inherit_promoted_position(session, iid, doc_id, gone_ids)`.
- `routes/layout.py`: the two thin routes. `routes/graphs.py` passes `get_positions(...)` into `build_graph`.
- `services/document_service.py`: the 8.5 delete and the 8.6 before/after step.
- Order: backend build-plan step 13 (Wave 2).

## Acceptance criteria
- [ ] `PATCH` two positions, then `GET /graph`: those nodes carry `position` with the same x and y. Other nodes have no `position`.
- [ ] `PUT` with one entry leaves exactly one row. `PUT {"positions": {}}` leaves none.
- [ ] A body with `"x": NaN`, an x of 1,000,001, the node ID `"ph-misc-…"`, a card number as the node ID, or an extra field returns 422. An unknown investigation returns 404.
- [ ] After `PATCH`, the investigation's `updated_at` and `has_unsaved_changes` are unchanged.
- [ ] Deleting document 12 removes the row `"12"`. Deleting the investigation removes all its rows.
- [ ] A Gift Card placeholder with a saved position, then a POSTed Gift Card with that number: the new document's node has the placeholder's position, and the placeholder's row is gone.
- [ ] A Transaction placeholder with store unknown (`?`) and a saved position, then a POSTed Transaction with the same number and date and store `042`: the new node inherits the position.
- [ ] A PUT that promotes a placeholder for a document that already has a position keeps the document's own position.
- [ ] Export then import: the new investigation has no rows.

## Course requirements
Traces: FR-10, FR-18 (both weak; see [../project/traceability.md](../project/traceability.md)). Wave 2 (P1).
