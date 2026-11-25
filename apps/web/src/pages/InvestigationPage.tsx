import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { Core } from "cytoscape";
import ApiErrorBanner from "../components/ApiErrorBanner";
import GraphCanvas from "../components/GraphCanvas";
import GraphToolbar from "../components/GraphToolbar";
import PropertyPanel, { type ConnectedNode } from "../components/PropertyPanel";
import { errorMessage } from "../api/client";
import { getGraph } from "../api/graphApi";
import { getSettings } from "../api/settingsApi";
import { toElements } from "../graph/graphMapper";
import type { ListedDocument } from "../types/document";
import type { GraphOut } from "../types/graph";
import type { InvestigationSettings } from "../types/settings";

interface InvestigationPageProps {
    investigationId: number;
    documents: ListedDocument[]; // the same list the Documents page shows; the panel reads it
}

interface Loaded {
    graph: GraphOut;
    settings: InvestigationSettings;
}

// Investigation page (route "/"): the auto-generated graph. The page is mounted again every time
// the user navigates to it, so it always shows the graph after the latest document save (UI-8).
export default function InvestigationPage({ investigationId, documents }: InvestigationPageProps) {
    const navigate = useNavigate();
    const [loaded, setLoaded] = useState<Loaded | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [attempt, setAttempt] = useState(0); // bumped by Retry
    const [cy, setCy] = useState<Core | null>(null);
    const [showEdgeLabels, setShowEdgeLabels] = useState(true); // on by default (UI-7)
    const [selectedId, setSelectedId] = useState<string | null>(null);

    // The graph and the settings load together (UI-29).
    useEffect(() => {
        let current = true;
        setLoaded(null);
        setError(null);
        Promise.all([getGraph(investigationId), getSettings(investigationId)])
            .then(([graph, settings]) => current && setLoaded({ graph, settings }))
            .catch((reason) => current && setError(errorMessage(reason)));
        return () => {
            current = false; // ignore an answer that arrives after the page closed
        };
    }, [investigationId, attempt]);

    const elements = useMemo(() => (loaded ? toElements(loaded.graph) : []), [loaded]);

    const selectedDoc = documents.find((doc) => doc.id === selectedId);

    // The nodes joined to the selected one by an edge, in either direction (UI-6).
    const connected = useMemo((): ConnectedNode[] => {
        if (!loaded || !selectedId) return [];
        const ids = new Set<string>();
        for (const edge of loaded.graph.elements.edges) {
            if (edge.data.source === selectedId) ids.add(edge.data.target);
            if (edge.data.target === selectedId) ids.add(edge.data.source);
        }
        return documents.filter((doc) => ids.has(doc.id)).map((doc) => ({ id: doc.id, title: doc.title }));
    }, [loaded, selectedId, documents]);

    const closePanel = useCallback(() => setSelectedId(null), []);

    return (
        <div className="investigation-page">
            {error && <ApiErrorBanner message={error} onRetry={() => setAttempt((n) => n + 1)} />}
            <GraphToolbar
                cy={cy}
                hasNodes={elements.length > 0}
                showEdgeLabels={showEdgeLabels}
                onToggleEdgeLabels={setShowEdgeLabels}
            />
            <div className="investigation-page__body">
                <section className="investigation-canvas" aria-label="Graph">
                    {loaded ? (
                        <GraphCanvas
                            elements={elements}
                            settings={loaded.settings}
                            showEdgeLabels={showEdgeLabels}
                            selectedId={selectedId}
                            onSelect={setSelectedId}
                            onReady={setCy}
                        />
                    ) : (
                        !error && <span className="spinner" aria-label="Loading graph" /> // UI-5
                    )}
                </section>
                {selectedDoc && (
                    <PropertyPanel
                        doc={selectedDoc}
                        connected={connected}
                        onSelect={setSelectedId}
                        onEdit={(id) => navigate(`/documents?doc=${encodeURIComponent(id)}`)}
                        onClose={closePanel}
                    />
                )}
            </div>
        </div>
    );
}
