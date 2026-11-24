# UI: Investigation Page (graph)

- **Status:** Agreed (from `page-and-ui-layout.md` v2). Updated 2026-11-17 (user decisions): D9 styles become per-investigation defaults (D27); importance styles and the PropertyPanel toggle (D31, UI-26); styles taken from settings (UI-29); updated non-goals. Updated 2026-11-23 (user decisions) to follow `docs/development/drawioactivitydiagrams/Investigation.drawio`: live export orientation preview (D36, UI-32) and the legend toggle (D37, UI-33).
- **Scope:** The Investigation page at `/`: the read-only Cytoscape graph on the mist canvas, node shapes, fills, labels and the incomplete style, edge styles and labels, the automatic layout, the empty and loading states, the toolbar (fit, zoom, re-layout, edge labels, Export PNG, legend), the PropertyPanel, and landscape/portrait PNG export.
- **Master plan:** [../master-plan.md](../master-plan.md) (B13 card masking)
- **Related:** [color-system.md](color-system.md) (palette tokens), [../backend/graph-output.md](../backend/graph-output.md) (`GraphOut`, classes, frontend vs backend split), [documents-page.md](documents-page.md) ("Edit in Documents" target), [app-shell.md](app-shell.md)

## Non-goals
- Creating, linking or deleting nodes on the graph itself.
- Searching on the graph. Document search is on the Documents page (D33).
- Path finding, path highlighting and named paths. FR-15 and UC07 are met by importance (BD27, D31).
- Saving dragged node positions, including positions set by the export preview (D36).

## Decisions
| # | Decision | Rationale | Alternatives considered |
|---|---|---|---|
| D7 | Graph structure is read-only. Users can pan, zoom and drag. Clicking a node opens a read-only PropertyPanel with an "Edit in Documents" button | The plan says nodes come from forms, not drawing | Editing directly on the graph |
| D8 | Nodes are placed by the automatic `cose` layout, with a Re-layout button. Dragged positions are not saved in v1 | Avoids storing layout data in the CSV | Save positions |
| D9 | Each node type gets its own shape and fill. Incomplete nodes use 75% opacity plus a dashed border | The palette alone can't separate 4 types, so shape does the work | Color only |
| D10 | Gift card numbers are shown as the last 4 digits only ("…1234") on the graph, in PNG exports and in list titles. The full number appears in the panel and the form | Card numbers are sensitive | Always show in full |
| D11 | Edges carry short labels, with a toolbar toggle to hide them | Explains what each connection means | No labels |
| D36 | **Export orientation is a live preview.** In ExportDialog, choosing Landscape or Portrait re-runs the `cose` layout on the on-screen graph inside a bounding box of that aspect ratio, then fits the view: the user sees the nodes move. **Landscape** = 16:9, exported at 1920×1080 px; **Portrait** = 9:16, exported at 1080×1920 px. Landscape is preselected and applied when the dialog opens. **Cancel** (or Esc) restores the node positions from just before the dialog opened. After **Export**, the previewed positions stay until the next Re-layout | User decision (2026-11-23), following the diagram's "move graph nodes to fit landscape/portrait image" | Frame only the exported image, with no on-screen change (the old UI-7) |
| D37 | **Legend is a toolbar checkbox**, off by default. When on, it is an overlay in the **bottom-left** corner of the canvas (the PropertyPanel is on the right). The PNG export includes the legend only when it is on | User decision (2026-11-23), following the diagram's "activate/deactivate legend" and mockup Figures 4 and 5 | Legend always shown; a legend panel outside the canvas |
| D31 | **Importance on the graph.** An important node (class `important`) gets a 6px **double ink** border instead of its 2px solid one. An important edge (class `important`, from 4.4) is a 4px solid line, with its line and arrow in the investigation's important-edge color (D27, default ink). An important edge that is also incomplete stays dashed. The PropertyPanel has an **"Important"** checkbox that saves immediately through the BD28 `PATCH`. It is disabled on incomplete nodes, with the note "Save this document to mark it important" | Uses the F5 highlight suggestion. Crimson is already the selection color, so the node highlight uses ink. The edge color follows the investigation settings, as the user asked | A crimson node ring; a toggle only on the Documents page |

## Graph styles (`cytoscapeConfig.ts`)
The table below gives the **default** shape and fill for each type (D9). Each investigation can override them on the Investigation settings page (D27). `cytoscapeConfig.ts` builds the stylesheet from `GET .../settings` (BD31), mapping token names to hex through `palette.ts`. Borders, labels, and the incomplete and selection styles never change.

| Node type | Default shape | Default fill | Border |
|---|---|---|---|
| Transaction | ellipse | slate | 2px solid ink |
| Gift Card | round-rectangle (1.6:1 aspect ratio, card-like) | crimson | 2px solid ink |
| Online Order | hexagon | ink | 2px solid ink |
| Misc | diamond | rose | 2px solid ink (needed because rose against mist is only 2.2:1) |

- **Node labels:** below the node, black, 12px, showing the primary ID: `TXN 12345678`, `GC …1234`, `ORD 87654321`, or the Misc node's Node Name. When two or more visible Transaction nodes share a transaction number, each of their labels adds the store: `TXN 12345678 · S042`. A placeholder whose store is unknown leaves the store part out (`TXN 12345678`).
- **Incomplete node:** `opacity: 0.75`, 3px dashed ink border, and " (incomplete)" added to the label.
- **Selected node:** solid crimson underlay ring, 6px of padding outside the ink border. The ink border keeps the ring visible even on crimson Gift Card nodes.
- **Edges:** 2px slate line with a target arrow (6.5:1 against mist). An edge to an incomplete node is dashed. (Per BD15, ambiguous edges also carry the `incomplete` class and are dashed the same way; see [graph-output](../backend/graph-output.md).)
- **Edge labels:** black, 10px, on a mist text background.
- **Selected edge:** 3px crimson.
- **Important node / edge:** see D31.
- **Legend** (D37): mist chips. Each chip shows a type's **current** shape and fill (from settings) and its name. The legend also has a sample of the incomplete style, an important node sample, and an important edge sample.
- **PNG export:** mist background, same styles as the screen.

## Behavior
- **UI-4. Investigation page, empty:** with 0 nodes, the canvas shows centered black italic 20px text "add forms to begin graphing" and a secondary "Go to Documents" button.
- **UI-5. Investigation page, loading:** a spinner is centered on the canvas while the graph loads. If loading fails, the API error banner appears with a Retry button.
- **UI-6.** Clicking a node opens the PropertyPanel, which shows:
  - the node type
  - all fields, including the full gift card number
  - notes
  - connected nodes (clicking one selects it)
  - the "Important" checkbox (D31, UI-26)
  - an "Edit in Documents" button, which navigates to `/documents?doc=<id>`

  Clicking empty canvas or pressing Esc closes the panel.
- **UI-7.** Toolbar controls:
  - Fit to screen
  - Zoom in / Zoom out
  - Re-layout (runs `cose` again)
  - Edge labels on/off (on by default)
  - Export PNG: opens ExportDialog (D36, UI-32). The export downloads `<investigation-name>-graph.png`, with all nodes fitting within and filling the chosen orientation.
  - Legend checkbox (D37, UI-33), off by default
- **UI-8.** Navigating to the Investigation page after any document save refetches the graph.
- **UI-26. Toggling Important in the PropertyPanel (D31):**
  - Checking or unchecking calls `PATCH .../documents/{id}` and then refetches the graph, so edges gain or lose the important style. The current selection and zoom are kept.
  - While the request runs, the checkbox is disabled.
  - On failure, the checkbox reverts and an error toast appears.
- **UI-32. Export preview (D36):**
  - On open: save a snapshot of every node position, then apply Landscape.
  - Clicking Landscape or Portrait applies that layout. Switching back and forth is allowed. Each switch re-runs the layout, so the result can differ slightly.
  - Export renders the PNG at the chosen size on the mist background, closes the dialog, and keeps the current positions.
  - Cancel or Esc restores the snapshot and closes the dialog. Nothing is saved to the server either way.
- **UI-33. Legend (D37):** toggling the checkbox shows or hides the bottom-left overlay at once. The state is held in app state only (never in browser storage, D34), so it is off again after a reload.
- **UI-29. Styles from settings:** the page loads `GET .../settings` together with the graph, and rebuilds the stylesheet whenever either changes. Settings saved on the Investigation settings page apply the next time this page is opened (the graph is marked stale, UI-22).

## Components
| Component | Responsibility |
|---|---|
| `pages/InvestigationPage` | GraphToolbar + GraphCanvas + PropertyPanel, plus empty and loading states |
| `GraphToolbar` | Fit, zoom, re-layout, edge-label toggle, Export, legend |
| `GraphCanvas` | Cytoscape rendering, selection events, empty state |
| `PropertyPanel` | Read-only node details, the Important checkbox (D31), and "Edit in Documents" |
| `ExportDialog` (new) | Landscape/Portrait live preview, position snapshot and restore, PNG export (D36) |
| `GraphLegend` (new) | Bottom-left legend overlay, shown when the Legend checkbox is on (D37) |
| `src/graph/cytoscapeConfig.ts` | `buildStylesheet(settings)`: the graph stylesheet from the rules above and the investigation settings. Imports `palette.ts` |
| `src/graph/graphMapper.ts` | Converts API data into Cytoscape elements, including masked labels |

## Acceptance criteria
- [ ] With 0 nodes, the canvas shows the black italic "add forms to begin graphing" and a "Go to Documents" button.
- [ ] Each node type renders with the shape and fill in the node table. Incomplete nodes have 75% opacity, a dashed border, and the "(incomplete)" label suffix.
- [ ] Gift card numbers are masked to the last 4 digits on the graph, in PNG exports and in list titles, and shown in full in the PropertyPanel and form.
- [ ] Clicking a node opens the PropertyPanel, and "Edit in Documents" opens that document's form.
- [ ] Export PNG produces a 1920×1080 landscape or 1080×1920 portrait image with all nodes visible and filling the frame, on a #D2CDCB background.
- [ ] Opening ExportDialog visibly re-arranges the graph for Landscape. Choosing Portrait re-arranges it again. Cancel puts every node back where it was. After Export, the nodes stay where the preview put them.
- [ ] The Legend checkbox is off on first open. Turning it on shows the legend bottom-left, and the PNG includes it only while it is on.

- [ ] An important node shows the double ink border. An edge between two important nodes is 4px in the settings color. Un-checking either node returns the edge to normal after the refetch.
- [ ] The Important checkbox is disabled on incomplete nodes.
- [ ] After changing a type's color and shape in settings, nodes, the legend and PNG exports use the new style.

## Course requirements
Traces: FR-02, FR-09, FR-10, FR-13, FR-14, FR-15, FR-17, FR-20, FR-21, UC01, UC03, UC06 to UC09 (full map in [../project/traceability.md](../project/traceability.md)). Still open:
- F7: "details page" wording.
- F9: which mouse button pans (suggestion NQ-8).
- Suggestion S-1: add edge kinds to the legend.

FR-25 / UC10 is Future.
