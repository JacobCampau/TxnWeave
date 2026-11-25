import type { Core } from "cytoscape";
import { fitView, runLayout, zoomBy } from "../graph/cytoscapeConfig";

interface GraphToolbarProps {
    cy: Core | null;
    hasNodes: boolean;
    showEdgeLabels: boolean;
    onToggleEdgeLabels: (show: boolean) => void;
}

const ZOOM_STEP = 1.25;

// The Investigation toolbar (UI-7): slate with white text (color-system). Export PNG and the
// Legend checkbox are Wave 2 (UI build-plan step 10).
export default function GraphToolbar({ cy, hasNodes, showEdgeLabels, onToggleEdgeLabels }: GraphToolbarProps) {
    const disabled = !cy || !hasNodes;

    function run(action: (cy: Core) => void) {
        if (cy && hasNodes) action(cy);
    }

    // aria-disabled instead of disabled keeps the buttons focusable (as in FormShell).
    const buttonClass = disabled ? "button button--disabled" : "button button--secondary-on-dark";

    return (
        <div className="graph-toolbar" role="toolbar" aria-label="Graph tools">
            <button type="button" className={buttonClass} aria-disabled={disabled} onClick={() => run(fitView)}>
                Fit to screen
            </button>
            <button
                type="button"
                className={buttonClass}
                aria-disabled={disabled}
                aria-label="Zoom in"
                onClick={() => run((c) => zoomBy(c, ZOOM_STEP))}
            >
                +
            </button>
            <button
                type="button"
                className={buttonClass}
                aria-disabled={disabled}
                aria-label="Zoom out"
                onClick={() => run((c) => zoomBy(c, 1 / ZOOM_STEP))}
            >
                −
            </button>
            <button type="button" className={buttonClass} aria-disabled={disabled} onClick={() => run(runLayout)}>
                Re-layout
            </button>
            <label className="graph-toolbar__toggle">
                <input type="checkbox" checked={showEdgeLabels} onChange={(event) => onToggleEdgeLabels(event.target.checked)} />
                Edge labels
            </label>
        </div>
    );
}
