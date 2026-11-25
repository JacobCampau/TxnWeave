import type { ListedDocument, NewDocument, TxnDocument } from "../types/document";
import { request } from "./client";

const base = (investigationId: number) => `/investigations/${investigationId}/documents`;

// Saved documents and incomplete nodes together, each with its referenced_by.
export function listDocuments(investigationId: number): Promise<ListedDocument[]> {
    return request(base(investigationId));
}

export function createDocument(investigationId: number, doc: NewDocument): Promise<TxnDocument> {
    return request(base(investigationId), { method: "POST", body: JSON.stringify(doc) });
}

// PUT replaces the whole document (api.md 2.3).
export function updateDocument(investigationId: number, id: string, doc: NewDocument): Promise<TxnDocument> {
    return request(`${base(investigationId)}/${id}`, { method: "PUT", body: JSON.stringify(doc) });
}

export function deleteDocument(investigationId: number, id: string): Promise<void> {
    return request(`${base(investigationId)}/${id}`, { method: "DELETE" });
}
