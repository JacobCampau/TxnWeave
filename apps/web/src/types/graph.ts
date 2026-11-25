import type { DocumentType } from "./document";

// The graph payload from GET .../graph (graph-output.md "GraphOut"). It is already in
// Cytoscape's element format, with classes set by the backend (B12).
export type EdgeKind = "activated" | "used_in" | "related";
export type GraphStatus = "complete" | "incomplete";

export interface NodeData {
    id: string;
    document_id: string;
    node_type: DocumentType;
    status: GraphStatus;
    display_key: string; // number, "…1234" for a card (never the full number, B13), or the Misc name
    date: string | null;
    time: string | null;
    store_number: string | null;
    register_number: string | null;
    important: boolean;
}

export interface EdgeData {
    id: string;
    source: string;
    target: string;
    kind: EdgeKind;
    status: GraphStatus;
    match: "exact" | "ambiguous";
    refs: string[];
    ref_count: number;
    important: boolean;
}

export interface GraphOut {
    investigation_id: number;
    generated_at: string;
    counts: { nodes: number; edges: number; incomplete_nodes: number };
    elements: {
        nodes: { data: NodeData; classes: string }[];
        edges: { data: EdgeData; classes: string }[];
    };
}
