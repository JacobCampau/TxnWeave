import type { FormEvent, ReactNode } from "react";
import type { Errors } from "../../documents/fieldRules";

interface FormShellProps {
    errors: Errors;
    formError: string | null; // an error from the server, such as a duplicate key
    saveDisabled: boolean; // no unsaved changes (UI-34), or a save is in progress
    onSave: () => void;
    onCancel: () => void;
    onDelete?: () => void; // only when editing a saved document
    children: ReactNode;
}

// The frame around every document form: the error summary at the top (UI-13),
// the fields, and the Save / Cancel / Delete buttons.
export default function FormShell({
    errors,
    formError,
    saveDisabled,
    onSave,
    onCancel,
    onDelete,
    children,
}: FormShellProps) {
    const errorCount = Object.keys(errors).length;

    function handleSubmit(event: FormEvent) {
        event.preventDefault(); // stay on the page; the form is handled in React
        if (!saveDisabled) {
            onSave();
        }
    }

    return (
        // noValidate: our own checks run instead of the browser's built-in popups.
        <form className="document-form" onSubmit={handleSubmit} noValidate>
            {errorCount > 0 && (
                <div className="form-error-summary" role="alert">
                    Error: {errorCount === 1 ? "1 field needs" : `${errorCount} fields need`} fixing
                    before this document can be saved.
                </div>
            )}
            {formError && (
                <div className="form-error-summary" role="alert">
                    {formError}
                </div>
            )}

            {children}

            <div className="document-form__actions">
                {/* aria-disabled instead of disabled keeps the button focusable, and
                    color-system's disabled style never uses transparency. */}
                <button
                    type="submit"
                    className={saveDisabled ? "button button--disabled" : "button button--primary"}
                    aria-disabled={saveDisabled}
                >
                    Save
                </button>
                <button type="button" className="button button--secondary" onClick={onCancel}>
                    Cancel
                </button>
                {onDelete && (
                    <button
                        type="button"
                        className="button button--destructive document-form__delete"
                        onClick={onDelete}
                    >
                        Delete
                    </button>
                )}
            </div>
        </form>
    );
}
