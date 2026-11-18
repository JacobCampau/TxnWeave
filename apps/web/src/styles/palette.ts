// The five palette colors (D19). Cytoscape styles read them from here.
// global.css mirrors them as CSS custom properties. No other file may hold a hex color.
export const palette = {
    ink: "#131313",
    slate: "#394249",
    mist: "#D2CDCB",
    rose: "#D26D6F",
    crimson: "#C11E20",
} as const;

export const textOnDark = "#FFFFFF";
export const textOnLight = "#000000";
