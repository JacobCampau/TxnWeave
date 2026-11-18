# Backend: Persistence (SQLite and ORM)

- **Status:** Agreed (from `backend-graphing-design.md` v3). Updated 2026-11-17 (user decisions): `documents.important` (BD27) and the `investigation_settings` table (BD30).
- **Scope:** How investigation data is stored: the SQLite file and its location, the SQLAlchemy 2.0 models, every table, column and CHECK constraint, indexes, where the duplicate-key check runs, how updates replace child rows, and the storage-level decisions (the database is the autosave, retention of old investigations, unencrypted storage, last write wins). Field meanings and validation are in [data-model.md](data-model.md).
- **Master plan:** [../master-plan.md](../master-plan.md)
- **Related:** [data-model.md](data-model.md) (fields and key tuple), [api.md](api.md) (writes that commit, investigation delete), [build-plan.md](build-plan.md) (config, Compose volume)

## Non-goals
- Database migrations (Alembic). Before the first release, a schema change means deleting the dev database file.
- Encryption at rest (BD21).

## Decisions
| # | Decision | Rationale | Alternatives considered |
|---|---|---|---|
| B1 | SQLite file accessed through **SQLAlchemy 2.0** typed ORM (`Mapped[...]` style). Tables are created at startup with `Base.metadata.create_all`. No Alembic yet | SQLAlchemy is the standard choice with FastAPI. Typed models are readable, and cascading deletes of child rows come for free | Raw `sqlite3`; SQLModel |
| B2 | The server-side SQLite database **is the autosave**. Every successful document save is committed straight away. "Resume last session" reopens the most recently updated investigation | Meets G3 with no extra machinery | Browser `localStorage` snapshots; periodic CSV snapshots on the server |
| B10 | Database layout: a shared `documents` table, one detail table per type keyed by `document_id`, and child tables `payments` and `gift_card_history_entries` | Document IDs are unique across types, notes live in one place, and payments need one foreign key | One table per type; a JSON column |
| BD4 | The duplicate-key check stays in the **service layer**, comparing the normalized key tuple (blank becomes `""`). There is no database UNIQUE index | Accepted default for OQ-10. Single user, so a check inside the write transaction is enough | Copy `investigation_id` onto the detail tables and add a UNIQUE expression index |
| BD7 | Old investigations: after New or Load, the frontend deletes the previous investigation once it has been exported (`has_unsaved_changes == false`) or the user chose Discard. The database then normally holds one working investigation, and CSV files are the archive | Accepted default (OQ-7). Keeps less sensitive data on the server | Keep everything; age-based cleanup |
| BD21 | The SQLite file is stored unencrypted. Access is limited to localhost or the VPN | Accepted default (OQ-8) | SQLCipher |
| BD22 | A form still being typed is lost if the browser crashes | Accepted default (OQ-12) | `sessionStorage` drafts |
| BD23 | Concurrent edits: last write wins, no locking | Accepted default (OQ-13) | Optimistic locking |
| BD30 | **Per-investigation settings** live in one `investigation_settings` row per investigation, which exists only after the first settings save. **No row means the defaults** (BD29). Reset to defaults deletes the row. Every settings write or reset updates `investigations.updated_at`, so `has_unsaved_changes` becomes true (B16), because settings are exported (BD33). Importance is the `documents.important` column (BD27) | Explicit columns with CHECKs are easy to review. "No row = defaults" makes reset trivial | A JSON column; columns on `investigations` |

## Database file
The file location comes from `TXNWEAVE_DB_PATH` (default `./data/txnweave.db` locally and `/data/txnweave.db` in the container, on a named volume). `PRAGMA foreign_keys=ON` is set on every connection through a SQLAlchemy `connect` listener.

## Tables
| Table | Columns |
|---|---|
| `investigations` | `id INTEGER PK`, `name TEXT NULL`, `created_at TEXT NOT NULL`, `updated_at TEXT NOT NULL`, `last_exported_at TEXT NULL` |
| `documents` | `id INTEGER PK`, `investigation_id INTEGER NOT NULL FK→investigations.id ON DELETE CASCADE`, `type TEXT NOT NULL CHECK(type IN ('transaction','gift_card','online_order','misc'))`, `notes TEXT NULL`, `important INTEGER NOT NULL DEFAULT 0 CHECK(important IN (0,1))`, `created_at TEXT NOT NULL`, `updated_at TEXT NOT NULL` |
| `investigation_settings` | `investigation_id INTEGER PK FK→investigations.id ON DELETE CASCADE`; `transaction_color`, `gift_card_color`, `online_order_color`, `misc_color` `TEXT NOT NULL CHECK(... IN ('ink','slate','mist','rose','crimson'))`; `transaction_shape`, `gift_card_shape`, `online_order_shape`, `misc_shape` `TEXT NOT NULL CHECK(... IN ('ellipse','rectangle','round-rectangle','triangle','diamond','hexagon','octagon','star'))`; `important_edge_color TEXT NOT NULL CHECK(important_edge_color IN ('ink','slate','crimson'))`; `updated_at TEXT NOT NULL`. The distinctness rule (BD29) is checked in the service layer |
| `transactions` | `document_id INTEGER PK FK→documents.id ON DELETE CASCADE`, `transaction_number TEXT NOT NULL`, `date TEXT NOT NULL`, `time TEXT NOT NULL`, `store_number TEXT NOT NULL`, `register_number TEXT NULL` |
| `gift_cards` | `document_id PK FK`, `gift_card_number TEXT NOT NULL`, `activation_transaction_number TEXT NOT NULL`, `activation_date TEXT NOT NULL`, `activation_time TEXT NOT NULL`, `activation_store_number TEXT NULL`, `activation_amount_cents INTEGER NULL CHECK(activation_amount_cents BETWEEN 0 AND 9999999)` |
| `gift_card_history_entries` | `id INTEGER PK`, `gift_card_document_id INTEGER NOT NULL FK→documents.id ON DELETE CASCADE`, `position INTEGER NOT NULL`, `transaction_number TEXT NOT NULL`, `date TEXT NOT NULL`, `time TEXT NOT NULL`, `store_number TEXT NULL`, `amount_cents INTEGER NULL CHECK(amount_cents BETWEEN -9999999 AND 9999999)` |
| `online_orders` | `document_id PK FK`, `order_number TEXT NOT NULL`, `placed_date TEXT NOT NULL`, `placed_time TEXT NOT NULL`, `customer_city TEXT NULL`, `customer_state TEXT NULL`, `pickup_store_number TEXT NULL` |
| `misc_nodes` | `document_id PK FK`, `name TEXT NOT NULL`, `date TEXT NOT NULL`, `time TEXT NOT NULL`, `transaction_number TEXT NULL`, `order_number TEXT NULL` |
| `payments` | `id INTEGER PK`, `document_id INTEGER NOT NULL FK→documents.id ON DELETE CASCADE`, `position INTEGER NOT NULL`, `type TEXT NOT NULL CHECK(type IN (...))`, `gift_card_number TEXT NULL`, `amount_cents INTEGER NOT NULL CHECK(amount_cents BETWEEN -9999999 AND 9999999)`, `CHECK((type='gift_card') = (gift_card_number IS NOT NULL))` |

Blank optional values are stored as `NULL`. The "blank counts as `""`" rule (BD1) is applied in Python when the key tuple is built, not in the database.

Placeholders (incomplete nodes) are never stored (B4, [relationship-resolution.md](relationship-resolution.md)).

## Indexes
- `documents(investigation_id, type)`
- `transactions(transaction_number, date)`, used by the duplicate check and matching
- `gift_cards(gift_card_number)`
- `gift_cards(activation_transaction_number)`
- `gift_card_history_entries(transaction_number)`
- `online_orders(order_number)`
- `misc_nodes(transaction_number)`
- `misc_nodes(order_number)`
- `payments(gift_card_number)`

## Uniqueness (B14, BD4)
Enforced in the service layer, inside the same database transaction as the write:
- **Transaction:** load the investigation's saved transactions with the same `transaction_number` and `date`, and compare full key tuples.
- **Gift Card and Online Order:** compare the single number.

## Updates
Updates replace child rows wholesale.

## ORM
One class per table in `db/models.py`, with plain one-to-one and one-to-many `relationship()`s (`cascade="all, delete-orphan"` for children). Don't use SQLAlchemy's polymorphic inheritance feature.

## Acceptance criteria
- [ ] Composite uniqueness:
  - Saving `(00482913, 2026-03-14, 042, 003)` twice returns 409 with `existing_id`.
  - Changing only the register (to `007` or to blank), only the store, or only the date, is accepted.
  - Two transactions `(00482913, 2026-03-14, 042, blank register)` return 409 on the second.
  - The same key in a different investigation is accepted.
- [ ] Gift Card and Online Order keep single-number keys: a second card with the same number returns 409.

- [ ] With no `investigation_settings` row, settings read as the defaults. Deleting the investigation removes its settings row (cascade).
- [ ] `important` accepts only 0 and 1, and defaults to 0.

## Course requirements
Traces: FR-01, FR-13, FR-14, FR-18 (full map in [../project/traceability.md](../project/traceability.md)). BD21 and BD23 have no FR behind them; they are listed as untraced there.
