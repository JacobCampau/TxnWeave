# UI: App Shell, Start Flow and Shared Feedback

- **Status:** Agreed (from `page-and-ui-layout.md` v2). Updated 2026-11-17 (user decisions): Settings tab and route (D26), Rename on the TopBar (D30, UI-25). Updated 2026-11-23 (user decisions) to follow the activity diagram `docs/development/drawioactivitydiagrams/Starting An Investigation.drawio`: start flow (D34, UI-30), CSV load checks (D35, UI-31), UI-1 and UI-17 revised.
- **Scope:** Everything around the two pages: routes, the `App.tsx` shell and active-investigation state, the TopBar (wordmark, tabs, investigation name, autosave status, Load, Save, user-menu slot), the StartDialog gate, the Save first / Discard / Cancel prompt, CSV load with LoadReportDialog, the API error banner and toasts, keyboard access, and the minimum width rule.
- **Master plan:** [../master-plan.md](../master-plan.md)
- **Related:** [investigation-page.md](investigation-page.md), [documents-page.md](documents-page.md), [color-system.md](color-system.md) (top bar, banner, toast, dialog and focus-ring colors), [../backend/api.md](../backend/api.md) (investigation endpoints, resume, retention), [../backend/csv-save-load.md](../backend/csv-save-load.md) (export, dry-run import, `ImportReport`)

## Non-goals
- Login/IAM screens (project-wide non-goal in the master plan; the TopBar keeps the reserved user-menu slot, D6).
- CSV file layout, including the "sheet per node type" issue (deferred to the CSV design; the backend has since chosen a sectioned single CSV, BD9).
- Backend relationship resolution.
- Where autosave data is stored (since settled by the backend: the server-side database, B2).

## Decisions
| # | Decision | Rationale | Alternatives considered |
|---|---|---|---|
| D1 | Use `react-router-dom`: `/` is the Investigation page, `/documents` is the Documents page | Real URLs, a working back button, links to a specific document | Plain state-based page switching (no URLs) |
| D2 | Rename `HomePage.tsx` to `InvestigationPage.tsx` and `GraphPage.tsx` to `DocumentsPage.tsx`. Delete `EdgeEditor.tsx` | Matches the plan's terms. Edges are derived by the backend and never edited by users | Keep the placeholder names |
| D3 | "Load" means loading a CSV file from the agent's computer. The start popup also offers "Resume last session" when an autosave exists | Simplest option, and sensitive data stays local | A server-side list of investigations |
| D4 | Investigations have an optional name, shown in the top bar and used as the default file name | Makes saved cases easier to tell apart | No names |
| D5 | Starting or loading an investigation with unsaved changes asks: Save first / Discard / Cancel | Prevents accidental data loss | Silently replace |
| D6 | Top bar holds the wordmark, tabs, investigation name, autosave status, Load, Save, and the reserved user-menu slot. Export PNG lives in the Investigation toolbar | The plan puts Save in the top nav. Export only makes sense next to the graph | Export in the top bar |
| D21 | Desktop only, minimum width 1280px | Agents work at desktops | Responsive layout |
| D34 | **Start flow follows the "Starting An Investigation" diagram.** StartDialog appears on **every** app open and **every** browser reload. Nothing about the session (no investigation ID, no data) is stored in the browser: no cookies, `localStorage` or `sessionStorage`. "Resume last session" reopens the most recently updated investigation from the server autosave (B2, API 1.2). The diagram's "from cookies" means this autosave. The "missing information?" check applies **only** to CSV loads. Resume and New go straight to the Investigation page. After New, Resume or Load, the app always navigates to `/` | User decision (2026-11-23). Keeps B2 and keeps card data out of the browser. A deep link opened with no active investigation has nothing to show, so landing on `/` is always valid | Remember the investigation ID in the browser; auto-resume on reload |
| D35 | **CSV load checks, in diagram order.** (1) **Filetype:** the picker uses `accept=".csv"`. A file whose name doesn't end in `.csv` (any case) is rejected in the browser, without uploading. (2) **Format:** the server's dry run rejects a file without the validity marker with 422 `not_a_txnweave_file` (BD34). (3) **Missing information:** a file with the marker whose `ImportReport` has problems opens LoadReportDialog. Failures of (1) and (2), and a non-UTF-8 422, are **hard errors** with no way to load: the message appears inline in StartDialog (which stays open) on startup, or as an error toast when Load came from the TopBar | User decision (2026-11-23, former Q3 and Q5), following the diagram's filetype and format branches | Proceed anyway on markerless files (old UI-17); a server-only filetype check |
| D30 | **Rename on the TopBar.** The investigation name in the TopBar is a button (accessible name "Rename investigation"). Clicking it, or pressing Enter on it, swaps it for an inline text input filled with the current name. Enter or blur saves through `PATCH /investigations/{iid}` (BD32). Esc cancels | FR-01 "edit" (former F11). The name is already shown there, so editing it in place is the most discoverable option | A rename field on the Investigation settings page |

## Behavior
UI behavior numbers are kept from the original doc. UI-4 to UI-8 are in [investigation-page.md](investigation-page.md), UI-9 to UI-16 in [documents-page.md](documents-page.md).

- **UI-1.** On every app load and reload (D34), and whenever there is no active investigation (for example after D29's delete), show StartDialog. It can't be dismissed without choosing an option:
  - Resume last session (shown only if an autosave exists; details in UI-30). Opens that investigation and goes to `/`.
  - New investigation (optional name field, placeholder "Untitled investigation"). Creates it (API 1.1) and goes to `/`, which shows the empty state (UI-4).
  - Load CSV (opens the file picker; flow in UI-31).
- **UI-2.** Choosing New or Load while there are unsaved changes opens ConfirmDialog: Save first / Discard / Cancel.
- **UI-3.** The top bar shows the investigation name ("Untitled investigation" if blank) and the autosave status: "Saved HH:MM", "Saving…", or "Not saved".
- **UI-17.** Loading a CSV that has the validity marker but whose dry-run report has problems opens LoadReportDialog. It lists the problems and offers **"Load documents"** (import the valid rows, `dry_run=false`) or **"Cancel"**. Cancel returns to where the load started: StartDialog on startup, or the current investigation, unchanged, when Load came from the TopBar. A report with no problems skips the dialog and loads straight away. A file without the marker never reaches this dialog (D35).
- **UI-30. Resume row (D34).** The Resume option shows, from the first `InvestigationOut` of `GET /investigations`: the name ("Untitled investigation" if blank), "Last saved MM-DD-YYYY at HH:MM" (from `updated_at`, local time), and "N documents, M incomplete nodes". Resume is the primary (crimson) button.
- **UI-31. Load CSV flow (D35)**, the same from StartDialog and from the TopBar Load button (after UI-2's prompt):
  1. The file picker opens. Closing it without a file changes nothing: StartDialog stays open, or the current investigation stays.
  2. Filetype check. Not `.csv`: error "Choose a TxnWeave .csv file."
  3. Upload with `dry_run=true`. A 422 `not_a_txnweave_file`: error "This file is not a TxnWeave save file." Any other 422 (not UTF-8): error "This file could not be read." A 413: error "This file is larger than 5 MB."
  4. Report with problems: LoadReportDialog (UI-17). No problems: go to step 5.
  5. Upload again with `dry_run=false`. The new investigation becomes active, and the app goes to `/` (D34).
  - Errors in steps 2 and 3 appear inline in StartDialog under the Load CSV row, or as an error toast from the TopBar (D35). The user can then choose any option again.
- **UI-18.** If the API can't be reached, a crimson banner with Retry appears below the top bar on any page. If Save or Load fails, an error toast appears.
- **UI-19.** All controls can be reached with the keyboard and show the focus ring defined in the color table. Esc closes dialogs and the PropertyPanel.
- **UI-20.** Below 1280px wide, the page scrolls horizontally instead of rearranging.
- **UI-25. Rename (D30):**
  - The input allows at most 200 characters. Typing past the limit shows "Error: 200 characters at most" and doesn't save.
  - A blank name saves as `null` and shows "Untitled investigation".
  - On success, the TopBar shows the new name and the autosave status updates.
  - On failure, an error toast appears and the old name comes back.
- **Tabs:** the TopBar tabs are Investigation (`/`), Documents (`/documents`) and Settings (`/settings`, D26). Leaving a page with unsaved edits prompts first (UI-14, UI-22).

## Interfaces

**Routes:** `/` is InvestigationPage. `/documents` is DocumentsPage, and the optional `?doc=<id>` parameter selects a document. `/settings` is SettingsPage (D26, [settings-page.md](settings-page.md)). No route ever carries search text (D33).

**Components** (in `apps/web/src/components/` unless another path is given):

| Component | Responsibility |
|---|---|
| `App.tsx` | Router, app shell, active-investigation state, StartDialog gate |
| `TopBar` (new) | Wordmark, tabs (Investigation, Documents, Settings), name with inline Rename (D30), autosave status, Load, Save, user-menu slot |
| `StartDialog` (new) | Resume (with UI-30 details) / New / Load on startup, and inline load errors (D34, D35) |
| `ConfirmDialog`, `Toast`, `ApiErrorBanner`, `LoadReportDialog` (new) | Shared dialogs, toasts and the error banner |
| *removed:* `EdgeEditor.tsx` | — |

**Backend operations:** the original UI design assumed only three operations exist: list documents, save/delete a document, and get the graph, leaving the endpoints to the data-model and CSV designs. Those endpoints are now defined in [../backend/api.md](../backend/api.md).

## Acceptance criteria
- [ ] `/` and `/documents` render the correct pages, and the browser's back and forward buttons work between them.
- [ ] StartDialog appears on every open and every reload, and can't be dismissed. "Resume" appears only when an autosave exists, and shows the name, last-saved time and counts. The browser's cookies, `localStorage` and `sessionStorage` hold nothing from TxnWeave.
- [ ] New, Resume and a completed Load all land on `/`.
- [ ] Choosing a `.txt` file shows "Choose a TxnWeave .csv file." without any upload. A `.csv` without the marker shows "This file is not a TxnWeave save file." and offers no way to load it. In both cases StartDialog stays open.
- [ ] A marked file with problems opens LoadReportDialog with "Load documents" and "Cancel". Cancel from the TopBar keeps the current investigation unchanged.
- [ ] Unsaved-change prompts appear when switching documents or pages and when starting or loading an investigation.
- [ ] Every control can be reached by keyboard and shows a visible focus ring.

- [ ] Clicking the TopBar name allows renaming. Enter saves, Esc cancels, and blank shows "Untitled investigation". Delete investigation is on the Settings page (D29).

## Course requirements
Traces: FR-01, FR-02, FR-07, FR-09, FR-11, FR-13, FR-17, FR-18, FR-19, UC02, UC04, UC05 (full map in [../project/traceability.md](../project/traceability.md)). D21, UI-18, UI-19 and UI-20 have no FR behind them; they are listed as untraced.
