import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, errorMessage } from "../api/client";
import { deleteInvestigation, getInvestigation } from "../api/investigationsApi";
import { getSettings, resetSettings, saveSettings } from "../api/settingsApi";
import ApiErrorBanner from "../components/ApiErrorBanner";
import AppearanceTable, { findClashes } from "../components/AppearanceTable";
import ConfirmDialog from "../components/ConfirmDialog";
import { useToast } from "../components/Toast";
import type { Investigation } from "../types/investigation";
import type { InvestigationSettings, InvestigationSettingsOut } from "../types/settings";

interface SettingsPageProps {
    investigationId: number;
    // Called after the investigation is deleted. App picks the next investigation to work on.
    onDeleted: () => Promise<void>;
}

const UNEXPORTED_WARNING = "This investigation has changes that were never exported to CSV. They will be lost.";

// Only the editable fields, without is_default.
function editable({ node_styles, important_edge_color }: InvestigationSettingsOut): InvestigationSettings {
    return { node_styles, important_edge_color };
}

// Investigation settings page (route "/settings", D26): Appearance (D27, D28, UI-21 to UI-23)
// and the Investigation section with Delete investigation (D29, UI-24).
export default function SettingsPage({ investigationId, onDeleted }: SettingsPageProps) {
    const navigate = useNavigate();
    const [investigation, setInvestigation] = useState<Investigation | null>(null);
    // The values last loaded from or saved to the backend, and the user's local edits (UI-22:
    // changes stay local until Save).
    const [saved, setSaved] = useState<InvestigationSettingsOut | null>(null);
    const [draft, setDraft] = useState<InvestigationSettings | null>(null);
    const [loadError, setLoadError] = useState<string | null>(null);
    const [busy, setBusy] = useState(false); // a save or reset is in flight
    const [appearanceError, setAppearanceError] = useState<string | null>(null);
    const showToast = useToast();
    const [confirmingReset, setConfirmingReset] = useState(false);
    const [confirmingDelete, setConfirmingDelete] = useState(false);
    const [deleteError, setDeleteError] = useState<string | null>(null);

    // UI-21: load both, and show the error banner if either fails.
    async function load() {
        setLoadError(null);
        try {
            const [loadedInvestigation, loadedSettings] = await Promise.all([
                getInvestigation(investigationId),
                getSettings(investigationId),
            ]);
            setInvestigation(loadedInvestigation);
            setSaved(loadedSettings);
            setDraft(editable(loadedSettings));
        } catch (error) {
            setLoadError(errorMessage(error));
        }
    }

    useEffect(() => {
        void load();
    }, [investigationId]);

    const clashes = draft ? findClashes(draft) : [];
    const saveDisabled = busy || clashes.length > 0;
    const resetDisabled = busy || !saved || saved.is_default;

    function editDraft(next: InvestigationSettings) {
        setDraft(next);
        setAppearanceError(null);
    }

    // UI-22: blocked while two types look the same. A 422 from the backend shows as a summary.
    async function save() {
        if (!draft || saveDisabled) return;
        setBusy(true);
        setAppearanceError(null);
        try {
            const result = await saveSettings(investigationId, draft);
            setSaved(result);
            setDraft(editable(result));
            showToast("Appearance saved.");
        } catch (error) {
            setAppearanceError(
                error instanceof ApiError && error.status === 422 && error.code !== "indistinct_styles"
                    ? "Error: The appearance couldn't be saved. Check the colors and shapes and try again."
                    : errorMessage(error),
            );
        } finally {
            setBusy(false);
        }
    }

    // UI-23: confirmed first; the backend returns the defaults.
    async function reset() {
        setConfirmingReset(false);
        setBusy(true);
        setAppearanceError(null);
        try {
            const result = await resetSettings(investigationId);
            setSaved(result);
            setDraft(editable(result));
            showToast("Appearance reset to the defaults.");
        } catch (error) {
            setAppearanceError(errorMessage(error));
        } finally {
            setBusy(false);
        }
    }

    // UI-24: on failure nothing changes and the error is shown; on success App starts the
    // next investigation and we go to the Investigation page.
    async function deleteAndLeave() {
        setConfirmingDelete(false);
        setDeleteError(null);
        try {
            await deleteInvestigation(investigationId);
        } catch (error) {
            setDeleteError(errorMessage(error));
            return;
        }
        // Navigate first: onDeleted clears the active investigation, which unmounts this page.
        navigate("/");
        await onDeleted();
    }

    const name = investigation?.name ?? "Untitled investigation";
    const loading = !loadError && (investigation === null || draft === null);

    return (
        <div className="settings-page">
            {loadError && <ApiErrorBanner message={loadError} onRetry={() => void load()} />}
            <div className="settings-page__column">
                <section aria-label="Appearance">
                    <h2>Appearance</h2>
                    {loading && (
                        <p className="settings-page__loading" role="status">
                            <span className="spinner" aria-hidden="true" /> Loading…
                        </p>
                    )}
                    {draft && (
                        <>
                            <AppearanceTable value={draft} onChange={editDraft} clashes={clashes} />
                            {appearanceError && (
                                <p className="form-error-summary" role="alert">
                                    {appearanceError}
                                </p>
                            )}
                            <div className="settings-page__actions">
                                <button
                                    type="button"
                                    className={saveDisabled ? "button button--disabled" : "button button--primary"}
                                    disabled={saveDisabled}
                                    onClick={() => void save()}
                                >
                                    Save appearance
                                </button>
                                <button
                                    type="button"
                                    className={resetDisabled ? "button button--disabled" : "button button--secondary"}
                                    disabled={resetDisabled}
                                    onClick={() => setConfirmingReset(true)}
                                >
                                    Reset to defaults
                                </button>
                            </div>
                        </>
                    )}
                </section>

                <section aria-label="Investigation">
                    <h2>Investigation</h2>
                    {investigation && (
                        <>
                            {/* Read-only here; renaming is done on the TopBar (D30). */}
                            <p>
                                <strong>Name:</strong> {name}
                            </p>
                            {deleteError && (
                                <p className="form-error-summary" role="alert">
                                    {deleteError}
                                </p>
                            )}
                            <button
                                type="button"
                                className="button button--destructive"
                                onClick={() => setConfirmingDelete(true)}
                            >
                                Delete investigation
                            </button>
                        </>
                    )}
                </section>
            </div>

            <ConfirmDialog
                open={confirmingReset}
                title="Reset appearance?"
                message="Reset appearance to the default colors and shapes?"
                confirmLabel="Reset"
                onConfirm={() => void reset()}
                onCancel={() => setConfirmingReset(false)}
            />

            <ConfirmDialog
                open={confirmingDelete}
                title="Delete investigation?"
                message={`"${name}" and all its documents will be permanently deleted.`}
                items={investigation?.has_unsaved_changes ? [UNEXPORTED_WARNING] : undefined}
                confirmLabel="Delete investigation"
                onConfirm={() => void deleteAndLeave()}
                onCancel={() => setConfirmingDelete(false)}
            />
        </div>
    );
}
