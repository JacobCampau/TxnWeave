import type { ElementDefinition } from "cytoscape";
import type { EdgeKind, GraphOut, NodeData } from "../types/graph";

// Turns the backend's graph into Cytoscape elements. The backend already decided the nodes,
// edges and classes (B12); this file only adds the label text (graph-output.md split).

const EDGE_LABELS: Record<EdgeKind, string> = {
    activated: "activated",
    used_in: "used in",
    related: "related",
};

// Primary ID (investigation-page.md "Node labels"): TXN 12345678, GC …1234, ORD 87654321,
// or the Misc node's name.
function baseLabel(data: NodeData): string {
    switch (data.node_type) {
        case "transaction":
            return `TXN ${data.display_key}`;
        case "gift_card":
            return `GC ${data.display_key}`;
        case "online_order":
            return `ORD ${data.display_key}`;
        case "misc":
            return data.display_key;
    }
}

export function toElements(graph: GraphOut): ElementDefinition[] {
    const { nodes, edges } = graph.elements;

    // Transaction numbers used by two or more visible nodes get a store suffix (F1).
    const seen = new Map<string, number>();
    for (const node of nodes) {
        if (node.data.node_type === "transaction") {
            seen.set(node.data.display_key, (seen.get(node.data.display_key) ?? 0) + 1);
        }
    }

    const nodeElements = nodes.map((node): ElementDefinition => {
        const data = node.data;
        let label = baseLabel(data);
        if (data.node_type === "transaction" && (seen.get(data.display_key) ?? 0) > 1 && data.store_number) {
            label += ` · S${data.store_number}`; // a placeholder with no known store leaves it out
        }
        if (data.status === "incomplete") {
            label += " (incomplete)";
        }
        return { group: "nodes", data: { ...data, label }, classes: node.classes };
    });

    const edgeElements = edges.map(
        (edge): ElementDefinition => ({
            group: "edges",
            data: { ...edge.data, label: EDGE_LABELS[edge.data.kind] },
            classes: edge.classes,
        }),
    );

    return [...nodeElements, ...edgeElements];
}
