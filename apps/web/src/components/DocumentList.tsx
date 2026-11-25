import type { ChangeEvent } from "react";
import { documentDate } from "../documents/documentDate";
import { toDisplayDate } from "../documents/fieldRules";
import { DOCUMENT_TYPES, DOCUMENT_TYPE_LABELS, type DocumentType, type ListedDocument } from "../types/document";

interface DocumentListProps {
    documents: ListedDocument[]; // saved documents and incomplete nodes together
    selectedId: string | null;
    onSelect: (id: string) => void;
    onNew: (type: DocumentType) => void;
}

// Title A–Z (D13's default sort). Ties sort by ID, so the order never jumps around.
// Incomplete nodes are sorted in with the rest, not pinned to the top (D13).
function byTitle(a: ListedDocument, b: ListedDocument): number {
    return a.title.localeCompare(b.title) || a.id.localeCompare(b.id, undefined, { numeric: true });
}

// The list pane of the Documents page: the "New document" type dropdown (UI-10), the
// incomplete count, and the documents (UI-11). Clicking an item opens it (UI-12).
// Filters, search and the Important badge come later.
export default function DocumentList({ documents, selectedId, onSelect, onNew }: DocumentListProps) {
    const sorted = [...documents].sort(byTitle);
    const incompleteCount = documents.filter((doc) => doc.status === "incomplete").length;

    // Choosing a type opens its form. The dropdown always shows "New document…" again
    // afterwards (its value stays ""), so the same type can be chosen twice in a row.
    function handleChoose(event: ChangeEvent<HTMLSelectElement>) {
        const type = event.target.value as DocumentType | "";
        if (type !== "") {
            onNew(type);
        }
    }

    return (
        <>
            <div className="document-list__header">
                <h2>Documents</h2>
                <select
                    className="new-document-select"
                    aria-label="New document"
                    value=""
                    onChange={handleChoose}
                >
                    <option value="" disabled>
                        New document…
                    </option>
                    {DOCUMENT_TYPES.map((type) => (
                        <option key={type} value={type}>
                            {DOCUMENT_TYPE_LABELS[type]}
                        </option>
                    ))}
                </select>
            </div>

            {incompleteCount > 0 && <p className="document-list__count">{incompleteCount} incomplete</p>}

            {sorted.length === 0 ? (
                <p>No documents yet – create one to begin</p>
            ) : (
                <ul className="document-list">
                    {sorted.map((doc) => {
                        const isSelected = doc.id === selectedId;
                        const isIncomplete = doc.status === "incomplete";
                        const date = documentDate(doc);
                        const classes = ["document-list__item"];
                        if (isSelected) classes.push("document-list__item--selected");
                        if (isIncomplete) classes.push("document-list__item--incomplete");
                        return (
                            <li key={doc.id}>
                                <button
                                    type="button"
                                    className={classes.join(" ")}
                                    aria-current={isSelected ? "true" : undefined}
                                    onClick={() => onSelect(doc.id)}
                                >
                                    <span className="document-list__type">
                                        {DOCUMENT_TYPE_LABELS[doc.type]}
                                        {isIncomplete && <span className="badge badge--incomplete">Incomplete</span>}
                                    </span>
                                    <span className="document-list__title">{doc.title}</span>
                                    <span className="document-list__date">{date ? toDisplayDate(date) : "No date"}</span>
                                </button>
                            </li>
                        );
                    })}
                </ul>
            )}
        </>
    );
}
