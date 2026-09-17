import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  type Edge,
  type Node,
} from "@xyflow/react";

import "@xyflow/react/dist/style.css";

type HealthResponse = {
  status: string;
  service: string;
};

type LoginResponse = {
  access_token: string;
  token_type?: string;
};

type TraceTransfer = {
  transaction_hash: string;
  asset: string | null;
  value: number | null;
  category: string | null;
  block_number: number | null;
  timestamp: string | null;
  contract_address: string | null;
};

type Trace = {
  wallets: string[];
  transfers: TraceTransfer[];
  hop_count: number;
  direction: string;
};

type TraceResponse = {
  address: string;
  chain: string;
  direction: string;
  max_hops: number;
  trace_count: number;
  traces: Trace[];
};

const API_URL = import.meta.env.VITE_API_URL;

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);

  const [token, setToken] = useState<string | null>(
    localStorage.getItem("access_token"),
  );

  const [email, setEmail] = useState("test@example.com");
  const [password, setPassword] = useState("TestPassword123!");

  const [address, setAddress] = useState(
    "0x0000000000000000000000000000000000000000",
  );

  const [chain, setChain] = useState("ethereum");
  const [direction, setDirection] = useState("both");
  const [maxHops, setMaxHops] = useState("2");

  const [trace, setTrace] = useState<TraceResponse | null>(null);

  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);

  const [loginLoading, setLoginLoading] = useState(false);
  const [traceLoading, setTraceLoading] = useState(false);

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/health`)
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

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setLoginLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/users/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          password,
        }),
      });

      if (!response.ok) {
        const message = await response.text();
        throw new Error(
          message || `Login failed with status ${response.status}`,
        );
      }

      const data: LoginResponse = await response.json();

      localStorage.setItem("access_token", data.access_token);
      setToken(data.access_token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoginLoading(false);
    }
  }

  function handleLogout() {
    localStorage.removeItem("access_token");

    setToken(null);
    setTrace(null);
    setNodes([]);
    setEdges([]);
    setError(null);
  }

  async function handleTrace(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!token) {
      setError("Please login first.");
      return;
    }

    setTraceLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/wallets/trace/${address}?chain=${chain}&direction=${direction}&max_hops=${maxHops}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      if (response.status === 401) {
        localStorage.removeItem("access_token");
        setToken(null);
        throw new Error("Session expired. Please login again.");
      }

      if (!response.ok) {
        const message = await response.text();

        throw new Error(
          message || `Trace API returned ${response.status}`,
        );
      }

      const data: TraceResponse = await response.json();

      setTrace(data);

      const walletAddresses = new Set<string>();

      data.traces.forEach((item) => {
        item.wallets.forEach((wallet) => {
          walletAddresses.add(wallet);
        });
      });

      const walletList = Array.from(walletAddresses);

      const generatedNodes: Node[] = walletList.map(
        (wallet, index) => ({
          id: wallet,
          position: {
            x: (index % 4) * 300,
            y: Math.floor(index / 4) * 220,
          },
          data: {
            label:
              wallet.toLowerCase() === data.address.toLowerCase()
                ? `TARGET WALLET\n${wallet}`
                : `WALLET\n${wallet}`,
          },
          style: {
            padding: 12,
            borderRadius: 8,
            border:
              wallet.toLowerCase() === data.address.toLowerCase()
                ? "2px solid #ef4444"
                : "1px solid #64748b",
            background:
              wallet.toLowerCase() === data.address.toLowerCase()
                ? "#3f1720"
                : "#172033",
            color: "#ffffff",
            width: 220,
            fontSize: 12,
          },
        }),
      );

      const generatedEdges: Edge[] = [];

      data.traces.forEach((item, traceIndex) => {
        for (let i = 0; i < item.wallets.length - 1; i += 1) {
          const source = item.wallets[i];
          const target = item.wallets[i + 1];

          const transfer = item.transfers[i];

          generatedEdges.push({
            id: `${source}-${target}-${traceIndex}-${i}`,
            source,
            target,
            label: transfer?.asset
              ? `${transfer.asset} ${transfer.value ?? ""}`
              : "TRANSFER",
            animated: false,
            style: {
              strokeWidth: 2,
            },
          });
        }
      });

      setNodes(generatedNodes);
      setEdges(generatedEdges);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Trace failed");
    } finally {
      setTraceLoading(false);
    }
  }

  return (
    <main
      style={{
        width: "100vw",
        height: "100vh",
        margin: 0,
        padding: 0,
        background: "#0f1117",
        color: "#ffffff",
        overflow: "hidden",
        fontFamily: "Arial, sans-serif",
      }}
    >
      {/* TOP BAR */}
      <header
        style={{
          height: "70px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 24px",
          background: "#171a23",
          borderBottom: "1px solid #2b3040",
          boxSizing: "border-box",
        }}
      >
        <div>
          <h1
            style={{
              margin: 0,
              fontSize: "22px",
            }}
          >
            Crypto Guard V2
          </h1>

          <div
            style={{
              marginTop: "5px",
              fontSize: "12px",
              color: health?.status === "healthy" ? "#4ade80" : "#f87171",
            }}
          >
            Backend: {health?.status ?? "checking..."}
          </div>
        </div>

        {token && (
          <button
            onClick={handleLogout}
            style={{
              background: "#272d3a",
              color: "#ffffff",
              border: "1px solid #475569",
              borderRadius: "6px",
              padding: "8px 16px",
              cursor: "pointer",
            }}
          >
            Logout
          </button>
        )}
      </header>

      {/* LOGIN */}
      {!token && (
        <section
          style={{
            position: "absolute",
            zIndex: 20,
            top: "100px",
            left: "50%",
            transform: "translateX(-50%)",
            width: "360px",
            background: "#171a23",
            border: "1px solid #2f3545",
            borderRadius: "12px",
            padding: "28px",
            boxSizing: "border-box",
            boxShadow: "0 20px 50px rgba(0,0,0,0.4)",
          }}
        >
          <h2
            style={{
              marginTop: 0,
              marginBottom: "8px",
            }}
          >
            Sign in
          </h2>

          <p
            style={{
              color: "#94a3b8",
              fontSize: "13px",
              marginBottom: "20px",
            }}
          >
            Login to access blockchain tracing.
          </p>

          <form onSubmit={handleLogin}>
            <label
              style={{
                display: "block",
                fontSize: "13px",
                marginBottom: "6px",
              }}
            >
              Email
            </label>

            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              style={inputStyle}
            />

            <label
              style={{
                display: "block",
                fontSize: "13px",
                marginBottom: "6px",
                marginTop: "14px",
              }}
            >
              Password
            </label>

            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              style={inputStyle}
            />

            <button
              type="submit"
              disabled={loginLoading}
              style={primaryButtonStyle}
            >
              {loginLoading ? "Signing in..." : "Sign In"}
            </button>
          </form>
        </section>
      )}

      {/* TRACE CONTROLS */}
      {token && (
        <section
          style={{
            position: "absolute",
            zIndex: 10,
            top: "86px",
            left: "20px",
            width: "360px",
            background: "#171a23",
            border: "1px solid #2f3545",
            borderRadius: "10px",
            padding: "16px",
            boxSizing: "border-box",
            boxShadow: "0 10px 30px rgba(0,0,0,0.35)",
          }}
        >
          <h3
            style={{
              margin: "0 0 14px 0",
            }}
          >
            Wallet Tracing
          </h3>

          <form onSubmit={handleTrace}>
            <label style={labelStyle}>Wallet Address</label>

            <input
              value={address}
              onChange={(event) => setAddress(event.target.value)}
              style={inputStyle}
              placeholder="0x..."
              required
            />

            <label style={labelStyle}>Chain</label>

            <select
              value={chain}
              onChange={(event) => setChain(event.target.value)}
              style={inputStyle}
            >
              <option value="ethereum">Ethereum</option>
              <option value="polygon">Polygon</option>
              <option value="arbitrum">Arbitrum</option>
              <option value="optimism">Optimism</option>
              <option value="base">Base</option>
            </select>

            <label style={labelStyle}>Direction</label>

            <select
              value={direction}
              onChange={(event) => setDirection(event.target.value)}
              style={inputStyle}
            >
              <option value="both">Both</option>
              <option value="outgoing">Outgoing</option>
              <option value="incoming">Incoming</option>
            </select>

            <label style={labelStyle}>Max Hops</label>

            <select
              value={maxHops}
              onChange={(event) => setMaxHops(event.target.value)}
              style={inputStyle}
            >
              <option value="1">1 Hop</option>
              <option value="2">2 Hops</option>
            </select>

            <button
              type="submit"
              disabled={traceLoading}
              style={primaryButtonStyle}
            >
              {traceLoading ? "Tracing..." : "Trace Wallet"}
            </button>
          </form>

          {trace && (
            <div
              style={{
                marginTop: "14px",
                paddingTop: "12px",
                borderTop: "1px solid #2f3545",
                fontSize: "12px",
                color: "#cbd5e1",
              }}
            >
              <div>
                <strong>Traces:</strong> {trace.trace_count}
              </div>

              <div>
                <strong>Chain:</strong> {trace.chain}
              </div>

              <div>
                <strong>Direction:</strong> {trace.direction}
              </div>

              <div>
                <strong>Max hops:</strong> {trace.max_hops}
              </div>

              <div>
                <strong>Wallets:</strong> {nodes.length}
              </div>

              <div>
                <strong>Connections:</strong> {edges.length}
              </div>
            </div>
          )}
        </section>
      )}

      {/* ERROR */}
      {error && (
        <div
          style={{
            position: "absolute",
            zIndex: 30,
            bottom: "20px",
            left: "20px",
            right: "20px",
            padding: "12px 16px",
            background: "#3f1720",
            border: "1px solid #ef4444",
            borderRadius: "8px",
            color: "#fecaca",
            fontSize: "13px",
          }}
        >
          {error}
        </div>
      )}

      {/* GRAPH */}
      <div
        style={{
          width: "100%",
          height: "calc(100vh - 70px)",
        }}
      >
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          minZoom={0.2}
          maxZoom={2}
        >
          <Background />
          <Controls />
          <MiniMap
            nodeColor={(node) => {
              const label = String(node.data?.label ?? "");

              return label.startsWith("TARGET")
                ? "#ef4444"
                : "#64748b";
            }}
          />
        </ReactFlow>
      </div>
    </main>
  );
}

const inputStyle: React.CSSProperties = {
  width: "100%",
  boxSizing: "border-box",
  padding: "10px",
  marginBottom: "4px",
  background: "#0f1117",
  color: "#ffffff",
  border: "1px solid #3b4254",
  borderRadius: "6px",
  outline: "none",
};

const labelStyle: React.CSSProperties = {
  display: "block",
  fontSize: "12px",
  color: "#cbd5e1",
  marginTop: "10px",
  marginBottom: "5px",
};

const primaryButtonStyle: React.CSSProperties = {
  width: "100%",
  marginTop: "16px",
  padding: "10px",
  background: "#2563eb",
  color: "#ffffff",
  border: "none",
  borderRadius: "6px",
  cursor: "pointer",
  fontWeight: 600,
};

export default App;