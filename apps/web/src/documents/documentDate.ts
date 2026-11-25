import type { ListedDocument } from "../types/document";

// The document's main date as ISO, for the list (UI-28): Transaction date, Gift Card activation
// date, Online Order placed date, or Misc date. null when an incomplete node doesn't know it
// (only incomplete Transactions can know a date).
export function documentDate(doc: ListedDocument): string | null {
    if (doc.status === "incomplete") {
        return doc.type === "transaction" ? doc.date : null;
    }
    switch (doc.type) {
        case "transaction":
            return doc.date;
        case "gift_card":
            return doc.activation.date;
        case "online_order":
            return doc.placed_date;
        case "misc":
            return doc.date;
    }
}
