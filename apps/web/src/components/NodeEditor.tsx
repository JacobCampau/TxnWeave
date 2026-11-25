import {
    DOCUMENT_TYPE_LABELS,
    type DocumentRef,
    type DocumentType,
    type Placeholder,
    type TxnDocument,
} from "../types/document";
import GiftCardForm from "./forms/GiftCardForm";
import MiscForm from "./forms/MiscForm";
import OnlineOrderForm from "./forms/OnlineOrderForm";
import TransactionForm from "./forms/TransactionForm";
import type { SaveHandler } from "./forms/useDocumentForm";

// What the form pane is showing: an empty form for a new document, a saved one to edit,
// or an incomplete node to fill in.
export type EditorTarget =
    | { kind: "new"; type: DocumentType }
    | { kind: "edit"; doc: TxnDocument }
    | { kind: "placeholder"; doc: Placeholder };

interface NodeEditorProps {
    target: EditorTarget;
    referencedBy: DocumentRef[]; // documents that reference this one (shown for incomplete nodes)
    onSave: SaveHandler;
    onCancel: () => void;
    onDelete: () => void;
    onDirtyChange: (dirty: boolean) => void;
}

// The form pane of the Documents page (UI-10, UI-12): the right form for the document's type,
// empty for a new document, filled in for a saved one, or prefilled for an incomplete node.
// Delete is offered only for saved documents (UI-35).
export default function NodeEditor({ target, referencedBy, onSave, onCancel, onDelete, onDirtyChange }: NodeEditorProps) {
    const shared = { onSave, onCancel, onDirtyChange };

    function renderForm() {
        switch (target.kind) {
            case "new":
                switch (target.type) {
                    case "transaction":
                        return <TransactionForm {...shared} />;
                    case "gift_card":
                        return <GiftCardForm {...shared} />;
                    case "online_order":
                        return <OnlineOrderForm {...shared} />;
                    case "misc":
                        return <MiscForm {...shared} />;
                }
                break;

            // Switching on doc.type narrows `doc` to that type, so each form gets its own kind.
            case "edit": {
                const doc = target.doc;
                switch (doc.type) {
                    case "transaction":
                        return <TransactionForm {...shared} initial={doc} onDelete={onDelete} />;
                    case "gift_card":
                        return <GiftCardForm {...shared} initial={doc} onDelete={onDelete} />;
                    case "online_order":
                        return <OnlineOrderForm {...shared} initial={doc} onDelete={onDelete} />;
                    case "misc":
                        return <MiscForm {...shared} initial={doc} onDelete={onDelete} />;
                }
                break;
            }

            case "placeholder": {
                const doc = target.doc;
                switch (doc.type) {
                    case "transaction":
                        return <TransactionForm {...shared} prefill={doc} />;
                    case "gift_card":
                        return <GiftCardForm {...shared} prefill={doc} />;
                    case "online_order":
                        return <OnlineOrderForm {...shared} prefill={doc} />;
                }
            }
        }
    }

    const heading = target.kind === "new" ? `New ${DOCUMENT_TYPE_LABELS[target.type]}` : target.doc.title;

    return (
        <>
            <h2>{heading}</h2>
            {target.kind === "placeholder" && (
                <div className="placeholder-note">
                    <p>
                        <span className="badge badge--incomplete">Incomplete</span> No document exists for this
                        yet. It was filled in from the documents below. Add the missing details and Save to
                        create it.
                    </p>
                    <ul>
                        {referencedBy.map((ref) => (
                            <li key={ref.id}>
                                {ref.title}
                                {ref.match === "ambiguous" && " (could also mean another document)"}
                            </li>
                        ))}
                    </ul>
                </div>
            )}
            {renderForm()}
        </>
    );
}
