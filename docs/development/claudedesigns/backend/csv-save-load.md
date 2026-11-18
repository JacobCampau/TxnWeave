# Backend: CSV Save and Load

- **Status:** Agreed (from `backend-graphing-design.md` v3, behavior section 5 and the `ImportReport` interface). Updated 2026-11-17 (user decisions): BD33 (`important` column and optional `settings` section).
- **Scope:** `services/csv_service.py`, `GET .../export.csv` and `POST /investigations/import`: the single sectioned CSV file, the validity marker, `ref` / `parent_ref` row joins, cell writing rules (including formula escaping and money), import parsing, the two-step dry-run import, skipped-row rules, the `ImportReport`, and which conditions return an error status. The full column layout is deferred to a future CSV design.
- **Master plan:** [../master-plan.md](../master-plan.md) (B6 digit strings, B7 cents, B8 date formats, BD25 signs)
- **Related:** [data-model.md](data-model.md) (rows are validated against `*In` models), [relationship-resolution.md](relationship-resolution.md) (references re-resolve on load), [api.md](api.md) (endpoint rows, B16 `last_exported_at`), [../ui/app-shell.md](../ui/app-shell.md) (Save, Load, LoadReportDialog)

## Non-goals
- The full CSV column layout. This design fixes the endpoints, the validity marker, the error report, the section style, the key and reference columns, and the money and escaping rules. Everything else goes in the CSV design.

## Decisions
| # | Decision | Rationale | Alternatives considered |
|---|---|---|---|
| B17 | CSV import is **stateless and two-step**: `?dry_run=true` returns the report. To proceed, the same file is posted again with `dry_run=false` | Matches LoadReportDialog without server-side import sessions | Server-side import session |
| BD9 | The CSV is **one `.csv` file split into sections** (OQ-9 option a). Sections are joined by export-local row references (BD10). Dates are written `MM-DD-YYYY` | Accepted default (OQ-9). It is still one CSV and opens in Excel | A zip of CSVs; XLSX |
| BD10 | Each document row in the CSV has a `ref` column (`T1`, `G1`, `O1`, `M1`, assigned at export time). The payment and history sections point at their parent through `parent_ref`, never through natural key columns | With a 4-part transaction key, repeating the key on every child row is clumsy and error-prone. Misc has no key at all | Repeat the natural key columns on child rows |
| BD11 | CSV amount cells are written as plain signed decimals (`-25.50`, `1250.00`) under a header ending in `($)`, are **never** formula-escaped, and are parsed with `Decimal`, never `float` | Keeps amounts as real numbers in a spreadsheet. A leading `-` on a number is not a formula risk | `$`-prefixed text cells; escaping every leading `-` |
| BD12 | The validity marker is the first row `TXNWEAVE_SAVE,format_version,1` | Accepted assumption A2 | — |
| BD13 | Import always creates a **new** investigation. The file limit is 5 MB | Accepted assumptions A3 and A4 | Merge into the open investigation |
| BD33 | **Importance and settings in the CSV.** (a) Each document section (`transactions`, `gift_cards`, `online_orders`, `misc`) has an `important` column, written as `true` or `false`. (b) The export always writes an optional **`settings`** section **last**, with the columns `setting,color,shape` and five rows: `transaction`, `gift_card`, `online_order` and `misc` (color token and shape), and `important_edge` (color token, blank shape). Values are the effective ones (BD29). **On import, settings never affect whether documents import.** A missing section means the defaults, with no problem reported. The rules are in 5.9. `format_version` stays `1`, because no file has been released yet | User decision (former F4): settings are saved with the export, and documents must still import without them | A separate settings file; bumping `format_version` |

## 5. Behavior
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
- References (activation, history, Misc) are written as their own field columns, not as `ref` links. They are re-resolved by [relationship resolution](relationship-resolution.md) (section 3) on load.
- The exact column order is left to the CSV design.

5.4 **Placeholders are not exported.** They are recreated on load.

5.5 **Cell writing rules:**

| Cell kind | Written as | Formula-escaped? |
|---|---|---|
| Free text (name, notes, city, investigation name) | as-is | Yes. A leading `=`, `+`, `-`, `@`, tab or carriage return gets a `'` prefix |
| Digit strings (transaction, order, card, store and register numbers) | as-is | No. These cells can only contain digits, so there is no risk |
| Dates / times | `MM-DD-YYYY` / `HH:MM` | No |
| Amounts | Plain signed decimal with exactly 2 decimals, no `$` and no thousands separator: `-25.50`, `0.00`, `1250.00`. The header names the unit, for example `amount ($)` | **No** (BD11). A leading `-` on a number is not a formula, and escaping it would turn the amount into text |
| Enum values (payment type, `important`, setting name, color token, shape) | snake_case value, `true`/`false` | No |

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

5.9 **Importing `important` and `settings` (BD33):**
- **`important` cell:**
  - A missing column or a blank cell means `false`.
  - Accepted values, in any case: `true`, `false`, `yes`, `no`, `1`, `0`.
  - Anything else is a `warning` with code `invalid_format`. The row is still imported, with `false`.
- **`settings` section:**
  - A row with an unknown setting name, an invalid token or shape, or a non-blank shape on `important_edge` is a `warning` with code `invalid_setting`. That entry uses its default.
  - If the resulting node styles break the distinctness rule (BD29), there is one `warning` with code `indistinct_styles`, and all four node styles revert to the defaults.
  - A duplicate setting row: the first one is kept, and the duplicate gets an `invalid_setting` warning.
  - If every setting equals the default, no `investigation_settings` row is created (BD30).

## `ImportReport`
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
`severity` is `error` (the row was skipped) or `warning` (the row was imported). Other codes: `not_a_txnweave_file`, `unknown_parent_ref`, `parent_skipped`, `missing_required`, `out_of_range`, `invalid_setting`, `indistinct_styles` (5.9). Settings problems use `section: "settings"`.

The non-dry-run response is `{investigation, report}` (201).

## Acceptance criteria
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
- [ ] CSV export and import never change a sign.
- [ ] Import `dry_run=true` writes nothing. A file without the marker reports `not_a_txnweave_file`. Proceeding imports the valid rows into a new investigation.

- [ ] Export writes `important` on every document row and a 5-row `settings` section last.
- [ ] Importing a file with no `settings` section and no `important` column imports every valid document, with defaults and `false`, and reports no settings problem.
- [ ] A `settings` row `misc,purple,diamond` gives a `warning` with code `invalid_setting`, Misc keeps its default, and the documents still import. Two identical node styles give `indistinct_styles`, and all node styles revert to the defaults.
- [ ] Export, then import, keeps every `important` flag and every setting.

## Course requirements
Traces: FR-11, FR-13, FR-14, FR-19, FR-22, UC04, UC05, UC08 (full map in [../project/traceability.md](../project/traceability.md)). F8 (UC04 "sheet" wording) is still open.
