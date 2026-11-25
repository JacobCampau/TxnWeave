import type { Investigation } from "../types/investigation";
import { request } from "./client";

// Newest first: the first one is "Resume last session" (api.md 1.2).
export function listInvestigations(): Promise<Investigation[]> {
    return request("/investigations");
}

// "New investigation". A blank name is stored as null ("Untitled investigation").
export function createInvestigation(name: string | null = null): Promise<Investigation> {
    return request("/investigations", { method: "POST", body: JSON.stringify({ name }) });
}

// Rename (D30, BD32): trimmed by the backend; blank becomes null.
export function renameInvestigation(id: number, name: string | null): Promise<Investigation> {
    return request(`/investigations/${id}`, { method: "PATCH", body: JSON.stringify({ name }) });
}

export function getInvestigation(id: number): Promise<Investigation> {
    return request(`/investigations/${id}`);
}

// Cascades to the investigation's documents and settings (api.md 1.3, 1.6).
export function deleteInvestigation(id: number): Promise<void> {
    return request(`/investigations/${id}`, { method: "DELETE" });
}
