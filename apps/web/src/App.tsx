import { useState, useRef } from "react";
import { BrowserRouter, Route, Routes, useNavigate } from "react-router-dom";
import TopBar, { type AutosaveState } from "./components/TopBar";
import Footer from "./components/Footer";
import ApiErrorBanner from "./components/ApiErrorBanner";
import ConfirmDialog from "./components/ConfirmDialog";
import StartDialog from "./components/StartDialog";
import { ToastProvider, useToast } from "./components/Toast";
import { useCsvLoad } from "./components/useCsvLoad";
import InvestigationPage from "./pages/InvestigationPage";
import DocumentsPage from "./pages/DocumentsPage";
import SettingsPage from "./pages/SettingsPage";
import { errorMessage } from "./api/client";
import { downloadExport } from "./api/csvApi";
import * as documentsApi from "./api/documentsApi";
import {
    createInvestigation,
    deleteInvestigation,
    getInvestigation,
    renameInvestigation,
} from "./api/investigationsApi";
import type { ListedDocument, NewDocument } from "./types/document";
import type { Investigation } from "./types/investigation";

export default function App() {
    return (
        <BrowserRouter>
            <ToastProvider>
                <Shell />
            </ToastProvider>
        </BrowserRouter>
    );
}

// The UI-2 question, waiting for an answer.
interface LeavingPrompt {
    previous: Investigation;
    resolve: (proceed: boolean) => void;
}

// App shell (D1): top bar, the routed page, and the footer. It holds the active investigation.
// Nothing about it is kept in the browser (D34): every open and reload starts at StartDialog.
function Shell() {
    const navigate = useNavigate();
    const showToast = useToast();
    // null: no active investigation, so StartDialog is shown (UI-1).
    const [investigation, setInvestigation] = useState<Investigation | null>(null);
    // Saved documents and incomplete nodes, as the backend returns them.
    const [documents, setDocuments] = useState<ListedDocument[]>([]);
    const [listError, setListError] = useState<string | null>(null);
    const [autosave, setAutosave] = useState<AutosaveState>("saved");
    const [exporting, setExporting] = useState(false);
    const [starting, setStarting] = useState(false); // StartDialog's New is in progress
    const [startError, setStartError] = useState<string | null>(null);
    const [leaving, setLeaving] = useState<LeavingPrompt | null>(null);
    // Where the current Load started (its errors go inline or to a toast, D35), and the
    // investigation it will replace (BD7).
    const loadSource = useRef<"start" | "topbar">("start");
    const loadPrevious = useRef<Investigation | null>(null);

    const csvLoad = useCsvLoad({
        onLoaded: (loaded) => {
            void activate(loaded);
            void retire(loadPrevious.current, loaded.id);
            showToast(`Loaded ${loaded.name ?? "Untitled investigation"}.`);
        },
        onError: (message) => {
            if (loadSource.current === "start") setStartError(message);
            else showToast(message, "error");
        },
    });

    // ---- The active investigation ----

    async function loadDocuments(id: number) {
        setListError(null);
        try {
            setDocuments(await documentsApi.listDocuments(id));
        } catch (error) {
            setListError(errorMessage(error));
        }
    }

    // New, Resume and Load all land on the Investigation page (D34).
    async function activate(next: Investigation) {
        setInvestigation(next);
        setStartError(null);
        setAutosave("saved");
        navigate("/");
        await loadDocuments(next.id);
    }

    // updated_at and has_unsaved_changes change with every write.
    async function refresh(id: number) {
        try {
            setInvestigation(await getInvestigation(id));
        } catch {
            // Keep what we have; the next write or reload tries again.
        }
    }

    // ---- Replacing an investigation (UI-2, BD7) ----

    // Resolves true when it's fine to replace `previous`: it has no unsaved changes, or the
    // user chose Save first (and the save worked) or Discard.
    function confirmLeaving(previous: Investigation | null): Promise<boolean> {
        if (!previous || !previous.has_unsaved_changes) return Promise.resolve(true);
        return new Promise((resolve) => setLeaving({ previous, resolve }));
    }

    async function answerLeaving(choice: "save" | "discard" | "cancel") {
        if (!leaving) return;
        const { previous, resolve } = leaving;
        setLeaving(null);
        resolve(choice === "save" ? await saveCsv(previous) : choice === "discard");
    }

    // BD7: once replaced, the previous investigation is deleted; the CSV file is the archive.
    async function retire(previous: Investigation | null, keepId: number) {
        if (!previous || previous.id === keepId) return;
        try {
            await deleteInvestigation(previous.id);
        } catch {
            // Not harmful: it stays in the database and can still be resumed.
        }
    }

    async function startNew(name: string | null, previous: Investigation | null) {
        if (!(await confirmLeaving(previous))) return;
        setStarting(true);
        setStartError(null);
        try {
            const created = await createInvestigation(name);
            await activate(created);
            await retire(previous, created.id);
        } catch (error) {
            setStartError(errorMessage(error));
        } finally {
            setStarting(false);
        }
    }

    async function startLoad(source: "start" | "topbar", previous: Investigation | null) {
        // Ask with fresh values: a settings change elsewhere may have made it unsaved.
        const current = previous ? await getInvestigation(previous.id).catch(() => previous) : null;
        if (!(await confirmLeaving(current))) return;
        loadSource.current = source;
        loadPrevious.current = current;
        setStartError(null);
        csvLoad.open();
    }

    // ---- Save (CSV export) ----

    async function saveCsv(target: Investigation): Promise<boolean> {
        setExporting(true);
        try {
            const filename = await downloadExport(target.id);
            showToast(`Saved ${filename}.`);
            if (investigation?.id === target.id) await refresh(target.id);
            return true;
        } catch (error) {
            showToast(errorMessage(error), "error"); // UI-18
            return false;
        } finally {
            setExporting(false);
        }
    }

    async function rename(name: string | null): Promise<boolean> {
        if (!investigation) return false;
        try {
            setInvestigation(await renameInvestigation(investigation.id, name));
            return true;
        } catch (error) {
            showToast(errorMessage(error), "error"); // the old name stays (UI-25)
            return false;
        }
    }

    // ---- Document writes ----

    // Every write commits on the server straight away (B2). These throw on failure; the
    // Documents page shows the message.
    async function write<T>(id: number, action: () => Promise<T>): Promise<T> {
        setAutosave("saving");
        try {
            const result = await action();
            setAutosave("saved");
            // Incomplete nodes, titles and referenced_by are all worked out by the backend (B4).
            await Promise.all([loadDocuments(id), refresh(id)]);
            return result;
        } catch (error) {
            setAutosave("failed");
            throw error;
        }
    }

    // After Delete investigation (D29) there is no active investigation: StartDialog (UI-1).
    async function afterDelete() {
        setInvestigation(null);
        setDocuments([]);
    }

    const id = investigation?.id ?? null;

    return (
        <div className="app-shell">
            <TopBar
                investigation={investigation}
                autosave={autosave}
                busy={exporting || csvLoad.busy}
                onRename={rename}
                onSave={() => investigation && void saveCsv(investigation)}
                onLoad={() => void startLoad("topbar", investigation)}
            />
            {listError && id !== null && <ApiErrorBanner message={listError} onRetry={() => void loadDocuments(id)} />}
            <main className="app-main">
                {id !== null && (
                    <Routes>
                        <Route path="/" element={<InvestigationPage investigationId={id} documents={documents} />} />
                        <Route
                            path="/documents"
                            element={
                                <DocumentsPage
                                    documents={documents}
                                    onCreate={(doc: NewDocument) =>
                                        write(id, () => documentsApi.createDocument(id, doc)).then((saved) => saved.id)
                                    }
                                    onUpdate={(docId, doc) => write(id, () => documentsApi.updateDocument(id, docId, doc)).then(() => {})}
                                    onDelete={(docId) => write(id, () => documentsApi.deleteDocument(id, docId))}
                                />
                            }
                        />
                        <Route path="/settings" element={<SettingsPage investigationId={id} onDeleted={afterDelete} />} />
                    </Routes>
                )}
            </main>
            <Footer />

            {investigation === null && (
                <StartDialog
                    onResume={(previous) => void activate(previous)}
                    onNew={(name, previous) => void startNew(name, previous)}
                    onLoad={(previous) => void startLoad("start", previous)}
                    error={startError}
                    busy={starting || csvLoad.busy}
                />
            )}
            {csvLoad.elements}
            <ConfirmDialog
                open={leaving !== null}
                title="Save changes first?"
                message={`"${leaving?.previous.name ?? "Untitled investigation"}" has changes that aren't in a saved CSV file. It will be replaced.`}
                confirmLabel="Discard"
                extraAction={{ label: "Save first", onClick: () => void answerLeaving("save") }}
                onConfirm={() => void answerLeaving("discard")}
                onCancel={() => void answerLeaving("cancel")}
            />
        </div>
    );
}
