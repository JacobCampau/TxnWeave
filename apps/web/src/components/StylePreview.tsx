import { palette } from "../styles/palette";
import type { EdgeColorToken, NodeColorToken, NodeShape } from "../types/settings";

const SIZE = 32;
const BORDER = 2; // every node keeps its 2px ink border (D27)

// Points for each polygon shape, in a 0..1 box. Ellipse and the rectangles are drawn separately.
const POLYGONS: Partial<Record<NodeShape, [number, number][]>> = {
    triangle: [[0.5, 0], [1, 1], [0, 1]],
    diamond: [[0.5, 0], [1, 0.5], [0.5, 1], [0, 0.5]],
    hexagon: [[0.25, 0], [0.75, 0], [1, 0.5], [0.75, 1], [0.25, 1], [0, 0.5]],
    octagon: [[0.3, 0], [0.7, 0], [1, 0.3], [1, 0.7], [0.7, 1], [0.3, 1], [0, 0.7], [0, 0.3]],
    star: starPoints(),
};

function starPoints(): [number, number][] {
    const points: [number, number][] = [];
    for (let i = 0; i < 10; i++) {
        const radius = i % 2 === 0 ? 0.5 : 0.2;
        const angle = -Math.PI / 2 + (i * Math.PI) / 5;
        points.push([0.5 + radius * Math.cos(angle), 0.5 + radius * Math.sin(angle)]);
    }
    return points;
}

interface NodePreviewProps {
    color: NodeColorToken;
    shape: NodeShape;
}

// One shape-and-color chip, as the node will look on the graph (settings-page "Layout").
export function NodePreview({ color, shape }: NodePreviewProps) {
    const inner = SIZE - BORDER * 2; // keep the border inside the box
    const common = { fill: palette[color], stroke: palette.ink, strokeWidth: BORDER };
    const polygon = POLYGONS[shape];

    let body;
    if (shape === "ellipse") {
        body = <ellipse cx={SIZE / 2} cy={SIZE / 2} rx={inner / 2} ry={inner / 2} {...common} />;
    } else if (polygon) {
        const points = polygon.map(([x, y]) => `${BORDER + x * inner},${BORDER + y * inner}`).join(" ");
        body = <polygon points={points} {...common} />;
    } else {
        const radius = shape === "round-rectangle" ? 6 : 0;
        body = <rect x={BORDER} y={BORDER} width={inner} height={inner} rx={radius} {...common} />;
    }

    return (
        <svg className="style-preview" width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`} aria-hidden="true">
            {body}
        </svg>
    );
}

// The important-connection edge: a 4px line.
export function EdgePreview({ color }: { color: EdgeColorToken }) {
    return (
        <svg className="style-preview" width={SIZE * 2} height={SIZE} viewBox={`0 0 ${SIZE * 2} ${SIZE}`} aria-hidden="true">
            <line x1={2} y1={SIZE / 2} x2={SIZE * 2 - 2} y2={SIZE / 2} stroke={palette[color]} strokeWidth={4} />
        </svg>
    );
}

// A small square of one palette color, shown next to the color dropdown.
export function Swatch({ color }: { color: NodeColorToken }) {
    return (
        <svg className="style-preview" width={16} height={16} viewBox="0 0 16 16" aria-hidden="true">
            <rect x={1} y={1} width={14} height={14} fill={palette[color]} stroke={palette.ink} strokeWidth={1} />
        </svg>
    );
}
