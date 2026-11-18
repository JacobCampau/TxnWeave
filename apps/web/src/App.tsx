import { BrowserRouter, Route, Routes } from "react-router-dom";
import TopBar from "./components/TopBar";
import Footer from "./components/Footer";
import InvestigationPage from "./pages/InvestigationPage";
import DocumentsPage from "./pages/DocumentsPage";

// App shell (D1): top bar, the routed page, and the footer.
export default function App() {
    return (
        <BrowserRouter>
            <div className="app-shell">
                <TopBar />
                <main className="app-main">
                    <Routes>
                        <Route path="/" element={<InvestigationPage />} />
                        <Route path="/documents" element={<DocumentsPage />} />
                    </Routes>
                </main>
                <Footer />
            </div>
        </BrowserRouter>
    );
}
