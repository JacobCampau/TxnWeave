// An investigation as the backend returns it (api.md "InvestigationOut").
export interface Investigation {
    id: number;
    name: string | null; // null shows as "Untitled investigation"
    created_at: string;
    updated_at: string;
    last_exported_at: string | null;
    document_count: number;
    incomplete_count: number;
    has_unsaved_changes: boolean;
}
