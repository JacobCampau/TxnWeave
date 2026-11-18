import { NavLink } from "react-router-dom";

// Top bar (D6). Mock-up only: the name, status, Load and Save are static.
export default function TopBar() {
    return (
        <header className="top-bar">
            <span className="top-bar__wordmark">TxnWeave</span>

            <nav className="top-bar__tabs" aria-label="Pages">
                <NavLink to="/" end className="top-bar__tab">
                    Investigation
                </NavLink>
                <NavLink to="/documents" className="top-bar__tab">
                    Documents
                </NavLink>
            </nav>

            <span className="top-bar__name">Untitled investigation</span>
            <span>Not saved</span>

            <div className="top-bar__actions">
                <button type="button" className="button button--secondary-on-dark">
                    Load
                </button>
                <button type="button" className="button button--primary">
                    Save
                </button>
            </div>
        </header>
    );
}
