import { useEffect, useId, useRef } from "react";

interface ConfirmDialogProps {
    open: boolean;
    title: string;
    message: string;
    items?: string[]; // an optional list shown under the message
    confirmLabel: string; // names the action, e.g. "Discard" or "Delete" (color-system)
    onConfirm: () => void;
    onCancel: () => void;
    // An optional safe alternative shown first as the primary button, e.g. UI-2's "Save first".
    extraAction?: { label: string; onClick: () => void };
}

// A modal yes/no question (app-shell's ConfirmDialog). Uses the browser's <dialog> element:
// showModal() blocks the rest of the page, keeps keyboard focus inside the dialog, and
// Esc fires the "cancel" event, which we treat as Cancel.
export default function ConfirmDialog({
    open,
    title,
    message,
    items,
    confirmLabel,
    onConfirm,
    onCancel,
    extraAction,
}: ConfirmDialogProps) {
    const dialogRef = useRef<HTMLDialogElement>(null);
    const cancelRef = useRef<HTMLButtonElement>(null);
    const titleId = useId();

    useEffect(() => {
        const dialog = dialogRef.current;
        if (!dialog) return;
        if (open && !dialog.open) {
            dialog.showModal();
            cancelRef.current?.focus(); // start on the safe choice
        } else if (!open && dialog.open) {
            dialog.close();
        }
    }, [open]);

    return (
        <dialog
            ref={dialogRef}
            className="confirm-dialog"
            aria-labelledby={titleId}
            onCancel={(event) => {
                event.preventDefault(); // let React state decide when it closes
                onCancel();
            }}
        >
            <h2 id={titleId}>{title}</h2>
            <p>{message}</p>
            {items && items.length > 0 && (
                <ul>
                    {items.map((item, index) => (
                        <li key={index}>{item}</li>
                    ))}
                </ul>
            )}
            <div className="confirm-dialog__actions">
                {extraAction && (
                    <button type="button" className="button button--primary" onClick={extraAction.onClick}>
                        {extraAction.label}
                    </button>
                )}
                <button type="button" className="button button--destructive" onClick={onConfirm}>
                    {confirmLabel}
                </button>
                <button ref={cancelRef} type="button" className="button button--secondary" onClick={onCancel}>
                    Cancel
                </button>
            </div>
        </dialog>
    );
}
