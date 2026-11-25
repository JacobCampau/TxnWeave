import type { CoseLayoutOptions, Core, StylesheetJson } from "cytoscape";
import { palette, textOnLight } from "../styles/palette";
import { DOCUMENT_TYPES, type DocumentType } from "../types/document";
import type { InvestigationSettings } from "../types/settings";
import { importantEdgeColor, nodeStyleFor } from "./nodeStyles";

// The graph stylesheet (investigation-page.md "Graph styles"). Each type's color and shape come
// from the investigation settings (D27, UI-29). Borders, labels, and the incomplete and
// selection styles never change.

// The backend's node class for each type (graph-output.md "Classes").
const TYPE_CLASS: Record<DocumentType, string> = {
    transaction: "transaction",
    gift_card: "gift-card",
    online_order: "online-order",
    misc: "misc",
};

const NODE_SIZE = 40;

export function buildStylesheet(settings: InvestigationSettings): StylesheetJson {
    return [
        {
            selector: "node",
            style: {
                width: NODE_SIZE,
                height: NODE_SIZE,
                label: "data(label)",
                "text-valign": "bottom",
                "text-margin-y": 6,
                "font-size": 12,
                color: textOnLight,
            },
        },
        // One block per type: fill, shape and the 2px ink border (D9, D27).
        ...DOCUMENT_TYPES.map((type) => ({
            selector: `node.${TYPE_CLASS[type]}`,
            style: nodeStyleFor(type, settings),
        })),
        // Gift Cards are card-like: 1.6:1 (D9).
        { selector: "node.gift-card", style: { width: NODE_SIZE * 1.2, height: (NODE_SIZE * 1.2) / 1.6 } },
        {
            selector: "node.incomplete",
            style: { opacity: 0.75, "border-width": 3, "border-style": "dashed" },
        },
        {
            selector: "node.important", // D31
            style: { "border-width": 6, "border-style": "double", "border-color": palette.ink },
        },
        {
            // A crimson ring 6px outside the ink border.
            selector: "node:selected",
            style: { "underlay-color": palette.crimson, "underlay-opacity": 1, "underlay-padding": 6 },
        },
        {
            selector: "edge",
            style: {
                width: 2,
                "line-color": palette.slate,
                "target-arrow-color": palette.slate,
                "target-arrow-shape": "triangle",
                "curve-style": "bezier",
                label: "data(label)",
                "font-size": 10,
                color: textOnLight,
                "text-background-color": palette.mist,
                "text-background-opacity": 1,
            },
        },
        // The toolbar's "Edge labels" toggle adds this class to every edge (D11, UI-7).
        { selector: "edge.no-label", style: { label: "" } },
        // Incomplete includes ambiguous edges (BD15).
        { selector: "edge.incomplete", style: { "line-style": "dashed" } },
        {
            selector: "edge.important", // D31: stays dashed if it is also incomplete
            style: {
                width: 4,
                "line-color": importantEdgeColor(settings),
                "target-arrow-color": importantEdgeColor(settings),
            },
        },
        {
            selector: "edge:selected",
            style: { width: 3, "line-color": palette.crimson, "target-arrow-color": palette.crimson },
        },
    ];
}

// ---- The automatic layout (D8) ----

// cose's defaults are tuned for tiny unlabeled nodes and clump ours together, so edges are
// longer and nodes push each other apart harder.
const coseOptions: CoseLayoutOptions = {
    name: "cose",
    animate: false,
    fit: false, // runLayout fits the view itself, so it can limit the zoom
    randomize: false, // start from the seeded positions below
    nodeDimensionsIncludeLabels: true,
    idealEdgeLength: () => 100,
    nodeRepulsion: () => 400000,
    nodeOverlap: 20,
    gravity: 0.25,
    componentSpacing: 100,
};

const FIT_PADDING = 40;
// A small graph is shown at normal size instead of being blown up to fill the canvas.
const MAX_FIT_ZOOM = 1;

// Gives every node a fixed starting spot on a circle, in the order the backend sent them
// (3.12). cose moves nodes that sit exactly on top of each other apart in a random direction;
// without this they would all start at (0, 0) and the layout would differ on every load.
function seedPositions(cy: Core) {
    const nodes = cy.nodes();
    const radius = 40 * nodes.length;
    nodes.forEach((node, i) => {
        const angle = (2 * Math.PI * i) / nodes.length;
        node.position({ x: radius * Math.cos(angle), y: radius * Math.sin(angle) });
    });
}

// Lays the graph out and fits it in view. The same graph always gets the same layout.
export function runLayout(cy: Core) {
    seedPositions(cy);
    const layout = cy.layout(coseOptions);
    layout.one("layoutstop", () => fitView(cy));
    layout.run();
}

// Fits every node in view, but never zooms a small graph past 100% (toolbar "Fit", UI-7).
export function fitView(cy: Core) {
    cy.fit(undefined, FIT_PADDING);
    if (cy.zoom() > MAX_FIT_ZOOM) {
        cy.zoom(MAX_FIT_ZOOM);
        cy.center();
    }
}

// Zoom in or out by one step, around the middle of the canvas (UI-7).
export function zoomBy(cy: Core, factor: number) {
    cy.zoom({ level: cy.zoom() * factor, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } });
}
