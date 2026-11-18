// Investigation page (route "/"). Mock-up only: shows the empty graph canvas.
export default function InvestigationPage() {
    return (
        <section className="investigation-canvas" aria-label="Graph">
            <p className="empty-state">
                No documents yet. Add one on the Documents page.
            </p>
        </section>
    );
}
