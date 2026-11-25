import { useEffect, useState } from "react";
import type { Errors } from "../../documents/fieldRules";
import type { NewDocument } from "../../types/document";

// What each form's validate function returns: the errors found, and the finished
// document when there are none.
export interface ValidationResult {
    errors: Errors;
    doc: NewDocument | null;
}

// Saves the document on the server. Resolves to an error message to show (for example a
// duplicate key), or null when the save worked.
export type SaveHandler = (doc: NewDocument) => Promise<string | null>;

// Props shared by the four document forms. At most one of `initial` (a saved document to
// edit) and `prefill` (an incomplete node to fill in) is given; neither means a new, empty
// form. `onDelete` is only passed when editing a saved document.
export interface DocumentFormProps<Doc, Prefill = never> {
    initial?: Doc;
    prefill?: Prefill;
    onSave: SaveHandler;
    onCancel: () => void;
    onDelete?: () => void;
    onDirtyChange: (dirty: boolean) => void;
}

interface UseDocumentFormOptions<Draft> {
    initialDraft: () => Draft;
    validate: (draft: Draft) => ValidationResult;
    onSave: SaveHandler;
    onDirtyChange: (dirty: boolean) => void;
    // An incomplete node: its missing required fields show as errors straight away (UI-12), and
    // Save is always enabled, because saving it is what promotes it (UI-34).
    isPlaceholder: boolean;
}

// Shared state for the four document forms. A form keeps its fields as typed text
// (the "draft") and only converts them to a document when Save passes validation (UI-13).
// Returns `shell`, the props for FormShell.
export function useDocumentForm<Draft>({
    initialDraft,
    validate,
    onSave,
    onDirtyChange,
    isPlaceholder,
}: UseDocumentFormOptions<Draft>) {
    const [draft, setDraft] = useState<Draft>(initialDraft);
    // The draft as it was last saved (or as the form opened). Comparing against it tells us
    // whether there are unsaved changes (UI-14, UI-34).
    const [baseline, setBaseline] = useState<Draft>(draft);
    const [errors, setErrors] = useState<Errors>(() => (isPlaceholder ? validate(draft).errors : {}));
    // An error from the server, such as a duplicate key (B14).
    const [formError, setFormError] = useState<string | null>(null);
    const [saving, setSaving] = useState(false);

    const isDirty = JSON.stringify(draft) !== JSON.stringify(baseline);

    // Tell the page whenever the form becomes dirty or clean...
    useEffect(() => {
        onDirtyChange(isDirty);
    }, [isDirty, onDirtyChange]);

    // ...and that there's nothing unsaved once the form closes.
    useEffect(() => {
        return () => onDirtyChange(false);
    }, [onDirtyChange]);

    function setField<K extends keyof Draft>(field: K, value: Draft[K]) {
        setDraft((prev) => ({ ...prev, [field]: value }));
    }

    async function save() {
        const result = validate(draft);
        if (!result.doc) {
            setErrors(result.errors);
            setFormError(null);
            // Move focus to the first invalid field (UI-13). Errors are keyed by element id,
            // in field order.
            const firstId = Object.keys(result.errors)[0];
            if (firstId) {
                document.getElementById(firstId)?.focus();
            }
            return;
        }

        setErrors({});
        setSaving(true);
        const error = await onSave(result.doc);
        setSaving(false);
        if (error) {
            setFormError(error);
        } else {
            setFormError(null);
            setBaseline(draft); // saved, so the form is clean again
        }
    }

    const shell = {
        errors,
        formError,
        saveDisabled: saving || (!isDirty && !isPlaceholder),
        onSave: () => void save(),
    };

    return { draft, setField, errors, shell };
}
