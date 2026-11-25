import { useRef, useState } from "react";
import { NavLink } from "react-router-dom";
import type { Investigation } from "../types/investigation";
import { localTime } from "./localTime";

// The autosave is the server database (B2): "Saving…" while a write is in flight, "Not saved"
// after a write failed, otherwise "Saved HH:MM" from the last change (UI-3).
export type AutosaveState = "saving" | "failed" | "saved";

interface TopBarProps {
    investigation: Investigation | null;
    autosave: AutosaveState;
    busy: boolean; // a Save or Load is in progress
    onRename: (name: string | null) => Promise<boolean>; // false: it failed (App shows the toast)
    onSave: () => void;
    onLoad: () => void;
}

const NAME_LIMIT = 200;

// Top bar (D6): wordmark, tabs, investigation name with inline Rename (D30), autosave status,
// Load, Save, and the reserved user-menu slot.
export default function TopBar({ investigation, autosave, busy, onRename, onSave, onLoad }: TopBarProps) {
    const [editing, setEditing] = useState(false);
    const [draft, setDraft] = useState("");
    const [tooLong, setTooLong] = useState(false);
    const done = useRef(false); // Enter or Esc already finished this edit, so blur must not save

    const name = investigation?.name ?? "Untitled investigation";

    function startEditing() {
        setDraft(investigation?.name ?? "");
        setTooLong(false);
        done.current = false;
        setEditing(true);
    }

    async function commit() {
        if (done.current) return;
        if (draft.length > NAME_LIMIT) {
            setTooLong(true); // UI-25: shown, and nothing is saved
            return;
        }
        done.current = true;
        setEditing(false);
        if ((draft.trim() || null) !== (investigation?.name ?? null)) {
            await onRename(draft.trim() || null); // blank saves as null (BD32)
        }
    }

    function cancel() {
        done.current = true;
        setEditing(false);
    }

    let status = "Not saved";
    if (autosave === "saving") status = "Saving…";
    else if (autosave === "saved" && investigation) status = `Saved ${localTime(investigation.updated_at)}`;

    const actionsDisabled = !investigation || busy;

    return (
        <header className="top-bar">
            <span className="top-bar__wordmark">TxnWeave</span>

            <nav className="top-bar__tabs" aria-label="Pages">
                <NavLink to="/" end className="top-bar__tab">
                    Investigation
                </NavLink>
                <NavLink to="/documents" className="top-bar__tab">
                    Documents
                </NavLink>
                <NavLink to="/settings" className="top-bar__tab">
                    Settings
                </NavLink>
            </nav>

            <div className="top-bar__name">
                {editing ? (
                    <>
                        <input
                            className="top-bar__name-input"
                            aria-label="Investigation name"
                            autoFocus
                            value={draft}
                            onChange={(event) => {
                                setDraft(event.target.value);
                                setTooLong(event.target.value.length > NAME_LIMIT);
                            }}
                            onKeyDown={(event) => {
                                if (event.key === "Enter") void commit();
                                if (event.key === "Escape") cancel();
                            }}
                            onBlur={() => void commit()}
                        />
                        {tooLong && (
                            <span className="top-bar__name-error" role="alert">
                                Error: {NAME_LIMIT} characters at most
                            </span>
                        )}
                    </>
                ) : (
                    <button
                        type="button"
                        className="top-bar__name-button"
                        aria-label="Rename investigation"
                        disabled={!investigation}
                        onClick={startEditing}
                    >
                        {name}
                    </button>
                )}
            </div>
            <span role="status">{investigation ? status : ""}</span>

            <div className="top-bar__actions">
                <button type="button" className="button button--secondary-on-dark" disabled={actionsDisabled} onClick={onLoad}>
                    Load
                </button>
                <button type="button" className="button button--primary" disabled={actionsDisabled} onClick={onSave}>
                    Save
                </button>
            </div>
            {/* Reserved for the future user menu (D6, IAM is out of scope). */}
            <span className="top-bar__user-slot" aria-hidden="true" />
        </header>
    );
}
