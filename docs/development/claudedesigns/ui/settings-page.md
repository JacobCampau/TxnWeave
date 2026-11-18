# UI: Investigation Settings Page

- **Status:** Agreed (2026-11-17, user decisions on follow-ups F3, F4 and F11)
- **Scope:** The Investigation settings page at `/settings`:
  - how to reach it;
  - the Appearance section (color and shape for each document type, and the important-edge color);
  - validation, Save, and Reset to defaults;
  - the Delete investigation action.

  Storage, endpoints and CSV are backend work. They are cited here, not repeated.
- **Master plan:** [../master-plan.md](../master-plan.md) (D19 via color-system, BD27 importance, P1 waves)
- **Related:**
  - Backend: [../backend/data-model.md](../backend/data-model.md) (BD29 settings schema), [../backend/persistence.md](../backend/persistence.md) (BD30), [../backend/api.md](../backend/api.md) (BD31 endpoints, investigation DELETE), [../backend/csv-save-load.md](../backend/csv-save-load.md) (BD33 settings section).
  - UI: [color-system.md](color-system.md), [investigation-page.md](investigation-page.md) (applies the settings), [app-shell.md](app-shell.md) (TopBar tab).
- **Requirements:** FR-13, UC06, UC08 (appearance), FR-01 (delete). Wave 1 covers the route and Delete investigation. Wave 2 covers Appearance (P1).

## Non-goals
- Changing the palette itself, or entering colors in any other way (hex, picker). Only palette tokens are allowed (D27).
- Changing the incomplete-node style, the selection style, label text or edge kinds.
- App-wide settings shared between investigations. Every setting belongs to one investigation.

## Decisions
| # | Decision | Rationale | Alternatives considered |
|---|---|---|---|
| D26 | The Investigation settings page is the route **`/settings`**. It is reached from a third TopBar tab, **"Settings"**, after "Investigation" and "Documents" | One more tab needs no new navigation pattern. A route gives the page a real URL and back-button support (D1) | A dialog opened from a gear icon; a section on the Investigation page |
| D27 | **Appearance choices.** For each document type the user picks a **fill color** from the 5 palette tokens (ink, slate, mist, rose, crimson) and a **shape** from 8 Cytoscape shapes: `ellipse`, `rectangle`, `round-rectangle`, `triangle`, `diamond`, `hexagon`, `octagon`, `star`. Every node keeps its 2px ink border, whatever its fill. The **important-edge color** can be ink, slate or crimson only. **No two document types may share the same color and shape.** The defaults are D9's styles, with ink as the important-edge color | Palette tokens keep D19's no-hex and black-or-white-text rules: node labels sit **outside** the node on the mist canvas, so a fill never changes text contrast. The ink border keeps every fill visible against mist (11.8:1), even a mist or rose fill. Rose (2.2:1) and mist (1:1) fail 3:1 against the canvas, so they are left out as edge colors. Distinct color-and-shape pairs keep the four types distinguishable | Any color; limiting fills to tokens with 3:1 against mist (that would drop mist and rose, and rose is a default) |
| D28 | **Reset to defaults** restores every appearance value to the D9 defaults for this investigation. It asks for confirmation first, then calls `DELETE .../settings` (BD31) | One clear way back, for a non-expert user (NQ-1) | Reset each type separately |
| D29 | **Delete investigation** lives on this page, in a separate "Investigation" section. It asks for confirmation, then calls `DELETE /investigations/{iid}`. Afterward there is no active investigation, so StartDialog opens (UI-1) | FR-01 asks for delete. A settings page is the expected place for a destructive, rarely used action, and it keeps the TopBar uncluttered | A TopBar menu; delete only through BD7 |

## Layout
- The page background is mist. One centered column, 720px wide, has two sections.
- **Appearance**
  - A table with one row per document type (Transaction, Gift Card, Online Order, Misc). Columns:
    - Type name.
    - A live **preview chip**: the shape filled with the chosen color, with a 2px ink border, drawn by a small Cytoscape instance or SVG using `palette.ts`.
    - A **Color** dropdown listing Ink, Slate, Mist, Rose and Crimson, each with a swatch.
    - A **Shape** dropdown listing Circle, Rectangle, Rounded rectangle, Triangle, Diamond, Hexagon, Octagon and Star.
  - One more row, **"Important connections"**, with a Color dropdown (Ink, Slate, Crimson) and a preview line 4px wide.
  - Under the table, the primary button **Save appearance** and the secondary button **Reset to defaults**.
- **Investigation**
  - The investigation's name, shown read-only. Renaming is done on the TopBar (D30).
  - The destructive button **Delete investigation**.

## Behavior
- **UI-21. Load:** opening `/settings` calls `GET .../settings` (BD31) and fills the form with the effective values. While loading, a spinner shows. If loading fails, the API error banner (UI-18) appears.
- **UI-22. Save appearance:**
  - Changes stay local until Save.
  - Save is blocked while two types share the same color and shape. Both rows then show the error style and the message "Error: <Type A> and <Type B> look the same. Change the color or shape of one."
  - On Save, the page calls `PUT .../settings`. On success, a success toast appears and the graph is marked stale. A 422 response shows the error summary.
  - Leaving the page with unsaved appearance changes asks "Discard changes?", as in UI-14.
- **UI-23. Reset to defaults:** the button opens ConfirmDialog ("Reset appearance to the default colors and shapes?" Reset / Cancel). Confirming calls `DELETE .../settings`, reloads the defaults and shows a toast. The button is disabled when `is_default` is true.
- **UI-24. Delete investigation:**
  - The button opens ConfirmDialog, which names the investigation.
  - If `has_unsaved_changes` is true, the dialog adds "This investigation has changes that were never exported to CSV. They will be lost."
  - The buttons are **Delete investigation** (destructive) and **Cancel**.
  - Confirming calls `DELETE /investigations/{iid}`, clears the active investigation, navigates to `/`, and opens StartDialog (UI-1). On failure, an error toast appears and nothing changes.

## Components
| Component | Responsibility |
|---|---|
| `pages/SettingsPage` (new) | Loads settings. Appearance and Investigation sections |
| `AppearanceTable` (new) | Rows, dropdowns, preview chips, distinctness check, Save and Reset buttons |
| `StylePreview` (new) | Draws one shape-and-color chip from palette tokens |

## Acceptance criteria
- [ ] The TopBar shows a "Settings" tab that opens `/settings`. Back and forward work.
- [ ] The color dropdowns offer only the 5 palette tokens (only ink, slate and crimson for important connections), and the shape dropdown offers only the 8 listed shapes.
- [ ] Choosing the same color and shape for two types blocks Save and shows the error on both rows.
- [ ] After Save, the Investigation page draws each type with the saved color and shape, and the legend matches.
- [ ] Reset to defaults asks for confirmation and restores the D9 styles. The button is disabled when the settings are already the defaults.
- [ ] Delete investigation warns about unexported changes when `has_unsaved_changes` is true. After confirming, StartDialog appears and the investigation no longer exists (`GET` returns 404).
- [ ] `apps/web/src` still contains hex colors only in `palette.ts` and `global.css`. Settings use token names.
