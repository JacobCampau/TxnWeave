import { useEffect, useId, useRef, useState } from "react";
import { errorMessage } from "../api/client";
import { listInvestigations } from "../api/investigationsApi";
import type { Investigation } from "../types/investigation";
import { localDate, localTime } from "./localTime";

interface StartDialogProps {
    // `previous` is the autosaved investigation that Resume would open, or null. New and Load
    // replace it (BD7), so App needs to know which one it is.
    onResume: (investigation: Investigation) => void;
    onNew: (name: string | null, previous: Investigation | null) => void;
    onLoad: (previous: Investigation | null) => void;
    error: string | null; // a failed New or Load, shown inline (D35)
    busy: boolean;
}

const NAME_LIMIT = 200;

// StartDialog (D34, UI-1): shown on every open and reload, and whenever there is no active
// investigation. It can't be dismissed without choosing an option.
export default function StartDialog({ onResume, onNew, onLoad, error, busy }: StartDialogProps) {
    const dialogRef = useRef<HTMLDialogElement>(null);
    const titleId = useId();
    const nameId = useId();
    // undefined: still asking the server. null: nothing to resume.
    const [previous, setPrevious] = useState<Investigation | null | undefined>(undefined);
    const [listError, setListError] = useState<string | null>(null);
    const [name, setName] = useState("");

    async function lookUp() {
        setListError(null);
        try {
            const investigations = await listInvestigations(); // newest first (api.md 1.2)
            setPrevious(investigations[0] ?? null);
        } catch (reason) {
            setListError(errorMessage(reason));
        }
    }

    useEffect(() => {
        const dialog = dialogRef.current;
        if (dialog && !dialog.open) dialog.showModal(); // StrictMode runs this twice in development
        void lookUp();
    }, []);

    const nameTooLong = name.length > NAME_LIMIT;
    const blocked = busy || previous === undefined;

    return (
        <dialog
            ref={dialogRef}
            className="confirm-dialog start-dialog"
            aria-labelledby={titleId}
            onCancel={(event) => event.preventDefault()} // Esc can't dismiss it (UI-1)
        >
            <h2 id={titleId}>TxnWeave</h2>

            {listError && (
                <p className="form-error-summary" role="alert">
                    {listError}{" "}
                    <button type="button" className="button button--secondary" onClick={() => void lookUp()}>
                        Retry
                    </button>
                </p>
            )}

            {previous && (
                // UI-30: the Resume row.
                <section className="start-dialog__option">
                    <h3>Resume last session</h3>
                    <p>
                        {previous.name ?? "Untitled investigation"}
                        <br />
                        Last saved {localDate(previous.updated_at)} at {localTime(previous.updated_at)}
                        <br />
                        {previous.document_count} documents, {previous.incomplete_count} incomplete nodes
                    </p>
                    <button type="button" className="button button--primary" disabled={blocked} onClick={() => onResume(previous)}>
                        Resume
                    </button>
                </section>
            )}

            <section className="start-dialog__option">
                <h3>New investigation</h3>
                <label htmlFor={nameId}>Name (optional)</label>
                <input
                    id={nameId}
                    className={nameTooLong ? "form-field__input form-field__input--error" : "form-field__input"}
                    placeholder="Untitled investigation"
                    value={name}
                    onChange={(event) => setName(event.target.value)}
                />
                {nameTooLong && <p className="form-field__error">Error: {NAME_LIMIT} characters at most</p>}
                <button
                    type="button"
                    className={previous ? "button button--secondary" : "button button--primary"}
                    disabled={blocked || nameTooLong}
                    onClick={() => onNew(name.trim() || null, previous ?? null)}
                >
                    New investigation
                </button>
            </section>

            <section className="start-dialog__option">
                <h3>Load CSV</h3>
                <p>Open an investigation saved with Save.</p>
                <button type="button" className="button button--secondary" disabled={blocked} onClick={() => onLoad(previous ?? null)}>
                    Load CSV
                </button>
                {error && (
                    <p className="form-field__error" role="alert">
                        Error: {error.replace(/^Error: /, "")}
                    </p>
                )}
            </section>
        </dialog>
    );
}
