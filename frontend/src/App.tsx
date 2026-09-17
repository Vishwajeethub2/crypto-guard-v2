import { useEffect, useState } from "react";
import type { FormEvent, MouseEvent } from "react";

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

type Case = {
  id: number;
  title: string;
  description: string | null;
  status: string;
  created_by: number;
};

type Wallet = {
  id: number;
  case_id: number;
  address: string;
  chain: string;
  label: string | null;
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

type RiskIndicator = {
  indicator: string;
  severity: "low" | "medium" | "high" | "critical";
  reason: string;
  evidence: Record<string, unknown>;
};

type RiskBehavior = {
  address: string;
  chain: string;
  outgoing_connections: number;
  incoming_connections: number;
  total_connections: number;
  outgoing_transaction_count: number;
  incoming_transaction_count: number;
  total_transaction_count: number;
  outgoing_value: number;
  incoming_value: number;
  unique_assets: number;
};

type RiskExposure = {
  risk_entity_address: string;
  risk_entity_chain: string;
  entity_type: string;
  entity_name: string | null;
  source: string | null;
  wallets: string[];
  transfers: TraceTransfer[];
  hop_count: number;
};

type RiskResponse = {
  address: string;
  chain: string;
  risk_score: number;
  risk_level: "low" | "moderate" | "high" | "critical";
  indicator_count: number;
  exposure_count: number;
  severity_counts: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  behavior: RiskBehavior | null;
  indicators: RiskIndicator[];
  exposures: RiskExposure[];
};

type WalletTransaction = {
  source: string;
  target: string;
  transfer: TraceTransfer;
  hop_count: number;
};

const API_URL = import.meta.env.VITE_API_URL;

function App() {
  const [health, setHealth] =
    useState<HealthResponse | null>(null);

  const [token, setToken] = useState<string | null>(
    localStorage.getItem("access_token"),
  );

  const [email, setEmail] =
    useState("test@example.com");

  const [password, setPassword] =
    useState("TestPassword123!");

  /* =========================
     CASE STATE
  ========================= */

  const [cases, setCases] = useState<Case[]>([]);

  const [selectedCase, setSelectedCase] =
    useState<Case | null>(null);

  const [caseLoading, setCaseLoading] =
    useState(false);

  const [showCreateCase, setShowCreateCase] =
    useState(false);

  const [newCaseTitle, setNewCaseTitle] =
    useState("");

  const [newCaseDescription, setNewCaseDescription] =
    useState("");

  /* =========================
     WALLET STATE
  ========================= */

  const [wallets, setWallets] =
    useState<Wallet[]>([]);

  const [selectedWalletId, setSelectedWalletId] =
    useState<number | null>(null);

  const [showAddWallet, setShowAddWallet] =
    useState(false);

  const [newWalletAddress, setNewWalletAddress] =
    useState("");

  const [newWalletChain, setNewWalletChain] =
    useState("ethereum");

  const [newWalletLabel, setNewWalletLabel] =
    useState("");

  /* =========================
     TRACING STATE
  ========================= */

  const [address, setAddress] = useState(
    "0x0000000000000000000000000000000000000000",
  );

  const [chain, setChain] =
    useState("ethereum");

  const [direction, setDirection] =
    useState("both");

  const [maxHops, setMaxHops] =
    useState("2");

  const [trace, setTrace] =
    useState<TraceResponse | null>(null);

  /* =========================
     RISK STATE
  ========================= */

  const [risk, setRisk] =
    useState<RiskResponse | null>(null);

  /* =========================
     GRAPH STATE
  ========================= */

  const [nodes, setNodes] =
    useState<Node[]>([]);

  const [edges, setEdges] =
    useState<Edge[]>([]);

  /* =========================
     INVESTIGATION STATE
  ========================= */

  const [selectedWallet, setSelectedWallet] =
    useState<string | null>(null);

  const [selectedTransfer, setSelectedTransfer] =
    useState<WalletTransaction | null>(null);

  /* =========================
     LOADING / ERROR
  ========================= */

  const [loginLoading, setLoginLoading] =
    useState(false);

  const [traceLoading, setTraceLoading] =
    useState(false);

  const [riskLoading, setRiskLoading] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  /* =========================
     HEALTH CHECK
  ========================= */

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(
            `API returned ${response.status}`,
          );
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

  /* =========================
     LOAD CASES AFTER LOGIN
  ========================= */

  useEffect(() => {
    if (!token) {
      return;
    }

    loadCases();
  }, [token]);

  /* =========================
     LOAD WALLETS WHEN CASE CHANGES
  ========================= */

  useEffect(() => {
    if (!token || !selectedCase) {
      setWallets([]);
      setSelectedWalletId(null);
      return;
    }

    loadWallets(selectedCase.id);
  }, [token, selectedCase]);

  /* =========================
     LOAD CASES
  ========================= */

  async function loadCases() {
    if (!token) {
      return;
    }

    try {
      const response = await fetch(
        `${API_URL}/cases/`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      if (response.status === 401) {
        localStorage.removeItem(
          "access_token",
        );

        setToken(null);

        throw new Error(
          "Session expired. Please login again.",
        );
      }

      if (!response.ok) {
        const message =
          await response.text();

        throw new Error(
          message ||
            `Cases API returned ${response.status}`,
        );
      }

      const data: Case[] =
        await response.json();

      setCases(data);

      if (data.length > 0) {
        setSelectedCase((current) => {
          if (current) {
            const refreshed = data.find(
              (item) =>
                item.id === current.id,
            );

            return refreshed ?? data[0];
          }

          return data[0];
        });
      } else {
        setSelectedCase(null);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load cases",
      );
    }
  }

  /* =========================
     LOAD WALLETS
  ========================= */

  async function loadWallets(caseId: number) {
    if (!token) {
      return;
    }

    try {
      const response = await fetch(
        `${API_URL}/wallets/?case_id=${caseId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      if (response.status === 401) {
        localStorage.removeItem(
          "access_token",
        );

        setToken(null);

        throw new Error(
          "Session expired. Please login again.",
        );
      }

      if (!response.ok) {
        const message =
          await response.text();

        throw new Error(
          message ||
            `Wallet API returned ${response.status}`,
        );
      }

      const data: Wallet[] =
        await response.json();

      setWallets(data);

      if (data.length > 0) {
        setSelectedWalletId((current) => {
          if (
            current &&
            data.some(
              (wallet) =>
                wallet.id === current,
            )
          ) {
            return current;
          }

          return data[0].id;
        });
      } else {
        setSelectedWalletId(null);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load wallets",
      );
    }
  }

  /* =========================
     LOGIN
  ========================= */

  async function handleLogin(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setLoginLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/users/login`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            email,
            password,
          }),
        },
      );

      if (!response.ok) {
        const message =
          await response.text();

        throw new Error(
          message ||
            `Login failed with status ${response.status}`,
        );
      }

      const data: LoginResponse =
        await response.json();

      localStorage.setItem(
        "access_token",
        data.access_token,
      );

      setToken(data.access_token);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Login failed",
      );
    } finally {
      setLoginLoading(false);
    }
  }

  /* =========================
     LOGOUT
  ========================= */

  function handleLogout() {
    localStorage.removeItem(
      "access_token",
    );

    setToken(null);

    setCases([]);
    setSelectedCase(null);

    setWallets([]);
    setSelectedWalletId(null);

    setTrace(null);
    setRisk(null);

    setNodes([]);
    setEdges([]);

    setSelectedWallet(null);
    setSelectedTransfer(null);

    setError(null);
  }

  /* =========================
     CREATE CASE
  ========================= */

  async function handleCreateCase(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (!token) {
      setError("Please login first.");
      return;
    }

    if (!newCaseTitle.trim()) {
      setError(
        "Case title is required.",
      );
      return;
    }

    setCaseLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/cases/`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            title:
              newCaseTitle.trim(),
            description:
              newCaseDescription.trim() ||
              null,
          }),
        },
      );

      if (response.status === 401) {
        localStorage.removeItem(
          "access_token",
        );

        setToken(null);

        throw new Error(
          "Session expired. Please login again.",
        );
      }

      if (!response.ok) {
        const message =
          await response.text();

        throw new Error(
          message ||
            `Create case failed with status ${response.status}`,
        );
      }

      const createdCase: Case =
        await response.json();

      setCases((current) => [
        createdCase,
        ...current,
      ]);

      setSelectedCase(createdCase);

      setWallets([]);
      setSelectedWalletId(null);

      setNewCaseTitle("");
      setNewCaseDescription("");
      setShowCreateCase(false);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to create case",
      );
    } finally {
      setCaseLoading(false);
    }
  }

  /* =========================
     DELETE CASE
  ========================= */

  async function handleDeleteCase(
    caseId: number,
  ) {
    if (!token) {
      setError("Please login first.");
      return;
    }

    const confirmed =
      window.confirm(
        "Delete this case? This action cannot be undone.",
      );

    if (!confirmed) {
      return;
    }

    setCaseLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/cases/${caseId}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      if (response.status === 401) {
        localStorage.removeItem(
          "access_token",
        );

        setToken(null);

        throw new Error(
          "Session expired. Please login again.",
        );
      }

      if (!response.ok) {
        const message =
          await response.text();

        throw new Error(
          message ||
            `Delete case failed with status ${response.status}`,
        );
      }

      const remainingCases =
        cases.filter(
          (item) =>
            item.id !== caseId,
        );

      setCases(remainingCases);

      if (
        selectedCase?.id ===
        caseId
      ) {
        setSelectedCase(
          remainingCases[0] ??
            null,
        );

        setWallets([]);
        setSelectedWalletId(
          null,
        );

        setTrace(null);
        setRisk(null);

        setNodes([]);
        setEdges([]);

        setSelectedWallet(null);
        setSelectedTransfer(null);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to delete case",
      );
    } finally {
      setCaseLoading(false);
    }
  }

  /* =========================
     ADD WALLET
  ========================= */

  async function handleAddWallet(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (!token || !selectedCase) {
      setError(
        "Please select a case first.",
      );
      return;
    }

    if (!newWalletAddress.trim()) {
      setError(
        "Wallet address is required.",
      );
      return;
    }

    setCaseLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/wallets/?case_id=${selectedCase.id}`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            address:
              newWalletAddress.trim(),
            chain:
              newWalletChain,
            label:
              newWalletLabel.trim() ||
              null,
          }),
        },
      );

      if (response.status === 401) {
        localStorage.removeItem(
          "access_token",
        );

        setToken(null);

        throw new Error(
          "Session expired. Please login again.",
        );
      }

      if (!response.ok) {
        const message =
          await response.text();

        throw new Error(
          message ||
            `Failed to add wallet (${response.status})`,
        );
      }

      const createdWallet: Wallet =
        await response.json();

      setWallets((current) => [
        ...current,
        createdWallet,
      ]);

      setSelectedWalletId(
        createdWallet.id,
      );

      setNewWalletAddress("");
      setNewWalletLabel("");
      setShowAddWallet(false);

      setAddress(
        createdWallet.address,
      );

      setChain(
        createdWallet.chain,
      );

      setTrace(null);
      setRisk(null);
      setNodes([]);
      setEdges([]);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to add wallet",
      );
    } finally {
      setCaseLoading(false);
    }
  }

  /* =========================
     DELETE WALLET
  ========================= */

  async function handleDeleteWallet(
    walletId: number,
  ) {
    if (!token) {
      return;
    }

    const confirmed =
      window.confirm(
        "Delete this wallet from the case?",
      );

    if (!confirmed) {
      return;
    }

    setCaseLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/wallets/${walletId}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      if (response.status === 401) {
        localStorage.removeItem(
          "access_token",
        );

        setToken(null);

        throw new Error(
          "Session expired. Please login again.",
        );
      }

      if (!response.ok) {
        const message =
          await response.text();

        throw new Error(
          message ||
            `Failed to delete wallet (${response.status})`,
        );
      }

      const remainingWallets =
        wallets.filter(
          (wallet) =>
            wallet.id !==
            walletId,
        );

      setWallets(
        remainingWallets,
      );

      if (
        selectedWalletId ===
        walletId
      ) {
        const nextWallet =
          remainingWallets[0];

        setSelectedWalletId(
          nextWallet?.id ??
            null,
        );

        if (nextWallet) {
          setAddress(
            nextWallet.address,
          );

          setChain(
            nextWallet.chain,
          );
        }
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to delete wallet",
      );
    } finally {
      setCaseLoading(false);
    }
  }

  /* =========================
     TRACE WALLET
  ========================= */

  async function handleTrace(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (!token) {
      setError("Please login first.");
      return;
    }

    if (!selectedCase) {
      setError(
        "Create or select a case first.",
      );
      return;
    }

    setTraceLoading(true);
    setError(null);

    setRisk(null);
    setSelectedWallet(null);
    setSelectedTransfer(null);

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
        localStorage.removeItem(
          "access_token",
        );

        setToken(null);

        throw new Error(
          "Session expired. Please login again.",
        );
      }

      if (!response.ok) {
        const message =
          await response.text();

        throw new Error(
          message ||
            `Trace API returned ${response.status}`,
        );
      }

      const data: TraceResponse =
        await response.json();

      setTrace(data);

      const walletAddresses =
        new Set<string>();

      data.traces.forEach(
        (item) => {
          item.wallets.forEach(
            (wallet) => {
              walletAddresses.add(
                wallet,
              );
            },
          );
        },
      );

      const walletList =
        Array.from(
          walletAddresses,
        );

      const generatedNodes: Node[] =
        walletList.map(
          (
            wallet,
            index,
          ) => {
            const isTarget =
              wallet.toLowerCase() ===
              data.address.toLowerCase();

            return {
              id: wallet,

              position: {
                x:
                  (index % 4) *
                  330,
                y:
                  Math.floor(
                    index / 4,
                  ) * 240,
              },

              data: {
                label: isTarget
                  ? `TARGET WALLET\n${shortenAddress(wallet)}`
                  : `WALLET\n${shortenAddress(wallet)}`,
              },

              style: {
                padding: 12,
                borderRadius: 8,

                border: isTarget
                  ? "2px solid #ef4444"
                  : "1px solid #64748b",

                background:
                  isTarget
                    ? "#3f1720"
                    : "#172033",

                color:
                  "#ffffff",

                width: 240,

                fontSize: 12,

                lineHeight: 1.5,

                textAlign:
                  "center",

                cursor:
                  "pointer",
              },
            };
          },
        );

      const generatedEdges: Edge[] =
        [];

      data.traces.forEach(
        (
          item,
          traceIndex,
        ) => {
          for (
            let i = 0;
            i <
              item.wallets
                .length -
                1;
            i += 1
          ) {
            const source =
              item.wallets[i];

            const target =
              item.wallets[i + 1];

            const transfer =
              item.transfers[i];

            generatedEdges.push({
              id: `${source}-${target}-${traceIndex}-${i}`,

              source,
              target,

              label: transfer?.asset
                ? `${transfer.asset} ${
                    transfer.value !==
                      null &&
                    transfer.value !==
                      undefined
                      ? formatNumber(
                          transfer.value,
                        )
                      : ""
                  }`
                : "TRANSFER",

              animated: false,

              style: {
                strokeWidth: 2,
              },

              labelStyle: {
                fontSize: 10,
                fontWeight: 600,
              },

              labelBgStyle: {
                fill: "#ffffff",
              },

              labelBgPadding: [
                4,
                2,
              ],

              labelBgBorderRadius:
                3,
            });
          }
        },
      );

      setNodes(
        generatedNodes,
      );

      setEdges(
        generatedEdges,
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Trace failed",
      );
    } finally {
      setTraceLoading(false);
    }
  }

  /* =========================
     RISK ANALYSIS
  ========================= */

  async function handleRiskAnalysis() {
    if (!token) {
      setError("Please login first.");
      return;
    }

    if (!selectedCase) {
      setError(
        "Create or select a case first.",
      );
      return;
    }

    setRiskLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/wallets/risk/${address}?chain=${chain}&max_hops=${maxHops}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      if (response.status === 401) {
        localStorage.removeItem(
          "access_token",
        );

        setToken(null);

        throw new Error(
          "Session expired. Please login again.",
        );
      }

      if (!response.ok) {
        const message =
          await response.text();

        throw new Error(
          message ||
            `Risk API returned ${response.status}`,
        );
      }

      const data: RiskResponse =
        await response.json();

      setRisk(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Risk analysis failed",
      );
    } finally {
      setRiskLoading(false);
    }
  }

  /* =========================
     NODE CLICK
  ========================= */

  function handleNodeClick(
    _event: MouseEvent,
    node: Node,
  ) {
    setSelectedTransfer(null);
    setSelectedWallet(node.id);
  }

  /* =========================
     EDGE CLICK
  ========================= */

  function handleEdgeClick(
    _event: MouseEvent,
    edge: Edge,
  ) {
    if (!trace) {
      return;
    }

    const matchingTransfer =
      findTransferForEdge(
        trace,
        edge.source,
        edge.target,
      );

    if (matchingTransfer) {
      setSelectedWallet(null);

      setSelectedTransfer(
        matchingTransfer,
      );
    }
  }

  /* =========================
     CLOSE INVESTIGATION
  ========================= */

  function closeInvestigationPanel() {
    setSelectedWallet(null);
    setSelectedTransfer(null);
  }

  const selectedWalletTransactions =
    selectedWallet
      ? getWalletTransactions(
          trace,
          selectedWallet,
        )
      : [];

  /* =========================
     RENDER
  ========================= */

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
        fontFamily:
          "Arial, sans-serif",
      }}
    >
      {/* =====================
          TOP BAR
      ===================== */}

      <header
        style={{
          height: "70px",
          display: "flex",
          alignItems: "center",
          justifyContent:
            "space-between",
          padding:
            "0 24px",
          background:
            "#171a23",
          borderBottom:
            "1px solid #2b3040",
          boxSizing:
            "border-box",
          position:
            "relative",
          zIndex: 50,
        }}
      >
        <div>
          <h1
            style={{
              margin: 0,
              fontSize:
                "22px",
            }}
          >
            Crypto Guard V2
          </h1>

          <div
            style={{
              marginTop:
                "5px",
              fontSize:
                "12px",
              color:
                health?.status ===
                "healthy"
                  ? "#4ade80"
                  : "#f87171",
            }}
          >
            Backend:{" "}
            {health?.status ??
              "checking..."}
          </div>
        </div>

        {token && (
          <button
            onClick={
              handleLogout
            }
            style={{
              background:
                "#272d3a",
              color:
                "#ffffff",
              border:
                "1px solid #475569",
              borderRadius:
                "6px",
              padding:
                "8px 16px",
              cursor:
                "pointer",
            }}
          >
            Logout
          </button>
        )}
      </header>

      {/* =====================
          LOGIN
      ===================== */}

      {!token && (
        <section
          style={{
            position:
              "absolute",
            zIndex: 100,
            top: "100px",
            left: "50%",
            transform:
              "translateX(-50%)",
            width: "360px",
            background:
              "#171a23",
            border:
              "1px solid #2f3545",
            borderRadius:
              "12px",
            padding:
              "28px",
            boxSizing:
              "border-box",
            boxShadow:
              "0 20px 50px rgba(0,0,0,0.4)",
          }}
        >
          <h2
            style={{
              marginTop:
                0,
              marginBottom:
                "8px",
              textAlign:
                "center",
            }}
          >
            Sign in
          </h2>

          <p
            style={{
              color:
                "#94a3b8",
              fontSize:
                "13px",
              marginBottom:
                "20px",
              textAlign:
                "center",
            }}
          >
            Login to access
            blockchain
            tracing.
          </p>

          <form
            onSubmit={
              handleLogin
            }
          >
            <label
              style={
                labelStyle
              }
            >
              Email
            </label>

            <input
              type="email"
              value={
                email
              }
              onChange={(
                event,
              ) =>
                setEmail(
                  event.target
                    .value,
                )
              }
              required
              style={
                inputStyle
              }
            />

            <label
              style={
                labelStyle
              }
            >
              Password
            </label>

            <input
              type="password"
              value={
                password
              }
              onChange={(
                event,
              ) =>
                setPassword(
                  event.target
                    .value,
                )
              }
              required
              style={
                inputStyle
              }
            />

            <button
              type="submit"
              disabled={
                loginLoading
              }
              style={
                primaryButtonStyle
              }
            >
              {loginLoading
                ? "Signing in..."
                : "Sign In"}
            </button>
          </form>
        </section>
      )}

      {/* =====================
          LEFT SIDEBAR
      ===================== */}

      {token && (
        <section
          style={{
            position:
              "absolute",
            zIndex: 20,
            top: "86px",
            left: "20px",
            width: "390px",
            maxHeight:
              "calc(100vh - 106px)",
            overflowY:
              "auto",
            background:
              "#171a23",
            border:
              "1px solid #2f3545",
            borderRadius:
              "10px",
            padding:
              "16px",
            boxSizing:
              "border-box",
            boxShadow:
              "0 10px 30px rgba(0,0,0,0.35)",
          }}
        >
          {/* ===================
              CASE MANAGEMENT
          =================== */}

          <div
            style={{
              paddingBottom:
                "14px",
              borderBottom:
                "1px solid #2f3545",
            }}
          >
            <div
              style={{
                display:
                  "flex",
                justifyContent:
                  "space-between",
                alignItems:
                  "center",
              }}
            >
              <h3
                style={{
                  margin: 0,
                  fontSize:
                    "18px",
                }}
              >
                Cases
              </h3>

              <button
                onClick={() =>
                  setShowCreateCase(
                    (current) =>
                      !current,
                  )
                }
                style={{
                  background:
                    "#2563eb",
                  color:
                    "#ffffff",
                  border:
                    "none",
                  borderRadius:
                    "5px",
                  padding:
                    "6px 10px",
                  cursor:
                    "pointer",
                  fontSize:
                    "11px",
                  fontWeight:
                    600,
                }}
              >
                + New Case
              </button>
            </div>

            {/* CREATE CASE */}

            {showCreateCase && (
              <form
                onSubmit={
                  handleCreateCase
                }
                style={{
                  marginTop:
                    "12px",
                  padding:
                    "12px",
                  background:
                    "#0f1117",
                  border:
                    "1px solid #3b4254",
                  borderRadius:
                    "7px",
                }}
              >
                <label
                  style={
                    labelStyle
                  }
                >
                  Case Title
                </label>

                <input
                  value={
                    newCaseTitle
                  }
                  onChange={(
                    event,
                  ) =>
                    setNewCaseTitle(
                      event.target
                        .value,
                    )
                  }
                  placeholder="Enter case title"
                  required
                  style={
                    inputStyle
                  }
                />

                <label
                  style={
                    labelStyle
                  }
                >
                  Description
                </label>

                <textarea
                  value={
                    newCaseDescription
                  }
                  onChange={(
                    event,
                  ) =>
                    setNewCaseDescription(
                      event.target
                        .value,
                    )
                  }
                  placeholder="Enter case description"
                  rows={3}
                  style={{
                    ...inputStyle,
                    resize:
                      "vertical",
                  }}
                />

                <button
                  type="submit"
                  disabled={
                    caseLoading
                  }
                  style={
                    primaryButtonStyle
                  }
                >
                  {caseLoading
                    ? "Creating..."
                    : "Create Case"}
                </button>
              </form>
            )}

            {/* CASE LIST */}

            <div
              style={{
                marginTop:
                  "12px",
              }}
            >
              {cases.length ===
              0 ? (
                <div
                  style={{
                    padding:
                      "14px",
                    textAlign:
                      "center",
                    color:
                      "#94a3b8",
                    fontSize:
                      "12px",
                    border:
                      "1px dashed #3b4254",
                    borderRadius:
                      "6px",
                  }}
                >
                  No cases yet.
                  Create your
                  first
                  investigation
                  case.
                </div>
              ) : (
                cases.map(
                  (item) => {
                    const isSelected =
                      selectedCase?.id ===
                      item.id;

                    return (
                      <div
                        key={
                          item.id
                        }
                        style={{
                          padding:
                            "10px",
                          marginBottom:
                            "7px",
                          background:
                            isSelected
                              ? "#202a3d"
                              : "#0f1117",
                          border:
                            isSelected
                              ? "1px solid #2563eb"
                              : "1px solid #3b4254",
                          borderRadius:
                            "7px",
                          cursor:
                            "pointer",
                        }}
                        onClick={() => {
                          setSelectedCase(
                            item,
                          );

                          setTrace(
                            null,
                          );

                          setRisk(
                            null,
                          );

                          setNodes(
                            [],
                          );

                          setEdges(
                            [],
                          );

                          setSelectedWallet(
                            null,
                          );

                          setSelectedTransfer(
                            null,
                          );

                          setSelectedWalletId(
                            null,
                          );
                        }}
                      >
                        <div
                          style={{
                            display:
                              "flex",
                            justifyContent:
                              "space-between",
                            gap:
                              "8px",
                          }}
                        >
                          <strong
                            style={{
                              fontSize:
                                "12px",
                            }}
                          >
                            {
                              item.title
                            }
                          </strong>

                          <span
                            style={{
                              fontSize:
                                "9px",
                              textTransform:
                                "uppercase",
                              color:
                                item.status ===
                                "open"
                                  ? "#4ade80"
                                  : "#94a3b8",
                            }}
                          >
                            {
                              item.status
                            }
                          </span>
                        </div>

                        {item.description && (
                          <div
                            style={{
                              marginTop:
                                "5px",
                              color:
                                "#94a3b8",
                              fontSize:
                                "10px",
                              lineHeight:
                                1.4,
                            }}
                          >
                            {
                              item.description
                            }
                          </div>
                        )}

                        {isSelected && (
                          <button
                            onClick={(
                              event,
                            ) => {
                              event.stopPropagation();

                              handleDeleteCase(
                                item.id,
                              );
                            }}
                            disabled={
                              caseLoading
                            }
                            style={{
                              marginTop:
                                "8px",
                              background:
                                "#3f1720",
                              color:
                                "#fecaca",
                              border:
                                "1px solid #ef4444",
                              borderRadius:
                                "5px",
                              padding:
                                "5px 8px",
                              cursor:
                                "pointer",
                              fontSize:
                                "10px",
                            }}
                          >
                            Delete Case
                          </button>
                        )}
                      </div>
                    );
                  },
                )
              )}
            </div>
          </div>

          {/* ===================
              ACTIVE CASE
          =================== */}

          {selectedCase && (
            <div
              style={{
                padding:
                  "14px 0",
                borderBottom:
                  "1px solid #2f3545",
              }}
            >
              <div
                style={{
                  fontSize:
                    "10px",
                  color:
                    "#94a3b8",
                  textTransform:
                    "uppercase",
                }}
              >
                Active Case
              </div>

              <div
                style={{
                  marginTop:
                    "4px",
                  fontSize:
                    "15px",
                  fontWeight:
                    700,
                }}
              >
                {
                  selectedCase.title
                }
              </div>

              <div
                style={{
                  marginTop:
                    "5px",
                  fontSize:
                    "11px",
                  color:
                    "#94a3b8",
                }}
              >
                Case #
                {
                  selectedCase.id
                }
                {" • "}
                {
                  selectedCase.status
                }
              </div>
            </div>
          )}

          {/* ===================
              CASE WALLETS
          =================== */}

          {selectedCase && (
            <div
              style={{
                padding:
                  "14px 0",
                borderBottom:
                  "1px solid #2f3545",
              }}
            >
              <div
                style={{
                  display:
                    "flex",
                  justifyContent:
                    "space-between",
                  alignItems:
                    "center",
                }}
              >
                <h3
                  style={{
                    margin: 0,
                    fontSize:
                      "16px",
                  }}
                >
                  Case Wallets
                </h3>

                <button
                  type="button"
                  onClick={() =>
                    setShowAddWallet(
                      (current) =>
                        !current,
                    )
                  }
                  style={{
                    background:
                      "#2563eb",
                    color:
                      "#ffffff",
                    border:
                      "none",
                    borderRadius:
                      "5px",
                    padding:
                      "6px 9px",
                    cursor:
                      "pointer",
                    fontSize:
                      "11px",
                    fontWeight:
                      600,
                  }}
                >
                  + Add Wallet
                </button>
              </div>

              {/* ADD WALLET FORM */}

              {showAddWallet && (
                <form
                  onSubmit={
                    handleAddWallet
                  }
                  style={{
                    marginTop:
                      "12px",
                    padding:
                      "12px",
                    background:
                      "#0f1117",
                    border:
                      "1px solid #3b4254",
                    borderRadius:
                      "7px",
                  }}
                >
                  <label
                    style={
                      labelStyle
                    }
                  >
                    Wallet Address
                  </label>

                  <input
                    value={
                      newWalletAddress
                    }
                    onChange={(
                      event,
                    ) =>
                      setNewWalletAddress(
                        event.target
                          .value,
                      )
                    }
                    placeholder="0x..."
                    required
                    style={
                      inputStyle
                    }
                  />

                  <label
                    style={
                      labelStyle
                    }
                  >
                    Chain
                  </label>

                  <select
                    value={
                      newWalletChain
                    }
                    onChange={(
                      event,
                    ) =>
                      setNewWalletChain(
                        event.target
                          .value,
                      )
                    }
                    style={
                      inputStyle
                    }
                  >
                    <option value="ethereum">
                      Ethereum
                    </option>

                    <option value="polygon">
                      Polygon
                    </option>

                    <option value="arbitrum">
                      Arbitrum
                    </option>

                    <option value="optimism">
                      Optimism
                    </option>

                    <option value="base">
                      Base
                    </option>
                  </select>

                  <label
                    style={
                      labelStyle
                    }
                  >
                    Label
                  </label>

                  <input
                    value={
                      newWalletLabel
                    }
                    onChange={(
                      event,
                    ) =>
                      setNewWalletLabel(
                        event.target
                          .value,
                      )
                    }
                    placeholder="e.g. Suspected wallet"
                    style={
                      inputStyle
                    }
                  />

                  <button
                    type="submit"
                    disabled={
                      caseLoading
                    }
                    style={
                      primaryButtonStyle
                    }
                  >
                    {caseLoading
                      ? "Adding..."
                      : "Add Wallet"}
                  </button>
                </form>
              )}

              {/* WALLET LIST */}

              <div
                style={{
                  marginTop:
                    "12px",
                }}
              >
                {wallets.length ===
                0 ? (
                  <div
                    style={{
                      padding:
                        "12px",
                      textAlign:
                        "center",
                      color:
                        "#94a3b8",
                      fontSize:
                        "11px",
                      border:
                        "1px dashed #3b4254",
                      borderRadius:
                        "6px",
                    }}
                  >
                    No wallets
                    saved in
                    this case.
                  </div>
                ) : (
                  wallets.map(
                    (wallet) => {
                      const selected =
                        selectedWalletId ===
                        wallet.id;

                      return (
                        <div
                          key={
                            wallet.id
                          }
                          onClick={() => {
                            setSelectedWalletId(
                              wallet.id,
                            );

                            setAddress(
                              wallet.address,
                            );

                            setChain(
                              wallet.chain,
                            );

                            setTrace(
                              null,
                            );

                            setRisk(
                              null,
                            );

                            setNodes(
                              [],
                            );

                            setEdges(
                              [],
                            );

                            setSelectedWallet(
                              null,
                            );

                            setSelectedTransfer(
                              null,
                            );
                          }}
                          style={{
                            padding:
                              "10px",
                            marginBottom:
                              "7px",
                            background:
                              selected
                                ? "#202a3d"
                                : "#0f1117",
                            border:
                              selected
                                ? "1px solid #2563eb"
                                : "1px solid #3b4254",
                            borderRadius:
                              "6px",
                            cursor:
                              "pointer",
                          }}
                        >
                          <div
                            style={{
                              display:
                                "flex",
                              justifyContent:
                                "space-between",
                              alignItems:
                                "center",
                              gap:
                                "8px",
                            }}
                          >
                            <strong
                              style={{
                                fontSize:
                                  "11px",
                              }}
                            >
                              {
                                wallet.label ||
                                "Unnamed Wallet"
                              }
                            </strong>

                            <button
                              type="button"
                              onClick={(
                                event,
                              ) => {
                                event.stopPropagation();

                                handleDeleteWallet(
                                  wallet.id,
                                );
                              }}
                              disabled={
                                caseLoading
                              }
                              style={{
                                background:
                                  "#3f1720",
                                color:
                                  "#fecaca",
                                border:
                                  "1px solid #ef4444",
                                borderRadius:
                                  "4px",
                                padding:
                                  "3px 6px",
                                cursor:
                                  "pointer",
                                fontSize:
                                  "9px",
                              }}
                            >
                              Delete
                            </button>
                          </div>

                          <div
                            style={{
                              marginTop:
                                "5px",
                              color:
                                "#cbd5e1",
                              fontSize:
                                "10px",
                              wordBreak:
                                "break-all",
                            }}
                          >
                            {
                              shortenAddress(
                                wallet.address,
                              )
                            }
                          </div>

                          <div
                            style={{
                              marginTop:
                                "3px",
                              color:
                                "#64748b",
                              fontSize:
                                "9px",
                              textTransform:
                                "uppercase",
                            }}
                          >
                            {
                              wallet.chain
                            }
                          </div>
                        </div>
                      );
                    },
                  )
                )}
              </div>
            </div>
          )}

          {/* ===================
              WALLET TRACING
          =================== */}

          {selectedCase && (
            <>
              <h3
                style={{
                  margin:
                    "16px 0 14px",
                  fontSize:
                    "18px",
                  textAlign:
                    "center",
                }}
              >
                Wallet Tracing
              </h3>

              <form
                onSubmit={
                  handleTrace
                }
              >
                <label
                  style={
                    labelStyle
                  }
                >
                  Wallet Address
                </label>

                <input
                  value={
                    address
                  }
                  onChange={(
                    event,
                  ) =>
                    setAddress(
                      event.target
                        .value,
                    )
                  }
                  style={
                    inputStyle
                  }
                  placeholder="0x..."
                  required
                />

                <label
                  style={
                    labelStyle
                  }
                >
                  Chain
                </label>

                <select
                  value={
                    chain
                  }
                  onChange={(
                    event,
                  ) =>
                    setChain(
                      event.target
                        .value,
                    )
                  }
                  style={
                    inputStyle
                  }
                >
                  <option value="ethereum">
                    Ethereum
                  </option>

                  <option value="polygon">
                    Polygon
                  </option>

                  <option value="arbitrum">
                    Arbitrum
                  </option>

                  <option value="optimism">
                    Optimism
                  </option>

                  <option value="base">
                    Base
                  </option>
                </select>

                <label
                  style={
                    labelStyle
                  }
                >
                  Direction
                </label>

                <select
                  value={
                    direction
                  }
                  onChange={(
                    event,
                  ) =>
                    setDirection(
                      event.target
                        .value,
                    )
                  }
                  style={
                    inputStyle
                  }
                >
                  <option value="both">
                    Both
                  </option>

                  <option value="outgoing">
                    Outgoing
                  </option>

                  <option value="incoming">
                    Incoming
                  </option>
                </select>

                <label
                  style={
                    labelStyle
                  }
                >
                  Max Hops
                </label>

                <select
                  value={
                    maxHops
                  }
                  onChange={(
                    event,
                  ) =>
                    setMaxHops(
                      event.target
                        .value,
                    )
                  }
                  style={
                    inputStyle
                  }
                >
                  <option value="1">
                    1 Hop
                  </option>

                  <option value="2">
                    2 Hops
                  </option>
                </select>

                <button
                  type="submit"
                  disabled={
                    traceLoading
                  }
                  style={
                    primaryButtonStyle
                  }
                >
                  {traceLoading
                    ? "Tracing..."
                    : "Trace Wallet"}
                </button>
              </form>

              {/* TRACE SUMMARY */}

              {trace && (
                <div
                  style={{
                    marginTop:
                      "14px",
                    paddingTop:
                      "12px",
                    borderTop:
                      "1px solid #2f3545",
                    fontSize:
                      "12px",
                    color:
                      "#cbd5e1",
                    lineHeight:
                      1.8,
                  }}
                >
                  <div>
                    <strong>
                      Traces:
                    </strong>{" "}
                    {
                      trace.trace_count
                    }
                  </div>

                  <div>
                    <strong>
                      Chain:
                    </strong>{" "}
                    {
                      trace.chain
                    }
                  </div>

                  <div>
                    <strong>
                      Direction:
                    </strong>{" "}
                    {
                      trace.direction
                    }
                  </div>

                  <div>
                    <strong>
                      Max hops:
                    </strong>{" "}
                    {
                      trace.max_hops
                    }
                  </div>

                  <div>
                    <strong>
                      Wallets:
                    </strong>{" "}
                    {
                      nodes.length
                    }
                  </div>

                  <div>
                    <strong>
                      Connections:
                    </strong>{" "}
                    {
                      edges.length
                    }
                  </div>
                </div>
              )}

              {/* RISK BUTTON */}

              <button
                type="button"
                onClick={
                  handleRiskAnalysis
                }
                disabled={
                  riskLoading
                }
                style={
                  riskButtonStyle
                }
              >
                {riskLoading
                  ? "Analyzing Risk..."
                  : "Analyze Risk"}
              </button>

              {/* RISK DASHBOARD */}

              {risk && (
                <RiskDashboard
                  risk={risk}
                />
              )}
            </>
          )}
        </section>
      )}

      {/* =====================
          INVESTIGATION PANEL
      ===================== */}

      {(selectedWallet ||
        selectedTransfer) && (
        <section
          style={{
            position:
              "absolute",
            zIndex: 40,
            top: "86px",
            right: "20px",
            width: "360px",
            maxHeight:
              "calc(100vh - 106px)",
            overflowY:
              "auto",
            background:
              "#171a23",
            border:
              "1px solid #3b4254",
            borderRadius:
              "10px",
            padding:
              "18px",
            boxSizing:
              "border-box",
            boxShadow:
              "0 15px 40px rgba(0,0,0,0.45)",
          }}
        >
          <div
            style={{
              display:
                "flex",
              alignItems:
                "center",
              justifyContent:
                "space-between",
              marginBottom:
                "14px",
            }}
          >
            <h3
              style={{
                margin: 0,
                fontSize:
                  "18px",
              }}
            >
              Investigation
            </h3>

            <button
              onClick={
                closeInvestigationPanel
              }
              style={{
                background:
                  "#272d3a",
                color:
                  "#ffffff",
                border:
                  "1px solid #475569",
                borderRadius:
                  "5px",
                padding:
                  "5px 9px",
                cursor:
                  "pointer",
              }}
            >
              ✕
            </button>
          </div>

          {/* WALLET DETAILS */}

          {selectedWallet && (
            <>
              <div
                style={
                  panelSectionStyle
                }
              >
                <div
                  style={
                    sectionTitleStyle
                  }
                >
                  Wallet
                </div>

                <div
                  style={{
                    marginTop:
                      "8px",
                    padding:
                      "10px",
                    background:
                      "#0f1117",
                    border:
                      "1px solid #3b4254",
                    borderRadius:
                      "6px",
                    wordBreak:
                      "break-all",
                    fontSize:
                      "12px",
                    lineHeight:
                      1.6,
                  }}
                >
                  {
                    selectedWallet
                  }
                </div>
              </div>

              <div
                style={
                  panelSectionStyle
                }
              >
                <div
                  style={
                    detailRowStyle
                  }
                >
                  <span>
                    Chain
                  </span>

                  <strong>
                    {trace?.chain ??
                      chain}
                  </strong>
                </div>

                <div
                  style={
                    detailRowStyle
                  }
                >
                  <span>
                    Target
                  </span>

                  <strong>
                    {selectedWallet.toLowerCase() ===
                    address.toLowerCase()
                      ? "Yes"
                      : "No"}
                  </strong>
                </div>

                <div
                  style={
                    detailRowStyle
                  }
                >
                  <span>
                    Transactions
                  </span>

                  <strong>
                    {
                      selectedWalletTransactions.length
                    }
                  </strong>
                </div>
              </div>

              {/* RELATED TRANSFERS */}

              <div
                style={
                  panelSectionStyle
                }
              >
                <div
                  style={
                    sectionTitleStyle
                  }
                >
                  Related
                  Transfers
                </div>

                {selectedWalletTransactions.length ===
                0 ? (
                  <p
                    style={{
                      fontSize:
                        "12px",
                      color:
                        "#94a3b8",
                    }}
                  >
                    No transfer
                    details
                    found for
                    this wallet
                    in the
                    current
                    trace.
                  </p>
                ) : (
                  selectedWalletTransactions.map(
                    (
                      item,
                      index,
                    ) => (
                      <div
                        key={`${item.transfer.transaction_hash}-${index}`}
                        style={{
                          marginTop:
                            "8px",
                          padding:
                            "10px",
                          background:
                            "#0f1117",
                          border:
                            "1px solid #3b4254",
                          borderRadius:
                            "6px",
                          fontSize:
                            "11px",
                          lineHeight:
                            1.6,
                        }}
                      >
                        <div>
                          <strong>
                            Direction:
                          </strong>{" "}
                          {item.source.toLowerCase() ===
                          selectedWallet.toLowerCase()
                            ? "Outgoing"
                            : "Incoming"}
                        </div>

                        <div
                          style={{
                            marginTop:
                              "4px",
                            wordBreak:
                              "break-all",
                          }}
                        >
                          <strong>
                            Transaction:
                          </strong>{" "}
                          {
                            item
                              .transfer
                              .transaction_hash
                          }
                        </div>

                        <div>
                          <strong>
                            Asset:
                          </strong>{" "}
                          {item
                            .transfer
                            .asset ??
                            "Unknown"}
                        </div>

                        <div>
                          <strong>
                            Value:
                          </strong>{" "}
                          {item
                            .transfer
                            .value !==
                          null
                            ? formatNumber(
                                item
                                  .transfer
                                  .value,
                              )
                            : "Unknown"}
                        </div>

                        <div>
                          <strong>
                            Hop:
                          </strong>{" "}
                          {
                            item.hop_count
                          }
                        </div>
                      </div>
                    ),
                  )
                )}
              </div>
            </>
          )}

          {/* TRANSACTION DETAILS */}

          {selectedTransfer && (
            <>
              <div
                style={
                  panelSectionStyle
                }
              >
                <div
                  style={
                    sectionTitleStyle
                  }
                >
                  Transaction
                </div>

                <div
                  style={{
                    marginTop:
                      "8px",
                    padding:
                      "10px",
                    background:
                      "#0f1117",
                    border:
                      "1px solid #3b4254",
                    borderRadius:
                      "6px",
                    wordBreak:
                      "break-all",
                    fontSize:
                      "11px",
                  }}
                >
                  {
                    selectedTransfer
                      .transfer
                      .transaction_hash
                  }
                </div>
              </div>

              <div
                style={
                  panelSectionStyle
                }
              >
                <div
                  style={
                    detailRowStyle
                  }
                >
                  <span>
                    From
                  </span>

                  <strong
                    style={{
                      maxWidth:
                        "210px",
                      wordBreak:
                        "break-all",
                      textAlign:
                        "right",
                      fontSize:
                        "10px",
                    }}
                  >
                    {
                      selectedTransfer.source
                    }
                  </strong>
                </div>

                <div
                  style={
                    detailRowStyle
                  }
                >
                  <span>
                    To
                  </span>

                  <strong
                    style={{
                      maxWidth:
                        "210px",
                      wordBreak:
                        "break-all",
                      textAlign:
                        "right",
                      fontSize:
                        "10px",
                    }}
                  >
                    {
                      selectedTransfer.target
                    }
                  </strong>
                </div>

                <div
                  style={
                    detailRowStyle
                  }
                >
                  <span>
                    Asset
                  </span>

                  <strong>
                    {
                      selectedTransfer
                        .transfer
                        .asset ??
                      "Unknown"
                    }
                  </strong>
                </div>

                <div
                  style={
                    detailRowStyle
                  }
                >
                  <span>
                    Value
                  </span>

                  <strong>
                    {
                      selectedTransfer
                        .transfer
                        .value !==
                      null
                        ? formatNumber(
                            selectedTransfer
                              .transfer
                              .value,
                          )
                        : "Unknown"
                    }
                  </strong>
                </div>

                <div
                  style={
                    detailRowStyle
                  }
                >
                  <span>
                    Category
                  </span>

                  <strong>
                    {
                      selectedTransfer
                        .transfer
                        .category ??
                      "Unknown"
                    }
                  </strong>
                </div>

                <div
                  style={
                    detailRowStyle
                  }
                >
                  <span>
                    Block
                  </span>

                  <strong>
                    {
                      selectedTransfer
                        .transfer
                        .block_number ??
                      "Unknown"
                    }
                  </strong>
                </div>

                <div
                  style={
                    detailRowStyle
                  }
                >
                  <span>
                    Hop
                  </span>

                  <strong>
                    {
                      selectedTransfer.hop_count
                    }
                  </strong>
                </div>
              </div>

              <div
                style={
                  panelSectionStyle
                }
              >
                <div
                  style={
                    sectionTitleStyle
                  }
                >
                  Timestamp
                </div>

                <div
                  style={{
                    marginTop:
                      "7px",
                    fontSize:
                      "11px",
                    color:
                      "#cbd5e1",
                  }}
                >
                  {
                    selectedTransfer
                      .transfer
                      .timestamp ??
                    "Unknown"
                  }
                </div>
              </div>

              <div
                style={
                  panelSectionStyle
                }
              >
                <div
                  style={
                    sectionTitleStyle
                  }
                >
                  Contract
                  Address
                </div>

                <div
                  style={{
                    marginTop:
                      "7px",
                    fontSize:
                      "10px",
                    color:
                      "#94a3b8",
                    wordBreak:
                      "break-all",
                  }}
                >
                  {
                    selectedTransfer
                      .transfer
                      .contract_address ??
                    "Native transfer / Unknown"
                  }
                </div>
              </div>
            </>
          )}
        </section>
      )}

      {/* =====================
          ERROR
      ===================== */}

      {error && (
        <div
          style={{
            position:
              "absolute",
            zIndex: 200,
            bottom: "20px",
            left: "20px",
            right: "20px",
            padding:
              "12px 16px",
            background:
              "#3f1720",
            border:
              "1px solid #ef4444",
            borderRadius:
              "8px",
            color:
              "#fecaca",
            fontSize:
              "13px",
          }}
        >
          {error}
        </div>
      )}

      {/* =====================
          GRAPH
      ===================== */}

      <div
        style={{
          width: "100%",
          height:
            "calc(100vh - 70px)",
        }}
      >
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          minZoom={0.2}
          maxZoom={2}
          onNodeClick={
            handleNodeClick
          }
          onEdgeClick={
            handleEdgeClick
          }
          onPaneClick={
            closeInvestigationPanel
          }
        >
          <Background />

          <Controls />

          <MiniMap
            nodeColor={(node) => {
              const label =
                String(
                  node.data?.label ??
                    "",
                );

              return label.startsWith(
                "TARGET",
              )
                ? "#ef4444"
                : "#64748b";
            }}
          />
        </ReactFlow>
      </div>
    </main>
  );
}

/* =========================
   RISK DASHBOARD
========================= */

function RiskDashboard({
  risk,
}: {
  risk: RiskResponse;
}) {
  return (
    <div
      style={{
        marginTop:
          "16px",
        paddingTop:
          "16px",
        borderTop:
          "1px solid #2f3545",
      }}
    >
      <h3
        style={{
          margin:
            "0 0 12px 0",
          fontSize:
            "18px",
        }}
      >
        Risk Analysis
      </h3>

      <div
        style={{
          display:
            "grid",
          gridTemplateColumns:
            "1fr 1fr",
          gap: "8px",
        }}
      >
        <div
          style={
            statCardStyle
          }
        >
          <div
            style={
              smallTitleStyle
            }
          >
            Risk Score
          </div>

          <div
            style={{
              fontSize:
                "26px",
              fontWeight:
                700,
              marginTop:
                "4px",
            }}
          >
            {
              risk.risk_score
            }

            <span
              style={{
                fontSize:
                  "12px",
                color:
                  "#94a3b8",
              }}
            >
              /100
            </span>
          </div>
        </div>

        <div
          style={
            statCardStyle
          }
        >
          <div
            style={
              smallTitleStyle
            }
          >
            Risk Level
          </div>

          <div
            style={{
              fontSize:
                "16px",
              fontWeight:
                700,
              marginTop:
                "8px",
              textTransform:
                "uppercase",
              color:
                riskLevelColor(
                  risk.risk_level,
                ),
            }}
          >
            {
              risk.risk_level
            }
          </div>
        </div>
      </div>

      <div
        style={{
          display:
            "grid",
          gridTemplateColumns:
            "1fr 1fr 1fr",
          gap: "6px",
          marginTop:
            "8px",
        }}
      >
        <div
          style={
            miniStatStyle
          }
        >
          <span>
            Indicators
          </span>

          <strong>
            {
              risk.indicator_count
            }
          </strong>
        </div>

        <div
          style={
            miniStatStyle
          }
        >
          <span>
            Exposures
          </span>

          <strong>
            {
              risk.exposure_count
            }
          </strong>
        </div>

        <div
          style={
            miniStatStyle
          }
        >
          <span>
            Critical
          </span>

          <strong>
            {
              risk.severity_counts
                .critical
            }
          </strong>
        </div>
      </div>

      <div
        style={{
          marginTop:
            "12px",
          padding:
            "10px",
          background:
            "#0f1117",
          border:
            "1px solid #3b4254",
          borderRadius:
            "6px",
          fontSize:
            "12px",
        }}
      >
        <div
          style={
            smallTitleStyle
          }
        >
          Severity
          Distribution
        </div>

        <div
          style={{
            display:
              "grid",
            gridTemplateColumns:
              "1fr 1fr",
            gap: "6px",
            marginTop:
              "8px",
          }}
        >
          <div>
            Low:{" "}
            {
              risk.severity_counts
                .low
            }
          </div>

          <div>
            Medium:{" "}
            {
              risk.severity_counts
                .medium
            }
          </div>

          <div>
            High:{" "}
            {
              risk.severity_counts
                .high
            }
          </div>

          <div>
            Critical:{" "}
            {
              risk.severity_counts
                .critical
            }
          </div>
        </div>
      </div>

      {risk.behavior && (
        <div
          style={{
            marginTop:
              "14px",
          }}
        >
          <h4
            style={{
              margin:
                "0 0 8px 0",
            }}
          >
            Wallet
            Behavior
          </h4>

          <div
            style={{
              display:
                "grid",
              gridTemplateColumns:
                "1fr 1fr",
              gap: "6px",
            }}
          >
            <div
              style={
                behaviorCardStyle
              }
            >
              <span>
                Connections
              </span>

              <strong>
                {
                  risk.behavior
                    .total_connections
                }
              </strong>
            </div>

            <div
              style={
                behaviorCardStyle
              }
            >
              <span>
                Transactions
              </span>

              <strong>
                {
                  risk.behavior
                    .total_transaction_count
                }
              </strong>
            </div>

            <div
              style={
                behaviorCardStyle
              }
            >
              <span>
                Outgoing
              </span>

              <strong>
                {
                  risk.behavior
                    .outgoing_transaction_count
                }
              </strong>
            </div>

            <div
              style={
                behaviorCardStyle
              }
            >
              <span>
                Incoming
              </span>

              <strong>
                {
                  risk.behavior
                    .incoming_transaction_count
                }
              </strong>
            </div>

            <div
              style={
                behaviorCardStyle
              }
            >
              <span>
                Unique Assets
              </span>

              <strong>
                {
                  risk.behavior
                    .unique_assets
                }
              </strong>
            </div>

            <div
              style={
                behaviorCardStyle
              }
            >
              <span>
                Outgoing Value
              </span>

              <strong>
                {risk.behavior.outgoing_value.toLocaleString()}
              </strong>
            </div>
          </div>
        </div>
      )}

      {/* RISK INDICATORS */}

      <div
        style={{
          marginTop:
            "14px",
        }}
      >
        <h4
          style={{
            margin:
              "0 0 8px 0",
          }}
        >
          Risk
          Indicators
        </h4>

        {risk.indicators.map(
          (
            indicator,
            index,
          ) => (
            <div
              key={`${indicator.indicator}-${index}`}
              style={{
                padding:
                  "10px",
                marginBottom:
                  "8px",
                background:
                  "#0f1117",
                border:
                  "1px solid #3b4254",
                borderRadius:
                  "6px",
              }}
            >
              <div
                style={{
                  fontWeight:
                    600,
                  fontSize:
                    "12px",
                }}
              >
                {
                  indicator.indicator
                }
              </div>

              <div
                style={{
                  marginTop:
                    "4px",
                  fontSize:
                    "10px",
                  textTransform:
                    "uppercase",
                  color:
                    riskSeverityColor(
                      indicator.severity,
                    ),
                  fontWeight:
                    700,
                }}
              >
                {
                  indicator.severity
                }
              </div>

              <div
                style={{
                  marginTop:
                    "6px",
                  fontSize:
                    "11px",
                  color:
                    "#cbd5e1",
                  lineHeight:
                    1.5,
                }}
              >
                {
                  indicator.reason
                }
              </div>
            </div>
          ),
        )}
      </div>

      {/* RISK EXPOSURES */}

      {risk.exposures.length >
        0 && (
        <div
          style={{
            marginTop:
              "14px",
          }}
        >
          <h4
            style={{
              margin:
                "0 0 8px 0",
            }}
          >
            Risk
            Exposures
          </h4>

          {risk.exposures.map(
            (
              exposure,
              index,
            ) => (
              <div
                key={`${exposure.risk_entity_address}-${index}`}
                style={{
                  padding:
                    "10px",
                  background:
                    "#0f1117",
                  border:
                    "1px solid #3b4254",
                  borderRadius:
                    "6px",
                  marginBottom:
                    "8px",
                  fontSize:
                    "11px",
                  lineHeight:
                    1.6,
                }}
              >
                <div>
                  <strong>
                    Entity:
                  </strong>{" "}
                  {
                    exposure.entity_name ??
                    exposure.entity_type
                  }
                </div>

                <div>
                  <strong>
                    Type:
                  </strong>{" "}
                  {
                    exposure.entity_type
                  }
                </div>

                <div>
                  <strong>
                    Hop:
                  </strong>{" "}
                  {
                    exposure.hop_count
                  }
                </div>

                {exposure.source && (
                  <div>
                    <strong>
                      Source:
                    </strong>{" "}
                    {
                      exposure.source
                    }
                  </div>
                )}
              </div>
            ),
          )}
        </div>
      )}
    </div>
  );
}

/* =========================
   TRACE HELPERS
========================= */

function findTransferForEdge(
  trace: TraceResponse,
  source: string,
  target: string,
): WalletTransaction | null {
  for (const item of trace.traces) {
    for (
      let i = 0;
      i <
        item.wallets.length -
          1;
      i += 1
    ) {
      const currentSource =
        item.wallets[i];

      const currentTarget =
        item.wallets[i + 1];

      if (
        currentSource.toLowerCase() ===
          source.toLowerCase() &&
        currentTarget.toLowerCase() ===
          target.toLowerCase()
      ) {
        const transfer =
          item.transfers[i];

        if (!transfer) {
          continue;
        }

        return {
          source:
            currentSource,
          target:
            currentTarget,
          transfer,
          hop_count:
            item.hop_count,
        };
      }
    }
  }

  return null;
}

function getWalletTransactions(
  trace: TraceResponse | null,
  wallet: string,
): WalletTransaction[] {
  if (!trace) {
    return [];
  }

  const transactions:
    WalletTransaction[] =
    [];

  trace.traces.forEach(
    (item) => {
      for (
        let i = 0;
        i <
          item.wallets.length -
            1;
        i += 1
      ) {
        const source =
          item.wallets[i];

        const target =
          item.wallets[i + 1];

        const transfer =
          item.transfers[i];

        if (!transfer) {
          continue;
        }

        if (
          source.toLowerCase() ===
            wallet.toLowerCase() ||
          target.toLowerCase() ===
            wallet.toLowerCase()
        ) {
          const alreadyAdded =
            transactions.some(
              (existing) =>
                existing
                  .transfer
                  .transaction_hash ===
                transfer.transaction_hash,
            );

          if (
            !alreadyAdded
          ) {
            transactions.push(
              {
                source,
                target,
                transfer,
                hop_count:
                  item.hop_count,
              },
            );
          }
        }
      }
    },
  );

  return transactions;
}

/* =========================
   GENERAL HELPERS
========================= */

function shortenAddress(
  address: string,
): string {
  if (address.length <= 14) {
    return address;
  }

  return `${address.slice(
    0,
    8,
  )}...${address.slice(-6)}`;
}

function formatNumber(
  value: number,
): string {
  return value.toLocaleString(
    undefined,
    {
      maximumFractionDigits: 6,
    },
  );
}

function riskLevelColor(
  level: RiskResponse["risk_level"],
) {
  switch (level) {
    case "critical":
      return "#f87171";

    case "high":
      return "#fb923c";

    case "moderate":
      return "#facc15";

    case "low":
      return "#4ade80";

    default:
      return "#ffffff";
  }
}

function riskSeverityColor(
  severity: RiskIndicator["severity"],
) {
  switch (severity) {
    case "critical":
      return "#f87171";

    case "high":
      return "#fb923c";

    case "medium":
      return "#facc15";

    case "low":
      return "#4ade80";

    default:
      return "#cbd5e1";
  }
}

/* =========================
   STYLES
========================= */

const inputStyle: React.CSSProperties =
  {
    width: "100%",
    boxSizing:
      "border-box",
    padding: "10px",
    marginBottom:
      "4px",
    background:
      "#0f1117",
    color:
      "#ffffff",
    border:
      "1px solid #3b4254",
    borderRadius:
      "6px",
    outline:
      "none",
  };

const labelStyle: React.CSSProperties =
  {
    display:
      "block",
    fontSize:
      "12px",
    color:
      "#cbd5e1",
    marginTop:
      "10px",
    marginBottom:
      "5px",
  };

const primaryButtonStyle: React.CSSProperties =
  {
    width: "100%",
    marginTop:
      "16px",
    padding:
      "10px",
    background:
      "#2563eb",
    color:
      "#ffffff",
    border:
      "none",
    borderRadius:
      "6px",
    cursor:
      "pointer",
    fontWeight:
      600,
  };

const riskButtonStyle: React.CSSProperties =
  {
    width: "100%",
    marginTop:
      "10px",
    padding:
      "10px",
    background:
      "#7c3aed",
    color:
      "#ffffff",
    border:
      "none",
    borderRadius:
      "6px",
    cursor:
      "pointer",
    fontWeight:
      600,
  };

const statCardStyle: React.CSSProperties =
  {
    padding:
      "12px",
    background:
      "#0f1117",
    borderRadius:
      "6px",
    border:
      "1px solid #3b4254",
  };

const miniStatStyle: React.CSSProperties =
  {
    padding:
      "8px",
    background:
      "#0f1117",
    borderRadius:
      "6px",
    border:
      "1px solid #3b4254",
    display:
      "flex",
    flexDirection:
      "column",
    gap:
      "3px",
    fontSize:
      "10px",
    color:
      "#94a3b8",
  };

const behaviorCardStyle: React.CSSProperties =
  {
    padding:
      "8px",
    background:
      "#0f1117",
    border:
      "1px solid #3b4254",
    borderRadius:
      "6px",
    display:
      "flex",
    flexDirection:
      "column",
    gap:
      "3px",
    fontSize:
      "10px",
    color:
      "#94a3b8",
  };

const smallTitleStyle: React.CSSProperties =
  {
    fontSize:
      "11px",
    color:
      "#94a3b8",
  };

const panelSectionStyle: React.CSSProperties =
  {
    marginTop:
      "14px",
    paddingTop:
      "12px",
    borderTop:
      "1px solid #2f3545",
  };

const sectionTitleStyle: React.CSSProperties =
  {
    fontSize:
      "12px",
    fontWeight:
      700,
    color:
      "#ffffff",
  };

const detailRowStyle: React.CSSProperties =
  {
    display:
      "flex",
    justifyContent:
      "space-between",
    gap:
      "12px",
    padding:
      "7px 0",
    fontSize:
      "11px",
    color:
      "#cbd5e1",
  };

export default App;