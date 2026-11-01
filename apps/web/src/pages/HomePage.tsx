import { useEffect, useState } from "react";
import { getHelloWorld } from "../api/graphApi";

export default function HomePage() {
    const [message, setMessage] = useState("Connecting...");

    useEffect(() => {
        getHelloWorld()
        .then(setMessage)
        .catch(() => setMessage("API connection failed"));
    }, []);

    return (
        <main>
        <h1>{message}</h1>
        </main>
    );
}