# Project: Course Requirements (FR and UC)

- **Status:** Agreed for the wave assignments and the decisions cited (user decisions 2026-11-17). Items marked "open" refer to follow-ups still waiting for the user in [../design-history.md](../design-history.md).
- **Source plans:** `docs/development/CS420_Project_Discovery and Specification.pdf`, sections 3 (use cases) and 4 (requirement levels)
- **Master plan:** [../master-plan.md](../master-plan.md) (P1 waves, P2 traceability, BD27 importance)
- **Related:**
  - [traceability.md](traceability.md): design elements → FR/UC.
  - [context.md](context.md): stakeholders, persona, interviews, quality goals, risks.

## How to read this
- **Wave** (P1). The PDF's levels are replaced:
  - **Wave 1:** FR-01 to FR-12, fully implemented.
  - **Wave 2:** FR-13 to FR-21, at least started.
  - **Future:** everything else, after the assignment is submitted.
- **Coverage:**
  - **Covered:** a decision or behavior meets the requirement.
  - **Partial:** the missing piece is named.
  - **Future:** intentionally not designed yet.
- The FR and UC IDs are the PDF's own IDs.

## Terminology mapping
| PDF term | TxnWeave term |
|---|---|
| node management page | Documents page |
| canvas, node graph | Investigation page graph |
| investigation settings | Investigation settings page (D26) |
| custom node, arbitrary item | Misc document |
| node details page | PropertyPanel (F7, open) |
| save file, structured file | Sectioned CSV (BD9) |
| important path, named path, main route | A chain of important nodes and the important edges between them (BD27) |

## Functional requirements
| ID | Requirement (short) | Wave | Coverage | Where |
|---|---|---|---|---|
| FR-01 | Create, edit, open and delete investigations | 1 | Covered | 1.1, UI-1 (create); D3, UI-1 (open: Resume, Load CSV); D30, BD32 (rename); D29, 1.6 (delete) |
| FR-02 | Data shown as an interactive graph | 1 | Covered | D7, B12, [investigation-page](../ui/investigation-page.md) |
| FR-03 | Transaction form | 1 | Covered. The design also requires a store number (BD26) | [data-model](../backend/data-model.md), [documents-page](../ui/documents-page.md) |
| FR-04 | Gift card form | 1 | Covered | same |
| FR-05 | Online order form | 1 | Covered | same |
| FR-06 | Custom node: label, description, notes, payments | 1 | Partial. "Description" maps to Notes (F12, open) | Misc |
| FR-07 | Edit and delete nodes | 1 | Covered | D14, D15, 2.3, 2.4 |
| FR-08 | Relationships come from the forms, never drawn | 1 | Covered | G1, B12, R1 to R6 |
| FR-09 | Clicking a node shows its properties | 1 | Covered | D7, UI-6 |
| FR-10 | Zoom, pan and reposition nodes | 1 | Covered. Which mouse button pans is open (F9) | D7, D8 |
| FR-11 | Export and import investigation data | 1 | Covered | B17, BD9 to BD13, BD33 |
| FR-12 | Inputs validated before node creation | 1 | Covered | D14, UI-13, 2.1 |
| FR-13 | Users assign colors to nodes and relationships | 2 | Covered. Per-type color and shape, and the important-edge color, on the Investigation settings page. Individual edges aren't colored, because edges aren't stored | D26 to D28, BD29 to BD31, BD33 |
| FR-14 | Mark nodes and relationships as important | 2 | Covered. Nodes are marked; a relationship is important when both of its ends are | BD27, BD28, D31, D32 |
| FR-15 | Identify and highlight a path connecting selected nodes | 2 | Covered **through importance**. There is no path finding (see below) | BD27, D31 |
| FR-16 | Search graph elements by identifier or text | 2 | Covered **on the Documents page**. No search on the graph | D33, UI-28 |
| FR-17 | Export the graph as an image | 2 | Covered | UI-7 |
| FR-18 | Autosave | 2 | Covered | B2 |
| FR-19 | Identify invalid import data | 2 | Covered | 5.2, 5.7, 5.9, UI-17 |
| FR-20 | Workspace grows as nodes are added or moved | 2 | Covered: Cytoscape's canvas has no fixed size, plus Fit and pan | D8, UI-7 |
| FR-21 | Legend for element types and meanings | 2 | Covered for node types, incomplete style and important style. Edge kinds would come from suggestion S-1 | Legend, [investigation-page](../ui/investigation-page.md) |
| FR-22 | Location and reason for each import error | Future | Already met by `ImportReport` | [csv-save-load](../backend/csv-save-load.md) |
| FR-23 | User authentication | Future | IAM design still to come | — |
| FR-24 | Restrict investigations by permissions | Future | IAM | — |
| FR-25 | Navigate from a gift card to its transaction history | Future | Partly met: PropertyPanel connected nodes (UI-6), document search by card digits (D33) | — |
| FR-26 | Track user logins | Future | IAM | — |
| FR-27 | AI analysis of the graph | Future | Not designed. A forked build that runs only on the user's machine could keep the data local (former F18) | — |

## Use cases (Discovery PDF, Table 1)
| ID | Use case | Coverage | Where |
|---|---|---|---|
| UC01 | View the graph: scroll to zoom, drag to pan | Covered. Right-drag is still open (F9) | D7 |
| UC02 | Manage nodes on the node management page | Covered | Documents page, UI-9 to UI-16, UI-28 |
| UC03 | Inspect node details | Covered | UI-6, F7 (wording) |
| UC04 | Save to a readable CSV | Covered | BD9 ("section", not "sheet", F8) |
| UC05 | Open a saved file and edit everything in it | Covered | BD13, UI-17 |
| UC06 | Check a box to mark a node important; it is highlighted | Covered. The highlight is a fixed ink double border; the **edge** color comes from settings | D31, D32, BD27 |
| UC07 | Named important paths | Covered through importance, without names (see below) | BD27 |
| UC08 | Per-type colors and shapes, saved with the export | Covered | D26 to D28, BD33 |
| UC09 | Export the graph as a picture | Covered | UI-7 |
| UC10 | Isolated graph for one gift card | Future (FR-25) | — |

## Paths are met by importance (FR-15, UC07)
User decision (former F16): no path finding, no path highlighting and no named paths are designed. To show a path or "main route":
1. The agent marks each node along the route as important. This can be done in the PropertyPanel (D31) or in the form (D32).
2. Every edge whose two ends are both important is drawn in the important-edge style (BD27, 4.4). The route stands out on the graph and in PNG exports.
3. Un-marking a node removes its edges from the highlight automatically.
4. "Important only" on the Documents page lists the route's documents (D33).

Limits:
- There is one highlight set per investigation, not several named paths.
- An edge between two important nodes that aren't on the intended route is highlighted too.

## Suggestions still open
- **S-1 (FR-21):** add the three edge kinds and a dashed-edge sample to the legend.
- **NQ-8 (UC01, F9):** pan by left- or right-drag on empty canvas, and suppress the context menu.
