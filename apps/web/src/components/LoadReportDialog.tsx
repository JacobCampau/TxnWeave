import { useEffect, useId, useRef } from "react";
import type { ImportReport } from "../types/imports";

interface LoadReportDialogProps {
    report: ImportReport | null; // null: closed
    onLoad: () => void; // "Load documents": import the valid rows
    onCancel: () => void;
}

const SECTION_LABELS: Record<string, string> = {
    transactions: "Transactions",
    gift_cards: "Gift cards",
    online_orders: "Online orders",
    misc: "Misc",
    payments: "Payments",
    gift_card_history: "Gift card history",
    settings: "Settings",
};

// UI-17: a file with the marker whose dry run found problems. Errors are rows that will be
// skipped; warnings are rows that load with a default.
export default function LoadReportDialog({ report, onLoad, onCancel }: LoadReportDialogProps) {
    const dialogRef = useRef<HTMLDialogElement>(null);
    const cancelRef = useRef<HTMLButtonElement>(null);
    const titleId = useId();

    useEffect(() => {
        const dialog = dialogRef.current;
        if (!dialog) return;
        if (report && !dialog.open) {
            dialog.showModal();
            cancelRef.current?.focus();
        } else if (!report && dialog.open) {
            dialog.close();
        }
    }, [report]);

    const counts = report?.counts;

    return (
        <dialog
            ref={dialogRef}
            className="confirm-dialog load-report"
            aria-labelledby={titleId}
            onCancel={(event) => {
                event.preventDefault(); // Esc is Cancel
                onCancel();
            }}
        >
            <h2 id={titleId}>Some rows have problems</h2>
            {counts && (
                <p>
                    {counts.documents_imported} documents can be loaded. {counts.rows_skipped} of {counts.rows_read} rows
                    will be skipped.
                </p>
            )}
            <ul className="load-report__problems">
                {report?.problems.map((problem, index) => (
                    <li key={index}>
                        <strong>{problem.severity === "error" ? "Skipped" : "Warning"}:</strong>{" "}
                        {SECTION_LABELS[problem.section] ?? problem.section}
                        {problem.row !== null && `, row ${problem.row}`}
                        {problem.field && ` (${problem.field})`}: {problem.message}
                    </li>
                ))}
            </ul>
            <div className="confirm-dialog__actions">
                <button type="button" className="button button--primary" onClick={onLoad}>
                    Load documents
                </button>
                <button ref={cancelRef} type="button" className="button button--secondary" onClick={onCancel}>
                    Cancel
                </button>
            </div>
        </dialog>
    );
}
