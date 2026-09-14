import { useEffect, useState } from "react";

type HealthResponse = {
  status: string;
  service: string;
};

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const apiUrl = import.meta.env.VITE_API_URL;

    fetch(`${apiUrl}/health`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`API returned ${response.status}`);
        }

        return response.json();
      })
      .then((data: HealthResponse) => {
        setHealth(data);
      })
      .catch((err: Error) => {
        setError(err.message);
      });
  }, []);

  return (
    <main>
      <h1>Crypto Guard V2</h1>

      {health && (
        <section>
          <h2>Backend Status: Connected ✅</h2>
          <p>Status: {health.status}</p>
          <p>Service: {health.service}</p>
        </section>
      )}

      {error && (
        <section>
          <h2>Backend Status: Failed ❌</h2>
          <p>{error}</p>
        </section>
      )}
    </main>
  );
}

export default App;