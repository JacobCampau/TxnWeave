// Documents page (route "/documents"). Mock-up only: the empty list and form panes.
export default function DocumentsPage() {
    return (
        <>
            <section className="documents-list" aria-label="Documents">
                <h2>Documents</h2>
                <p>No documents yet.</p>
            </section>

            <section className="documents-form" aria-label="Document form">
                <h2>New document</h2>
                <p>Select a document type to begin.</p>
            </section>
        </>
    );
}
