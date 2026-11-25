# UI: Investigation Page (graph)

- **Status:** Agreed (from `page-and-ui-layout.md` v2). Updated 2026-11-17 (user decisions): D9 styles become per-investigation defaults (D27); importance styles and the PropertyPanel toggle (D31, UI-26); styles taken from settings (UI-29); updated non-goals. Updated 2026-11-23 (user decisions) to follow `docs/development/drawioactivitydiagrams/Investigation.drawio`: live export orientation preview (D36, UI-32) and the legend toggle (D37, UI-33). Updated 2026-11-24 (user decisions): node positions are saved (D8 amended, D38, UI-36 to UI-38); the export preview always restores the saved positions (D36, UI-32); the layout is deterministic (UI-32 wording).
- **Scope:** The Investigation page at `/`: the read-only Cytoscape graph on the mist canvas, node shapes, fills, labels and the incomplete style, edge styles and labels, the automatic layout, saved node positions and new-node placement, the empty and loading states, the toolbar (fit, zoom, re-layout, edge labels, Export PNG, legend), the PropertyPanel, and landscape/portrait PNG export.
- **Master plan:** [../master-plan.md](../master-plan.md) (B13 card masking)
- **Related:** [color-system.md](color-system.md) (palette tokens), [../backend/graph-output.md](../backend/graph-output.md) (`GraphOut`, classes, frontend vs backend split), [../backend/node-positions.md](../backend/node-positions.md) (BD35 to BD37, layout endpoints), [documents-page.md](documents-page.md) ("Edit in Documents" target), [app-shell.md](app-shell.md)

## Non-goals
- Creating, linking or deleting nodes on the graph itself.
- Searching on the graph. Document search is on the Documents page (D33).
- Path finding, path highlighting and named paths. FR-15 and UC07 are met by importance (BD27, D31).
- Saving positions set by the export preview (D36). Saving zoom and pan.
- Node positions in the CSV (BD35, F22).

## Decisions
| # | Decision | Rationale | Alternatives considered |
|---|---|---|---|
| D7 | Graph structure is read-only. Users can pan, zoom and drag. Clicking a node opens a read-only PropertyPanel with an "Edit in Documents" button | The plan says nodes come from forms, not drawing | Editing directly on the graph |
| D8 | **Every node's position is saved** on the server (BD35), and no node moves on its own between loads. When no node has a saved position (a new investigation, or one loaded from CSV), the full automatic `cose` layout (deterministic: the same data always gives the same positions) runs and its result is saved. Dragging a node saves its new position (UI-36). Nodes that appear later are placed by D38. Re-layout replaces every saved position after a confirm (UI-37) | User decision (2026-11-24), reversing v1. An agent's arrangement of a case should survive reloads. The CSV still holds no layout data (BD35), which was v1's reason | v1 text, reversed: "Dragged positions are not saved in v1"; keep positions for the session only; save only dragged nodes |
| D38 | **Placing new nodes.** A "new node" is any node in the graph response without a `position` (new document, new incomplete node, or an incomplete node whose placeholder ID changed because its key changed, 3.6). New nodes are placed, and only the **nodes nearest to them** may move to make room: each new node's direct neighbors (one edge away) and any node within 150 model px of a new node's starting spot. Every other node is locked during the layout run. Afterwards every node that moved is saved (UI-38) | User decision: "the nodes nearest to it can be moved as needed to fit the new node". Neighbors plus a fixed radius is simple, deterministic and easy to test | Move no saved nodes; re-run the whole layout |
| D9 | Each node type gets its own shape and fill. Incomplete nodes use 75% opacity plus a dashed border | The palette alone can't separate 4 types, so shape does the work | Color only |
| D10 | Gift card numbers are shown as the last 4 digits only ("…1234") on the graph, in PNG exports and in list titles. The full number appears in the panel and the form | Card numbers are sensitive | Always show in full |
| D11 | Edges carry short labels, with a toolbar toggle to hide them | Explains what each connection means | No labels |
| D36 | **Export orientation is a live preview.** In ExportDialog, choosing Landscape or Portrait re-runs the `cose` layout on the on-screen graph inside a bounding box of that aspect ratio, then fits the view: the user sees the nodes move. **Landscape** = 16:9, exported at 1920×1080 px; **Portrait** = 9:16, exported at 1080×1920 px. Landscape is preselected and applied when the dialog opens. **Cancel** (or Esc) and **Export** both restore the node positions from just before the dialog opened, which are the saved positions (D8). The preview is never saved | User decision (2026-11-23), following the diagram's "move graph nodes to fit landscape/portrait image". Restore after Export: user decision (2026-11-24), so the screen always matches what is saved | Frame only the exported image, with no on-screen change (the old UI-7); Export saves the previewed positions; previewed positions stay on screen after Export (2026-11-23 text, replaced) |
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
  - Re-layout: replaces every saved position with a fresh full layout, after a confirm (UI-37). Disabled when there are no nodes
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
  - Clicking Landscape or Portrait applies that layout. Switching back and forth is allowed. The layout is deterministic, so switching back gives the same arrangement as before.
  - Nodes can't be dragged while the dialog is open (`cy.autoungrabify(true)`, undone on close), so no position is saved from the preview.
  - Export renders the PNG at the chosen size on the mist background, restores the snapshot, and closes the dialog.
  - Cancel or Esc restores the snapshot and closes the dialog. Nothing is saved to the server either way.
- **UI-36. Saving a drag (D8).** On Cytoscape `dragfree`, the node's ID and position go into a pending batch. 250 ms after the last `dragfree`, the batch is sent as one `PATCH .../layout` (BD36). Dragging several selected nodes at once therefore sends one request. Leaving the page sends a pending batch at once. On failure, the toast "Couldn't save node position" appears, and the node stays where it was dropped (it returns to its last saved spot the next time the page opens). A drag never changes `has_unsaved_changes` (BD35).
- **UI-37. Re-layout (D8).** Clicking Re-layout opens a ConfirmDialog: "Re-layout will replace the saved positions of every node." Buttons: **Re-layout** (primary) and **Cancel**. On confirm, the full automatic layout runs (the same result a first open would give for this data), the view is fitted, and every node's position is sent with `PUT .../layout`. On failure, the toast "Couldn't save the new layout" appears. The nodes stay where the layout put them, and the old positions come back on the next open.
- **UI-38. Placing nodes when the graph loads.** Every time graph data arrives (page open, UI-8; refetch, UI-26):
  1. Every node with a `position` is put there.
  2. **No node has a position** (and there is at least one node): run the full automatic layout, then `PUT` every position.
  3. **Some nodes have none:** place them by D38, then `PATCH` the new nodes and every other node that moved by more than 0.5 px:
     - Starting spot, one new node at a time in backend order: if any of its neighbors already has a position (including new nodes placed earlier in this pass), the centroid of those neighbors plus 60 px at an angle of 137.5° × (its index among the new nodes). Otherwise, a column 150 px to the right of the bounding box of the placed nodes: x = right edge + 150, y = top edge + 80 × k, where k counts the nodes already put in that column.
     - Movable: the new nodes, their direct neighbors, and nodes within 150 px (center to center) of any new node's starting spot. Lock every other node, run `cose` with the existing options (no randomize, no fit), then unlock all.
  4. **Every node has a position:** nothing moves and nothing is saved.
  5. On a page open, fit the view as before (zoom capped at 100%). On a refetch that keeps the view (UI-26), don't fit.

  Saving placed positions (steps 2 and 3) is the only time the page writes positions without a drag. On failure, the toast "Couldn't save node positions" appears. The positions stay on screen and are worked out again (with the same result) on the next open.
- **UI-33. Legend (D37):** toggling the checkbox shows or hides the bottom-left overlay at once. The state is held in app state only (never in browser storage, D34), so it is off again after a reload.
- **UI-29. Styles from settings:** the page loads `GET .../settings` together with the graph, and rebuilds the stylesheet whenever either changes. Settings saved on the Investigation settings page apply the next time this page is opened (the graph is marked stale, UI-22).

## Components
| Component | Responsibility |
|---|---|
| `pages/InvestigationPage` | GraphToolbar + GraphCanvas + PropertyPanel, plus empty and loading states |
| `GraphToolbar` | Fit, zoom, re-layout (with its ConfirmDialog, UI-37), edge-label toggle, Export, legend |
| `GraphCanvas` | Cytoscape rendering, selection events, empty state, applying saved positions and the drag-save batch (UI-36, UI-38) |
| `src/graph/placement.ts` (new) | `placeNewNodes(cy, newIds) -> string[]` (D38: starting spots, movable set, locked `cose` run; returns the IDs whose positions changed) and `collectPositions(cy, ids)` for the layout requests |
| `PropertyPanel` | Read-only node details, the Important checkbox (D31), and "Edit in Documents" |
| `ExportDialog` (new) | Landscape/Portrait live preview, position snapshot and restore, PNG export (D36) |
| `GraphLegend` (new) | Bottom-left legend overlay, shown when the Legend checkbox is on (D37) |
| `src/graph/cytoscapeConfig.ts` | `buildStylesheet(settings)`: the graph stylesheet from the rules above and the investigation settings. Imports `palette.ts`. `runLayout(cy)`: the full deterministic layout (D8) |
| `src/graph/graphMapper.ts` | Converts API data into Cytoscape elements, including masked labels |

## Acceptance criteria
- [ ] With 0 nodes, the canvas shows the black italic "add forms to begin graphing" and a "Go to Documents" button.
- [ ] Each node type renders with the shape and fill in the node table. Incomplete nodes have 75% opacity, a dashed border, and the "(incomplete)" label suffix.
- [ ] Gift card numbers are masked to the last 4 digits on the graph, in PNG exports and in list titles, and shown in full in the PropertyPanel and form.
- [ ] Clicking a node opens the PropertyPanel, and "Edit in Documents" opens that document's form.
- [ ] Export PNG produces a 1920×1080 landscape or 1080×1920 portrait image with all nodes visible and filling the frame, on a #D2CDCB background.
- [ ] Opening ExportDialog visibly re-arranges the graph for Landscape. Choosing Portrait re-arranges it again. Choosing Landscape again gives the same arrangement as the first time. Cancel and Export both put every node back at its saved position, and no layout request is sent.
- [ ] Drag a node and reload: it is where it was dropped. Dragging three selected nodes sends one `PATCH`. `has_unsaved_changes` is unchanged.
- [ ] First open of an investigation with no saved positions sends one `PUT` with every node. Reopening sends nothing and nothing moves.
- [ ] Add a document connected to node A: on the next open, only the new node, A and other nodes within 150 px of the new node's starting spot have moved, and one `PATCH` holds exactly those nodes.
- [ ] Re-layout shows the confirm. Cancel changes nothing. Re-layout gives the same arrangement as a first open of the same data, and sends one `PUT`.
- [ ] Saving a document that promotes an incomplete node: the new node appears where the incomplete node was (BD37).
- [ ] The Legend checkbox is off on first open. Turning it on shows the legend bottom-left, and the PNG includes it only while it is on.

- [ ] An important node shows the double ink border. An edge between two important nodes is 4px in the settings color. Un-checking either node returns the edge to normal after the refetch.
- [ ] The Important checkbox is disabled on incomplete nodes.
- [ ] After changing a type's color and shape in settings, nodes, the legend and PNG exports use the new style.

## Course requirements
Traces: FR-02, FR-09, FR-10, FR-13, FR-14, FR-15, FR-17, FR-18, FR-20, FR-21, UC01, UC03, UC06 to UC09 (full map in [../project/traceability.md](../project/traceability.md)). Still open:
- F7: "details page" wording.
- F9: which mouse button pans (suggestion NQ-8).
- Suggestion S-1: add edge kinds to the legend.

FR-25 / UC10 is Future.
