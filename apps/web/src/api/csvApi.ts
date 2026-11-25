import type { ImportReport, ImportResult } from "../types/imports";
import { request, requestResponse } from "./client";

// CSV Save and Load (csv-save-load.md). The file stays on the agent's computer (D3).

// Save: downloads `<investigation-name>.csv` and returns the file name. The backend sets
// last_exported_at, which clears "unsaved changes" (B16).
export async function downloadExport(investigationId: number): Promise<string> {
    const response = await requestResponse(`/investigations/${investigationId}/export.csv`);
    const disposition = response.headers.get("Content-Disposition") ?? "";
    const filename = /filename="([^"]+)"/.exec(disposition)?.[1] ?? "untitled-investigation.csv";

    const url = URL.createObjectURL(await response.blob());
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click(); // the browser asks where to save it, or saves to Downloads
    URL.revokeObjectURL(url);
    return filename;
}

function upload(file: File) {
    const body = new FormData();
    body.append("file", file);
    return { method: "POST", body };
}

// Step 1 of a load (B17): checks the file and writes nothing.
export function checkImport(file: File): Promise<ImportReport> {
    return request(`/investigations/import?dry_run=true`, upload(file));
}

// Step 2: always creates a new investigation (BD13).
export function runImport(file: File): Promise<ImportResult> {
    return request(`/investigations/import?dry_run=false`, upload(file));
}
