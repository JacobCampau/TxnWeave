# Design History

- **Scope:** Version metadata, changelogs and follow-ups carried over from the two original design documents, plus the course-PDF follow-ups, so the feature docs can stay focused on current requirements. Nothing here is a requirement on its own; current rules live in the feature docs.
- **Master plan:** [master-plan.md](master-plan.md)

## Reorganization (2026-11-17)
`backend-graphing-design.md` (v3) and `page-and-ui-layout.md` (v2) were split into [master-plan.md](master-plan.md) plus the feature docs under `backend/` and `ui/`. No requirement was added, removed or changed. Decision IDs were kept. UI behaviors were given `UI-` prefixes (`UI-1` to `UI-20`, same numbering as the original list).

## Historical records kept on purpose
`backend-graphing-design.md` and `page-and-ui-layout.md`, in this folder, are **kept unchanged at the user's request**. They record how the user's use of AI for design work improved over time.
- They are **superseded**: the master plan and the feature docs are authoritative, and implementing agents must not use the old files as requirements.
- They are **exempt from the 250-line limit**, and must not be edited or split.

## Original document metadata

### `backend-graphing-design.md` — Design: Backend Graphing System (data model, relationship resolution, Cytoscape output)
- **Status:** Agreed. The user accepted the v1 defaults, chose a composite Transaction identity and signed amounts (v2), then answered the remaining questions: store number is required on Transactions, there is a sign convention between transactions and gift cards, and ambiguous edges are dashed (v3).
- **Version:** 3 (2026-11-17)
- **Source plans:** `docs/development/initial-plans.md`
- **Related designs (as written at v3):** `page-and-ui-layout.md` (Agreed v1). This design follows its decisions D3, D5, D8, D10, D14, D15, D18 and D25. It also needs some changes to that design, which the user must approve separately. They are listed in "Follow-ups" and that file has not been edited. Still to come: a CSV save/load format design and an IAM design.
- **Summary:** The FastAPI backend stores an investigation's documents (Transaction, Gift Card, Online Order, Misc) in SQLite. It works out every relationship between them from the reference fields in the documents, and returns a graph that Cytoscape.js can load directly. When a document references a transaction, gift card or online order that has no document yet, the backend shows an incomplete node (a placeholder) in both the document list and the graph, and never raises an error. When the user later saves a matching real document, the placeholder is replaced automatically.

### `page-and-ui-layout.md` — Design: Page and UI Layout
- **Status:** Agreed
- **Version:** 2 (2026-11-17)
- **Source plans:** `docs/development/initial-plans.md`
- **Related designs (as written):** none yet. Planned and referenced: data model / relationship resolution, CSV save/load format, autosave/storage, IAM.
- **Summary:** Defines the pages, layout, components, user flows, UI states and color system for the TxnWeave web app. There are two pages: the Investigation page, which shows the auto-generated graph, and the Documents page, where agents create and edit the documents that become nodes. Every color on the site comes from a fixed five-color palette, and text is always black or white.

## Follow-ups (from the backend design)
- **F1.** Changes needed in `page-and-ui-layout.md`: the Transaction title (BD24), store required (BD26), signed money inputs (B7, BD25), and sign hints. **Approved and applied** in `page-and-ui-layout.md` v2.
- **F2.** Reverse-direction prefill. **Confirmed by the user**; recorded in [backend/relationship-resolution.md](backend/relationship-resolution.md) "Resolved follow-ups".

## Follow-ups from the course PDFs
Traceability is in [project/requirements.md](project/requirements.md) and [project/traceability.md](project/traceability.md). Background is in [project/context.md](project/context.md).

### Closed by user decisions (2026-11-17)
| # | Topic | Resolution |
|---|---|---|
| F3 | FR-13, UC08: user-assigned colors and shapes | **Accepted.** D9 stays the default look. The Investigation settings page (D26 to D28, [ui/settings-page.md](ui/settings-page.md)) changes the color and shape per document type, from palette tokens only (D27). Schema BD29, storage BD30, endpoints BD31 |
| F4 | UC08: settings saved with the export | **Accepted.** Optional CSV `settings` section. Documents import whether or not it is present (BD33) |
| F5 | FR-14, UC06: important nodes and relationships | **Accepted with changes.** Importance is a stored flag on documents. Edges are never marked: an edge is important exactly when both of its end nodes are important, worked out on every graph read. Placeholders can't be marked (BD27, master plan). Toggle endpoint BD28. Graph style and PropertyPanel toggle D31. Form, badge and filter D32 |
| F6 | FR-16: search | **Accepted, moved.** Document search (sort, filters, keyword) is on the Documents page, client-side (D33). Graph search stays out of scope on the Investigation page |
| F11 | FR-01: rename and delete investigations | **Accepted.** Inline Rename on the TopBar (D30, BD32). "Delete investigation" on the Investigation settings page (D29) |
| F16 | FR-15, UC07: paths | **Resolved without a path feature.** No path finding, path highlighting or named paths. Both requirements are met by importance: mark the nodes along a path, and the edges between them highlight automatically (BD27). Mapping in [project/requirements.md](project/requirements.md) |
| F17 | Meaning of Level 2 | **Dropped.** The PDF's level wording is replaced by implementation waves (P1, master plan) |
| F18 | FR-27: AI analysis | **Future work only.** No design now. Note: a forked build that runs only on the user's machine could keep the data local |

### Still open (no answer yet; recommendations unchanged, not applied)
| # | PDF source | Agreed side | Issue | Rec. |
|---|---|---|---|---|
| F7 | FR-09, UC03: "details page" | D7 (PropertyPanel drawer) | Wording | Keep D7. The drawer is the details page |
| F8 | UC04: "a sheet for each node type" | BD9 | Already resolved | Keep BD9. Change the course wording to "section" |
| F9 | UC01: "right click and drag to move around" | D7 names no mouse button | Gap | NQ-8: left- or right-drag on empty canvas pans, and the context menu is suppressed |
| F10 | Interview Q10: no size limit | B11 rationale "Investigations are small" | Weakens a rationale | Keep B11. Target: 500 documents resolve and render within 3 seconds, with a test fixture |
| F12 | FR-06: custom node "label, description" | Misc fields | Partial | Misc is the custom node. Description = Notes. No new field |
| F13 | Interview Q2: transactions linked to earlier transactions | R1 to R6 only | Gap | Defer. Possible R7 `related` |
| F14 | Interview Q3: personal information | No such fields | Gap, sensitive | Notes only until the IAM design |
| F15 | Interview Q6: one person's actions | No person entity | Gap | Defer. Workaround: one Misc document per person |
| F20 | `Starting An Investigation.drawio`: "Load last investigation from cookies" | D34, B2 (server autosave; nothing stored in the browser) | Diagram wording only | Relabel the diagram box "Load last investigation from autosave" next time the diagram is edited |
| F21 | `visualdesigns/fr-11-fr-19-uc05-load-report-dialog.html` and `visualdesigns/index.html` | UI-17 (button now "Load documents"), BD34 (markerless files rejected) | Mockups out of date | Ask the ui-designer agent to refresh them. The design docs win |
| F22 | User decision 2026-11-24 (BD35) | Node positions are not in the CSV | A loaded CSV gets a fresh automatic layout, and BD7 makes CSV the normal archive, so arrangements don't survive a save and load | Future: an optional `layout` section keyed by `ref` (placeholder IDs survive import unchanged), like the BD33 `settings` section |
| F19 | `CS420_Project_Concept.pdf` | — | **Unread.** The pages render blank, and the text is in compressed font streams. Only the outline and link targets could be read | Re-run the comparison once the text is available |

## Changelog: CSV column layout (2026-11-24)
User-approved implementation plan (2026-11-24), relayed by the coordinating agent. Records the full CSV column layout that [backend/csv-save-load.md](backend/csv-save-load.md) had left to "the CSV design". No new decision ID: the layout is behavior 5.10 under the existing BD9, BD10, BD12 and BD33.
- **New behavior 5.10** "Column layout": row 2 `investigation_name,<name>,exported_at,<ISO 8601 UTC>` (names the imported investigation; a missing or malformed row 2 is not a problem); the `section,<name>` block format; the seven sections in order (`transactions`, `gift_cards`, `online_orders`, `misc`, `payments`, `gift_card_history`, `settings`) with their exact headers; refs numbered per type in 3.12 order; headers matched by name; `missing_required` for a missing required column; rows before the first section ignored.
- **New problem code:** `unknown_section` (always a `warning`; the section's rows are skipped).
- **Changed agreed text:**
  - csv-save-load: Status and Scope; the non-goal "The full CSV column layout ..." removed; 5.2 and 5.3 point to 5.10 (old 5.3: "The exact column order is left to the CSV design."); the `ImportReport` code list; new acceptance criteria.
  - [master-plan.md](master-plan.md): "Still to come: a CSV save/load format design (full column layout) and an IAM design." became "Still to come: an IAM design."
  - [ui/app-shell.md](ui/app-shell.md) non-goal: "deferred to the CSV design" now points to 5.10 (wording only).
  - [project/traceability.md](project/traceability.md): two new rows for 5.10 (FR-11, FR-19, UC04, UC05).
- F8 (UC04 "sheet" wording) stays open. F22 (positions in the CSV) is unchanged; an imported `layout` section would currently get the `unknown_section` warning.

## Changelog: saved node positions (2026-11-24)
User decisions, asked by the coordinating agent and relayed to the project-designer agent. The user chose "Saved permanently" over "keep for this session only".
- **D8 reversed and amended in place** ([ui/investigation-page.md](ui/investigation-page.md)):
  - Old: "Nodes are placed by the automatic `cose` layout, with a Re-layout button. Dragged positions are not saved in v1." Rationale: "Avoids storing layout data in the CSV."
  - New: "**Every node's position is saved** on the server (BD35), and no node moves on its own between loads. When no node has a saved position (a new investigation, or one loaded from CSV), the full automatic `cose` layout (deterministic: the same data always gives the same positions) runs and its result is saved. Dragging a node saves its new position (UI-36). Nodes that appear later are placed by D38. Re-layout replaces every saved position after a confirm (UI-37)." The CSV still holds no layout data, so v1's reason still stands.
- **New decisions:**
  - BD35 to BD37 in the new [backend/node-positions.md](backend/node-positions.md): the `node_positions` table, including incomplete nodes keyed by placeholder ID; positions not in the CSV and not an unsaved change; `PUT` and `PATCH .../layout`; promotion keeps the placeholder's position.
  - D38: new nodes are placed, and only their direct neighbors and nodes within 150 px may move. The user said: "I want everything saved. But when adding a new node, the nodes nearest to it can be moved as needed to fit the new node."
- **New behaviors:** 8.1 to 8.9 (node-positions), 4.5 (graph `position`), api 2.12, UI-36 (drag save), UI-37 (Re-layout confirm), UI-38 (placement on load).
- **Changed agreed text:**
  - D36 and UI-32: Export now restores the saved positions too. Old: "After **Export**, the previewed positions stay until the next Re-layout." No dragging while the dialog is open.
  - UI-32 determinism fix. Old: "Each switch re-runs the layout, so the result can differ slightly." New: "The layout is deterministic, so switching back gives the same arrangement as before."
  - The investigation-page non-goal "Saving dragged node positions, including positions set by the export preview (D36)" now covers only the preview, zoom and pan, and the CSV.
  - The graph-output non-goal "Graph layout and node positions (D8)" becomes "Computing graph layout".
  - UI-7 Re-layout. api.md: endpoint rows, 1.3, 2.4, the `updated_at` note. persistence.md: the new table. relationship-resolution 3.8: a pointer to BD37. csv-save-load: a non-goal. Master plan: goal, principle 2, conventions, index.
  - Both build plans: backend step 13 and UI step 14 (Wave 2); UI step 10 reworded.
  - traceability.md and requirements.md: new rows. Saved positions are weakly traced to FR-10 and FR-18.
- **Accepted caveat:** a placeholder whose key changes gets a new ID and is placed again as a new node (8.7).
- **New follow-up:** F22.

## Changelog: frontend dependency (2026-11-24)
User decision, relayed by the coordinating agent: drop `@types/cytoscape`. `cytoscape` 3.35 (installed in `apps/web/package.json` as `"cytoscape": "^3.35.0"`) ships its own TypeScript definitions (`index.d.ts`, the `"types"` field in its `package.json`), so the separate types package is redundant and can conflict with them.
- **Changed agreed text:**
  - [master-plan.md](master-plan.md) "Tech stack", Frontend row: `cytoscape` + `@types/cytoscape` became `cytoscape` (≥3.35, bundles its own types).
  - [ui/build-plan.md](ui/build-plan.md) "Dependencies to add": `@types/cytoscape` removed, with a note on why.
- **No new decision ID.** This is a tooling change with no FR behind it, and the tech stack has no decision IDs. [project/traceability.md](project/traceability.md) doesn't list dependencies, so it is unchanged.
- The historical `page-and-ui-layout.md` still lists `@types/cytoscape`. It is left unchanged on purpose (see "Historical records kept on purpose").

## Changelog: activity diagrams (2026-11-23)
Design docs aligned with the user's two UML activity diagrams, `docs/development/drawioactivitydiagrams/Starting An Investigation.drawio` and `docs/development/drawioactivitydiagrams/Investigation.drawio`, which are Figures 1 and 2 in `docs/development/CS420_Project_Design.pdf` (sections 3.1 and 3.2; mockups in Figures 3 to 9). The user answered every question (Q1 to Q8 and group C), relayed by the coordinating agent.
- **New decisions:**
  - D34 ([ui/app-shell.md](ui/app-shell.md)): StartDialog on every open and reload. Nothing is stored in the browser. The diagram's "cookies" means the server autosave (B2). The "missing information?" check applies only to CSV loads. Land on `/` after New, Resume or Load.
  - D35 (app-shell): CSV load checks in diagram order: filetype, then format marker, then problems. The first two are hard errors, shown inline in StartDialog or as a toast from the TopBar.
  - BD34 ([backend/csv-save-load.md](backend/csv-save-load.md)): a file without the validity marker gets 422 `not_a_txnweave_file`. Marker matching tolerates a BOM and trailing blank cells.
  - D36 ([ui/investigation-page.md](ui/investigation-page.md)): live export orientation preview (16:9 at 1920×1080, 9:16 at 1080×1920). Landscape is preselected. Cancel restores positions.
  - D37 (investigation-page): the legend is a checkbox, off by default, shown bottom-left, and in the PNG only when it's on.
- **New behaviors:** UI-30 (Resume row details), UI-31 (Load CSV flow), UI-32 (export preview), UI-33 (legend), UI-34 (Save disabled with no changes; always enabled on incomplete documents), UI-35 (delete details: no Delete on incomplete documents, a "no references" message, nothing selected afterwards). There's also a note in documents-page mapping the diagram's "create incomplete node" step to derived placeholders (B4).
- **Changed agreed text:**
  - **G4 narrowed** (master plan): best-effort loading now applies only to files that have the marker. Markerless files are rejected. Before, 5.2 and UI-17 offered "Proceed anyway" on them.
  - csv-save-load 5.2, 5.7, 5.8: the `not_a_txnweave_file` problem code is removed from the `ImportReport` and becomes the 422 code. `ImportReport.valid_marker` is removed.
  - UI-1: StartDialog on every open. UI-17: the "Proceed anyway" button is renamed "Load documents", and Cancel returns to where the load started. UI-7: points to D36 and D37.
  - api.md: import 422 code and 1.2 note.
  - Both build plans: UI steps 8, 8a (Wave 1) and 10 (Wave 2); backend step 9 (Wave 1).
  - traceability.md and requirements.md: new rows and citations.
  - The master-plan conventions line now gives the ID ranges as BD1 to BD34, D1 to D37, UI-1 to UI-35, behavior sections 1.x to 7.x (section 7 already existed) and F1 to F21.
- **Left out on purpose:** the diagram's "cookies" (see D34 and F20), and storing incomplete nodes (B4). Re-layout, Settings, Rename, TopBar Save/Load, list selection and the unsaved-change prompts are not in the diagrams (PDF 3.2 says minor functions were omitted), and they stay in the design.
- **New follow-ups:** F20, F21.

## Changelog: course-requirement decisions (2026-11-17)
User decisions on the course-PDF follow-ups, applied as agreed design:
- **New cross-cutting decisions** in [master-plan.md](master-plan.md):
  - P1: implementation waves replace the PDF's levels.
  - P2: every design element traces to an FR or UC.
  - BD27: importance.
- **New backend decisions:**
  - BD28: the `PATCH` endpoint for importance.
  - BD29: the investigation settings schema and its validation.
  - BD30: the `investigation_settings` table and the `documents.important` column.
  - BD31: the settings endpoints.
  - BD32: rename rules.
  - BD33: the CSV `important` column and the optional `settings` section.
  - Graph output behaviors 4.3 and 4.4.
- **New UI decisions:**
  - D26 to D29: the new [ui/settings-page.md](ui/settings-page.md).
  - D30: Rename on the TopBar.
  - D31: important styles and the PropertyPanel toggle.
  - D32: Important in the form and the list.
  - D33: document search, sort and filters. D33 replaces D13's "Incomplete only" checkbox with a three-way status filter.
  - New behaviors UI-21 to UI-29.
- **Changed agreed text:**
  - The investigation-page non-goal "Graph search" now points to D33. Path features were added as a non-goal.
  - D9's style table is now the default appearance.
  - Both build plans now tag every step Wave 1, Wave 2 or Future.
- **New [project/traceability.md](project/traceability.md):** every decision, behavior and component mapped to FR or UC IDs, with an explicit list of elements that have no FR behind them.
- **Old docs** marked as kept historical records (see above).
- Closed F3, F4, F5, F6, F11, F16, F17 and F18. F7 to F10, F12 to F15 and F19 stay open.

## Changelog: course-PDF pass (2026-11-17)
- Added [project/context.md](project/context.md) and [project/requirements.md](project/requirements.md) (Draft), and follow-ups F3 to F19.
- Feature docs got a "Course requirements" note. No agreed decision changed in this pass.

## Changelog: backend design
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

## Changelog: UI design
- v2 (2026-11-17): Brought into line with `backend-graphing-design.md` v3 (follow-up F1, approved by the user). Changes:
  - Transaction display title now includes date, store and register, leaving out a blank register or unknown placeholder parts (BD24).
  - Transaction node labels add the store when two visible transactions share a number.
  - Store number is required on the Transaction form (BD26).
  - Payment and history amounts are signed (-$99,999.99 to $99,999.99), and the activation amount is $0 or more (B7, BD25).
  - Payment running totals can be negative.
  - Added short sign hints and an "Amount signs" note (BD25).
- v1 (2026-11-16): Initial agreed version. Open questions OQ1–OQ4 were resolved with their suggested defaults and recorded as decisions D22–D25.
