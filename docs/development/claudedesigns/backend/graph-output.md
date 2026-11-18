# Backend: Graph Output (Cytoscape elements)

- **Status:** Agreed (from `backend-graphing-design.md` v3, behavior section 4 and the `GraphOut` interface). Updated 2026-11-17 (user decisions): node and edge `important` (BD27), behaviors 4.3 and 4.4.
- **Scope:** `services/graph_service.py` and `GET /api/investigations/{iid}/graph`: how saved documents, placeholders and merged links become Cytoscape nodes and edges, the `GraphOut` payload, every node and edge `data` field, the classes the backend sets, and the exact split of graph work between backend and frontend.
- **Master plan:** [../master-plan.md](../master-plan.md) (B13 card masking, G1)
- **Related:** [relationship-resolution.md](relationship-resolution.md) (produces the input), [api.md](api.md) (endpoint row), [../ui/investigation-page.md](../ui/investigation-page.md) (renders it: labels, styles, layout, PNG export)

## Non-goals
- PNG export. This happens entirely in the frontend (`cy.png()` in `ExportDialog`, [investigation-page](../ui/investigation-page.md) UI-7). The backend has no part in it.
- Graph layout and node positions (D8).

## Decisions
| # | Decision | Rationale | Alternatives considered |
|---|---|---|---|
| B12 | The graph endpoint returns **Cytoscape's element format**. The backend sets the classes. `graphMapper.ts` only builds label text | Keeps structure in the backend (G1) and presentation in the frontend | The frontend builds the graph |

## 4. Behavior
4.1 `GET .../graph` maps every saved document and placeholder to a Cytoscape node, and every merged link to an edge.
4.2 An empty investigation returns 200 with empty `nodes` and `edges`.
4.3 **Node importance (BD27):** `data.important` copies the document's flag. Placeholders are always `false`. Important nodes get the class `important`.
4.4 **Edge importance (BD27):** after merging (3.9), `data.important` is `true` exactly when both the source and the target nodes have `important: true`. It is computed in `build_graph` on every call and never stored. It doesn't depend on `kind`, `status` or `match`, but it can't be true when either end is a placeholder. Important edges get the class `important`. Settings (colors and shapes) are **not** part of `GraphOut` (BD31).

Ordering follows [relationship-resolution](relationship-resolution.md) 3.12 (determinism).

## `GraphOut`
```json
{
  "investigation_id": 1,
  "generated_at": "2026-11-17T15:04:05Z",
  "counts": {"nodes": 3, "edges": 2, "incomplete_nodes": 0},
  "elements": {
    "nodes": [
      {"data": {"id": "12", "document_id": "12", "node_type": "transaction", "status": "complete",
                "display_key": "00482913", "date": "2026-03-14", "time": "18:05",
                "store_number": "042", "register_number": "003"},
       "classes": "transaction"},
      {"data": {"id": "13", "document_id": "13", "node_type": "transaction", "status": "complete",
                "display_key": "00482913", "date": "2026-03-14", "time": "18:20",
                "store_number": "042", "register_number": "007"},
       "classes": "transaction"},
      {"data": {"id": "15", "document_id": "15", "node_type": "gift_card", "status": "complete",
                "display_key": "…0123", "date": "2026-02-01", "time": "10:00",
                "store_number": "042", "register_number": null},
       "classes": "gift-card"}
    ],
    "edges": [
      {"data": {"id": "e-used_in-15-12", "source": "15", "target": "12", "kind": "used_in",
                "status": "incomplete", "match": "ambiguous", "refs": ["gift_card_history"], "ref_count": 1},
       "classes": "used-in incomplete ambiguous"},
      {"data": {"id": "e-used_in-15-13", "source": "15", "target": "13", "kind": "used_in",
                "status": "incomplete", "match": "ambiguous", "refs": ["gift_card_history"], "ref_count": 1},
       "classes": "used-in incomplete ambiguous"}
    ]
  }
}
```

## Node `data` fields
| Field | Type | Meaning |
|---|---|---|
| `id` | `DocumentId` | Equal to `document_id` |
| `document_id` | `DocumentId` | Used for `GET .../documents/{id}` and "Edit in Documents" |
| `node_type` | `DocumentType` | |
| `status` | `DocumentStatus` | |
| `display_key` | `string` | Transaction or order number, `…` plus the last 4 card digits, or the Misc name |
| `date`, `time` | `string \| null` | The main date and time (activation date and time for a gift card) |
| `store_number` | `string \| null` | Transaction store, gift card activation store, or order pickup store |
| `register_number` | `string \| null` | Transactions only |
| `important` | `bool` | 4.3. Example nodes above omit it for brevity; it is always present |

## Edge `data` fields
`id` (`e-<kind>-<source>-<target>`), `source`, `target`, `kind`, `status`, `match` (`"exact" | "ambiguous"`), `refs: string[]`, `ref_count: int`, `important: bool` (4.4, always present).

## Classes
- Nodes: `transaction`, `gift-card`, `online-order` or `misc`, plus `incomplete` or `important` when they apply. They never both apply.
- Edges: `activated`, `used-in` or `related`, plus `incomplete` when it applies, plus `ambiguous` when `match` is ambiguous, plus `important` (4.4). The UI styles only `incomplete`, so ambiguous edges are dashed like any incomplete edge (BD15). `ambiguous` stays in the data in case a style is wanted later.

## Frontend vs backend split (B12)
| Concern | Where |
|---|---|
| Nodes, placeholders, matching, ambiguity, edges, merging, status, classes, card masking, `title`, node and edge `important` | Backend |
| Building the per-type color and shape stylesheet from `GET .../settings` (BD31) | `cytoscapeConfig.ts` |
| Node label text (`TXN 00482913` plus a distinguishing store suffix if follow-up F1 is approved, `GC …0123`, `ORD …`, Misc name, " (incomplete)"), edge label text from `kind` | `graphMapper.ts` |
| Styles, layout, PNG export, label toggle | `cytoscapeConfig.ts` / components |
| `MM-DD-YYYY` ↔ ISO and `$` ↔ signed cents conversion in forms | Frontend form code |

Note: F1 has since been approved and applied (the store suffix rule is in [../ui/investigation-page.md](../ui/investigation-page.md)). See [../design-history.md](../design-history.md).

## Acceptance criteria
- [ ] `GET /graph` on an empty investigation returns 200 with empty lists.
- [ ] The same data gives identical `elements` across two calls.

Also see `sample-graph.json` in [build-plan.md](build-plan.md) step 7.

- [ ] With A and B important and C not, the A–B edge has `important: true` and class `important`, and the A–C edge does not. Un-marking A makes A–B `false` on the next call.
- [ ] An edge to a placeholder is never important.

## Course requirements
Traces: FR-02, FR-08, FR-14, FR-15, UC06, UC07 (full map in [../project/traceability.md](../project/traceability.md)).
