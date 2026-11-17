# Design: Page and UI Layout

- **Status:** Agreed
- **Version:** 2 (2026-11-17)
- **Source plans:** `docs/development/initial-plans.md`
- **Related designs:** none yet. Planned and referenced: data model / relationship resolution, CSV save/load format, autosave/storage, IAM.

## Summary
Defines the pages, layout, components, user flows, UI states and color system for the TxnWeave web app. There are two pages: the **Investigation page**, which shows the auto-generated graph, and the **Documents page**, where agents create and edit the documents that become nodes. Every color on the site comes from a fixed five-color palette, and text is always black or white.

## Goals
- An agent can start, resume, or load an investigation immediately on opening the app.
- An agent can create and edit Transaction, Gift Card, Online Order and Misc documents through validated forms.
- An agent can view the resulting graph, explore it (pan, zoom, drag, inspect a node), and export it as a PNG in landscape or portrait.
- Incomplete nodes are always visible and easy to find on both pages.
- The UI uses only the five palette colors, with WCAG-compliant black or white text.

## Non-goals / out of scope
- Login/IAM screens. A slot is reserved in the top bar for a future user menu.
- CSV file layout, including the "sheet per node type" issue (deferred to the CSV design).
- Backend relationship resolution.
- Where autosave data is stored.
- Mobile layout (desktop only, minimum width 1280px).
- Creating, linking or deleting nodes on the graph itself.
- Graph search.
- Saving dragged node positions.
- Undo.

## Decisions

| # | Decision | Rationale | Alternatives considered |
|---|---|---|---|
| D1 | Use `react-router-dom`: `/` is the Investigation page, `/documents` is the Documents page | Real URLs, a working back button, links to a specific document | Plain state-based page switching (no URLs) |
| D2 | Rename `HomePage.tsx` to `InvestigationPage.tsx` and `GraphPage.tsx` to `DocumentsPage.tsx`. Delete `EdgeEditor.tsx` | Matches the plan's terms. Edges are derived by the backend and never edited by users | Keep the placeholder names |
| D3 | "Load" means loading a CSV file from the agent's computer. The start popup also offers "Resume last session" when an autosave exists | Simplest option, and sensitive data stays local | A server-side list of investigations |
| D4 | Investigations have an optional name, shown in the top bar and used as the default file name | Makes saved cases easier to tell apart | No names |
| D5 | Starting or loading an investigation with unsaved changes asks: Save first / Discard / Cancel | Prevents accidental data loss | Silently replace |
| D6 | Top bar holds the wordmark, tabs, investigation name, autosave status, Load, Save, and the reserved user-menu slot. Export PNG lives in the Investigation toolbar | The plan puts Save in the top nav. Export only makes sense next to the graph | Export in the top bar |
| D7 | Graph structure is read-only. Users can pan, zoom and drag. Clicking a node opens a read-only PropertyPanel with an "Edit in Documents" button | The plan says nodes come from forms, not drawing | Editing directly on the graph |
| D8 | Nodes are placed by the automatic `cose` layout, with a Re-layout button. Dragged positions are not saved in v1 | Avoids storing layout data in the CSV | Save positions |
| D9 | Each node type gets its own shape and fill. Incomplete nodes use 75% opacity plus a dashed border | The palette alone can't separate 4 types, so shape does the work | Color only |
| D10 | Gift card numbers are shown as the last 4 digits only ("…1234") on the graph, in PNG exports and in list titles. The full number appears in the panel and the form | Card numbers are sensitive | Always show in full |
| D11 | Edges carry short labels, with a toolbar toggle to hide them | Explains what each connection means | No labels |
| D12 | The Documents page is a split view: list on the left (360px), form on the right | Fast to work through many documents | Form in a popup; separate route |
| D13 | Sort by Title A–Z / Z–A or Date newest / oldest. Filter by type and by "Incomplete only". Incomplete documents are **not** pinned to the top. They get a badge, a count and a filter instead | Pins down the plan's vague "alphabetical" | Pin incomplete documents to the top |
| D14 | Each document saves only when the user clicks Save. Fields are validated on blur and on Save. Leaving a document with unsaved edits prompts first | Half-finished forms never create half-formed links | Save automatically while typing |
| D15 | Delete asks for confirmation and warns about the documents that reference this one (they will now show it as incomplete). There is no undo | Deleting has visible effects on other nodes | Delete without asking |
| D16 | Payments and gift card history are repeatable rows with Add/Remove. The gift card number field appears only when the payment type is Gift Card. A running payment total is shown | Matches the plan | — |
| D17 | Dates and times use text inputs that enforce the format as the user types (`MM-DD-YYYY`, `HH:MM` 24-hour) | The browser's built-in date picker follows the computer's regional format, not MM-DD-YYYY | Built-in browser date/time pickers |
| D18 | The plan's `DD-YYYY` is treated as a typo for `MM-DD-YYYY`. All ID and number fields are digits-only text. Customer city is free text, and customer state is 2 letters | The plan contradicts itself, and a 24-digit INT overflows and drops leading zeros | — |
| D19 | **Every color comes from the 5-color palette. Text is #000000 or #FFFFFF, chosen by WCAG contrast** | User rule | — |
| D20 | The graph canvas is #D2CDCB, not white | White isn't in the palette. #D2CDCB is the closest color to the plan's "white canvas", gives 13.3:1 contrast with black text, and keeps all four node fills distinguishable | #131313 dark canvas (an #131313 node fill would disappear, and exports would be harder to read) |
| D21 | Desktop only, minimum width 1280px | Agents work at desktops | Responsive layout |
| D22 | Transparency is allowed in exactly two places: the plan's 75% opacity on incomplete nodes, and the dialog backdrop (ink at 70%). Nothing else may use transparency | Transparency blends colors into shades outside the palette. These two uses are required by the plan or needed for usability | Solid ink backdrop with no transparency at all |
| D23 | Empty-state text is black italic, 20px, on the mist canvas. This replaces the plan's "greyed text" | Grey text would break the black-or-white text rule | Grey text; text on a slate card |
| D24 | When a dropdown is open, some browsers draw its option list in the operating system's colors. This is an accepted exception | CSS can't fully control native dropdown lists | Build a custom dropdown component |
| D25 | ID fields only cap the maximum length in the UI (for example up to 8 digits). Whether a value must be exactly that length is decided in the data-model design | Keeps validation rules in one place | Require exact length in the UI |

## Color system

### Palette tokens
Defined once in `apps/web/src/styles/palette.ts` (for Cytoscape) and mirrored as CSS custom properties in `apps/web/src/styles/global.css`. No other file may contain a hex color.

| Token (CSS / TS) | Hex | Text color on it | Contrast | Contrast with the other text color |
|---|---|---|---|---|
| `--color-ink` / `palette.ink` | #131313 | #FFFFFF | 18.6:1 | black 1.1:1 |
| `--color-slate` / `palette.slate` | #394249 | #FFFFFF | 10.2:1 | black 2.0:1 |
| `--color-mist` / `palette.mist` | #D2CDCB | #000000 | 13.3:1 | white 1.6:1 |
| `--color-rose` / `palette.rose` | #D26D6F | #000000 | 6.2:1 | white 3.4:1 (fails for normal text) |
| `--color-crimson` / `palette.crimson` | #C11E20 | #FFFFFF | 6.0:1 | black 3.5:1 (fails for normal text) |
| `--text-on-dark` | #FFFFFF | Used on ink, slate, crimson | — | — |
| `--text-on-light` | #000000 | Used on mist, rose | — | — |

Every chosen text pairing meets WCAG AA for normal text (4.5:1 or better).

### Contrast between palette colors (borders and shapes need 3:1 against what's next to them)

| Pair | Ratio | 3:1 or better? |
|---|---|---|
| mist / ink | 11.8 | yes |
| mist / slate | 6.5 | yes |
| mist / crimson | 3.8 | yes |
| mist / rose | 2.2 | **no**. Rose shapes always get an ink border |
| ink / rose | 5.5 | yes |
| ink / crimson | 3.1 | yes |
| slate / rose | 3.0 | just meets it |
| slate / crimson | 1.7 | **no**. Never put crimson directly against slate |

### Color usage

| Element | Background | Text | Border / other |
|---|---|---|---|
| Top bar | ink | white | Active tab: 3px crimson underline and bold text. Inactive tabs: regular weight |
| Investigation toolbar | slate | white | 1px ink bottom border |
| Graph canvas | mist | black | — |
| PropertyPanel drawer | slate | white | 1px ink left border |
| Documents list pane | slate | white | — |
| List item (normal) | slate | white | 1px ink divider |
| List item (selected) | ink | white | — |
| List item (incomplete) | same as its normal or selected state | white | 4px rose left border and an "Incomplete" badge |
| "Incomplete" badge | rose | black | — |
| Form pane | mist | black | — |
| Text inputs / dropdowns | mist | black | 1px slate border |
| Input in error | mist | black | 2px crimson border plus a black message starting "Error:" (color is never the only signal) |
| Focus ring on light backgrounds | — | — | 3px ink outline, 2px offset |
| Focus ring on dark backgrounds | — | — | 3px mist outline, 2px offset |
| Primary button (one per view: Save, New document, Export) | crimson | white | — |
| Secondary button on a light background | slate | white | — |
| Secondary button on a dark background | mist | black | — |
| Destructive button (Delete, Discard) | rose | black | 1px ink border. The label always names the action |
| Disabled button | mist | black | 1px dashed slate border, `cursor: not-allowed`, `aria-disabled`. Never uses transparency |
| API error banner | crimson | white | Retry button: ink background, white text |
| Success toast | slate | white | 1px ink border |
| Error toast | crimson | white | 1px ink border |
| Dialogs | mist | black | 1px ink border. Backdrop is ink at 70% opacity (D22) |
| Loading spinner | — | — | Crimson on mist. Mist on slate or ink |
| Selected text highlight (`::selection`) | crimson | white | — |
| Scrollbars (`scrollbar-color`) | track ink | — | thumb slate |

### Graph styles (`cytoscapeConfig.ts`)

| Node type | Shape | Fill | Border |
|---|---|---|---|
| Transaction | ellipse | slate | 2px solid ink |
| Gift Card | round-rectangle (1.6:1 aspect ratio, card-like) | crimson | 2px solid ink |
| Online Order | hexagon | ink | 2px solid ink |
| Misc | diamond | rose | 2px solid ink (needed because rose against mist is only 2.2:1) |

- **Node labels:** below the node, black, 12px, showing the primary ID: `TXN 12345678`, `GC …1234`, `ORD 87654321`, or the Misc node's Node Name. When two or more visible Transaction nodes share a transaction number, each of their labels adds the store: `TXN 12345678 · S042`. A placeholder whose store is unknown leaves the store part out (`TXN 12345678`).
- **Incomplete node:** `opacity: 0.75`, 3px dashed ink border, and " (incomplete)" added to the label.
- **Selected node:** solid crimson underlay ring, 6px of padding outside the ink border. The ink border keeps the ring visible even on crimson Gift Card nodes.
- **Edges:** 2px slate line with a target arrow (6.5:1 against mist). An edge to an incomplete node is dashed.
- **Edge labels:** black, 10px, on a mist text background.
- **Selected edge:** 3px crimson.
- **Legend:** mist chips, each showing a type's shape and name, plus a sample of the incomplete style.
- **PNG export:** mist background, same styles as the screen.

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

**Display titles** (used in the list and for sorting): `Transaction <number> · <MM-DD-YYYY> · Store <store> · Reg <register>`, `Gift Card …<last 4>`, `Online Order <number>`, `<Node name>`. A blank register, or any part an incomplete (placeholder) Transaction doesn't know yet, is left out together with its ` · ` separator, for example `Transaction 12345678 · 05-01-2026`. The backend supplies these titles in the document `title` field (backend-graphing-design BD24).

**Amount signs** (backend-graphing-design BD25): payment amounts are from the transaction's point of view, so a return paid back onto a gift card is negative on the transaction. Gift card activation and history amounts are from the card's point of view, so that same return shows as positive in the card's history. Negative amounts are displayed as `-$25.00`.

## Behavior

1. On app load with no active investigation, show StartDialog. It can't be dismissed without choosing an option:
   - Resume last session (shown only if an autosave exists)
   - New investigation (optional name field)
   - Load CSV (opens the file picker)
2. Choosing New or Load while there are unsaved changes opens ConfirmDialog: Save first / Discard / Cancel.
3. The top bar shows the investigation name ("Untitled investigation" if blank) and the autosave status: "Saved HH:MM", "Saving…", or "Not saved".
4. **Investigation page, empty:** with 0 nodes, the canvas shows centered black italic 20px text "add forms to begin graphing" and a secondary "Go to Documents" button.
5. **Investigation page, loading:** a spinner is centered on the canvas while the graph loads. If loading fails, the API error banner appears with a Retry button.
6. Clicking a node opens the PropertyPanel, which shows:
   - the node type
   - all fields, including the full gift card number
   - notes
   - connected nodes (clicking one selects it)
   - an "Edit in Documents" button, which navigates to `/documents?doc=<id>`

   Clicking empty canvas or pressing Esc closes the panel.
7. Toolbar controls:
   - Fit to screen
   - Zoom in / Zoom out
   - Re-layout (runs `cose` again)
   - Edge labels on/off (on by default)
   - Export PNG: opens ExportDialog (Landscape or Portrait, then Export). The export scales and positions the graph so all nodes fit within and fill the chosen orientation, then downloads `<investigation-name>-graph.png`.
   - Legend
8. Navigating to the Investigation page after any document save refetches the graph.
9. **Documents page, empty:** with no documents, the list shows "No documents yet – create one to begin". With no document selected, the form pane shows "Select or create a document".
10. "New document" opens a type menu (Transaction, Gift Card, Online Order, Misc) and then an empty form of the chosen type.
11. The document list:
    - The header shows the incomplete count (for example "3 incomplete").
    - Filters: type checkboxes (all on by default) and "Incomplete only".
    - Sort options: Title A–Z (default), Title Z–A, Date newest, Date oldest.
    - Each item shows a type icon (its graph shape), the title, the date, and an Incomplete badge where it applies. Incomplete items are not pinned to the top.
12. Selecting a document moves focus to the first field of its form. For an incomplete document, the form is pre-filled with the known values and the missing required fields show the error style straight away.
13. Validation runs on blur and on Save.
    - If any field is invalid, Save is blocked, focus moves to the first invalid field, and an error summary appears at the top of the form.
    - On a successful Save: a success toast appears, the list updates, and the graph is marked stale.
14. Leaving a form with unsaved edits asks "Discard changes?" (Discard / Cancel). This applies when switching documents, switching pages, or starting a new document.
15. Delete opens ConfirmDialog, which lists the documents that reference this one and warns they will show it as incomplete. Confirming deletes it and shows a toast. There is no undo.
16. Repeatable rows:
    - "Add payment" and "Add history entry" append a row, and each row has a Remove (×) button.
    - Payment sections show a running "Total $X.XX". The total can be negative, and is then shown as "Total -$X.XX".
    - Changing a row's type away from Gift Card clears and hides that row's card number field.
17. Loading a CSV with problems opens LoadReportDialog, which lists the problems and offers "Proceed anyway" (load as much as possible) or "Cancel". A file that isn't a valid TxnWeave save gets the same dialog with that message.
18. If the API can't be reached, a crimson banner with Retry appears below the top bar on any page. If Save or Load fails, an error toast appears.
19. All controls can be reached with the keyboard and show the focus ring defined in the color table. Esc closes dialogs and the PropertyPanel.
20. Below 1280px wide, the page scrolls horizontally instead of rearranging.

## Interfaces

**Routes:** `/` is InvestigationPage. `/documents` is DocumentsPage, and the optional `?doc=<id>` parameter selects a document.

**Components** (in `apps/web/src/components/` unless another path is given):

| Component | Responsibility |
|---|---|
| `App.tsx` | Router, app shell, active-investigation state, StartDialog gate |
| `TopBar` (new) | Wordmark, tabs, name, autosave status, Load, Save, user-menu slot |
| `StartDialog` (new) | Resume / New / Load on startup |
| `pages/InvestigationPage` | GraphToolbar + GraphCanvas + PropertyPanel, plus empty and loading states |
| `GraphToolbar` | Fit, zoom, re-layout, edge-label toggle, Export, legend |
| `GraphCanvas` | Cytoscape rendering, selection events, empty state |
| `PropertyPanel` | Read-only node details and "Edit in Documents" |
| `ExportDialog` (new) | Landscape/Portrait choice and PNG export |
| `pages/DocumentsPage` | DocumentList + NodeEditor split view. Reads `?doc` |
| `DocumentList` (new) | New-document menu, filters, sort, incomplete count, items |
| `NodeEditor` | Per-type forms, validation, repeatable rows, Save/Delete |
| `MaskedInput`, `MoneyInput`, `DigitsInput` (new) | Inputs that enforce their format as the user types |
| `ConfirmDialog`, `Toast`, `ApiErrorBanner`, `LoadReportDialog` (new) | Shared dialogs, toasts and the error banner |
| `src/graph/cytoscapeConfig.ts` | Graph stylesheet from the tables above. Imports `palette.ts` |
| `src/graph/graphMapper.ts` | Converts API data into Cytoscape elements, including masked labels |
| `src/styles/palette.ts` (new) + `global.css` | The only places hex colors may appear |
| *removed:* `EdgeEditor.tsx` | — |

The data-model and CSV designs define the API endpoints. This design assumes only three operations exist: list documents, save/delete a document, and get the graph.

## Implementation guidance

**Dependencies to add:** `react-router-dom`, `cytoscape`, `@types/cytoscape`.

**Suggested order** (small, reviewable steps):
1. `palette.ts`, the CSS tokens in `global.css`, and base styles (body, buttons, inputs, focus ring).
2. Router, app shell and TopBar. Rename the pages and delete EdgeEditor.
3. DocumentsPage split layout and DocumentList, using mock data.
4. NodeEditor, one form type at a time, with the masked and digits-only inputs and validation.
5. GraphCanvas with mock elements, the cytoscapeConfig styles, and the empty state.
6. PropertyPanel and the `?doc` deep link.
7. GraphToolbar actions and ExportDialog.
8. StartDialog, Save/Load, ConfirmDialog, toasts, the error banner and LoadReportDialog. Wire these to the backend once the CSV and storage designs exist.

## Acceptance criteria
- [ ] `/` and `/documents` render the correct pages, and the browser's back and forward buttons work between them.
- [ ] With no active investigation, StartDialog appears and can't be dismissed. "Resume" appears only when an autosave exists.
- [ ] With 0 nodes, the canvas shows the black italic "add forms to begin graphing" and a "Go to Documents" button.
- [ ] Each node type renders with the shape and fill in the node table. Incomplete nodes have 75% opacity, a dashed border, and the "(incomplete)" label suffix.
- [ ] Gift card numbers are masked to the last 4 digits on the graph, in PNG exports and in list titles, and shown in full in the PropertyPanel and form.
- [ ] Clicking a node opens the PropertyPanel, and "Edit in Documents" opens that document's form.
- [ ] Export PNG produces a landscape or portrait image with all nodes visible and filling the frame, on a #D2CDCB background.
- [ ] The Documents list filters by type and by "Incomplete only", sorts by title and date, and shows the incomplete count. Incomplete items show the badge and rose border and are not pinned.
- [ ] Required fields are marked with * and validated on blur and on Save. Digits-only fields reject anything else. Date and time fields enforce `MM-DD-YYYY` and `HH:MM`.
- [ ] The gift card number field appears only on Gift Card payment rows, and the running payment total is correct.
- [ ] Unsaved-change prompts appear when switching documents or pages and when starting or loading an investigation.
- [ ] Delete asks for confirmation and lists the documents that reference the one being deleted.
- [ ] Searching `apps/web/src` for hex colors finds them only in `styles/palette.ts` and `styles/global.css`, and only the five palette colors plus #000000 and #FFFFFF.
- [ ] All text is #000000 or #FFFFFF and follows the text pairings in the palette table.
- [ ] Transparency appears only on incomplete nodes (75%) and the dialog backdrop (ink at 70%), per D22.
- [ ] Every control can be reached by keyboard and shows a visible focus ring.

## Changelog
- v2 (2026-11-17): Brought into line with `backend-graphing-design.md` v3 (follow-up F1, approved by the user). Changes:
  - Transaction display title now includes date, store and register, leaving out a blank register or unknown placeholder parts (BD24).
  - Transaction node labels add the store when two visible transactions share a number.
  - Store number is required on the Transaction form (BD26).
  - Payment and history amounts are signed (-$99,999.99 to $99,999.99), and the activation amount is $0 or more (B7, BD25).
  - Payment running totals can be negative.
  - Added short sign hints and an "Amount signs" note (BD25).
- v1 (2026-11-16): Initial agreed version. Open questions OQ1–OQ4 were resolved with their suggested defaults and recorded as decisions D22–D25.
