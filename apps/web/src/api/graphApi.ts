import type { GraphOut } from "../types/graph";
import { request } from "./client";

// The investigation's graph, worked out by the backend on every call (G1).
export function getGraph(investigationId: number): Promise<GraphOut> {
    return request(`/investigations/${investigationId}/graph`);
}
