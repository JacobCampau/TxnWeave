import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { errorMessage } from "../api/client";
import ConfirmDialog from "../components/ConfirmDialog";
import DocumentList from "../components/DocumentList";
import { useToast } from "../components/Toast";
import NodeEditor, { type EditorTarget } from "../components/NodeEditor";
import type { DocumentType, ListedDocument, NewDocument } from "../types/document";

// The three backend calls. Each one throws if the request fails.
interface DocumentsPageProps {
    documents: ListedDocument[]; // saved documents and incomplete nodes, from the backend
    onCreate: (doc: NewDocument) => Promise<string>; // resolves to the new document's id
    onUpdate: (id: string, doc: NewDocument) => Promise<void>;
    onDelete: (id: string) => Promise<void>;
}

// What the form pane shows: a new form of some type, a listed document (saved or
// incomplete) by id, or nothing.
type Selection = { kind: "new"; type: DocumentType } | { kind: "open"; id: string } | null;

// Documents page (route "/documents"): list on the left, form on the right (D12).
export default function DocumentsPage({ documents, onCreate, onUpdate, onDelete }: DocumentsPageProps) {
    const showToast = useToast();
    const [selection, setSelection] = useState<Selection>(null);
    // Goes up every time the selection is applied. It's part of the form's key, so the form
    // starts fresh even when the same document or type is chosen again (after Discard).
    const [formVersion, setFormVersion] = useState(0);
    // True while the open form has unsaved changes. The form reports it (UI-14).
    const [isDirty, setIsDirty] = useState(false);
    // A selection waiting on the "Discard changes?" question. undefined = no question open.
    const [pending, setPending] = useState<Selection | undefined>(undefined);
    const [confirmingDelete, setConfirmingDelete] = useState(false);
    // A failed delete, shown above the form.
    const [deleteError, setDeleteError] = useState<string | null>(null);

    const selectedId = selection?.kind === "open" ? selection.id : null;
    const selected = documents.find((doc) => doc.id === selectedId);
    const savedDoc = selected?.status === "complete" ? selected : undefined;

    let target: EditorTarget | null = null;
    if (selection?.kind === "new") {
        target = { kind: "new", type: selection.type };
    } else if (selected?.status === "complete") {
        target = { kind: "edit", doc: selected };
    } else if (selected?.status === "incomplete") {
        target = { kind: "placeholder", doc: selected };
    }
    const referencedBy = selected?.referenced_by ?? [];

    // "Edit in Documents" on the PropertyPanel opens /documents?doc=<id> (UI-6). The page has
    // just mounted, so no form is open yet. The parameter is then removed, so it can't reopen
    // the document after the user moves on.
    const [searchParams, setSearchParams] = useSearchParams();
    const deepLinkId = searchParams.get("doc");
    useEffect(() => {
        if (deepLinkId === null) return;
        if (documents.some((doc) => doc.id === deepLinkId)) {
            requestSelection({ kind: "open", id: deepLinkId });
        }
        setSearchParams({}, { replace: true });
    }, [deepLinkId]); // only the link itself: re-running on every list change would reopen it

    function applySelection(next: Selection) {
        setSelection(next);
        setFormVersion((version) => version + 1);
        setDeleteError(null);
    }

    // Every way of leaving the open form goes through here, so unsaved edits are never lost
    // without asking (UI-14).
    function requestSelection(next: Selection) {
        if (isDirty) {
            setPending(next);
        } else {
            applySelection(next);
        }
    }

    function discardAndContinue() {
        if (pending !== undefined) {
            applySelection(pending);
        }
        setPending(undefined);
    }

    // Returns an error message for the form to show, or null when the save worked.
    async function handleSave(doc: NewDocument): Promise<string | null> {
        try {
            if (savedDoc) {
                await onUpdate(savedDoc.id, doc);
            } else {
                // A new document, or an incomplete node being promoted (3.8). Either way it is a
                // new saved document (POST), which stays open after Save. A promoted placeholder
                // disappears from the list by itself once its references match the new document.
                const id = await onCreate(doc);
                applySelection({ kind: "open", id });
            }
            showToast("Document saved."); // UI-13
            return null;
        } catch (error) {
            // For example a 409 duplicate_key: "A transaction with this number ... already exists."
            return errorMessage(error);
        }
    }

    async function deleteAndClose() {
        setConfirmingDelete(false);
        if (!savedDoc) return;
        try {
            await onDelete(savedDoc.id);
            applySelection(null); // nothing selected after a delete (UI-35)
            showToast(`Deleted ${savedDoc.title}.`); // UI-15
        } catch (error) {
            setDeleteError(errorMessage(error));
        }
    }

    // UI-15 / UI-35: name the documents that reference this one; they will show it as incomplete.
    const deleteMessage =
        referencedBy.length === 0
            ? "No other documents reference this one. This can't be undone."
            : "These documents reference this one. After the delete they will show it as an incomplete document. This can't be undone.";

    return (
        <>
            <section className="documents-list" aria-label="Documents">
                <DocumentList
                    documents={documents}
                    selectedId={target && target.kind !== "new" ? target.doc.id : null}
                    onSelect={(id) => requestSelection({ kind: "open", id })}
                    onNew={(type) => requestSelection({ kind: "new", type })}
                />
            </section>

            <section className="documents-form" aria-label="Document form">
                {deleteError && (
                    <p className="form-error-summary" role="alert">
                        {deleteError}
                    </p>
                )}
                {target ? (
                    <NodeEditor
                        key={`${selection?.kind === "new" ? `new-${selection.type}` : selectedId}-${formVersion}`}
                        target={target}
                        referencedBy={referencedBy}
                        onSave={handleSave}
                        onCancel={() => requestSelection(null)}
                        onDelete={() => setConfirmingDelete(true)}
                        onDirtyChange={setIsDirty}
                    />
                ) : (
                    <p>Select or create a document</p>
                )}
            </section>

            <ConfirmDialog
                open={pending !== undefined}
                title="Discard changes?"
                message="This document has unsaved changes. They will be lost."
                confirmLabel="Discard"
                onConfirm={discardAndContinue}
                onCancel={() => setPending(undefined)}
            />

            <ConfirmDialog
                open={confirmingDelete}
                title={`Delete ${savedDoc?.title ?? "document"}?`}
                message={deleteMessage}
                items={referencedBy.map((ref) => ref.title)}
                confirmLabel="Delete"
                onConfirm={() => void deleteAndClose()}
                onCancel={() => setConfirmingDelete(false)}
            />
        </>
    );
}
