import { palette } from "../styles/palette";
import type { DocumentType } from "../types/document";
import type { InvestigationSettings } from "../types/settings";

// Turns investigation settings into Cytoscape style values (B12: the frontend builds the
// stylesheet from the settings). The future buildStylesheet in cytoscapeConfig.ts reads these
// (UI-29), so the graph and the settings page always agree.

export function nodeStyleFor(type: DocumentType, settings: InvestigationSettings) {
    const { color, shape } = settings.node_styles[type];
    return {
        "background-color": palette[color],
        shape,
        "border-width": 2,
        "border-color": palette.ink, // every node keeps its 2px ink border (D27)
    };
}

export function importantEdgeColor(settings: InvestigationSettings): string {
    return palette[settings.important_edge_color];
}
