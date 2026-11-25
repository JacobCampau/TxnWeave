import { useRef, useState } from "react";
import { ApiError, errorMessage } from "../api/client";
import { checkImport, runImport } from "../api/csvApi";
import type { ImportReport } from "../types/imports";
import type { Investigation } from "../types/investigation";
import LoadReportDialog from "./LoadReportDialog";

// The UI-31 messages for files that can't be loaded at all (D35).
function loadErrorMessage(error: unknown): string {
    if (error instanceof ApiError) {
        if (error.code === "not_a_txnweave_file") return "This file is not a TxnWeave save file.";
        if (error.status === 413) return "This file is larger than 5 MB.";
        if (error.status === 422) return "This file could not be read.";
    }
    return errorMessage(error);
}

interface CsvLoadOptions {
    onLoaded: (investigation: Investigation) => void; // step 5 finished
    onError: (message: string) => void; // shown inline or as a toast, by the caller (D35)
}

// The Load CSV flow (UI-31), shared by StartDialog and the TopBar's Load button. `open()` starts
// it; `elements` (the hidden file input and LoadReportDialog) must be rendered somewhere.
export function useCsvLoad({ onLoaded, onError }: CsvLoadOptions) {
    const inputRef = useRef<HTMLInputElement>(null);
    const [busy, setBusy] = useState(false);
    // A checked file whose report has problems, waiting on "Load documents" or "Cancel" (UI-17).
    const [pending, setPending] = useState<{ file: File; report: ImportReport } | null>(null);

    // 1. The file picker. Closing it without a file fires no change event, so nothing happens.
    function open() {
        const input = inputRef.current;
        if (!input) return;
        input.value = ""; // so choosing the same file again still counts as a change
        input.click();
    }

    async function load(file: File) {
        try {
            const result = await runImport(file); // 5. the real import: a new investigation
            onLoaded(result.investigation);
        } catch (error) {
            onError(loadErrorMessage(error));
        }
    }

    async function onFile(file: File | undefined) {
        if (!file) return;
        // 2. Filetype, in the browser, before any upload.
        if (!file.name.toLowerCase().endsWith(".csv")) {
            onError("Choose a TxnWeave .csv file.");
            return;
        }
        setBusy(true);
        try {
            const report = await checkImport(file); // 3. the dry run: marker, size, encoding
            if (report.problems.length > 0) {
                setPending({ file, report }); // 4. LoadReportDialog
            } else {
                await load(file);
            }
        } catch (error) {
            onError(loadErrorMessage(error));
        } finally {
            setBusy(false);
        }
    }

    async function confirmLoad() {
        if (!pending) return;
        const { file } = pending;
        setPending(null);
        setBusy(true);
        await load(file);
        setBusy(false);
    }

    const elements = (
        <>
            <input
                ref={inputRef}
                type="file"
                accept=".csv"
                hidden
                onChange={(event) => void onFile(event.target.files?.[0])}
            />
            <LoadReportDialog
                report={pending?.report ?? null}
                onLoad={() => void confirmLoad()}
                onCancel={() => setPending(null)} // back to where the load started (UI-17)
            />
        </>
    );

    return { open, busy, elements };
}
