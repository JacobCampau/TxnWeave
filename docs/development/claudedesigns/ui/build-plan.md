# UI: Build Plan

- **Status:** Agreed (from `page-and-ui-layout.md` v2, "Implementation guidance"). Updated 2026-11-17 (user decisions): steps tagged by wave (P1), and new steps for rename and delete (D29, D30), the settings page (D26 to D28), importance (D31, D32) and document search (D33).
- **Scope:** Frontend dependencies to add and the suggested order of small, reviewable steps for building the UI across all UI feature docs.
- **Master plan:** [../master-plan.md](../master-plan.md)
- **Related:** [color-system.md](color-system.md), [app-shell.md](app-shell.md), [investigation-page.md](investigation-page.md), [documents-page.md](documents-page.md), [settings-page.md](settings-page.md), [../backend/build-plan.md](../backend/build-plan.md)

## Dependencies to add
`react-router-dom`, `cytoscape`, `@types/cytoscape`.

## Where code lives
Components go in `apps/web/src/components/` unless another path is given. Pages are in `src/pages/`, graph config in `src/graph/`, styles in `src/styles/`. `src/styles/palette.ts` (new) + `global.css` are the only places hex colors may appear. Each UI doc lists its own components; `EdgeEditor.tsx` is removed (D2).

## Suggested order (small, reviewable steps)
Each step is tagged with its wave (P1) and the requirements it serves.

| # | Wave | Step | FRs |
|---|---|---|---|
| 1 | Wave 1 | `palette.ts`, the CSS tokens in `global.css`, and base styles (body, buttons, inputs, focus ring) | FR-02 |
| 2 | Wave 1 | Router (`/`, `/documents`, `/settings`), app shell and TopBar with the three tabs and inline Rename (D30, UI-25). Rename the pages and delete EdgeEditor | FR-01, FR-02 |
| 3 | Wave 1 | DocumentsPage split layout and DocumentList (type filter, D13 sort), using mock data | UC02, FR-07 |
| 4 | Wave 1 | NodeEditor, one form type at a time, with the masked and digits-only inputs and validation | FR-03 to FR-07, FR-12 |
| 5 | Wave 1 | GraphCanvas with mock elements, `buildStylesheet` using the **default** styles (D9), and the empty state | FR-02, FR-08, FR-10, FR-20 |
| 6 | Wave 1 | PropertyPanel and the `?doc` deep link | FR-09, UC03 |
| 7 | Wave 1 | GraphToolbar: fit, zoom, re-layout, edge-label toggle | FR-10 |
| 8 | Wave 1 | StartDialog, Save/Load, ConfirmDialog, toasts, the error banner and LoadReportDialog, wired to the backend | FR-01, FR-11 (also FR-19 early) |
| 9 | Wave 1 | SettingsPage shell (D26) with **Delete investigation** (D29, UI-24) | FR-01 |
| 10 | Wave 2 | ExportDialog (PNG) and the Legend | FR-17, FR-21, UC09 |
| 11 | Wave 2 | Importance: the PropertyPanel checkbox (D31, UI-26), the form checkbox and list badge (D32, UI-27), and the important node and edge styles | FR-14, FR-15, UC06, UC07 |
| 12 | Wave 2 | Document search: `documentSearch.ts`, the search box, the status and Important-only filters, date sort rules (D33, UI-28) | FR-16 |
| 13 | Wave 2 | Appearance: AppearanceTable, StylePreview, Save and Reset (D27, D28, UI-21 to UI-23). `buildStylesheet` and the legend read the settings (UI-29) | FR-13, UC08 |
| — | Future | IAM user menu (FR-23), FR-25 / UC10 gift card history view, FR-27, and open follow-ups F7, F9 (NQ-8), S-1 | — |

## Acceptance criteria
- [ ] Every Wave 1 step is complete before the assignment's Wave 1 milestone, and each Wave 2 step has at least been started (P1).
