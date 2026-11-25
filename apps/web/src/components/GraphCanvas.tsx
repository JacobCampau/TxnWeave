import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import cytoscape, { type Core, type ElementDefinition } from "cytoscape";
import { buildStylesheet, runLayout } from "../graph/cytoscapeConfig";
import type { InvestigationSettings } from "../types/settings";

interface GraphCanvasProps {
    elements: ElementDefinition[];
    settings: InvestigationSettings;
    showEdgeLabels: boolean;
    selectedId: string | null; // the node the PropertyPanel shows
    onSelect: (nodeId: string | null) => void; // a node was clicked, or empty canvas (null)
    onReady: (cy: Core | null) => void; // hands the instance to the toolbar
}

// The read-only Cytoscape graph on the mist canvas (D7). Users can pan, zoom and drag nodes,
// but never add, link or delete them.
export default function GraphCanvas({ elements, settings, showEdgeLabels, selectedId, onSelect, onReady }: GraphCanvasProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const cyRef = useRef<Core | null>(null);
    const navigate = useNavigate();
    // The latest callbacks, so the Cytoscape event handlers set up once always call them.
    const onSelectRef = useRef(onSelect);
    onSelectRef.current = onSelect;
    const onReadyRef = useRef(onReady);
    onReadyRef.current = onReady;

    // Create the Cytoscape instance once, and destroy it when the page closes.
    useEffect(() => {
        const cy = cytoscape({
            container: containerRef.current,
            boxSelectionEnabled: false,
            selectionType: "single",
            minZoom: 0.2,
            maxZoom: 4,
        });
        cy.on("tap", "node", (event) => onSelectRef.current(event.target.id())); // UI-6
        cy.on("tap", (event) => {
            if (event.target === cy) onSelectRef.current(null); // empty canvas closes the panel
        });
        cyRef.current = cy;
        onReadyRef.current(cy);
        return () => {
            onReadyRef.current(null);
            cy.destroy();
            cyRef.current = null;
        };
    }, []);

    // Settings change only colors and shapes, so restyle without moving any node (UI-29).
    // Declared before the layout effect so the first layout measures styled nodes and labels.
    useEffect(() => {
        cyRef.current?.style(buildStylesheet(settings));
    }, [settings]);

    // New data from the backend: replace every element and lay the graph out again (D8).
    useEffect(() => {
        const cy = cyRef.current;
        if (!cy) return;
        cy.batch(() => {
            cy.elements().remove();
            cy.add(elements);
        });
        runLayout(cy);
    }, [elements]);

    // Edge labels on or off (D11). Runs after new elements too, so new edges follow the toggle.
    useEffect(() => {
        cyRef.current?.edges().toggleClass("no-label", !showEdgeLabels);
    }, [showEdgeLabels, elements]);

    // Keep Cytoscape's selection in step with the page (a click in the panel's connected list).
    useEffect(() => {
        const cy = cyRef.current;
        if (!cy) return;
        cy.elements().unselect();
        if (selectedId) cy.getElementById(selectedId).select();
    }, [selectedId, elements]);

    return (
        <>
            <div ref={containerRef} className="graph-canvas" aria-label="Investigation graph" />
            {elements.length === 0 && (
                // UI-4: the empty state.
                <div className="graph-empty">
                    <p className="empty-state">add forms to begin graphing</p>
                    <button type="button" className="button button--secondary" onClick={() => navigate("/documents")}>
                        Go to Documents
                    </button>
                </div>
            )}
        </>
    );
}
