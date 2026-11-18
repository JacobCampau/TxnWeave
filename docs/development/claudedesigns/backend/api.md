# Backend: API (investigations and documents)

- **Status:** Agreed (from `backend-graphing-design.md` v3). Updated 2026-11-17 (user decisions): BD28 importance toggle, BD31 settings endpoints, BD32 rename rules.
- **Scope:** The full HTTP surface under `/api`: the endpoint table (including graph, export and import rows, whose details live in their own docs), the error body, the Investigation entity and `InvestigationOut`, investigation behavior (create, list, resume, delete, retention), document create/update/delete rules and status codes, JSON examples, and the sensitive-data handling rules for requests, responses and logs.
- **Master plan:** [../master-plan.md](../master-plan.md)
- **Related:** [data-model.md](data-model.md) (`DocumentIn` / `DocumentOut` fields), [persistence.md](persistence.md) (commits, cascades, uniqueness check, BD7 retention), [relationship-resolution.md](relationship-resolution.md) (placeholders, `referenced_by`, promotion), [graph-output.md](graph-output.md) (`GraphOut`), [csv-save-load.md](csv-save-load.md) (export/import), [../ui/app-shell.md](../ui/app-shell.md) (StartDialog, Save/Load)

## Decisions
| # | Decision | Rationale | Alternatives considered |
|---|---|---|---|
| B3 | Every document belongs to an **investigation**. All document, graph and export routes are nested under `/api/investigations/{investigation_id}` | Keeps New, Load and Resume from mixing cases | One global data set |
| B9 | One generic `/documents` resource takes a **Pydantic discriminated union** on the `type` field | Five routes instead of twenty | Separate routes per type |
| B16 | The investigation records `last_exported_at`. `has_unsaved_changes` is true when the investigation has at least one document and has never been exported, or `updated_at > last_exported_at` | Once the database is the autosave, "unsaved changes" (D5) means "changed since the last CSV save" | Frontend-only tracking |
| BD8 | A custom `RequestValidationError` handler removes Pydantic's `input` echo from 422 responses | Accepted default (OQ-11). Stops card numbers being echoed back | Default 422 body |
| BD28 | **Importance toggle:** `PATCH /investigations/{iid}/documents/{doc_id}` with the body `{"important": bool}` (no other field is allowed: 422) sets only the flag and returns `DocumentOut`. On a placeholder ID it returns 409 `placeholder_not_editable` (BD27). PUT still carries `important` too | The PropertyPanel toggles importance without sending the whole document (D31) | Toggle only through a full PUT |
| BD31 | **Settings endpoints:** `GET`, `PUT` and `DELETE /investigations/{iid}/settings`. GET returns the effective values (defaults if no row exists). PUT takes the full `InvestigationSettingsIn` (BD29). DELETE resets to defaults and returns the default `InvestigationSettingsOut`, so the client needs no second call. Settings are presentation data: `GET /graph` doesn't include them, and the frontend builds its stylesheet from them (B12) | Matches B12's split. One resource keeps the routes thin | Embed settings in `GraphOut`; `POST .../settings/reset` |
| BD32 | **Rename:** `PATCH /investigations/{iid}` with `{name}`. The name is trimmed, and an empty result is stored as `null` (shown as "Untitled investigation"). More than 200 characters returns 422. A rename updates `updated_at`, because the name is exported (CSV row 2), so `has_unsaved_changes` becomes true. **Delete** stays `DELETE /investigations/{iid}` (1.3), which the UI now calls directly (D29) | FR-01 "edit" and "delete" (former F11) | Names excluded from unsaved changes |

## Investigation entity
| Field | Type | Notes |
|---|---|---|
| `id` | `int` | |
| `name` | `str \| None`, at most 200 characters | |
| `created_at`, `updated_at` | `datetime` (UTC, ISO 8601) | `updated_at` changes on every document write |
| `last_exported_at` | `datetime \| None` | Set by a successful export (B16) |
| `document_count`, `incomplete_count` | `int` | Computed. `incomplete_count` counts placeholders |
| `has_unsaved_changes` | `bool` | Computed (B16) |

**`InvestigationOut`:** `{id, name, created_at, updated_at, last_exported_at, document_count, incomplete_count, has_unsaved_changes}`.

## Endpoints
All paths are prefixed with `/api`. The app error body is `{"detail": {"code": "<code>", "message": "<text>", ...extra}}`. Validation errors use FastAPI's standard 422 body, minus `input`.

| Method | Path | Request | Response | Status codes |
|---|---|---|---|---|
| GET | `/investigations` | — | `InvestigationOut[]` | 200 |
| POST | `/investigations` | `{name?: string \| null}` | `InvestigationOut` | 201, 422 |
| GET | `/investigations/{iid}` | — | `InvestigationOut` | 200, 404 |
| PATCH | `/investigations/{iid}` | `{name: string \| null}` | `InvestigationOut` | 200, 404, 422 |
| DELETE | `/investigations/{iid}` | — | — | 204, 404 |
| GET | `/investigations/{iid}/documents` | optional `?type=` (repeatable), `?status=` | `DocumentOut[]` (saved + placeholders, ordered per 3.12) | 200, 404 |
| GET | `/investigations/{iid}/documents/{doc_id}` | — | `DocumentOut` (works for placeholder IDs) | 200, 404 |
| POST | `/investigations/{iid}/documents` | `DocumentIn` | `DocumentOut` | 201, 404, 409 `duplicate_key` (`existing_id`), 422 |
| PUT | `/investigations/{iid}/documents/{doc_id}` | `DocumentIn` | `DocumentOut` | 200, 404, 409 `duplicate_key` / `placeholder_not_editable`, 422 |
| PATCH | `/investigations/{iid}/documents/{doc_id}` | `{important: bool}` (BD28) | `DocumentOut` | 200, 404, 409 `placeholder_not_editable`, 422 |
| DELETE | `/investigations/{iid}/documents/{doc_id}` | — | — | 204, 404, 409 `placeholder_not_editable` |
| GET | `/investigations/{iid}/settings` | — | `InvestigationSettingsOut` (BD29) | 200, 404 |
| PUT | `/investigations/{iid}/settings` | `InvestigationSettingsIn` | `InvestigationSettingsOut` | 200, 404, 422 (including `indistinct_styles`) |
| DELETE | `/investigations/{iid}/settings` | — | `InvestigationSettingsOut` (defaults) | 200, 404 |
| GET | `/investigations/{iid}/graph` | — | `GraphOut` ([graph-output.md](graph-output.md)) | 200, 404 |
| GET | `/investigations/{iid}/export.csv` | — | `text/csv` attachment ([csv-save-load.md](csv-save-load.md)) | 200, 404 |
| POST | `/investigations/import?dry_run=` | multipart `file` | dry run: `ImportReport`. Otherwise: `{investigation, report}` | 200 (dry run), 201, 413, 422 |

## Behavior

### 1. Investigations
1.1 `POST /investigations` creates an empty investigation. This is "New investigation".
1.2 `GET /investigations` lists investigations, newest `updated_at` first. "Resume last session" uses the first item, and is shown only when the list is non-empty.
1.3 Deleting an investigation cascades to all its documents.
1.4 Retention follows BD7 ([persistence.md](persistence.md)). The frontend calls `DELETE /investigations/{old_id}` after New or Load when the old investigation was exported or the user chose Discard.
1.5 Rename follows BD32.
1.6 The user can also delete the active investigation explicitly (D29). The cascade in 1.3 removes its documents and its settings row (BD30).

### 2. Document create, update and delete
2.1 POST and PUT validate against the strict `*In` model. Invalid input returns 422 (with `input` removed, BD8).
2.2 A key that already belongs to another **saved** document in the same investigation returns 409 `duplicate_key` with `existing_id`.
  - For a Transaction, "the same key" means an equal full key tuple (BD1). Same number and date with a different store, or a blank register vs `"003"`, is **not** a duplicate.
  - Matching a placeholder is never a conflict. It is how promotion works (3.8).
2.3 PUT replaces the whole document. The `type` can't change (422). The key can change, including a Transaction's date, store or register. References that no longer match fall back to placeholders automatically (B4).
2.4 DELETE of a saved document returns 204. References to it re-resolve on the next read: to another candidate, to a placeholder, or to an ambiguous set.
2.5 PUT or DELETE on a placeholder ID returns 409 `placeholder_not_editable`. Placeholders become real only through a POST.
2.6 Every successful write updates `documents.updated_at` and `investigations.updated_at`, and commits immediately (B2).
2.7 A Misc node with no references is valid and appears unconnected.
2.8 A document may reference itself indirectly, for example a Transaction paid with gift card X where X's activation is that same Transaction. Both edges are produced.

2.11 Changing importance (PUT or the BD28 PATCH) is a document write. It follows 2.6 (updates `updated_at` and commits immediately).

(2.9 and 2.10, amount and store validation, are in [data-model.md](data-model.md).)

### 7. Investigation settings
7.1 `GET .../settings` never fails because no row exists. It returns the defaults with `is_default: true`.
7.2 `PUT .../settings` validates per BD29, creates or replaces the row (BD30), and updates `investigations.updated_at`.
7.3 `DELETE .../settings` deletes the row if one exists, updates `updated_at` if a row was deleted, and returns the defaults.

### 6. Sensitive data handling
6.1 No endpoint takes a gift card number in its path or query string.
6.2 Request and response bodies are never logged. Uvicorn's access log stays at its default. 422 responses have `input` stripped (BD8). Import messages show at most the last 4 digits of a card number.
6.3 The SQLite file is unencrypted and reachable only from 127.0.0.1 or the VPN (BD21).

## Examples

### `DocumentIn` (Transaction with a return)
```json
{
  "type": "transaction",
  "transaction_number": "00482913",
  "date": "2026-03-14",
  "time": "18:05",
  "store_number": "042",
  "register_number": null,
  "payments": [
    {"type": "gift_card", "gift_card_number": "6006491234567890123", "amount_cents": 25000},
    {"type": "cash", "gift_card_number": null, "amount_cents": -1250}
  ],
  "notes": null
}
```
Its key tuple is `("00482913", "2026-03-14", "042", "")`.

### Transaction placeholder `DocumentOut`
```json
{
  "id": "ph-transaction-5d0e7c21a9f4",
  "investigation_id": 1,
  "type": "transaction",
  "status": "incomplete",
  "title": "Transaction 11112222 · 05-01-2026 · Store 042",
  "transaction_number": "11112222",
  "date": "2026-05-01",
  "time": "09:41",
  "store_number": "042",
  "register_number": null,
  "payments": [],
  "notes": null,
  "referenced_by": [
    {"id": "15", "type": "gift_card", "title": "Gift Card …0123", "match": "exact"},
    {"id": "22", "type": "misc", "title": "Suspicious return", "match": "exact"}
  ],
  "created_at": null,
  "updated_at": null
}
```

## Acceptance criteria
- [ ] PUT or DELETE on a placeholder ID returns 409 `placeholder_not_editable`.
- [ ] After a save, `has_unsaved_changes` is true until the next export.
- [ ] No full gift card number appears in any graph response, element ID, URL, `title`, import message, 422 body or log line during the tests.

(Composite-uniqueness 409 criteria are in [persistence.md](persistence.md).)

- [ ] PATCH `{important: true}` on a saved document returns it marked and sets `has_unsaved_changes`. On a placeholder it returns 409. A body with any other field returns 422.
- [ ] Rename trims the name, stores blank as `null`, rejects 201 characters with 422, and sets `has_unsaved_changes`.
- [ ] Settings: GET on a fresh investigation returns the defaults with `is_default: true`. PUT then GET round-trips. DELETE returns the defaults.

## Course requirements
Traces: FR-01, FR-03 to FR-07, FR-09, FR-11, FR-12, FR-13, FR-14 (full map in [../project/traceability.md](../project/traceability.md)). Section 6, B15 and BD8 have no FR behind them; they are listed as untraced. FR-23, FR-24 and FR-26 wait for the IAM design (Future, P1).
