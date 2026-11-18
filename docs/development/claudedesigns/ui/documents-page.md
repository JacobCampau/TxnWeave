# UI: Documents Page (list and forms)

- **Status:** Agreed (from `page-and-ui-layout.md` v2). Updated 2026-11-17 (user decisions): Important in the form and list (D32, UI-27); document search, sort and filters (D33, UI-28), which replaces D13's "Incomplete only" checkbox.
- **Scope:** The Documents page at `/documents`: the split view with the document list (new-document menu, filters, sort, incomplete count, items) and the NodeEditor form pane, the UI view of every form field, display titles, amount signs, format-enforcing inputs, validation, explicit Save, unsaved-edit prompts, repeatable payment and history rows, incomplete (placeholder) documents, delete confirmation, and the `?doc=<id>` deep link.
- **Master plan:** [../master-plan.md](../master-plan.md) (B6, B7, B8, BD25)
- **Related:** [../backend/data-model.md](../backend/data-model.md) (authoritative types, BD24 titles, BD26), [../backend/api.md](../backend/api.md) (document endpoints, `referenced_by`, 409 rules), [../backend/relationship-resolution.md](../backend/relationship-resolution.md) (placeholder prefill), [color-system.md](color-system.md), [app-shell.md](app-shell.md)

## Decisions
| # | Decision | Rationale | Alternatives considered |
|---|---|---|---|
| D12 | The Documents page is a split view: list on the left (360px), form on the right | Fast to work through many documents | Form in a popup; separate route |
| D13 | Sort by Title A–Z / Z–A or Date newest / oldest. Filter by type and by "Incomplete only". Incomplete documents are **not** pinned to the top. They get a badge, a count and a filter instead. *(The filters were extended by D33: the "Incomplete only" checkbox became a three-way status filter.)* | Pins down the plan's vague "alphabetical" | Pin incomplete documents to the top |
| D14 | Each document saves only when the user clicks Save. Fields are validated on blur and on Save. Leaving a document with unsaved edits prompts first | Half-finished forms never create half-formed links | Save automatically while typing |
| D15 | Delete asks for confirmation and warns about the documents that reference this one (they will now show it as incomplete). There is no undo | Deleting has visible effects on other nodes | Delete without asking |
| D16 | Payments and gift card history are repeatable rows with Add/Remove. The gift card number field appears only when the payment type is Gift Card. A running payment total is shown | Matches the plan | — |
| D17 | Dates and times use text inputs that enforce the format as the user types (`MM-DD-YYYY`, `HH:MM` 24-hour) | The browser's built-in date picker follows the computer's regional format, not MM-DD-YYYY | Built-in browser date/time pickers |
| D18 | The plan's `DD-YYYY` is treated as a typo for `MM-DD-YYYY`. All ID and number fields are digits-only text. Customer city is free text, and customer state is 2 letters | The plan contradicts itself, and a 24-digit INT overflows and drops leading zeros | — |
| D25 | ID fields only cap the maximum length in the UI (for example up to 8 digits). Whether a value must be exactly that length is decided in the data-model design | Keeps validation rules in one place | Require exact length in the UI |
| D32 | **Important on the Documents page.** Every form has an **"Important"** checkbox above Notes. It is saved with the form's Save (D14) and sent as `important` in PUT and POST (BD27). On an incomplete (placeholder) document the checkbox is disabled, with the note "Save this document to mark it important". List items for important documents show an **"Important"** badge (color-system) | One place to see and change the flag alongside the other fields. Matches UC06's "checks a box" | Toggle only on the graph |
| D33 | **Document search on the Documents page** (FR-16). Search, filters and sort all run **in the browser** over the document list already loaded from `GET .../documents` (saved documents and placeholders). The search text is component state only: it is **never** put in the URL or query string, never stored (not in `localStorage` or `sessionStorage`), and never sent to the server, so typed card numbers stay out of URLs and logs (B13). Rules in UI-28 | Investigations are small enough to filter in the browser (B11). Avoids a search endpoint that could carry card numbers | A server search endpoint (a POST body would be needed to keep card numbers out of the URL); search on the graph (out of scope) |

(D25 was settled by B6: maximum length only, no exact length.)

## Data shown in forms (UI view)
The data-model design owns the authoritative types. In this table, "digits(N)" means a digits-only text input with a maximum length of N (D25).

| Form | Field | Required | Input |
|---|---|---|---|
| Transaction | Transaction number | * | digits(8) |
| | Date | * | mask `MM-DD-YYYY` |
| | Time | * | mask `HH:MM` (24h) |
| | Register number | | digits(3) |
| | Store number | * | digits(3) |
| | Payments | * (at least 1 row) | Repeatable row with three fields: Type dropdown (Credit Card, Gift Card, Cash, Other); Gift card number digits(24), shown and required only when Type is Gift Card; Amount as signed money (`$`, 2 decimals, -$99,999.99 to $99,999.99), with the hint "Negative = returned to this tender" |
| | Notes | | multi-line text |
| Gift Card | Gift card number | * | digits(24) |
| | Activation: transaction number | * | digits(8) |
| | Activation: date | * | `MM-DD-YYYY` |
| | Activation: time | * | `HH:MM` |
| | Activation: store number | | digits(3) |
| | Activation: amount | | money, $0.00 to $99,999.99 (no negatives) |
| | History | (0 or more rows) | Repeatable row: transaction number* digits(8), date* `MM-DD-YYYY`, time* `HH:MM`, store number digits(3), amount as signed money (-$99,999.99 to $99,999.99) with the hint "+ added to card, − spent from card" |
| | Notes | | multi-line text |
| Online Order | Online order number | * | digits(8) |
| | Placed date | * | `MM-DD-YYYY` |
| | Placed time | * | `HH:MM` |
| | Customer city | | text |
| | Customer state | | 2 letters, uppercased |
| | Store number for pickup | | digits(3) |
| | Payments | * (at least 1 row) | Same row as Transaction |
| | Notes | | multi-line text |
| Misc | Node name | * | text |
| | Date | * | `MM-DD-YYYY` |
| | Time | * | `HH:MM` |
| | Transaction number | | digits(8) |
| | Online order number | | digits(8) |
| | Payments | (0 or more rows) | Same row as Transaction |
| | Notes | | multi-line text |

**Display titles** (used in the list and for sorting): `Transaction <number> · <MM-DD-YYYY> · Store <store> · Reg <register>`, `Gift Card …<last 4>`, `Online Order <number>`, `<Node name>`. A blank register, or any part an incomplete (placeholder) Transaction doesn't know yet, is left out together with its ` · ` separator, for example `Transaction 12345678 · 05-01-2026`. The backend supplies these titles in the document `title` field (BD24).

**Amount signs** (BD25): payment amounts are from the transaction's point of view, so a return paid back onto a gift card is negative on the transaction. Gift card activation and history amounts are from the card's point of view, so that same return shows as positive in the card's history. Negative amounts are displayed as `-$25.00`.

## Behavior
- **UI-9. Documents page, empty:** with no documents, the list shows "No documents yet – create one to begin". With no document selected, the form pane shows "Select or create a document".
- **UI-10.** "New document" opens a type menu (Transaction, Gift Card, Online Order, Misc) and then an empty form of the chosen type.
- **UI-11.** The document list:
  - The header shows the incomplete count (for example "3 incomplete").
  - Filters: type checkboxes (all on by default) and "Incomplete only".
  - Sort options: Title A–Z (default), Title Z–A, Date newest, Date oldest.
  - Each item shows a type icon (its graph shape), the title, the date, and an Incomplete or Important badge where it applies. Incomplete items are not pinned to the top.
  - The filters and sort are extended by UI-28 (D33).
- **UI-12.** Selecting a document moves focus to the first field of its form. For an incomplete document, the form is pre-filled with the known values and the missing required fields show the error style straight away.
- **UI-13.** Validation runs on blur and on Save.
  - If any field is invalid, Save is blocked, focus moves to the first invalid field, and an error summary appears at the top of the form.
  - On a successful Save: a success toast appears, the list updates, and the graph is marked stale.
- **UI-14.** Leaving a form with unsaved edits asks "Discard changes?" (Discard / Cancel). This applies when switching documents, switching pages, or starting a new document.
- **UI-15.** Delete opens ConfirmDialog, which lists the documents that reference this one and warns they will show it as incomplete. Confirming deletes it and shows a toast. There is no undo.
- **UI-16.** Repeatable rows:
  - "Add payment" and "Add history entry" append a row, and each row has a Remove (×) button.
  - Payment sections show a running "Total $X.XX". The total can be negative, and is then shown as "Total -$X.XX".
  - Changing a row's type away from Gift Card clears and hides that row's card number field.
- **UI-27. Important (D32):** checking the box marks the form as changed, like any other field (UI-14). After Save, the list badge and the graph (edges included, BD27) reflect the new value.
- **UI-28. Search, filters and sort (D33).** The list header holds a search box (`type="search"`, `autocomplete="off"`, placeholder "Search documents"), the filters, and the sort menu.
  - **Sort keys:** Title A–Z (default), Title Z–A, Date newest, Date oldest.
    - Date means the Transaction date, the Gift Card activation date, the Online Order placed date, or the Misc date.
    - Documents with no known date (some placeholders) sort last in both date orders.
    - Ties sort by title, then by ID.
  - **Filters:**
    - Type checkboxes for Transaction, Gift Card, Online Order and Misc. All are on by default.
    - Status: **All** (default), **Complete**, **Incomplete**.
    - An **Important only** checkbox.
    - All filters and the search combine with AND.
  - **Keyword search:**
    - Matching is case-insensitive and finds the text anywhere in a field. Words separated by spaces must **all** match, but each word may match a different field.
    - Fields searched:
      - `title`;
      - every number field of the document (transaction, order and gift card numbers, store, register, pickup store, activation transaction number and store);
      - the gift card numbers on payment rows, and the transaction numbers on history rows;
      - dates in `MM-DD-YYYY` form;
      - the Misc name and the Misc transaction and order numbers;
      - customer city and state;
      - notes.
    - Amounts are not searched.
    - Typing the last 4 digits finds a card and every document that paid with it (interview Q6).
  - **Results:** the header shows "Showing N of M". The incomplete count (UI-11) always counts the whole investigation. With no matches, the list shows "No documents match" and a "Clear search and filters" button.
  - Search, filters and sort reset when a different investigation becomes active. They survive switching between pages within the same session (held in app state, not the URL).

## Components
| Component | Responsibility |
|---|---|
| `pages/DocumentsPage` | DocumentList + NodeEditor split view. Reads `?doc` |
| `DocumentList` (new) | New-document menu, search box, filters, sort, incomplete count, items with badges |
| `src/documents/documentSearch.ts` (new) | Pure `filterAndSort(docs, query, filters, sort)` for UI-28, unit-tested |
| `NodeEditor` | Per-type forms, validation, repeatable rows, Save/Delete |
| `MaskedInput`, `MoneyInput`, `DigitsInput` (new) | Inputs that enforce their format as the user types |

## Acceptance criteria
- [ ] The Documents list filters by type and by "Incomplete only", sorts by title and date, and shows the incomplete count. Incomplete items show the badge and rose border and are not pinned.
- [ ] Required fields are marked with * and validated on blur and on Save. Digits-only fields reject anything else. Date and time fields enforce `MM-DD-YYYY` and `HH:MM`.
- [ ] The gift card number field appears only on Gift Card payment rows, and the running payment total is correct.
- [ ] Delete asks for confirmation and lists the documents that reference the one being deleted.

- [ ] Every form has an Important checkbox. It is disabled on incomplete documents, and saved documents show the Important badge.
- [ ] Search "0123" finds the card ending 0123 and every document whose payment used it. The URL never changes while typing.
- [ ] The Complete, Incomplete and Important-only filters combine with type filters and search. "Showing N of M" is correct.
- [ ] Date sorts put documents with no date last.

## Course requirements
The PDF's "node management page" is this page. Traces: FR-03 to FR-07, FR-12, FR-14, FR-16, UC02, UC06, UC07 (full map in [../project/traceability.md](../project/traceability.md)). UC07's named paths are not built; they are met by importance (BD27). Still open: F12, F13, F14.
