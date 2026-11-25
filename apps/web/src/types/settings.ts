import type { DocumentType } from "./document";

// Investigation settings (data-model.md "Investigation settings", BD29). Colors are palette
// token names; palette.ts turns them into hex.
export type NodeColorToken = "ink" | "slate" | "mist" | "rose" | "crimson";
export type EdgeColorToken = "ink" | "slate" | "crimson";
export type NodeShape =
    | "ellipse"
    | "rectangle"
    | "round-rectangle"
    | "triangle"
    | "diamond"
    | "hexagon"
    | "octagon"
    | "star";

export interface TypeStyle {
    color: NodeColorToken;
    shape: NodeShape;
}

export interface InvestigationSettings {
    node_styles: Record<DocumentType, TypeStyle>;
    important_edge_color: EdgeColorToken;
}

export interface InvestigationSettingsOut extends InvestigationSettings {
    is_default: boolean;
}

// D9's styles (BD29). Must match DEFAULT_SETTINGS in the backend's schemas/settings.py.
export const DEFAULT_SETTINGS: InvestigationSettings = {
    node_styles: {
        transaction: { color: "slate", shape: "ellipse" },
        gift_card: { color: "crimson", shape: "round-rectangle" },
        online_order: { color: "ink", shape: "hexagon" },
        misc: { color: "rose", shape: "diamond" },
    },
    important_edge_color: "ink",
};

// The dropdown choices (D27), in display order.
export const NODE_COLOR_OPTIONS: { value: NodeColorToken; label: string }[] = [
    { value: "ink", label: "Ink" },
    { value: "slate", label: "Slate" },
    { value: "mist", label: "Mist" },
    { value: "rose", label: "Rose" },
    { value: "crimson", label: "Crimson" },
];

// Rose and mist fail 3:1 against the mist canvas, so they are left out for edges (D27).
export const EDGE_COLOR_OPTIONS: { value: EdgeColorToken; label: string }[] = [
    { value: "ink", label: "Ink" },
    { value: "slate", label: "Slate" },
    { value: "crimson", label: "Crimson" },
];

export const SHAPE_OPTIONS: { value: NodeShape; label: string }[] = [
    { value: "ellipse", label: "Circle" },
    { value: "rectangle", label: "Rectangle" },
    { value: "round-rectangle", label: "Rounded rectangle" },
    { value: "triangle", label: "Triangle" },
    { value: "diamond", label: "Diamond" },
    { value: "hexagon", label: "Hexagon" },
    { value: "octagon", label: "Octagon" },
    { value: "star", label: "Star" },
];
