export async function getHelloWorld(): Promise<string> {
    const response = await fetch("/api/hello");

    if (!response.ok) {
        throw new Error("API request failed");
    }

    const data: { message: string } = await response.json();

    return data.message;
}