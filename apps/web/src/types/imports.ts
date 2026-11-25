import type { Investigation } from "./investigation";

// The CSV import report (csv-save-load.md "ImportReport").
export interface ImportProblem {
    severity: "error" | "warning"; // error: the row was skipped; warning: it was imported
    section: string;
    row: number | null;
    field: string | null;
    code: string;
    message: string;
}

export interface ImportReport {
    format_version: number;
    counts: { rows_read: number; documents_imported: number; rows_skipped: number };
    problems: ImportProblem[];
}

export interface ImportResult {
    investigation: Investigation;
    report: ImportReport;
}
