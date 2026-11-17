# Design: Backend Graphing System (data model, relationship resolution, Cytoscape output)

- **Status:** Agreed. The user accepted the v1 defaults, chose a composite Transaction identity and signed amounts (v2), then answered the remaining questions: store number is required on Transactions, there is a sign convention between transactions and gift cards, and ambiguous edges are dashed (v3).
- **Version:** 3 (2026-11-17)
- **Source plans:** `docs/development/initial-plans.md`
- **Related designs:** `docs/development/claudedesigns/page-and-ui-layout.md` (Agreed v1). This design follows its decisions D3, D5, D8, D10, D14, D15, D18 and D25. **It also needs some changes to that design**, which the user must approve separately. They are listed in "Follow-ups" and that file has not been edited. Still to come: a CSV save/load format design and an IAM design.

## Summary
The FastAPI backend stores an investigation's documents (Transaction, Gift Card, Online Order, Misc) in SQLite. It works out every relationship between them from the reference fields in the documents, and returns a graph that Cytoscape.js can load directly. When a document references a transaction, gift card or online order that has no document yet, the backend shows an **incomplete node** (a placeholder) in both the document list and the graph, and never raises an error. When the user later saves a matching real document, the placeholder is replaced automatically.

## Goals
- G1. One API produces the full Cytoscape element list for an investigation. The frontend never decides which nodes are connected.
- G2. Missing, partial, one-sided or ambiguous references never cause an error. They show up as incomplete nodes and edges.
- G3. Investigation data survives a browser crash or reload without the user doing anything (the plan's "saved occasionally").
- G4. The backend supports CSV export and import with a validity marker and a best-effort load.
- G5. Every piece is small enough to review on its own: pure-function relationship resolution, thin routes, one service per concern.

## Non-goals / out of scope
- PNG export. This happens entirely in the frontend (`cy.png()` in `ExportDialog`, page-and-ui-layout behavior 7). The backend has no part in it.
- Graph layout and node positions (page-and-ui-layout D8).
- The full CSV column layout. This design fixes the endpoints, the validity marker, the error report, the section style, the key and reference columns, and the money and escaping rules. Everything else goes in the CSV design.
- Links based on store number, register, date or amount alone (for example "same store"). Only the reference fields in R1 to R6 create edges.
- Flagging details that disagree between two documents, for example a history entry dated 01-02-2026 pointing at a transaction dated 01-03-2026 (BD19). Note that with composite matching, a disagreeing date or store simply doesn't match (section 3).
- Login, IAM and per-user ownership of investigations. Concurrent edits: last write wins (BD23).
- Database migrations (Alembic). Before the first release, a schema change means deleting the dev database file.
- Encryption at rest (BD21).
- Undo. Saving unsaved form drafts in the browser (BD22).

## Decisions
| # | Decision | Rationale | Alternatives considered |
|---|---|---|---|
| B1 | SQLite file accessed through **SQLAlchemy 2.0** typed ORM (`Mapped[...]` style). Tables are created at startup with `Base.metadata.create_all`. No Alembic yet | SQLAlchemy is the standard choice with FastAPI. Typed models are readable, and cascading deletes of child rows come for free | Raw `sqlite3`; SQLModel |
| B2 | The server-side SQLite database **is the autosave**. Every successful document save is committed straight away. "Resume last session" reopens the most recently updated investigation | Meets G3 with no extra machinery | Browser `localStorage` snapshots; periodic CSV snapshots on the server |
| B3 | Every document belongs to an **investigation**. All document, graph and export routes are nested under `/api/investigations/{investigation_id}` | Keeps New, Load and Resume from mixing cases | One global data set |
| B4 | **Incomplete nodes are derived, not stored.** On every read, references that match no saved document become placeholders in the response. Nothing is written to the database for placeholders | Placeholders can never fall out of sync. Orphaned placeholders vanish by themselves, deleted referenced documents show as incomplete again (page-and-ui-layout D15), and promotion is simply saving a matching document | Stored placeholder rows |
| B5 | A node is **incomplete** only when it is a placeholder. An edge is **incomplete** when either end is a placeholder **or** the edge came from an ambiguous match (BD15) | Simple and testable. Reuses the existing dashed edge style, so the UI doesn't change | One-sided references also count as incomplete (rejected, BD18) |
| B6 | Every ID-like number (transaction, order, gift card, store, register) is a **digits-only string**, never an integer. The maximum lengths are 8, 8, 24, 3 and 3. Matching is on the exact string as typed: leading zeros matter, and nothing is padded | INT overflows at 24 digits and drops leading zeros. This settles page-and-ui-layout D25 (maximum length only, no exact length) | Exact lengths; left-padding before matching |
| B7 | Money is **integer cents** (`amount_cents`), with a magnitude cap of $99,999.99. Payment and history amounts are **signed**, from -9,999,999 to 9,999,999. The activation amount is **0 to 9,999,999** (BD25). What the sign means depends on whose point of view the amount is recorded from (BD25) | Floating point can't hold amounts like 0.10 exactly. The user said returns are frequent | `REAL`/float; non-negative only |
| B8 | Dates are ISO `YYYY-MM-DD` in the API and the database. Times are `HH:MM` 24-hour strings (`00:00` to `23:59`). The frontend converts its `MM-DD-YYYY` input to ISO. The CSV uses `MM-DD-YYYY` | ISO dates sort correctly as text, and Pydantic's `date` type validates them | `MM-DD-YYYY` everywhere |
| B9 | One generic `/documents` resource takes a **Pydantic discriminated union** on the `type` field | Five routes instead of twenty | Separate routes per type |
| B10 | Database layout: a shared `documents` table, one detail table per type keyed by `document_id`, and child tables `payments` and `gift_card_history_entries` | Document IDs are unique across types, notes live in one place, and payments need one foreign key | One table per type; a JSON column |
| B11 | Relationship resolution is a **pure function** in `services/` that works on the whole investigation in memory | Easy to read and test without a database. Investigations are small | SQL joins |
| B12 | The graph endpoint returns **Cytoscape's element format**. The backend sets the classes. `graphMapper.ts` only builds label text | Keeps structure in the backend (G1) and presentation in the frontend | The frontend builds the graph |
| B13 | **Full gift card numbers never appear in a URL path, query string, graph payload, element ID, title, import message or log line.** The graph sends only a masked `display_key` (`…1234`). Placeholder IDs are hashes | Uvicorn's access log records URLs, and graph data ends up in PNG exports. Follows page-and-ui-layout D10 | — |
| B14 | **Natural keys, unique within an investigation:** **Transaction = (transaction_number, date, store_number, register_number)**. Online Order = `order_number`. Gift Card = `gift_card_number`. Misc has no key. A duplicate on create or update returns `409` with `existing_id` | User decision: a transaction number repeats across stores, registers and days. Order and card numbers are unique across the retailer by their nature, so they keep single-number keys | The number alone (rejected by the user) |
| B15 | API JSON uses **snake_case** field names | Pydantic's default, no alias configuration | camelCase through aliases |
| B16 | The investigation records `last_exported_at`. `has_unsaved_changes` is true when the investigation has at least one document and has never been exported, or `updated_at > last_exported_at` | Once the database is the autosave, "unsaved changes" (page-and-ui-layout D5) means "changed since the last CSV save" | Frontend-only tracking |
| B17 | CSV import is **stateless and two-step**: `?dry_run=true` returns the report. To proceed, the same file is posted again with `dry_run=false` | Matches LoadReportDialog without server-side import sessions | Server-side import session |
| BD1 | **In a saved Transaction's identity, a blank register number counts as the empty value `""`, which matches exactly.** `(00482913, 2026-03-14, "042", "")` and `(00482913, 2026-03-14, "042", "003")` are different transactions. Store number can never be blank (BD26) | The user asked for exact matching of missing values. It keeps uniqueness well defined while register stays optional | Make register required; treat a blank register as a wildcard in uniqueness (then two documents could each "cover" the other) |
| BD2 | **In a reference, a blank or absent component is a wildcard ("not known"), not `""`.** For example, a Gift Card activation with no store number matches a transaction at any store | References often hold less detail than the transaction itself (no register number ever). If a blank meant `""`, most references could never match a transaction that has a register number | Treat blanks in references as `""` (most activations and history entries would never connect) |
| BD3 | A reference matches a candidate transaction when every component the reference **knows** is equal to the candidate's value. One match links normally. Zero matches creates or joins a placeholder. Two or more matches links to **every** candidate with `match: "ambiguous"` (section 3) | It never errors, never hides a possible connection, and stays visibly uncertain (dashed edge) until the agent adds detail | Link to none and create a placeholder (makes a fake node next to real ones); pick one candidate (silently wrong) |
| BD4 | The duplicate-key check stays in the **service layer**, comparing the normalized key tuple (blank becomes `""`). There is no database UNIQUE index | Accepted default for OQ-10. Single user, so a check inside the write transaction is enough | Copy `investigation_id` onto the detail tables and add a UNIQUE expression index |
| BD5 | Gift card numbers allow 1 to 24 digits | Accepted default (OQ-2) | A fixed length |
| BD6 | Edge kinds and directions follow table 3.2 (`activated`, `used_in`, `related`) | Accepted default (OQ-4) | — |
| BD7 | Old investigations: after New or Load, the frontend deletes the previous investigation once it has been exported (`has_unsaved_changes == false`) or the user chose Discard. The database then normally holds one working investigation, and CSV files are the archive | Accepted default (OQ-7). Keeps less sensitive data on the server | Keep everything; age-based cleanup |
| BD8 | A custom `RequestValidationError` handler removes Pydantic's `input` echo from 422 responses | Accepted default (OQ-11). Stops card numbers being echoed back | Default 422 body |
| BD9 | The CSV is **one `.csv` file split into sections** (OQ-9 option a). Sections are joined by export-local row references (BD10). Dates are written `MM-DD-YYYY` | Accepted default (OQ-9). It is still one CSV and opens in Excel | A zip of CSVs; XLSX |
| BD10 | Each document row in the CSV has a `ref` column (`T1`, `G1`, `O1`, `M1`, assigned at export time). The payment and history sections point at their parent through `parent_ref`, never through natural key columns | With a 4-part transaction key, repeating the key on every child row is clumsy and error-prone. Misc has no key at all | Repeat the natural key columns on child rows |
| BD11 | CSV amount cells are written as plain signed decimals (`-25.50`, `1250.00`) under a header ending in `($)`, are **never** formula-escaped, and are parsed with `Decimal`, never `float` | Keeps amounts as real numbers in a spreadsheet. A leading `-` on a number is not a formula risk | `$`-prefixed text cells; escaping every leading `-` |
| BD12 | The validity marker is the first row `TXNWEAVE_SAVE,format_version,1` | Accepted assumption A2 | — |
| BD13 | Import always creates a **new** investigation. The file limit is 5 MB | Accepted assumptions A3 and A4 | Merge into the open investigation |
| BD14 | A placeholder's **single-value fields** (such as `time`) are prefilled only when every reference attached to it agrees. Its **repeatable rows** (payments, history entries) get one derived row per qualifying reference, with amounts sign-flipped per BD25 (3.7) | Accepted assumption A5, extended in v3 so the sign convention also applies to prefilled rows | First reference wins; never prefill amounts (v2) |
| BD15 | An ambiguous edge has `status: "incomplete"` and `match: "ambiguous"`, so it is drawn dashed with the existing incomplete-edge style. There is no separate ambiguous style (user decision, v3) | No UI change is needed. The `ambiguous` class stays in the data in case a style is wanted later | A distinct ambiguous style; a new status value |
| BD16 | An amount is required on every payment row. Misc node names don't need to be unique | Accepted assumptions A1 and A6 | — |
| BD17 | Online orders can't appear in gift card history. History entries reference transactions only | Accepted default (OQ-14) | — |
| BD18 | Completeness depends only on node existence and match quality. One-sided references are recorded in the edge's `refs` but don't change its status | Accepted default (OQ-5) | An `unconfirmed` status |
| BD19 | No checking for conflicting details in v1 | Accepted default (OQ-6) | — |
| BD21 | The SQLite file is stored unencrypted. Access is limited to localhost or the VPN | Accepted default (OQ-8) | SQLCipher |
| BD22 | A form still being typed is lost if the browser crashes | Accepted default (OQ-12) | `sessionStorage` drafts |
| BD23 | Concurrent edits: last write wins, no locking | Accepted default (OQ-13) | Optimistic locking |
| BD24 | The backend Transaction `title` includes the other identity parts: `Transaction 00482913 · 03-14-2026 · Store 042 · Reg 003`. A blank register is left out. On a placeholder, unknown parts are left out | Two transactions can now share a number, so `Transaction <number>` alone would give duplicate list titles. User confirmed (v3). The matching page-and-ui-layout change is follow-up F1 | Keep the number-only title |
| BD25 | **Amount sign convention.** Every amount is recorded from the point of view of the document that holds it. **Transaction / Online Order / Misc payment rows (transaction view):** positive = the customer paid with this tender, negative = money returned to this tender. **Gift Card activation and history amounts (card view):** positive = value went **onto** the card (activation, reload, return credited to the card), negative = value spent **from** the card. **Whenever the backend relates the two, the sign flips: card amount = −(payment amount).** This applies to placeholder prefill (3.7), any amount shown on or computed for an edge, and any future amount comparison or check (3.14). **Activation amounts must be at least 0**, because an activation always puts value onto the card. A zero activation is allowed | User decision (v3): "a return on a gift card should show negative on the transaction but positive in the gift card". Spends being negative in card view follows from the same flip | Spends recorded as positive in history (would need a second rule for loads, and would break the single flip) |
| BD26 | **Store number is required on Transaction documents.** Register number stays optional. References (activation, history, Misc) may still leave store blank, meaning "unknown" (BD2). A Transaction placeholder created from a reference with no store keeps store unknown (`null`) until the real document is saved | User decision (v3). Removes the case where a reference that gives a store could never match a saved transaction with a blank store | Optional store with blank counting as `""` (v2) |

## Plan inconsistencies and how this design resolves them
| Source line in `initial-plans.md` | Problem | Resolution |
|---|---|---|
| L36 `activation date*: DD-YYYY`, L45 `date*: DD-YYYY` | Contradicts `MM-DD-YYYY` on L23, L52 and L63 | A typo for `MM-DD-YYYY` (page-and-ui-layout D18). Stored as ISO (B8) |
| L22, L32, L35, L44, L52, L65, L66: number fields typed `INT` | Overflow, and lost leading zeros | Digits-only strings (B6) |
| L32 24 X's for a gift card number | Real cards are often 16 or 19 digits | 1 to 24 digits (BD5) |
| L24, L37, L46, L53 `time*: 2400` | `24:00` is not a valid time | `HH:MM`, `00:00` to `23:59` |
| L28, L39, L48: `$XXX.XX REAL` vs `$XXXX.XX REAL` | Two different caps, and float money | Integer cents with a $99,999.99 magnitude cap. Payments and history are signed, activation is 0 or more, and the sign convention is BD25 (B7) |
| L54 / L55 state `TEXT`, city `XX TEXT` | The `XX` belongs to state | State is 2 uppercase letters, city is free text |
| L57, L67 "added to a single transaction" | Copied text | Payments belong to any document type that has them |
| L57 `payment type*` vs L67 Misc `payments:` | Is a payment required? | At least 1 for Transaction and Online Order, 0 or more for Misc |
| L72 "and vice versa" | A Transaction has no field that records which card it activated | Completeness depends on node existence (B5, BD18). Two-way confirmation is recorded in `refs` |
| L80 "a new sheet for each node type" | CSV has no sheets | A sectioned single CSV (BD9) |
| L22 "Transaction number" treated as the identifier (implied by L72) | The number repeats across stores, registers and days (user answer) | Composite key (B14), partial-reference matching (section 3) |

## Data model

"digits(1..N)" means a string matching `^[0-9]{1,N}$`. Strings are trimmed of surrounding whitespace before validation. An empty string on an optional field is stored and returned as `null`.

### Shared value types
| Name | Python (Pydantic) | TypeScript | Rule | Example |
|---|---|---|---|---|
| `TxnNumber` | `Annotated[str, StringConstraints(pattern=r"^[0-9]{1,8}$")]` | `string` | digits(1..8) | `"00482913"` |
| `OrderNumber` | same | `string` | digits(1..8) | `"77120045"` |
| `GiftCardNumber` | pattern `^[0-9]{1,24}$` | `string` | digits(1..24) | `"6006491234567890123"` |
| `StoreNumber` | pattern `^[0-9]{1,3}$` | `string` | digits(1..3) | `"042"` |
| `RegisterNumber` | pattern `^[0-9]{1,3}$` | `string` | digits(1..3) | `"003"` |
| `IsoDate` | `datetime.date` | `string` (`YYYY-MM-DD`) | must be a real calendar date | `"2026-03-14"` |
| `Time24` | pattern `^([01][0-9]\|2[0-3]):[0-5][0-9]$` | `string` | `00:00` to `23:59` | `"18:05"` |
| `AmountCents` | `Annotated[int, Field(ge=-9_999_999, le=9_999_999, strict=True)]` | `number` (integer) | -$99,999.99 to $99,999.99. `0` is allowed. Floats and strings are rejected. Used for payment and history amounts. The sign follows BD25 | `-2550` (a $25.50 return, in transaction view) |
| `ActivationAmountCents` | `Annotated[int, Field(ge=0, le=9_999_999, strict=True)]` | `number` (integer) | $0.00 to $99,999.99, card view (BD25) | `50000` |
| `StateCode` | pattern `^[A-Z]{2}$`, uppercased before validation | `string` | | `"WI"` |
| `ShortText` | `str`, 1 to 200 characters | `string` | | `"Suspicious return"` |
| `Notes` | `str \| None`, at most 10,000 characters | `string \| null` | | |
| `PaymentType` | `Literal["credit_card","gift_card","cash","other"]` | union | | |
| `DocumentType` | `Literal["transaction","gift_card","online_order","misc"]` | union | | |
| `DocumentStatus` | `Literal["complete","incomplete"]` | union | `incomplete` only for placeholders | |
| `DocumentId` | `str` | `string` | A saved document is its integer ID as a string. A placeholder is `"ph-<type>-<12 hex>"` (3.6) | `"12"` |

### Payment (repeatable row)
| Field | Type | Required | Rule |
|---|---|---|---|
| `type` | `PaymentType` | yes | |
| `gift_card_number` | `GiftCardNumber \| None` | only when `type == "gift_card"` | Must be `null` for every other type, or the API returns 422 |
| `amount_cents` | `AmountCents` | yes | **Transaction view** (BD25): positive = paid with this tender, negative = returned to this tender. A $25.00 return loaded onto a gift card is `{"type":"gift_card", ..., "amount_cents": -2500}` |

Rows keep the order the user entered them in (`position`).

### Transaction
| Field | Type | Required | Part of the key? | Example |
|---|---|---|---|---|
| `transaction_number` | `TxnNumber` | yes | yes | `"00482913"` |
| `date` | `IsoDate` | yes | yes | `"2026-03-14"` |
| `time` | `Time24` | yes | no | `"18:05"` |
| `store_number` | `StoreNumber` | **yes** (BD26) | yes | `"042"` |
| `register_number` | `RegisterNumber \| None` | no | yes (blank counts as `""`, BD1) | `"003"` |
| `payments` | `list[Payment]`, at least 1 | yes | no | |
| `notes` | `Notes` | no | no | |

**Transaction key tuple** (used for uniqueness and for matching): `(transaction_number, date.isoformat(), store_number, register_number or "")`.

### Gift Card
| Field | Type | Required |
|---|---|---|
| `gift_card_number` | `GiftCardNumber` | yes, key |
| `activation.transaction_number` | `TxnNumber` | yes |
| `activation.date` | `IsoDate` | yes |
| `activation.time` | `Time24` | yes |
| `activation.store_number` | `StoreNumber \| None` | no |
| `activation.amount_cents` | `ActivationAmountCents \| None` | no (0 or more, card view) |
| `history` | `list[GiftCardHistoryEntry]`, 0 or more | no |
| `notes` | `Notes` | no |

**GiftCardHistoryEntry:** `transaction_number: TxnNumber` (required), `date: IsoDate` (required), `time: Time24` (required), `store_number: StoreNumber | None`, `amount_cents: AmountCents | None`. `amount_cents` is in **card view** (BD25): positive = value put onto the card in that transaction (for example a return credited to the card), negative = value spent from the card. Entries keep their order (`position`).

### Online Order
| Field | Type | Required |
|---|---|---|
| `order_number` | `OrderNumber` | yes, key |
| `placed_date` | `IsoDate` | yes |
| `placed_time` | `Time24` | yes |
| `customer_city` | `ShortText \| None` | no |
| `customer_state` | `StateCode \| None` | no |
| `pickup_store_number` | `StoreNumber \| None` | no |
| `payments` | `list[Payment]`, at least 1 | yes |
| `notes` | `Notes` | no |

### Misc
| Field | Type | Required |
|---|---|---|
| `name` | `ShortText` | yes (not unique) |
| `date` | `IsoDate` | yes |
| `time` | `Time24` | yes |
| `transaction_number` | `TxnNumber \| None` | no (a number-only reference, see R5) |
| `order_number` | `OrderNumber \| None` | no (a reference) |
| `payments` | `list[Payment]`, 0 or more | no |
| `notes` | `Notes` | no |

### Investigation
| Field | Type | Notes |
|---|---|---|
| `id` | `int` | |
| `name` | `str \| None`, at most 200 characters | |
| `created_at`, `updated_at` | `datetime` (UTC, ISO 8601) | `updated_at` changes on every document write |
| `last_exported_at` | `datetime \| None` | Set by a successful export (B16) |
| `document_count`, `incomplete_count` | `int` | Computed. `incomplete_count` counts placeholders |
| `has_unsaved_changes` | `bool` | Computed (B16) |

### Pydantic schema split (`schemas/`)
- `*In` models are **strict**: every required field is required. Used for POST and PUT bodies. `DocumentIn = Annotated[TransactionIn | GiftCardIn | OnlineOrderIn | MiscIn, Field(discriminator="type")]`.
- `*Out` models have the same fields, all optional, plus `id`, `investigation_id`, `type`, `status`, `title`, `referenced_by: list[DocumentRef]`, `created_at`, `updated_at` (`null` for placeholders).
- `DocumentRef = {id: DocumentId, type: DocumentType, title: str, match: "exact" | "ambiguous"}`. `match` tells the delete warning and the PropertyPanel whether the referencing document points at this one alone or at it and others.
- `title`:
  - Transaction: per BD24.
  - Gift Card: `Gift Card …<last 4>`.
  - Online Order: `Online Order <number>`.
  - Misc: `<name>`.

## SQLite schema
The file location comes from `TXNWEAVE_DB_PATH` (default `./data/txnweave.db` locally and `/data/txnweave.db` in the container, on a named volume). `PRAGMA foreign_keys=ON` is set on every connection through a SQLAlchemy `connect` listener.

| Table | Columns |
|---|---|
| `investigations` | `id INTEGER PK`, `name TEXT NULL`, `created_at TEXT NOT NULL`, `updated_at TEXT NOT NULL`, `last_exported_at TEXT NULL` |
| `documents` | `id INTEGER PK`, `investigation_id INTEGER NOT NULL FK→investigations.id ON DELETE CASCADE`, `type TEXT NOT NULL CHECK(type IN ('transaction','gift_card','online_order','misc'))`, `notes TEXT NULL`, `created_at TEXT NOT NULL`, `updated_at TEXT NOT NULL` |
| `transactions` | `document_id INTEGER PK FK→documents.id ON DELETE CASCADE`, `transaction_number TEXT NOT NULL`, `date TEXT NOT NULL`, `time TEXT NOT NULL`, `store_number TEXT NOT NULL`, `register_number TEXT NULL` |
| `gift_cards` | `document_id PK FK`, `gift_card_number TEXT NOT NULL`, `activation_transaction_number TEXT NOT NULL`, `activation_date TEXT NOT NULL`, `activation_time TEXT NOT NULL`, `activation_store_number TEXT NULL`, `activation_amount_cents INTEGER NULL CHECK(activation_amount_cents BETWEEN 0 AND 9999999)` |
| `gift_card_history_entries` | `id INTEGER PK`, `gift_card_document_id INTEGER NOT NULL FK→documents.id ON DELETE CASCADE`, `position INTEGER NOT NULL`, `transaction_number TEXT NOT NULL`, `date TEXT NOT NULL`, `time TEXT NOT NULL`, `store_number TEXT NULL`, `amount_cents INTEGER NULL CHECK(amount_cents BETWEEN -9999999 AND 9999999)` |
| `online_orders` | `document_id PK FK`, `order_number TEXT NOT NULL`, `placed_date TEXT NOT NULL`, `placed_time TEXT NOT NULL`, `customer_city TEXT NULL`, `customer_state TEXT NULL`, `pickup_store_number TEXT NULL` |
| `misc_nodes` | `document_id PK FK`, `name TEXT NOT NULL`, `date TEXT NOT NULL`, `time TEXT NOT NULL`, `transaction_number TEXT NULL`, `order_number TEXT NULL` |
| `payments` | `id INTEGER PK`, `document_id INTEGER NOT NULL FK→documents.id ON DELETE CASCADE`, `position INTEGER NOT NULL`, `type TEXT NOT NULL CHECK(type IN (...))`, `gift_card_number TEXT NULL`, `amount_cents INTEGER NOT NULL CHECK(amount_cents BETWEEN -9999999 AND 9999999)`, `CHECK((type='gift_card') = (gift_card_number IS NOT NULL))` |

Blank optional values are stored as `NULL`. The "blank counts as `""`" rule (BD1) is applied in Python when the key tuple is built, not in the database.

**Indexes:**
- `documents(investigation_id, type)`
- `transactions(transaction_number, date)`, used by the duplicate check and matching
- `gift_cards(gift_card_number)`
- `gift_cards(activation_transaction_number)`
- `gift_card_history_entries(transaction_number)`
- `online_orders(order_number)`
- `misc_nodes(transaction_number)`
- `misc_nodes(order_number)`
- `payments(gift_card_number)`

**Uniqueness (B14, BD4):** enforced in the service layer, inside the same database transaction as the write:
- **Transaction:** load the investigation's saved transactions with the same `transaction_number` and `date`, and compare full key tuples.
- **Gift Card and Online Order:** compare the single number.

**Updates** replace child rows wholesale.

**ORM:** one class per table in `db/models.py`, with plain one-to-one and one-to-many `relationship()`s (`cascade="all, delete-orphan"` for children). Don't use SQLAlchemy's polymorphic inheritance feature.

## Behavior

### 1. Investigations
1.1 `POST /investigations` creates an empty investigation. This is "New investigation".
1.2 `GET /investigations` lists investigations, newest `updated_at` first. "Resume last session" uses the first item, and is shown only when the list is non-empty.
1.3 Deleting an investigation cascades to all its documents.
1.4 Retention follows BD7. The frontend calls `DELETE /investigations/{old_id}` after New or Load when the old investigation was exported or the user chose Discard.

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
2.9 Negative and zero amounts are accepted on payment and history rows. Payment totals may be negative. A negative activation amount returns 422 (BD25). The backend stores each amount exactly as entered, in its own document's point of view, and never flips a sign on write. Flipping happens only when the backend relates two documents (3.7, 3.14).
2.10 A Transaction without a store number returns 422 (BD26).

### 3. Relationship resolution (`services/relationship_service.py`, pure function)
Input: all saved documents of one investigation. Output: placeholders, links, and `referenced_by`.

3.1 **Index the saved documents:**
- `card_by_number` and `order_by_number`: dictionaries keyed by number.
- `txns_by_number`: a dictionary from `transaction_number` to the list of saved Transactions with that number.

3.2 **Reference rules.** Each rule produces a reference `(source document, target type, known components, kind, ref)`.

| Rule | Reference field(s) | Target | Known components of the reference | Edge direction | `kind` | `ref` |
|---|---|---|---|---|---|---|
| R1 | Gift Card `activation.transaction_number`, `activation.date`, `activation.store_number` | Transaction | number, date, and store if not blank | Transaction → Gift Card | `activated` | `gift_card_activation` |
| R2a | Gift Card `history[i].transaction_number`, `.date`, `.store_number` | Transaction | number, date, and store if not blank | Gift Card → Transaction | `used_in` | `gift_card_history` |
| R2b | Transaction `payments[i].gift_card_number` | Gift Card | number | Gift Card → Transaction | `used_in` | `payment` |
| R3 | Online Order `payments[i].gift_card_number` | Gift Card | number | Gift Card → Online Order | `used_in` | `payment` |
| R4 | Misc `payments[i].gift_card_number` | Gift Card | number | Gift Card → Misc | `used_in` | `payment` |
| R5 | Misc `transaction_number` | Transaction | number only | Misc → Transaction | `related` | `misc_reference` |
| R6 | Misc `order_number` | Online Order | number | Misc → Online Order | `related` | `misc_reference` |

No reference ever knows a register number. Gift Card and Online Order references are single-number lookups: a match or a placeholder, never ambiguous.

3.3 **Matching a Transaction reference** against a candidate (a saved Transaction, or a placeholder, see 3.5). A candidate matches when, **for every component the reference knows**, the candidate has that component and the values are exactly equal. Components the reference doesn't know are ignored (BD2).

Saved candidates always have a store number (BD26), and a blank register is `""` (BD1). References never know a register, so the register never affects matching. It only affects uniqueness. A reference with no store matches a transaction at any store.

Examples. The saved transactions are:
- A = `(00482913, 2026-03-14, "042", "003")`
- B = `(00482913, 2026-03-14, "042", "007")`
- C = `(00482913, 2026-03-14, "051", "")`
- D = `(00482913, 2026-04-02, "042", "")`

| Reference | Known | Matches | Result |
|---|---|---|---|
| Activation `00482913`, 2026-04-02, store 042 | n, d, s | D | exact link to D |
| History `00482913`, 2026-03-14, store 051 | n, d, s | C | exact link to C |
| History `00482913`, 2026-03-14, store 042 | n, d, s | A, B | ambiguous links to A and B |
| History `00482913`, 2026-03-14, no store | n, d | A, B, C | ambiguous links to A, B and C |
| History `00482913`, 2026-05-01, store 042 | n, d, s | none | placeholder `(00482913, 2026-05-01, "042", ?)` |
| History `00482913`, 2026-05-01, no store | n, d | none | placeholder `(00482913, 2026-05-01, ?, ?)` (store unknown, BD26), or it joins the placeholder in the row above if both references exist (3.5) |
| Misc `00482913` | n | A, B, C, D | ambiguous links to all four |
| Misc `11112222` | n | none | placeholder `(11112222, ?, ?, ?)` |

3.4 **Outcome per reference:**
- **Exactly one saved match:** a link with `match: "exact"`.
- **Two or more saved matches:** one link to **each** match, with `match: "ambiguous"` (BD3).
- **Zero saved matches:** the reference resolves against placeholders (3.5).

3.5 **Placeholders for unmatched Transaction references.** This step runs after every reference has been tried against the saved documents, and is deterministic:
1. Collect the zero-match references. Sort them by number of known components, most first, then by known values, then by source document ID.
2. For each reference, find the placeholders already created that match it (3.3, where a placeholder's unknown components never match a component the reference knows).
   - One match: attach to it (`exact`).
   - Two or more: attach to each (`ambiguous`).
   - None: create a new placeholder whose key holds exactly the reference's known components. Its other components are unknown (`null`).
3. Because the most specific references go first, a number-only Misc reference joins an existing `(number, date, store)` placeholder instead of creating a second "Transaction 00482913".

   Example: activation `(11112222, 2026-05-01, 042)` and Misc `11112222`, both with zero saved matches, give **one** placeholder `(11112222, 2026-05-01, "042", ?)` with both attached as `exact`.

Gift Card and Online Order placeholders are keyed by the number alone and deduplicated by it.

3.6 **Placeholder ID:** `"ph-" + type + "-" + sha256(text).hexdigest()[:12]`, where `text` is:
- for a Transaction: `f"{investigation_id}:transaction:{number}|{date or '?'}|{store or '?'}|{register or '?'}"`. `?` marks an unknown component. A placeholder's store is `?` when none of its references gave a store (BD26), and its register is always `?`. A placeholder never has a blank `""` component, because references never carry blanks.
- for the other types: `f"{investigation_id}:{type}:{number}"`.

The ID stays the same as long as the placeholder's key doesn't change, and it contains no card number (B13).

3.7 **Placeholder prefill (BD14):** the placeholder's known key components are always filled in. Unknown components (store when no reference gave one, register always) are `null`, so the form shows store as a missing required field. Other fields:

| Placeholder type | From | Single-value fields (only if all attached references agree) | Derived rows (one per qualifying reference, in a stable order: source document ID, then row position) |
|---|---|---|---|
| Transaction | R1 activation | `time` ← `activation.time` | none (the activation transaction is where the card was bought, not a tender) |
| Transaction | R2a history entry | `time` | one payment row `{type: "gift_card", gift_card_number: <the card>, amount_cents: −(history.amount_cents)}`. If the history amount is blank, `amount_cents` is `null` |
| Transaction | R5 Misc | none | none |
| Gift Card | R2b Transaction payment | none | one history row `{transaction_number, date, time, store_number}` copied from the paying Transaction, with `amount_cents: −(payment.amount_cents)` |
| Gift Card | R3 / R4 order or Misc payments | none | none (history rows can only reference transactions, BD17) |
| Online Order | R6 Misc | none | none |

The `−(...)` is the sign flip from BD25. Activation details are never prefilled on a Gift Card placeholder, because no reference tells the backend how the card was activated.

**Worked example (BD25).** Transaction `00482913` (03-14-2026, store 042) has a payment row `gift_card 6006491234567890123, amount_cents: -2500`: a $25.00 return loaded onto the card. No Gift Card document exists yet.
- The Gift Card placeholder `…0123` gets the history row `{transaction_number: "00482913", date: "2026-03-14", time: "18:05", store_number: "042", amount_cents: 2500}`, which is **+$25.00 on the card**.
- The opposite direction: a saved Gift Card has a history row for transaction `11112222` (05-01-2026, store 042) with `amount_cents: -4000` (it spent $40.00), and no such Transaction exists. The Transaction placeholder gets the payment row `{type: "gift_card", gift_card_number: "6006491234567890123", amount_cents: 4000}`, which is **+$40.00 paid by that tender**.

3.8 **Promotion:** POSTing a real document makes the references that match it resolve to it on the next read (3.4 runs before 3.5), and the placeholder disappears once nothing is attached to it.
- The user must fill in the store if the placeholder didn't know it (BD26). Any store matches the references that had no store.
- If the user keeps the prefilled key parts and adds a register number, the references still match, because they don't know the register.
- If the user changes a prefilled date or store, the references no longer match and the placeholder stays. That is correct: the documents disagree, and the agent can see it.

3.9 **Edge merging:** links with the same `(source, target, kind)` merge into one edge.
- `refs`: the distinct `ref` values, sorted.
- `ref_count`: the number of underlying references.
- `match`: `"exact"` if **any** underlying reference matched this target uniquely, otherwise `"ambiguous"`.

Example: card X's history is ambiguous between transactions A and B, and A's own payment row uses card X (R2b, always exact). Then the X→A edge is `exact` with `refs: ["gift_card_history","payment"]`, and the X→B edge stays `ambiguous`.

3.10 **Edge status:** `incomplete` if either end is a placeholder or `match == "ambiguous"` (B5, BD15). Otherwise `complete`.

3.11 **`referenced_by`:** on each document, the distinct referencing documents, with `match` set as in 3.9.

3.12 **Determinism:** nodes are ordered by type (transaction, gift_card, online_order, misc), then by key tuple or name, then by ID. Edges are ordered by ID. The same data always gives identical output.

3.13 Resolution never raises an exception because of data content.

3.14 **Relating amounts (BD25).** All amount relationships go through one helper, `services/money.py: card_view(payment_amount_cents) -> int`, which returns `-payment_amount_cents`. Prefill (3.7) uses it, and so must any future feature that shows an amount on an edge, sums amounts across a card and its transactions, or compares a history amount with a payment amount (for example a check that history `+2500` agrees with payment `-2500`). Code must never compare a card-view amount with a transaction-view amount directly. v1 shows no amounts on edges and runs no amount checks (BD19). If either is added later, edge amounts are shown in **card view** for `activated` and `used_in` edges.

### 4. Graph output (`services/graph_service.py`)
4.1 `GET .../graph` maps every saved document and placeholder to a Cytoscape node, and every merged link to an edge.
4.2 An empty investigation returns 200 with empty `nodes` and `edges`.

### 5. CSV save and load
5.1 **Export:** `GET .../export.csv` streams UTF-8 with a BOM.
- `Content-Disposition: attachment; filename="<sanitized-name>.csv"` (default `untitled-investigation.csv`).
- Sets `last_exported_at`.
- Choosing where to save the file is done in the browser.

5.2 **Validity marker (BD12):**
- Row 1 is exactly `TXNWEAVE_SAVE,format_version,1`. Row 2 holds the investigation name and export time.
- A file without the marker gets the problem `not_a_txnweave_file`. If the user proceeds anyway, the importer attempts a best-effort parse.

5.3 **Sections (BD9, BD10):**
- Document sections: `transactions`, `gift_cards`, `online_orders`, `misc`. Child sections: `payments`, `gift_card_history`.
- Every document row starts with a `ref` column (`T1`, `G1`, ...). Child rows carry `parent_ref`.
- The `transactions` section holds all four key columns: `transaction_number`, `date`, `store_number`, `register_number`. A blank `register_number` cell means a blank register (BD1). A blank `store_number` cell is a row problem (5.7), because store is required (BD26).
- Amounts are written exactly as stored, each in its own document's point of view (BD25). Export never flips a sign: payment amounts are in transaction view, and activation and history amounts are in card view.
- References (activation, history, Misc) are written as their own field columns, not as `ref` links. They are re-resolved by section 3 on load.
- The exact column order is left to the CSV design.

5.4 **Placeholders are not exported.** They are recreated on load.

5.5 **Cell writing rules:**

| Cell kind | Written as | Formula-escaped? |
|---|---|---|
| Free text (name, notes, city, investigation name) | as-is | Yes. A leading `=`, `+`, `-`, `@`, tab or carriage return gets a `'` prefix |
| Digit strings (transaction, order, card, store and register numbers) | as-is | No. These cells can only contain digits, so there is no risk |
| Dates / times | `MM-DD-YYYY` / `HH:MM` | No |
| Amounts | Plain signed decimal with exactly 2 decimals, no `$` and no thousands separator: `-25.50`, `0.00`, `1250.00`. The header names the unit, for example `amount ($)` | **No** (BD11). A leading `-` on a number is not a formula, and escaping it would turn the amount into text |
| Enum values (payment type) | snake_case value | No |

5.6 **Import parsing:**
- Every cell is read as text. One leading `'` is stripped from any cell before parsing.
- **Amounts:**
  - Accepted forms: optional sign and optional `$` in either order (`-25.50`, `-$25.50`, `$-25.50`, `25.5`, `25`). Standard thousands grouping (`1,250.00`) is accepted, and so is Excel's accounting negative `(25.50)`.
  - Parsing uses `Decimal`, never `float`.
  - Rejected: more than 2 decimal places, any other characters, and values outside ±99,999.99. A negative activation amount is reported as `out_of_range` (BD25).
  - Import never flips a sign. Values are taken as written.
- **Digit-string cells:** must match their pattern exactly. Scientific notation (`6.00649E+18`) or lost leading zeros caused by Excel are reported as `invalid_format` and never repaired. A message may show at most the last 4 digits of a card number.

5.7 **Import endpoint:** `POST /investigations/import?dry_run=true|false`, with a multipart `file` of at most 5 MB (413 if larger).
- Rows are validated against the `*In` models.
- `dry_run=true` writes nothing and returns the report.
- `dry_run=false` creates a new investigation in one database transaction and imports the valid rows.
- Skipped rows:
  - Invalid rows. Example: a transaction row with a blank `store_number` produces a problem `{severity: "error", section: "transactions", row: N, field: "store_number", code: "missing_required"}`. The row is skipped, its payment rows are reported as `parent_skipped`, and the import carries on.
  - Child rows whose `parent_ref` is unknown or whose parent row was skipped.
  - Duplicate keys within the file, using the composite tuple for transactions. The first row is kept.
- A Transaction or Online Order whose payment rows were all skipped fails the "at least 1 payment" rule and is skipped too, with a problem entry for it.

5.8 File content never causes an error status (G2). Only a missing file part or bytes that aren't valid UTF-8 return 422, and an oversized file returns 413.

### 6. Sensitive data handling
6.1 No endpoint takes a gift card number in its path or query string.
6.2 Request and response bodies are never logged. Uvicorn's access log stays at its default. 422 responses have `input` stripped (BD8). Import messages show at most the last 4 digits of a card number.
6.3 The SQLite file is unencrypted and reachable only from 127.0.0.1 or the VPN (BD21).

## Interfaces

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
| DELETE | `/investigations/{iid}/documents/{doc_id}` | — | — | 204, 404, 409 `placeholder_not_editable` |
| GET | `/investigations/{iid}/graph` | — | `GraphOut` | 200, 404 |
| GET | `/investigations/{iid}/export.csv` | — | `text/csv` attachment | 200, 404 |
| POST | `/investigations/import?dry_run=` | multipart `file` | dry run: `ImportReport`. Otherwise: `{investigation, report}` | 200 (dry run), 201, 413, 422 |

### Example: `DocumentIn` (Transaction with a return)
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

### Example: Transaction placeholder `DocumentOut`
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

### `GraphOut`
```json
{
  "investigation_id": 1,
  "generated_at": "2026-11-17T15:04:05Z",
  "counts": {"nodes": 3, "edges": 2, "incomplete_nodes": 0},
  "elements": {
    "nodes": [
      {"data": {"id": "12", "document_id": "12", "node_type": "transaction", "status": "complete",
                "display_key": "00482913", "date": "2026-03-14", "time": "18:05",
                "store_number": "042", "register_number": "003"},
       "classes": "transaction"},
      {"data": {"id": "13", "document_id": "13", "node_type": "transaction", "status": "complete",
                "display_key": "00482913", "date": "2026-03-14", "time": "18:20",
                "store_number": "042", "register_number": "007"},
       "classes": "transaction"},
      {"data": {"id": "15", "document_id": "15", "node_type": "gift_card", "status": "complete",
                "display_key": "…0123", "date": "2026-02-01", "time": "10:00",
                "store_number": "042", "register_number": null},
       "classes": "gift-card"}
    ],
    "edges": [
      {"data": {"id": "e-used_in-15-12", "source": "15", "target": "12", "kind": "used_in",
                "status": "incomplete", "match": "ambiguous", "refs": ["gift_card_history"], "ref_count": 1},
       "classes": "used-in incomplete ambiguous"},
      {"data": {"id": "e-used_in-15-13", "source": "15", "target": "13", "kind": "used_in",
                "status": "incomplete", "match": "ambiguous", "refs": ["gift_card_history"], "ref_count": 1},
       "classes": "used-in incomplete ambiguous"}
    ]
  }
}
```

**Node `data` fields:**

| Field | Type | Meaning |
|---|---|---|
| `id` | `DocumentId` | Equal to `document_id` |
| `document_id` | `DocumentId` | Used for `GET .../documents/{id}` and "Edit in Documents" |
| `node_type` | `DocumentType` | |
| `status` | `DocumentStatus` | |
| `display_key` | `string` | Transaction or order number, `…` plus the last 4 card digits, or the Misc name |
| `date`, `time` | `string \| null` | The main date and time (activation date and time for a gift card) |
| `store_number` | `string \| null` | Transaction store, gift card activation store, or order pickup store |
| `register_number` | `string \| null` | Transactions only |

**Edge `data` fields:** `id` (`e-<kind>-<source>-<target>`), `source`, `target`, `kind`, `status`, `match` (`"exact" | "ambiguous"`), `refs: string[]`, `ref_count: int`.

**Classes:**
- Nodes: `transaction`, `gift-card`, `online-order` or `misc`, plus `incomplete` when it applies.
- Edges: `activated`, `used-in` or `related`, plus `incomplete` when it applies, plus `ambiguous` when `match` is ambiguous. The UI styles only `incomplete`, so ambiguous edges are dashed like any incomplete edge (BD15). `ambiguous` stays in the data in case a style is wanted later.

**Frontend vs backend split (B12):**

| Concern | Where |
|---|---|
| Nodes, placeholders, matching, ambiguity, edges, merging, status, classes, card masking, `title` | Backend |
| Node label text (`TXN 00482913` plus a distinguishing store suffix if follow-up F1 is approved, `GC …0123`, `ORD …`, Misc name, " (incomplete)"), edge label text from `kind` | `graphMapper.ts` |
| Styles, layout, PNG export, label toggle | `cytoscapeConfig.ts` / components |
| `MM-DD-YYYY` ↔ ISO and `$` ↔ signed cents conversion in forms | Frontend form code |

### `ImportReport`
```json
{
  "valid_marker": true,
  "format_version": 1,
  "counts": {"rows_read": 40, "documents_imported": 37, "rows_skipped": 3},
  "problems": [
    {"severity": "error", "section": "gift_cards", "row": 12, "field": "gift_card_number",
     "code": "invalid_format", "message": "Must be 1-24 digits (looks like a spreadsheet number; card ending …0123 cannot be recovered)"},
    {"severity": "error", "section": "transactions", "row": 7, "field": null,
     "code": "duplicate_key", "message": "Duplicate of row 3 (Transaction 00482913 · 03-14-2026 · Store 042)"}
  ]
}
```
`severity` is `error` (the row was skipped) or `warning` (the row was imported). Other codes: `not_a_txnweave_file`, `unknown_parent_ref`, `parent_skipped`, `missing_required`, `out_of_range`.

### `InvestigationOut`
`{id, name, created_at, updated_at, last_exported_at, document_count, incomplete_count, has_unsaved_changes}`.

## Implementation guidance

**Where code lives** (`apps/api/src/txnweave_api/`):

| File | Contents |
|---|---|
| `config.py` | `DB_PATH` from `TXNWEAVE_DB_PATH`, `MAX_IMPORT_BYTES = 5_000_000`. Plain `os.environ` |
| `db/database.py` | engine, session factory, foreign-key pragma listener, `init_db()`, the `get_session` dependency |
| `db/models.py` | ORM classes for the 8 tables |
| `schemas/common.py` | Shared value types |
| `schemas/documents.py` | `PaymentIn/Out`, `*In`, `*Out`, `DocumentIn`, `DocumentOut`, `DocumentRef` |
| `schemas/investigation.py` | `InvestigationCreate`, `InvestigationUpdate`, `InvestigationOut` |
| `schemas/graph.py` | `GraphOut`, `NodeData`, `EdgeData`, `CyNode`, `CyEdge` |
| `schemas/imports.py` | `ImportReport`, `ImportProblem` |
| `services/keys.py` | `transaction_key(doc) -> tuple[str, str, str, str]`, `TxnRef` (known components), `matches(ref, candidate) -> bool`. Small and pure, with its own tests |
| `services/document_service.py` | create, update, delete, duplicate-key check, ORM ↔ schema conversion, titles |
| `services/relationship_service.py` | **pure** `resolve(investigation_id, docs) -> Resolution(placeholders, links, referenced_by)` |
| `services/graph_service.py` | **pure** `build_graph(resolution, docs) -> GraphOut` |
| `services/investigation_service.py` | Investigation CRUD, `updated_at` bump, unsaved-changes flag |
| `services/money.py` | `parse_money_cell(text) -> int` (cents, using `Decimal`), `format_money_cell(cents) -> str`, and `card_view(payment_amount_cents) -> int`, the **only** place the BD25 sign flip is written (3.14) |
| `services/csv_service.py` | export and import |
| `routes/investigations.py`, `routes/documents.py`, `routes/graphs.py`, `routes/imports.py` | Thin routers. `main.py` calls `include_router(..., prefix="/api")` and runs `init_db()` in the lifespan |
| `tests/` | `test_keys.py`, `test_relationship_service.py`, `test_graph_service.py`, `test_money.py`, `test_documents_api.py` |

**Dependencies to add:** `sqlalchemy>=2.0,<3`, `python-multipart`. Dev-only: `pytest`, `httpx`.

**Compose:** add a named volume `txnweave-data:/data` to the `api` service, and set `TXNWEAVE_DB_PATH=/data/txnweave.db`.

**Suggested order** (small, reviewable steps):
1. `config.py`, `db/database.py`, the Investigation model and routes, pytest setup.
2. Shared value types (including signed `AmountCents`), and Transaction end to end (model, payments, service, routes) with the composite duplicate check.
3. Gift Card (with history), Online Order and Misc, one type per change.
4. `services/keys.py` with tests for the matching table in 3.3.
5. `relationship_service.resolve`: exact, ambiguous and zero-match references, the placeholder pass (3.5), prefill, merging, determinism. Table-driven tests.
6. Placeholders and `referenced_by` in the document endpoints, and the 409 rules.
7. `graph_service` and `GET /graph`. Fill `data/examples/sample-graph.json` with a real response.
8. The rest of `services/money.py` (the cell parsing and formatting), then the CSV export with `has_unsaved_changes`. (`card_view` is needed earlier, in step 5, for placeholder prefill.)
9. CSV import with `dry_run` and the report.
10. Hardening: the 422 `input` stripping handler and a log review.

## Acceptance criteria
- [ ] A Transaction with a 24-digit gift card payment and a leading-zero transaction number stores and returns both strings unchanged.
- [ ] Payment and history `amount_cents` accept `-9999999`, `0` and `9999999`. They reject `-10000000`, `10000000`, `25.5` and `"2550"` with 422.
- [ ] `activation.amount_cents` accepts `0` and `9999999` and rejects `-1` with 422.
- [ ] A Transaction with a missing or empty `store_number` returns 422. A Transaction with no `register_number` is accepted.
- [ ] A `cash` payment with a `gift_card_number` returns 422. A `gift_card` payment without one returns 422.
- [ ] Transaction and Online Order with 0 payments return 422. Misc with 0 payments is accepted.
- [ ] `2026-02-30` and `24:00` return 422.
- [ ] Composite uniqueness:
  - Saving `(00482913, 2026-03-14, 042, 003)` twice returns 409 with `existing_id`.
  - Changing only the register (to `007` or to blank), only the store, or only the date, is accepted.
  - Two transactions `(00482913, 2026-03-14, 042, blank register)` return 409 on the second.
  - The same key in a different investigation is accepted.
- [ ] Gift Card and Online Order keep single-number keys: a second card with the same number returns 409.
- [ ] Every row of the matching table in 3.3 produces exactly the stated result.
- [ ] Ambiguous references produce one edge per candidate, with `match: "ambiguous"`, `status: "incomplete"` and classes including `incomplete ambiguous`. No error status.
- [ ] An ambiguous X→A history edge that is also confirmed by A's own payment with card X becomes `match: "exact"` and `complete`.
- [ ] An activation `(11112222, 2026-05-01, 042)` and a Misc `11112222`, with no saved match, produce exactly one placeholder, prefilled with number, date, store and the activation time. Both are listed in `referenced_by`.
- [ ] POSTing `(11112222, 2026-05-01, 042, 003)` removes that placeholder, and both edges point at the new document as `complete`.
- [ ] POSTing `(11112222, 2026-05-02, 042, "")` instead leaves the placeholder in place (the dates disagree).
- [ ] A history reference with no store and no saved match produces a Transaction placeholder with `store_number: null`, and its title has no store part. POSTing the real Transaction with any store (and the same number and date) promotes it.
- [ ] **Sign convention (BD25):**
  - A Transaction with the gift card payment `-2500` and no Gift Card document produces a Gift Card placeholder whose history has one row for that transaction with `amount_cents: 2500`.
  - A gift card payment of `+4000` gives a history row of `-4000`.
  - A saved Gift Card with a history row of `-4000` for a missing transaction produces a Transaction placeholder with the payment row `{type: "gift_card", gift_card_number: <card>, amount_cents: 4000}`.
  - A history row with a blank amount gives a payment row with `amount_cents: null`.
  - Saving and then reading back any document returns every amount with the sign it was saved with. CSV export and import never change a sign.
  - `card_view(-2500) == 2500`, `card_view(4000) == -4000`, `card_view(0) == 0`. No other module negates an amount (checked by code review).
- [ ] Deleting a matched Transaction brings back the placeholder or the ambiguous links. Deleting the only referencer removes the placeholder.
- [ ] PUT or DELETE on a placeholder ID returns 409 `placeholder_not_editable`.
- [ ] Placeholder IDs stay the same between calls and contain no card numbers.
- [ ] `GET /graph` on an empty investigation returns 200 with empty lists.
- [ ] The same data gives identical `elements` across two calls.
- [ ] No full gift card number appears in any graph response, element ID, URL, `title`, import message, 422 body or log line during the tests.
- [ ] After a save, `has_unsaved_changes` is true until the next export.
- [ ] CSV export:
  - Writes amounts as `-12.50` (not `'-12.50`, not `$`).
  - Prefixes free text that starts with `-`, `=`, `+` or `@` with `'`.
  - Writes all four transaction key columns.
  - Joins child rows through `parent_ref`.
- [ ] CSV import:
  - Parses `-25.50`, `-$25.50`, `$-25.50`, `(25.50)` and `1,250.00` correctly into cents.
  - Rejects `25.505`, `1e3`, and anything beyond ±99,999.99.
  - Reports a negative activation amount as `out_of_range`.
  - Strips one leading `'` from a cell.
  - Reports a transaction row with a blank `store_number` as `missing_required`, skips it and its payment rows (`parent_skipped`), imports the rest, and returns no error status.
- [ ] Import `dry_run=true` writes nothing. A file without the marker reports `not_a_txnweave_file`. Proceeding imports the valid rows into a new investigation.
- [ ] `keys`, `relationship_service`, `graph_service` and `money` have unit tests that run without a database.

## Follow-ups
The backend decisions here are settled. These items are outside this document.

- **F1. Changes needed in `page-and-ui-layout.md`.** The user must approve these separately. That file has **not** been edited.
  - a. **Transaction display title** becomes `Transaction <number> · <MM-DD-YYYY> · Store <store>[ · Reg <register>]` (BD24). Suggested graph label: `TXN <number> · S<store>` when two visible transactions share a number.
  - b. **Transaction form:** store number becomes required (`*`) (BD26).
  - c. **Money inputs:** the form table currently says "Amount as money (`$`, non-negative, 2 decimals)". Payment and history amounts must accept negative values, and the activation amount stays 0 or more (B7, BD25). Payment running totals can be negative.
  - d. **Sign hints on the forms** (suggested): payment amount "negative = returned to this tender"; gift card history amount "positive = added to card, negative = spent from card" (BD25).
- **F2. Confirm the reverse-direction prefill.** Along with the requested flip from a transaction's gift card payment into a placeholder card's history, 3.7 also does the reverse: a gift card history entry prefills a gift card payment row on a placeholder Transaction, with the sign flipped. This is the designer's extension of the user's sign-convention answer. Remove that table row if it isn't wanted.

## Changelog
- v3 (2026-11-17): Still Agreed. The user answered RQ-1 to RQ-4:
  - **RQ-3:** store number is required on Transactions (new BD26). BD1 now covers only a blank register. `TransactionIn.store_number` is required, `transactions.store_number` is `NOT NULL`, and the key tuple no longer substitutes a blank store. The matching table is redone without blank-store transactions, and adds rows for references without a store. A placeholder whose references gave no store keeps `store_number: null` (`?` in its ID hash) until the real document is saved. CSV import reports a blank store as `missing_required` and skips the row. New behavior 2.10 and new acceptance criteria.
  - **RQ-4:** new sign convention BD25. Payments are in transaction view, activation and history amounts in card view, and card amount = −(payment amount) whenever the two are related. New `ActivationAmountCents` (0 or more) with a matching CHECK. BD14 and 3.7 now prefill derived rows with sign-flipped amounts (Gift Card placeholder history from transaction payments, and Transaction placeholder payments from history entries), with a worked example. New 3.14 and `money.card_view` as the single place the flip happens. Export and import never flip signs. New acceptance criteria.
  - **RQ-1:** ambiguous edges keep the dashed incomplete style (BD15 updated).
  - **RQ-2:** the backend title change (BD24) stays. The page-and-ui-layout changes are recorded as follow-up F1, not applied.
  - Replaced "Remaining questions" with "Follow-ups" (F1, F2).
- v2 (2026-11-17): Marked Agreed. The user accepted every v1 default (OQ-2 and OQ-4 to OQ-14) and assumptions A1 to A6, now recorded as BD4 to BD23 (there is no BD20). Changes:
  - **OQ-1 changed:** Transaction identity is now `(transaction_number, date, store_number, register_number)`. Added rules for blank values in identity vs references (BD1, BD2), partial-reference matching with exact, ambiguous and zero outcomes (3.3 to 3.5), placeholder keys and hashing (3.6), the `match` field on edges and `referenced_by` (3.9 to 3.11), the composite 409 check (BD4), the `transactions(transaction_number, date)` index, CSV `ref`/`parent_ref` columns (BD10), and a Transaction title that includes the identity parts (BD24).
  - **OQ-3 changed:** Amounts are signed, from -$99,999.99 to $99,999.99 (B7). Added CHECK constraints, the signed `AmountCents` type, and CSV money writing and parsing rules. Amount cells are never formula-escaped (BD11, 5.5, 5.6).
  - Gift Card and Online Order keep single-number keys.
  - Added the "Remaining questions" section (RQ-1 to RQ-4). Removed the v1 "Assumptions & Open Questions" section.
- v1 (2026-11-17): First draft, produced without interactive review.
