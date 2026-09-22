import { useEffect, useState } from "react";
import type { FormEvent, MouseEvent } from "react";

import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  applyNodeChanges,
  type Edge,
  type Node,
  type NodeChange,
  type ReactFlowInstance,
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

type GraphCounterparty = {
  address: string;
  chain: string;
  transaction_count: number;
  total_value: number;
};

type GraphRiskPath = {
  risk_entity_address: string;
  risk_entity_chain: string;
  entity_type: string;
  entity_name: string | null;
  hop_count: number;
  wallets: string[];
  transfers: TraceTransfer[];
};

type GraphSignal = {
  signal?: string;
  severity?: string;
  reason?: string;
  evidence?: Record<string, unknown>;
  [key: string]: unknown;
};

type GraphAnalyticsResponse = {
  address: string;
  chain: string;
  outgoing_connections: number;
  incoming_connections: number;
  outgoing_transaction_count: number;
  incoming_transaction_count: number;
  outgoing_value: number;
  incoming_value: number;
  fan_out: number;
  fan_in: number;
  top_outgoing_counterparties: GraphCounterparty[];
  top_incoming_counterparties: GraphCounterparty[];
  outgoing_concentration: number;
  incoming_concentration: number;
  multi_hop_risk_paths: GraphRiskPath[];
  multi_hop_exposure_count: number;
  graph_signals: GraphSignal[];
};

type TimelineTransaction = {
  transaction_hash: string;
  chain: string;
  direction: string;
  counterparty: string;
  asset: string | null;
  value: number;
  block_number: number | null;
  timestamp: string | null;
  contract_address: string | null;
};

type TimelineBurst = {
  start_time: string;
  end_time: string;
  transaction_count: number;
  duration_seconds: number;
};

type TimelineAnalyticsResponse = {
  address: string;
  chain: string;
  first_activity: string | null;
  last_activity: string | null;
  total_transactions: number;
  incoming_transactions: number;
  outgoing_transactions: number;
  incoming_value: number;
  outgoing_value: number;
  total_value: number;
  activity_duration_seconds: number;
  average_transaction_gap_seconds: number | null;
  shortest_transaction_gap_seconds: number | null;
  longest_transaction_gap_seconds: number | null;
  bursts: TimelineBurst[];
  largest_transactions: TimelineTransaction[];
  transactions: TimelineTransaction[];
  temporal_signals: GraphSignal[];
};

type MLRiskResponse = {
  address: string;
  chain: string;
  prediction: number;
  probability: number;
  model_version: string;
  schema_version: string;
  features: Record<string, unknown>;
  status: string;
  notice: string;
};

type AMLSignal = {
  source: string;
  signal: string;
  severity: string;
  reason: string;
  evidence: Record<string, unknown>;
};

type AMLAssessmentResponse = {
  address: string;
  chain: string;
  assessment_type: string;
  review_status: string;
  indicator_count: number;
  high_severity_indicator_count: number;
  medium_severity_indicator_count: number;
  indicators: string[];
  signals: AMLSignal[];
  ml: MLRiskResponse | null;
  notice: string;
};

type VaspCandidate = {
  name: string | null;
  address: string;
  chain: string;
  source: string | null;
  risk_category: string | null;
  confidence: number | null;
  evidence: string | null;
  hop: number | null;
  attribution_basis: string;
  reason: string;
  wallets: string[];
  transfers: TraceTransfer[];
};

type VaspAttributionResponse = {
  case_id: number;
  wallet_id: number;
  wallet_address: string;
  wallet_chain: string;
  address: string;
  chain: string;
  max_hops: number;
  status: string;
  candidate_count: number;
  candidates: VaspCandidate[];
  method: string;
  notice: string;
};

type CaseNote = {
  id: number;
  case_id: number;
  content: string;
  created_by: number;
  created_at: string | null;
  updated_at: string | null;
};

type CaseEvidence = {
  id: number;
  case_id: number;
  created_by: number;
  evidence_type: string;
  title: string;
  description: string | null;
  reference: string | null;
  created_at: string;
  updated_at: string;
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

  const [liveRefresh, setLiveRefresh] =
    useState(true);

  const [trace, setTrace] =
    useState<TraceResponse | null>(null);

  /* =========================
     RISK STATE
  ========================= */

  const [risk, setRisk] =
    useState<RiskResponse | null>(null);

  /* =========================
     WALLET ANALYTICS STATE
  ========================= */

  const [graphAnalytics, setGraphAnalytics] =
    useState<GraphAnalyticsResponse | null>(null);

  const [timelineAnalytics, setTimelineAnalytics] =
    useState<TimelineAnalyticsResponse | null>(null);

  const [analyticsLoading, setAnalyticsLoading] =
    useState(false);

  /* =========================
     ML / AML STATE
  ========================= */

  const [mlRisk, setMlRisk] =
    useState<MLRiskResponse | null>(null);

  const [amlAssessment, setAmlAssessment] =
    useState<AMLAssessmentResponse | null>(null);

  const [mlAmlLoading, setMlAmlLoading] =
    useState(false);

  /* =========================
     VASP ATTRIBUTION STATE
  ========================= */

  const [vaspAttribution, setVaspAttribution] =
    useState<VaspAttributionResponse | null>(null);

  const [vaspLoading, setVaspLoading] =
    useState(false);

  const [vaspLabelName, setVaspLabelName] =
    useState("");

  const [vaspLabelSource, setVaspLabelSource] =
    useState("Etherscan");

  const [vaspLabelConfidence, setVaspLabelConfidence] =
    useState("0.95");

  const [vaspLabelEvidence, setVaspLabelEvidence] =
    useState("");

  const [vaspLabelSaving, setVaspLabelSaving] =
    useState(false);

  /* =========================
     NOTES STATE
  ========================= */

  const [notes, setNotes] =
    useState<CaseNote[]>([]);

  const [notesLoading, setNotesLoading] =
    useState(false);

  const [noteSaving, setNoteSaving] =
    useState(false);

  const [newNoteContent, setNewNoteContent] =
    useState("");

  const [editingNoteId, setEditingNoteId] =
    useState<number | null>(null);

  const [editingNoteContent, setEditingNoteContent] =
    useState("");

  /* =========================
     CASE EVIDENCE STATE
  ========================= */

  const [evidenceItems, setEvidenceItems] =
    useState<CaseEvidence[]>([]);

  const [evidenceLoading, setEvidenceLoading] =
    useState(false);

  const [evidenceSaving, setEvidenceSaving] =
    useState(false);

  const [newEvidenceType, setNewEvidenceType] =
    useState("transaction");

  const [newEvidenceTitle, setNewEvidenceTitle] =
    useState("");

  const [newEvidenceDescription, setNewEvidenceDescription] =
    useState("");

  const [newEvidenceReference, setNewEvidenceReference] =
    useState("");

  const [editingEvidenceId, setEditingEvidenceId] =
    useState<number | null>(null);

  const [editingEvidenceType, setEditingEvidenceType] =
    useState("");

  const [editingEvidenceTitle, setEditingEvidenceTitle] =
    useState("");

  const [editingEvidenceDescription, setEditingEvidenceDescription] =
    useState("");

  const [editingEvidenceReference, setEditingEvidenceReference] =
    useState("");

  /* =========================
     GRAPH STATE
  ========================= */

  const [nodes, setNodes] =
    useState<Node[]>([]);

  const [edges, setEdges] =
    useState<Edge[]>([]);

  /* =========================
     GRAPH FILTER STATE
  ========================= */

  const [transactionSearch, setTransactionSearch] =
    useState("");

  const [assetFilter, setAssetFilter] =
    useState("all");

  const [directionFilter, setDirectionFilter] =
    useState("all");

  const [minValueFilter, setMinValueFilter] =
    useState("");

  const [maxValueFilter, setMaxValueFilter] =
    useState("");

  const [reactFlowInstance, setReactFlowInstance] =
    useState<ReactFlowInstance | null>(null);

  /* =========================
     INVESTIGATION STATE
  ========================= */

  const [selectedWallet, setSelectedWallet] =
    useState<string | null>(null);

  const [selectedTransfer, setSelectedTransfer] =
    useState<WalletTransaction | null>(null);

  const [investigationTab, setInvestigationTab] =
    useState<
      "wallet"
      | "transaction"
      | "analytics"
      | "ml-aml"
      | "vasp"
      | "notes"
      | "evidence"
    >("wallet");

  const [sidebarCollapsed, setSidebarCollapsed] =
    useState(false);

  const [graphFiltersOpen, setGraphFiltersOpen] =
    useState(false);

  /* =========================
     LOADING / ERROR
  ========================= */

  const [loginLoading, setLoginLoading] =
    useState(false);

  const [traceLoading, setTraceLoading] =
    useState(false);

  const [riskLoading, setRiskLoading] =
    useState(false);

  const [reportLoading, setReportLoading] =
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
      setNotes([]);
      return;
    }

    setNotes([]);
    setEvidenceItems([]);
    setEditingEvidenceId(null);
    loadWallets(selectedCase.id);
    void loadNotes(selectedCase.id);
    void loadEvidence(selectedCase.id);
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
     NOTES
  ========================= */

  async function loadNotes(caseId: number) {
    if (!token) return;

    setNotesLoading(true);
    try {
      const response = await fetch(
        `${API_URL}/cases/${caseId}/notes`,
        { headers: { Authorization: `Bearer ${token}` } },
      );

      if (response.status === 401) {
        localStorage.removeItem("access_token");
        setToken(null);
        throw new Error("Session expired. Please login again.");
      }

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || `Notes API returned ${response.status}`);
      }

      const data: CaseNote[] = await response.json();
      setNotes(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load notes");
    } finally {
      setNotesLoading(false);
    }
  }

  async function handleCreateNote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!token || !selectedCase) {
      setError("Please select a case first.");
      return;
    }

    const content = newNoteContent.trim();
    if (!content) {
      setError("Note content is required.");
      return;
    }

    setNoteSaving(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/cases/${selectedCase.id}/notes`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ content }),
        },
      );

      if (response.status === 401) {
        localStorage.removeItem("access_token");
        setToken(null);
        throw new Error("Session expired. Please login again.");
      }

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || `Create note failed with status ${response.status}`);
      }

      const createdNote: CaseNote = await response.json();
      setNotes((current) => [createdNote, ...current]);
      setNewNoteContent("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create note");
    } finally {
      setNoteSaving(false);
    }
  }

  async function handleUpdateNote(noteId: number) {
    if (!token || !selectedCase) {
      setError("Please select a case first.");
      return;
    }

    const content = editingNoteContent.trim();
    if (!content) {
      setError("Note content is required.");
      return;
    }

    setNoteSaving(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/cases/${selectedCase.id}/notes/${noteId}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ content }),
        },
      );

      if (response.status === 401) {
        localStorage.removeItem("access_token");
        setToken(null);
        throw new Error("Session expired. Please login again.");
      }

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || `Update note failed with status ${response.status}`);
      }

      const updatedNote: CaseNote = await response.json();
      setNotes((current) =>
        current.map((note) => note.id === noteId ? updatedNote : note),
      );
      setEditingNoteId(null);
      setEditingNoteContent("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update note");
    } finally {
      setNoteSaving(false);
    }
  }

  async function handleDeleteNote(noteId: number) {
    if (!token || !selectedCase) {
      setError("Please select a case first.");
      return;
    }

    if (!window.confirm("Delete this analyst note? This action cannot be undone.")) {
      return;
    }

    setNoteSaving(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/cases/${selectedCase.id}/notes/${noteId}`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        },
      );

      if (response.status === 401) {
        localStorage.removeItem("access_token");
        setToken(null);
        throw new Error("Session expired. Please login again.");
      }

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || `Delete note failed with status ${response.status}`);
      }

      setNotes((current) => current.filter((note) => note.id !== noteId));
      if (editingNoteId === noteId) {
        setEditingNoteId(null);
        setEditingNoteContent("");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete note");
    } finally {
      setNoteSaving(false);
    }
  }

  function startEditingNote(note: CaseNote) {
    setEditingNoteId(note.id);
    setEditingNoteContent(note.content);
    setError(null);
  }

  function cancelEditingNote() {
    setEditingNoteId(null);
    setEditingNoteContent("");
  }

  /* =========================
     CASE EVIDENCE
  ========================= */

  async function loadEvidence(caseId: number) {
    if (!token) return;

    setEvidenceLoading(true);
    try {
      const response = await fetch(
        `${API_URL}/cases/${caseId}/evidence`,
        { headers: { Authorization: `Bearer ${token}` } },
      );

      if (response.status === 401) {
        localStorage.removeItem("access_token");
        setToken(null);
        throw new Error("Session expired. Please login again.");
      }

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || `Evidence API returned ${response.status}`);
      }

      const data: CaseEvidence[] = await response.json();
      setEvidenceItems(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load evidence");
    } finally {
      setEvidenceLoading(false);
    }
  }

  function resetEvidenceForm() {
    setNewEvidenceType("transaction");
    setNewEvidenceTitle("");
    setNewEvidenceDescription("");
    setNewEvidenceReference("");
  }

  async function handleCreateEvidence(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!token || !selectedCase) {
      setError("Please select a case first.");
      return;
    }

    const evidenceType = newEvidenceType.trim();
    const title = newEvidenceTitle.trim();
    const description = newEvidenceDescription.trim();
    const reference = newEvidenceReference.trim();

    if (!evidenceType) {
      setError("Evidence type is required.");
      return;
    }

    if (!title) {
      setError("Evidence title is required.");
      return;
    }

    setEvidenceSaving(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/cases/${selectedCase.id}/evidence`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            evidence_type: evidenceType,
            title,
            description: description || null,
            reference: reference || null,
          }),
        },
      );

      if (response.status === 401) {
        localStorage.removeItem("access_token");
        setToken(null);
        throw new Error("Session expired. Please login again.");
      }

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || `Create evidence failed with status ${response.status}`);
      }

      const createdEvidence: CaseEvidence = await response.json();
      setEvidenceItems((current) => [...current, createdEvidence]);
      resetEvidenceForm();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create evidence");
    } finally {
      setEvidenceSaving(false);
    }
  }

  function startEditingEvidence(evidence: CaseEvidence) {
    setEditingEvidenceId(evidence.id);
    setEditingEvidenceType(evidence.evidence_type);
    setEditingEvidenceTitle(evidence.title);
    setEditingEvidenceDescription(evidence.description ?? "");
    setEditingEvidenceReference(evidence.reference ?? "");
    setError(null);
  }

  function cancelEditingEvidence() {
    setEditingEvidenceId(null);
    setEditingEvidenceType("");
    setEditingEvidenceTitle("");
    setEditingEvidenceDescription("");
    setEditingEvidenceReference("");
  }

  async function handleUpdateEvidence(evidenceId: number) {
    if (!token || !selectedCase) {
      setError("Please select a case first.");
      return;
    }

    const evidenceType = editingEvidenceType.trim();
    const title = editingEvidenceTitle.trim();
    const description = editingEvidenceDescription.trim();
    const reference = editingEvidenceReference.trim();

    if (!evidenceType) {
      setError("Evidence type is required.");
      return;
    }

    if (!title) {
      setError("Evidence title is required.");
      return;
    }

    setEvidenceSaving(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/cases/${selectedCase.id}/evidence/${evidenceId}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            evidence_type: evidenceType,
            title,
            description,
            reference,
          }),
        },
      );

      if (response.status === 401) {
        localStorage.removeItem("access_token");
        setToken(null);
        throw new Error("Session expired. Please login again.");
      }

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || `Update evidence failed with status ${response.status}`);
      }

      const updatedEvidence: CaseEvidence = await response.json();
      setEvidenceItems((current) =>
        current.map((item) =>
          item.id === evidenceId ? updatedEvidence : item,
        ),
      );
      cancelEditingEvidence();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update evidence");
    } finally {
      setEvidenceSaving(false);
    }
  }

  async function handleDeleteEvidence(evidenceId: number) {
    if (!token || !selectedCase) {
      setError("Please select a case first.");
      return;
    }

    if (!window.confirm("Delete this evidence item? This action cannot be undone.")) {
      return;
    }

    setEvidenceSaving(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/cases/${selectedCase.id}/evidence/${evidenceId}`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        },
      );

      if (response.status === 401) {
        localStorage.removeItem("access_token");
        setToken(null);
        throw new Error("Session expired. Please login again.");
      }

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || `Delete evidence failed with status ${response.status}`);
      }

      setEvidenceItems((current) =>
        current.filter((item) => item.id !== evidenceId),
      );

      if (editingEvidenceId === evidenceId) {
        cancelEditingEvidence();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete evidence");
    } finally {
      setEvidenceSaving(false);
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
    setGraphAnalytics(null);
    setTimelineAnalytics(null);
    setMlRisk(null);
    setAmlAssessment(null);
    setVaspAttribution(null);
    setNotes([]);
    setNewNoteContent("");
    setEditingNoteId(null);
    setEditingNoteContent("");

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
      setGraphAnalytics(null);
      setTimelineAnalytics(null);
      setMlRisk(null);
      setAmlAssessment(null);
      setVaspAttribution(null);
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
     GENERATE INVESTIGATION REPORT
  ========================= */

  async function handleGenerateReport() {
    if (!token) {
      setError("Please login first.");
      return;
    }

    if (!selectedCase) {
      setError("Create or select a case first.");
      return;
    }

    setReportLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/cases/${selectedCase.id}/reports`,
        {
          method: "POST",
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
          message || `Report generation returned ${response.status}`,
        );
      }

      const blob = await response.blob();

      if (blob.size === 0) {
        throw new Error("The generated report was empty.");
      }

      const contentDisposition = response.headers.get(
        "Content-Disposition",
      );

      const filenameMatch = contentDisposition?.match(
        /filename="?([^";]+)"?/i,
      );

      const filename =
        filenameMatch?.[1] ||
        `case_${selectedCase.id}_investigation_report.pdf`;

      const downloadUrl = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = downloadUrl;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to generate investigation report",
      );
    } finally {
      setReportLoading(false);
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
    setGraphAnalytics(null);
    setTimelineAnalytics(null);
    setMlRisk(null);
    setAmlAssessment(null);
    setVaspAttribution(null);
    setSelectedWallet(null);
    setSelectedTransfer(null);

    try {
      const response = await fetch(
        `${API_URL}/wallets/trace/${address}?chain=${chain}&direction=${direction}&max_hops=${maxHops}&refresh_live=${liveRefresh}`,
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

      // Build a graph-aware layout so wallets are separated by hop distance.
      const adjacency = new Map<string, string[]>();

      walletList.forEach((wallet) => {
        adjacency.set(wallet, []);
      });

      data.traces.forEach((item) => {
        for (
          let i = 0;
          i < item.wallets.length - 1;
          i += 1
        ) {
          const source = item.wallets[i];
          const target = item.wallets[i + 1];

          if (
            source.toLowerCase() ===
            target.toLowerCase()
          ) {
            continue;
          }

          adjacency.get(source)?.push(target);
          adjacency.get(target)?.push(source);
        }
      });

      const nodeLevels = new Map<string, number>();
      const layoutQueue: string[] = [data.address];

      nodeLevels.set(data.address, 0);

      let queueIndex = 0;

      while (queueIndex < layoutQueue.length) {
        const current = layoutQueue[queueIndex];
        queueIndex += 1;

        const currentLevel =
          nodeLevels.get(current) ?? 0;

        for (
          const neighbor of adjacency.get(current) ?? []
        ) {
          if (!nodeLevels.has(neighbor)) {
            nodeLevels.set(
              neighbor,
              currentLevel + 1,
            );

            layoutQueue.push(neighbor);
          }
        }
      }

      const fallbackLevel =
        Math.max(
          0,
          ...Array.from(nodeLevels.values()),
        ) + 1;

      walletList.forEach((wallet) => {
        if (!nodeLevels.has(wallet)) {
          nodeLevels.set(wallet, fallbackLevel);
        }
      });

      const nodesByLevel =
        new Map<number, string[]>();

      walletList.forEach((wallet) => {
        const level =
          nodeLevels.get(wallet) ?? 0;

        const levelWallets =
          nodesByLevel.get(level) ?? [];

        levelWallets.push(wallet);
        nodesByLevel.set(level, levelWallets);
      });

      const generatedNodes: Node[] =
        walletList.map((wallet) => {
          const isTarget =
            wallet.toLowerCase() ===
            data.address.toLowerCase();

          const level =
            nodeLevels.get(wallet) ?? 0;

          const levelWallets =
            nodesByLevel.get(level) ?? [];

          const levelIndex =
            levelWallets.indexOf(wallet);

          const verticalSpacing = 300;

          const levelHeight =
            (levelWallets.length - 1) *
            verticalSpacing;

          const y =
            levelIndex *
            verticalSpacing -
            levelHeight / 2;

          return {
            id: wallet,

            position: {
              x: level * 430,
              y,
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

              color: "#ffffff",

              width: 240,

              fontSize: 12,

              lineHeight: 1.5,

              textAlign: "center",

              cursor: "pointer",
            },
          };
        });
      const edgeMap = new Map<string, Edge & {
        connection_count?: number;
      }>();

      data.traces.forEach(
        (item) => {
          for (
            let i = 0;
            i < item.wallets.length - 1;
            i += 1
          ) {
            const source = item.wallets[i];
            const target = item.wallets[i + 1];
            const transfer = item.transfers[i];

            // Ignore self-loop connections.
            if (
              source.toLowerCase() ===
              target.toLowerCase()
            ) {
              continue;
            }

            // Treat A -> B and B -> A as one visual connection.
            const [firstWallet, secondWallet] =
              [source, target].sort();

            const key =
              `${firstWallet}->${secondWallet}`;

            const existing = edgeMap.get(key);

            if (existing) {
              existing.connection_count =
                (existing.connection_count ?? 1) + 1;

              if (existing.data) {
                existing.data = {
                  ...existing.data,
                  connection_count:
                    existing.connection_count,
                };
              }

              continue;
            }

            edgeMap.set(key, {
              id: `connection-${edgeMap.size}`,

              source,
              target,

              type: "default",


              data: {
                transfer,
                hop_count: item.hop_count,
                connection_count: 1,
              },

              label: transfer?.asset
                ? `${transfer.asset} ${
                    transfer.value !== null &&
                    transfer.value !== undefined
                      ? formatNumber(transfer.value)
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

              labelBgBorderRadius: 3,
            });
          }
        },
      );

      const generatedEdges: Edge[] =
        Array.from(edgeMap.values());
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
     LOAD WALLET ANALYTICS
  ========================= */

  async function handleLoadWalletAnalytics() {
    if (!token) {
      setError("Please login first.");
      return;
    }

    if (!selectedCase || !selectedWalletId || !selectedWallet) {
      setError("Select a saved case wallet first.");
      return;
    }

    const wallet = wallets.find(
      (item) => item.id === selectedWalletId,
    );

    if (!wallet || wallet.address.toLowerCase() !== selectedWallet.toLowerCase()) {
      setError("Analytics are available for wallets saved in the selected case.");
      return;
    }

    setAnalyticsLoading(true);
    setError(null);

    try {
      const headers = {
        Authorization: `Bearer ${token}`,
      };

      const [graphResponse, timelineResponse] = await Promise.all([
        fetch(
          `${API_URL}/cases/${selectedCase.id}/wallets/${selectedWalletId}/graph-analytics`,
          { headers },
        ),
        fetch(
          `${API_URL}/cases/${selectedCase.id}/wallets/${selectedWalletId}/timeline`,
          { headers },
        ),
      ]);

      if (graphResponse.status === 401 || timelineResponse.status === 401) {
        localStorage.removeItem("access_token");
        setToken(null);
        throw new Error("Session expired. Please login again.");
      }

      if (!graphResponse.ok) {
        const message = await graphResponse.text();
        throw new Error(
          message || `Graph analytics returned ${graphResponse.status}`,
        );
      }

      if (!timelineResponse.ok) {
        const message = await timelineResponse.text();
        throw new Error(
          message || `Timeline analytics returned ${timelineResponse.status}`,
        );
      }

      const graphData: GraphAnalyticsResponse = await graphResponse.json();
      const timelineData: TimelineAnalyticsResponse = await timelineResponse.json();

      setGraphAnalytics(graphData);
      setTimelineAnalytics(timelineData);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load wallet analytics",
      );
    } finally {
      setAnalyticsLoading(false);
    }
  }

  /* =========================
     LOAD ML RISK + AML ASSESSMENT
  ========================= */

  async function handleLoadMlAml() {
    if (!token) {
      setError("Please login first.");
      return;
    }

    if (!selectedCase || !selectedWalletId || !selectedWallet) {
      setError("Select a saved case wallet first.");
      return;
    }

    const wallet = wallets.find((item) => item.id === selectedWalletId);
    if (!wallet || wallet.address.toLowerCase() !== selectedWallet.toLowerCase()) {
      setError("ML and AML assessment are available for wallets saved in the selected case.");
      return;
    }

    setMlAmlLoading(true);
    setError(null);

    try {
      const headers = { Authorization: `Bearer ${token}` };
      const [mlResponse, amlResponse] = await Promise.all([
        fetch(`${API_URL}/cases/${selectedCase.id}/wallets/${selectedWalletId}/ml-risk`, { headers }),
        fetch(`${API_URL}/cases/${selectedCase.id}/wallets/${selectedWalletId}/aml-assessment`, { headers }),
      ]);

      if (mlResponse.status === 401 || amlResponse.status === 401) {
        localStorage.removeItem("access_token");
        setToken(null);
        throw new Error("Session expired. Please login again.");
      }
      if (!mlResponse.ok) {
        const message = await mlResponse.text();
        throw new Error(message || `ML risk returned ${mlResponse.status}`);
      }
      if (!amlResponse.ok) {
        const message = await amlResponse.text();
        throw new Error(message || `AML assessment returned ${amlResponse.status}`);
      }

      const mlData: MLRiskResponse = await mlResponse.json();
      const amlData: AMLAssessmentResponse = await amlResponse.json();
      setMlRisk(mlData);
      setAmlAssessment(amlData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load ML risk and AML assessment");
    } finally {
      setMlAmlLoading(false);
    }
  }

  /* =========================
     LOAD VASP ATTRIBUTION
  ========================= */

  async function handleLoadVaspAttribution() {
    if (!token) {
      setError("Please login first.");
      return;
    }

    if (!selectedCase || !selectedWalletId || !selectedWallet) {
      setError("Select a saved case wallet first.");
      return;
    }

    const wallet = wallets.find((item) => item.id === selectedWalletId);
    if (!wallet || wallet.address.toLowerCase() !== selectedWallet.toLowerCase()) {
      setError("VASP attribution is available for wallets saved in the selected case.");
      return;
    }

    setVaspLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/cases/${selectedCase.id}/wallets/${selectedWalletId}/vasp-attribution?max_hops=2`,
        { headers: { Authorization: `Bearer ${token}` } },
      );

      if (response.status === 401) {
        localStorage.removeItem("access_token");
        setToken(null);
        throw new Error("Session expired. Please login again.");
      }
      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || `VASP attribution returned ${response.status}`);
      }

      const data: VaspAttributionResponse = await response.json();
      setVaspAttribution(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load VASP attribution");
    } finally {
      setVaspLoading(false);
    }
  }

  async function handleAddKnownVaspLabel(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !selectedCase || !selectedWalletId || !selectedWallet) {
      setError("Select a saved case wallet first.");
      return;
    }

    const name = vaspLabelName.trim();
    const source = vaspLabelSource.trim();
    const evidence = vaspLabelEvidence.trim();
    const confidence = Number(vaspLabelConfidence);

    if (!name) {
      setError("VASP name is required.");
      return;
    }
    if (!source) {
      setError("Intelligence source is required.");
      return;
    }
    if (!Number.isFinite(confidence) || confidence < 0 || confidence > 1) {
      setError("Confidence must be between 0 and 1.");
      return;
    }

    setVaspLabelSaving(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/intelligence/risk-entities`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          address: selectedWallet,
          chain,
          entity_type: "vasp",
          name,
          source,
          risk_category: "centralized_exchange",
          confidence,
          evidence: evidence || undefined,
        }),
      });

      if (response.status === 401) {
        localStorage.removeItem("access_token");
        setToken(null);
        throw new Error("Session expired. Please login again.");
      }
      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || `Adding VASP label returned ${response.status}`);
      }

      setVaspLabelName("");
      setVaspLabelEvidence("");
      setVaspAttribution(null);
      await handleLoadVaspAttribution();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add known VASP label");
    } finally {
      setVaspLabelSaving(false);
    }
  }

  /* =========================
     NODE POSITION CHANGES
  ========================= */

  function handleNodesChange(changes: NodeChange[]) {
    setNodes((currentNodes) =>
      applyNodeChanges(changes, currentNodes),
    );
  }

  /* =========================
     GRAPH LAYOUT CONTROLS
  ========================= */

  function handleAutoLayout() {
    if (nodes.length === 0) {
      return;
    }

    const targetNode =
      nodes.find((node) =>
        String(node.data?.label ?? "").startsWith("TARGET"),
      ) ?? nodes[0];

    const adjacency = new Map<string, string[]>();

    nodes.forEach((node) => {
      adjacency.set(node.id, []);
    });

    edges.forEach((edge) => {
      adjacency.get(edge.source)?.push(edge.target);
      adjacency.get(edge.target)?.push(edge.source);
    });

    const levels = new Map<string, number>();
    const queue: string[] = [targetNode.id];
    levels.set(targetNode.id, 0);

    while (queue.length > 0) {
      const current = queue.shift();
      if (!current) {
        continue;
      }

      const currentLevel = levels.get(current) ?? 0;

      for (const neighbor of adjacency.get(current) ?? []) {
        if (!levels.has(neighbor)) {
          levels.set(neighbor, currentLevel + 1);
          queue.push(neighbor);
        }
      }
    }

    const fallbackLevel = Math.max(
      0,
      ...Array.from(levels.values()),
    ) + 1;

    nodes.forEach((node) => {
      if (!levels.has(node.id)) {
        levels.set(node.id, fallbackLevel);
      }
    });

    const levelCounts = new Map<number, number>();

    setNodes((currentNodes) =>
      currentNodes.map((node) => {
        const level = levels.get(node.id) ?? 0;
        const index = levelCounts.get(level) ?? 0;
        levelCounts.set(level, index + 1);

        return {
          ...node,
          position: {
            x: level * 320,
            y: index * 220,
          },
        };
      }),
    );

    window.setTimeout(() => {
      reactFlowInstance?.fitView({ padding: 0.2 });
    }, 0);
  }

  function handleResetLayout() {
    setNodes((currentNodes) =>
      currentNodes.map((node, index) => ({
        ...node,
        position: {
          x: (index % 4) * 330,
          y: Math.floor(index / 4) * 240,
        },
      })),
    );

    window.setTimeout(() => {
      reactFlowInstance?.fitView({ padding: 0.2 });
    }, 0);
  }

  function handleFitGraph() {
    reactFlowInstance?.fitView({ padding: 0.2 });
  }

  /* =========================
     NODE CLICK
  ========================= */

  function handleNodeClick(
    _event: MouseEvent,
    node: Node,
  ) {
    setSelectedTransfer(null);
    setMlRisk(null);
    setAmlAssessment(null);
    setSelectedWallet(node.id);
    const savedWallet = wallets.find(
      (wallet) => wallet.address.toLowerCase() === node.id.toLowerCase(),
    );
    setSelectedWalletId(savedWallet?.id ?? null);
    setInvestigationTab("wallet");
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
      setInvestigationTab("transaction");
    }
  }

  /* =========================
     CLOSE INVESTIGATION
  ========================= */

  function closeInvestigationPanel() {
    setSelectedWallet(null);
    setSelectedTransfer(null);
    setInvestigationTab("wallet");
  }

  const selectedWalletTransactions =
    selectedWallet
      ? getWalletTransactions(
          trace,
          selectedWallet,
        )
      : [];

  const availableAssets = Array.from(
    new Set(
      edges
        .map((edge) =>
          String(
            (edge.data as { transfer?: TraceTransfer } | undefined)
              ?.transfer?.asset ??
            "",
          ).trim(),
        )
        .filter(Boolean),
    ),
  ).sort();

  const filteredEdges = edges.filter((edge) => {
    const transfer = (
      edge.data as { transfer?: TraceTransfer } | undefined
    )?.transfer;

    if (!transfer) {
      return false;
    }

    const search = transactionSearch.trim().toLowerCase();
    if (
      search &&
      !transfer.transaction_hash.toLowerCase().includes(search)
    ) {
      return false;
    }

    if (
      assetFilter !== "all" &&
      (transfer.asset ?? "").toLowerCase() !==
        assetFilter.toLowerCase()
    ) {
      return false;
    }

    if (directionFilter !== "all" && trace) {
      const target = trace.address.toLowerCase();
      const source = edge.source.toLowerCase();
      const destination = edge.target.toLowerCase();

      const isOutgoing = source === target;
      const isIncoming = destination === target;

      if (directionFilter === "outgoing" && !isOutgoing) {
        return false;
      }

      if (directionFilter === "incoming" && !isIncoming) {
        return false;
      }
    }

    const value = transfer.value;

    if (minValueFilter.trim() && value !== null) {
      const minimum = Number(minValueFilter);
      if (Number.isFinite(minimum) && value < minimum) {
        return false;
      }
    }

    if (maxValueFilter.trim() && value !== null) {
      const maximum = Number(maxValueFilter);
      if (Number.isFinite(maximum) && value > maximum) {
        return false;
      }
    }

    return true;
  });

  const filteredNodeIds = new Set<string>();
  filteredEdges.forEach((edge) => {
    filteredNodeIds.add(edge.source);
    filteredNodeIds.add(edge.target);
  });

  const filteredNodes =
    transactionSearch.trim() ||
    assetFilter !== "all" ||
    directionFilter !== "all" ||
    minValueFilter.trim() ||
    maxValueFilter.trim()
      ? nodes.filter((node) => filteredNodeIds.has(node.id))
      : nodes;

  function clearGraphFilters() {
    setTransactionSearch("");
    setAssetFilter("all");
    setDirectionFilter("all");
    setMinValueFilter("");
    setMaxValueFilter("");
  }

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
      <style>{responsiveCss}</style>

      {/* =====================
          TOP BAR
      ===================== */}

      <header
        className="cg-header"
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
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <button
              type="button"
              onClick={handleGenerateReport}
              disabled={reportLoading || !selectedCase}
              title={
                selectedCase
                  ? "Generate investigation PDF for the active case"
                  : "Select a case first"
              }
              style={{
                ...workspaceToggleButtonStyle,
                background: reportLoading ? "#1e3a8a" : "#2563eb",
                borderColor: "#2563eb",
                opacity: reportLoading || !selectedCase ? 0.65 : 1,
                cursor: reportLoading || !selectedCase ? "not-allowed" : "pointer",
                fontWeight: 700,
              }}
            >
              {reportLoading ? "Generating..." : "📄 Report"}
            </button>
            <button
              type="button"
              onClick={() => setSidebarCollapsed((current) => !current)}
              title={sidebarCollapsed ? "Open workspace panel" : "Collapse workspace panel"}
              style={workspaceToggleButtonStyle}
            >
              {sidebarCollapsed ? "☰ Workspace" : "☰"}
            </button>
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
          </div>
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

      {token && !sidebarCollapsed && (
        <section
          className="cg-sidebar"
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
                          setGraphAnalytics(null);
                          setTimelineAnalytics(null);

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

              <button
                type="button"
                onClick={handleGenerateReport}
                disabled={reportLoading}
                style={{
                  marginTop: "10px",
                  width: "100%",
                  padding: "8px 10px",
                  border: "1px solid #2563eb",
                  borderRadius: "6px",
                  background: reportLoading ? "#1e3a8a" : "#2563eb",
                  color: "#ffffff",
                  cursor: reportLoading ? "not-allowed" : "pointer",
                  fontSize: "10px",
                  fontWeight: 700,
                }}
              >
                {reportLoading ? "Generating Investigation Report..." : "📄 Generate Investigation Report"}
              </button>
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
                            setSelectedWallet(wallet.address);
                            setInvestigationTab("wallet");
                            setGraphAnalytics(null);
                            setTimelineAnalytics(null);

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

                  <option value="3">
                    3 Hops
                  </option>

                  <option value="4">
                    4 Hops
                  </option>

                  <option value="5">
                    5 Hops
                  </option>
                </select>

                <label
                  style={{
                    ...labelStyle,
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    cursor: "pointer",
                    marginTop: "10px",
                  }}
                >
                  <input
                    type="checkbox"
                    checked={liveRefresh}
                    onChange={(event) =>
                      setLiveRefresh(
                        event.target.checked,
                      )
                    }
                  />
                  Live Blockchain Refresh
                </label>

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
                      new Set(
                          edges.map(
                            (edge) =>
                              `${edge.source}->${edge.target}`,
                          ),
                        ).size
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
          className="cg-investigation"
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

          {selectedWallet && (
            <div
              style={{
                ...investigationTabsStyle,
                gridTemplateColumns: selectedTransfer
                  ? "repeat(7, minmax(0, 1fr))"
                  : "repeat(6, minmax(0, 1fr))",
              }}
            >
              <button
                type="button"
                onClick={() => setInvestigationTab("wallet")}
                style={investigationTabStyle(investigationTab === "wallet")}
              >
                Wallet
              </button>

              {selectedTransfer && (
                <button
                  type="button"
                  onClick={() => setInvestigationTab("transaction")}
                  style={investigationTabStyle(investigationTab === "transaction")}
                >
                  Transaction
                </button>
              )}

              <button
                type="button"
                onClick={() => {
                  setInvestigationTab("analytics");
                  if (!graphAnalytics || !timelineAnalytics) {
                    void handleLoadWalletAnalytics();
                  }
                }}
                style={investigationTabStyle(investigationTab === "analytics")}
              >
                Analytics
              </button>

              <button
                type="button"
                onClick={() => {
                  setInvestigationTab("ml-aml");
                  if (!mlRisk || !amlAssessment) {
                    void handleLoadMlAml();
                  }
                }}
                style={investigationTabStyle(investigationTab === "ml-aml")}
              >
                ML / AML
              </button>

              <button
                type="button"
                onClick={() => {
                  setInvestigationTab("vasp");
                  if (!vaspAttribution) {
                    void handleLoadVaspAttribution();
                  }
                }}
                style={investigationTabStyle(investigationTab === "vasp")}
              >
                VASP Attribution
              </button>

              <button
                type="button"
                onClick={() => {
                  setInvestigationTab("notes");
                  if (selectedCase && notes.length === 0 && !notesLoading) {
                    void loadNotes(selectedCase.id);
                  }
                }}
                style={investigationTabStyle(investigationTab === "notes")}
              >
                Notes
              </button>

              <button
                type="button"
                onClick={() => {
                  setInvestigationTab("evidence");
                  if (selectedCase && !evidenceLoading) {
                    void loadEvidence(selectedCase.id);
                  }
                }}
                style={investigationTabStyle(investigationTab === "evidence")}
              >
                Evidence
              </button>
            </div>
          )}

          {/* VASP ATTRIBUTION */}

          {selectedWallet && investigationTab === "vasp" && (
            <>
              <div style={panelSectionStyle}>
                <div style={sectionTitleStyle}>VASP Attribution</div>
                <div style={{ marginTop: "7px", fontSize: "10px", color: "#94a3b8", lineHeight: 1.5 }}>
                  Known-VASP intelligence matching across transaction-connected wallets. This is a research-stage intelligence assessment.
                </div>
                {!selectedWalletId ? (
                  <div style={analyticsWarningStyle}>
                    This traced wallet is not saved in the selected case. Select a saved case wallet to load VASP attribution.
                  </div>
                ) : (
                  <button type="button" onClick={() => void handleLoadVaspAttribution()} disabled={vaspLoading} style={{ ...primaryButtonStyle, marginTop: "10px" }}>
                    {vaspLoading ? "Loading VASP Attribution..." : "Refresh VASP Attribution"}
                  </button>
                )}
              </div>

              {vaspLoading && (
                <div style={analyticsLoadingStyle}>Searching known VASP intelligence across the transaction graph...</div>
              )}

              {vaspAttribution && (
                <>
                  <div style={panelSectionStyle}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "8px" }}>
                      <div style={sectionTitleStyle}>Attribution Summary</div>
                      <span style={filterCountBadgeStyle}>
                        {vaspAttribution.candidate_count} candidate{vaspAttribution.candidate_count === 1 ? "" : "s"}
                      </span>
                    </div>
                    <div style={{ marginTop: "8px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px" }}>
                      <div style={analyticsStatStyle}><span>Status</span><strong>{vaspAttribution.status}</strong></div>
                      <div style={analyticsStatStyle}><span>Max hops</span><strong>{vaspAttribution.max_hops}</strong></div>
                      <div style={analyticsStatStyle}><span>Chain</span><strong>{vaspAttribution.chain}</strong></div>
                      <div style={analyticsStatStyle}><span>Candidates</span><strong>{vaspAttribution.candidate_count}</strong></div>
                    </div>
                    <div style={{ marginTop: "10px", color: "#64748b", fontSize: "9px", lineHeight: 1.5 }}>
                      {vaspAttribution.method}
                    </div>
                  </div>

                  {vaspAttribution.candidates.length === 0 ? (
                    <div style={analyticsEmptyStyle}>No known VASP candidates were found within the configured transaction path depth.</div>
                  ) : (
                    vaspAttribution.candidates.map((candidate, index) => (
                      <div key={`${candidate.address}-${candidate.name ?? "vasp"}-${index}`} style={panelSectionStyle}>
                        <div style={{ display: "flex", justifyContent: "space-between", gap: "8px", alignItems: "flex-start" }}>
                          <div style={{ minWidth: 0 }}>
                            <div style={sectionTitleStyle}>{candidate.name ?? "Known VASP"}</div>
                            <div style={{ marginTop: "5px", color: "#94a3b8", fontSize: "9px", wordBreak: "break-all" }}>{candidate.address}</div>
                          </div>
                          <span style={{ ...analyticsSeverityStyle, color: "#86efac", flexShrink: 0 }}>
                            {candidate.confidence !== null ? `${(candidate.confidence * 100).toFixed(1)}%` : "N/A"}
                          </span>
                        </div>
                        <div style={{ marginTop: "9px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px" }}>
                          <div style={analyticsStatStyle}><span>Hop</span><strong>{candidate.hop ?? "N/A"}</strong></div>
                          <div style={analyticsStatStyle}><span>Basis</span><strong>{candidate.attribution_basis}</strong></div>
                          <div style={analyticsStatStyle}><span>Source</span><strong>{candidate.source ?? "N/A"}</strong></div>
                          <div style={analyticsStatStyle}><span>Category</span><strong>{candidate.risk_category ?? "N/A"}</strong></div>
                        </div>
                        <div style={{ marginTop: "9px", color: "#cbd5e1", fontSize: "10px", lineHeight: 1.5 }}>
                          <strong>Reason:</strong> {candidate.reason}
                        </div>
                        {candidate.evidence && (
                          <div style={{ marginTop: "8px", color: "#94a3b8", fontSize: "10px", lineHeight: 1.5 }}>
                            <strong style={{ color: "#cbd5e1" }}>Evidence:</strong> {candidate.evidence}
                          </div>
                        )}
                        <details style={{ marginTop: "9px", color: "#94a3b8" }}>
                          <summary style={{ cursor: "pointer", color: "#60a5fa", fontSize: "10px" }}>Transaction Path Evidence</summary>
                          <div style={{ marginTop: "8px", fontSize: "9px", color: "#cbd5e1", lineHeight: 1.5 }}>
                            <div><strong>Wallet path:</strong></div>
                            <div style={{ marginTop: "4px", wordBreak: "break-all" }}>{candidate.wallets.join(" → ")}</div>
                            {candidate.transfers.map((transfer, transferIndex) => (
                              <div key={`${transfer.transaction_hash}-${transferIndex}`} style={{ marginTop: "8px", padding: "8px", background: "#0f1117", border: "1px solid #2f3545", borderRadius: "6px" }}>
                                <div><strong>Transaction:</strong> <span style={{ wordBreak: "break-all" }}>{transfer.transaction_hash}</span></div>
                                <div style={{ marginTop: "4px" }}><strong>Asset:</strong> {transfer.asset ?? "N/A"} · <strong>Value:</strong> {transfer.value ?? "N/A"}</div>
                                <div style={{ marginTop: "4px" }}><strong>Category:</strong> {transfer.category ?? "N/A"} · <strong>Block:</strong> {transfer.block_number ?? "N/A"}</div>
                                <div style={{ marginTop: "4px" }}><strong>Timestamp:</strong> {transfer.timestamp ?? "N/A"}</div>
                              </div>
                            ))}
                          </div>
                        </details>
                      </div>
                    ))
                  )}
                  <div style={amlDisclaimerStyle}>{vaspAttribution.notice}</div>
                </>
              )}

              <div style={panelSectionStyle}>
                <div style={sectionTitleStyle}>Add Known VASP Label</div>
                <div style={{ marginTop: "6px", color: "#64748b", fontSize: "9px", lineHeight: 1.45 }}>
                  Adds a known-VASP intelligence record to the selected wallet address. Use a documented intelligence source.
                </div>
                <form onSubmit={handleAddKnownVaspLabel} style={{ marginTop: "10px" }}>
                  <input value={vaspLabelName} onChange={(event) => setVaspLabelName(event.target.value)} placeholder="VASP name, e.g. Coinbase" style={inputStyle} disabled={vaspLabelSaving} />
                  <input value={vaspLabelSource} onChange={(event) => setVaspLabelSource(event.target.value)} placeholder="Intelligence source" style={{ ...inputStyle, marginTop: "7px" }} disabled={vaspLabelSaving} />
                  <input value={vaspLabelConfidence} onChange={(event) => setVaspLabelConfidence(event.target.value)} placeholder="Confidence 0-1" inputMode="decimal" style={{ ...inputStyle, marginTop: "7px" }} disabled={vaspLabelSaving} />
                  <textarea value={vaspLabelEvidence} onChange={(event) => setVaspLabelEvidence(event.target.value)} placeholder="Evidence / source description" rows={3} style={{ ...inputStyle, marginTop: "7px", resize: "vertical", lineHeight: 1.5 }} disabled={vaspLabelSaving} />
                  <button type="submit" disabled={vaspLabelSaving || !vaspLabelName.trim()} style={{ ...primaryButtonStyle, marginTop: "7px" }}>
                    {vaspLabelSaving ? "Saving..." : "Add Known VASP Label"}
                  </button>
                </form>
              </div>
            </>
          )}

          {/* CASE NOTES */}

          {selectedWallet && investigationTab === "notes" && (
            <>
              <div style={panelSectionStyle}>
                <div style={sectionTitleStyle}>Analyst Notes</div>
                <div style={{ marginTop: "6px", color: "#64748b", fontSize: "9px", lineHeight: 1.45 }}>
                  Notes are stored against the selected investigation case and are included in generated reports.
                </div>

                <form onSubmit={handleCreateNote} style={{ marginTop: "10px" }}>
                  <textarea
                    value={newNoteContent}
                    onChange={(event) => setNewNoteContent(event.target.value)}
                    placeholder="Record an investigation observation, decision, or follow-up..."
                    rows={4}
                    style={{ ...inputStyle, resize: "vertical", minHeight: "82px", lineHeight: 1.5 }}
                    disabled={noteSaving}
                  />
                  <button
                    type="submit"
                    disabled={noteSaving || !newNoteContent.trim()}
                    style={{ ...primaryButtonStyle, marginTop: "7px" }}
                  >
                    {noteSaving ? "Saving..." : "Add Note"}
                  </button>
                </form>
              </div>

              <div style={panelSectionStyle}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "8px" }}>
                  <div style={sectionTitleStyle}>Saved Notes</div>
                  <span style={filterCountBadgeStyle}>{notes.length}</span>
                </div>

                {notesLoading ? (
                  <div style={analyticsLoadingStyle}>Loading case notes...</div>
                ) : notes.length === 0 ? (
                  <div style={analyticsEmptyStyle}>No analyst notes have been recorded for this case.</div>
                ) : (
                  notes.map((note) => (
                    <div key={note.id} style={noteCardStyle}>
                      {editingNoteId === note.id ? (
                        <>
                          <textarea
                            value={editingNoteContent}
                            onChange={(event) => setEditingNoteContent(event.target.value)}
                            rows={4}
                            style={{ ...inputStyle, resize: "vertical", lineHeight: 1.5 }}
                            disabled={noteSaving}
                          />
                          <div style={noteActionsStyle}>
                            <button
                              type="button"
                              onClick={() => void handleUpdateNote(note.id)}
                              disabled={noteSaving || !editingNoteContent.trim()}
                              style={notePrimaryActionStyle}
                            >
                              {noteSaving ? "Saving..." : "Save"}
                            </button>
                            <button
                              type="button"
                              onClick={cancelEditingNote}
                              disabled={noteSaving}
                              style={noteSecondaryActionStyle}
                            >
                              Cancel
                            </button>
                          </div>
                        </>
                      ) : (
                        <>
                          <div style={{ color: "#e2e8f0", fontSize: "11px", lineHeight: 1.55, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                            {note.content}
                          </div>
                          <div style={noteMetaStyle}>
                            <span>
                              {note.created_at ? new Date(note.created_at).toLocaleString() : "Date unavailable"}
                            </span>
                            {note.updated_at && note.updated_at !== note.created_at && (
                              <span>Updated {new Date(note.updated_at).toLocaleString()}</span>
                            )}
                          </div>
                          <div style={noteActionsStyle}>
                            <button type="button" onClick={() => startEditingNote(note)} disabled={noteSaving} style={noteSecondaryActionStyle}>
                              Edit
                            </button>
                            <button type="button" onClick={() => void handleDeleteNote(note.id)} disabled={noteSaving} style={noteDangerActionStyle}>
                              Delete
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  ))
                )}
              </div>
            </>
          )}

          {/* WALLET DETAILS */}

          {selectedWallet && investigationTab === "wallet" && (
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

          {/* WALLET ANALYTICS */}

          {selectedWallet && investigationTab === "analytics" && (
            <>
              <div style={panelSectionStyle}>
                <div style={sectionTitleStyle}>
                  Graph & Timeline Analytics
                </div>
                <div
                  style={{
                    marginTop: "7px",
                    fontSize: "10px",
                    color: "#94a3b8",
                    lineHeight: 1.5,
                  }}
                >
                  Structured analytics from the case wallet APIs.
                </div>

                {!selectedWalletId ? (
                  <div
                    style={{
                      marginTop: "10px",
                      padding: "10px",
                      background: "#2a1f0b",
                      border: "1px solid #92400e",
                      borderRadius: "6px",
                      color: "#fcd34d",
                      fontSize: "11px",
                      lineHeight: 1.5,
                    }}
                  >
                    This traced wallet is not saved in the selected case. Select a case wallet to load case analytics.
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={() => void handleLoadWalletAnalytics()}
                    disabled={analyticsLoading}
                    style={{
                      ...primaryButtonStyle,
                      marginTop: "10px",
                    }}
                  >
                    {analyticsLoading ? "Loading Analytics..." : "Refresh Analytics"}
                  </button>
                )}
              </div>

              {analyticsLoading && (
                <div
                  style={{
                    padding: "14px",
                    color: "#94a3b8",
                    fontSize: "11px",
                    textAlign: "center",
                  }}
                >
                  Loading graph and timeline analytics...
                </div>
              )}

              {graphAnalytics && (
                <div style={panelSectionStyle}>
                  <div style={sectionTitleStyle}>Graph Analytics</div>

                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1fr 1fr",
                      gap: "6px",
                      marginTop: "8px",
                    }}
                  >
                    {[
                      ["Fan-out", graphAnalytics.fan_out],
                      ["Fan-in", graphAnalytics.fan_in],
                      ["Outgoing", graphAnalytics.outgoing_connections],
                      ["Incoming", graphAnalytics.incoming_connections],
                      ["Risk Paths", graphAnalytics.multi_hop_exposure_count],
                      ["Out Concentration", `${(graphAnalytics.outgoing_concentration * 100).toFixed(1)}%`],
                      ["In Concentration", `${(graphAnalytics.incoming_concentration * 100).toFixed(1)}%`],
                    ].map(([label, value]) => (
                      <div key={String(label)} style={analyticsStatStyle}>
                        <span>{label}</span>
                        <strong>{value}</strong>
                      </div>
                    ))}
                  </div>

                  <div style={{ marginTop: "12px" }}>
                    <div style={sectionTitleStyle}>Top Outgoing Counterparties</div>
                    {graphAnalytics.top_outgoing_counterparties.length === 0 ? (
                      <div style={analyticsEmptyStyle}>No outgoing counterparties.</div>
                    ) : (
                      graphAnalytics.top_outgoing_counterparties.slice(0, 5).map((item) => (
                        <div key={`out-${item.address}`} style={analyticsListItemStyle}>
                          <div style={{ wordBreak: "break-all" }}>{shortenAddress(item.address)}</div>
                          <div style={{ color: "#94a3b8", marginTop: "3px" }}>
                            {item.transaction_count} tx • {formatNumber(item.total_value)}
                          </div>
                        </div>
                      ))
                    )}
                  </div>

                  <div style={{ marginTop: "12px" }}>
                    <div style={sectionTitleStyle}>Graph Signals</div>
                    {graphAnalytics.graph_signals.length === 0 ? (
                      <div style={analyticsEmptyStyle}>No graph signals returned.</div>
                    ) : (
                      graphAnalytics.graph_signals.map((signal, index) => (
                        <div key={`graph-signal-${index}`} style={analyticsSignalStyle}>
                          <strong>{String(signal.signal ?? "Graph signal")}</strong>
                          {signal.severity && <span style={analyticsSeverityStyle}>{String(signal.severity)}</span>}
                          {signal.reason && (
                            <div style={{ marginTop: "4px", color: "#cbd5e1", lineHeight: 1.45 }}>
                              {String(signal.reason)}
                            </div>
                          )}
                        </div>
                      ))
                    )}
                  </div>

                  {graphAnalytics.multi_hop_risk_paths.length > 0 && (
                    <div style={{ marginTop: "12px" }}>
                      <div style={sectionTitleStyle}>Multi-hop Risk Paths</div>
                      {graphAnalytics.multi_hop_risk_paths.slice(0, 5).map((path, index) => (
                        <div key={`path-${index}`} style={analyticsListItemStyle}>
                          <strong>{path.entity_name ?? path.entity_type}</strong>
                          <div style={{ marginTop: "3px", color: "#94a3b8", wordBreak: "break-all" }}>
                            {shortenAddress(path.risk_entity_address)} • {path.hop_count} hop(s)
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {timelineAnalytics && (
                <div style={panelSectionStyle}>
                  <div style={sectionTitleStyle}>Timeline Analytics</div>

                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1fr 1fr",
                      gap: "6px",
                      marginTop: "8px",
                    }}
                  >
                    {[
                      ["Transactions", timelineAnalytics.total_transactions],
                      ["Incoming", timelineAnalytics.incoming_transactions],
                      ["Outgoing", timelineAnalytics.outgoing_transactions],
                      ["Bursts", timelineAnalytics.bursts.length],
                      ["Avg Gap", formatSeconds(timelineAnalytics.average_transaction_gap_seconds)],
                      ["Shortest Gap", formatSeconds(timelineAnalytics.shortest_transaction_gap_seconds)],
                      ["Longest Gap", formatSeconds(timelineAnalytics.longest_transaction_gap_seconds)],
                      ["Duration", formatSeconds(timelineAnalytics.activity_duration_seconds)],
                    ].map(([label, value]) => (
                      <div key={String(label)} style={analyticsStatStyle}>
                        <span>{label}</span>
                        <strong>{value}</strong>
                      </div>
                    ))}
                  </div>

                  <div style={{ marginTop: "12px" }}>
                    <div style={sectionTitleStyle}>Temporal Signals</div>
                    {timelineAnalytics.temporal_signals.length === 0 ? (
                      <div style={analyticsEmptyStyle}>No temporal signals returned.</div>
                    ) : (
                      timelineAnalytics.temporal_signals.map((signal, index) => (
                        <div key={`temporal-signal-${index}`} style={analyticsSignalStyle}>
                          <strong>{String(signal.signal ?? "Temporal signal")}</strong>
                          {signal.severity && <span style={analyticsSeverityStyle}>{String(signal.severity)}</span>}
                          {signal.reason && (
                            <div style={{ marginTop: "4px", color: "#cbd5e1", lineHeight: 1.45 }}>
                              {String(signal.reason)}
                            </div>
                          )}
                        </div>
                      ))
                    )}
                  </div>

                  <div style={{ marginTop: "12px" }}>
                    <div style={sectionTitleStyle}>Largest Transactions</div>
                    {timelineAnalytics.largest_transactions.length === 0 ? (
                      <div style={analyticsEmptyStyle}>No transactions returned.</div>
                    ) : (
                      timelineAnalytics.largest_transactions.slice(0, 5).map((tx) => (
                        <div key={tx.transaction_hash} style={analyticsListItemStyle}>
                          <div style={{ display: "flex", justifyContent: "space-between", gap: "8px" }}>
                            <strong>{tx.direction}</strong>
                            <strong>{formatNumber(tx.value)}</strong>
                          </div>
                          <div style={{ marginTop: "3px", color: "#94a3b8", wordBreak: "break-all" }}>
                            {shortenAddress(tx.counterparty)}
                          </div>
                          <div style={{ marginTop: "3px", color: "#64748b" }}>
                            {tx.timestamp ?? "Unknown time"}
                          </div>
                        </div>
                      ))
                    )}
                  </div>

                  {timelineAnalytics.bursts.length > 0 && (
                    <div style={{ marginTop: "12px" }}>
                      <div style={sectionTitleStyle}>Transaction Bursts</div>
                      {timelineAnalytics.bursts.slice(0, 5).map((burst, index) => (
                        <div key={`burst-${index}`} style={analyticsListItemStyle}>
                          <strong>{burst.transaction_count} transactions</strong>
                          <div style={{ marginTop: "3px", color: "#94a3b8" }}>
                            {burst.start_time} → {burst.end_time}
                          </div>
                          <div style={{ marginTop: "3px", color: "#64748b" }}>
                            Duration: {formatSeconds(burst.duration_seconds)}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </>
          )}

          {/* CASE EVIDENCE */}

          {selectedWallet && investigationTab === "evidence" && (
            <>
              <div style={panelSectionStyle}>
                <div style={sectionTitleStyle}>Case Evidence</div>
                <div style={{ marginTop: "6px", color: "#64748b", fontSize: "9px", lineHeight: 1.45 }}>
                  Record evidence references, source details, and investigation material against the selected case.
                </div>

                <form onSubmit={handleCreateEvidence} style={{ marginTop: "10px" }}>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "7px" }}>
                    <input
                      value={newEvidenceType}
                      onChange={(event) => setNewEvidenceType(event.target.value)}
                      placeholder="Evidence type (e.g. transaction)"
                      maxLength={50}
                      style={inputStyle}
                      disabled={evidenceSaving}
                    />
                    <input
                      value={newEvidenceTitle}
                      onChange={(event) => setNewEvidenceTitle(event.target.value)}
                      placeholder="Evidence title"
                      maxLength={255}
                      style={inputStyle}
                      disabled={evidenceSaving}
                    />
                  </div>

                  <textarea
                    value={newEvidenceDescription}
                    onChange={(event) => setNewEvidenceDescription(event.target.value)}
                    placeholder="Describe what this evidence shows and why it matters..."
                    maxLength={10000}
                    rows={4}
                    style={{ ...inputStyle, marginTop: "7px", resize: "vertical", minHeight: "82px", lineHeight: 1.5 }}
                    disabled={evidenceSaving}
                  />

                  <input
                    value={newEvidenceReference}
                    onChange={(event) => setNewEvidenceReference(event.target.value)}
                    placeholder="Reference: transaction hash, URL, source ID, document reference, etc."
                    maxLength={1000}
                    style={{ ...inputStyle, marginTop: "7px" }}
                    disabled={evidenceSaving}
                  />

                  <button
                    type="submit"
                    disabled={evidenceSaving || !newEvidenceType.trim() || !newEvidenceTitle.trim()}
                    style={{ ...primaryButtonStyle, marginTop: "7px" }}
                  >
                    {evidenceSaving ? "Saving..." : "Add Evidence"}
                  </button>
                </form>
              </div>

              <div style={panelSectionStyle}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "8px" }}>
                  <div style={sectionTitleStyle}>Recorded Evidence</div>
                  <button
                    type="button"
                    onClick={() => selectedCase && void loadEvidence(selectedCase.id)}
                    disabled={evidenceLoading || evidenceSaving}
                    style={secondaryButtonStyle}
                  >
                    {evidenceLoading ? "Loading..." : "Refresh"}
                  </button>
                </div>

                {evidenceLoading ? (
                  <div style={analyticsLoadingStyle}>Loading case evidence...</div>
                ) : evidenceItems.length === 0 ? (
                  <div style={{ ...analyticsEmptyStyle, marginTop: "8px" }}>
                    No evidence items have been recorded for this case yet.
                  </div>
                ) : (
                  <div style={{ marginTop: "8px", display: "grid", gap: "8px" }}>
                    {evidenceItems.map((evidence) => (
                      <div
                        key={evidence.id}
                        style={{
                          border: "1px solid #334155",
                          borderRadius: "7px",
                          padding: "10px",
                          background: "rgba(15, 23, 42, 0.72)",
                        }}
                      >
                        {editingEvidenceId === evidence.id ? (
                          <>
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "7px" }}>
                              <input
                                value={editingEvidenceType}
                                onChange={(event) => setEditingEvidenceType(event.target.value)}
                                maxLength={50}
                                style={inputStyle}
                                disabled={evidenceSaving}
                              />
                              <input
                                value={editingEvidenceTitle}
                                onChange={(event) => setEditingEvidenceTitle(event.target.value)}
                                maxLength={255}
                                style={inputStyle}
                                disabled={evidenceSaving}
                              />
                            </div>
                            <textarea
                              value={editingEvidenceDescription}
                              onChange={(event) => setEditingEvidenceDescription(event.target.value)}
                              maxLength={10000}
                              rows={4}
                              style={{ ...inputStyle, marginTop: "7px", resize: "vertical", lineHeight: 1.5 }}
                              disabled={evidenceSaving}
                            />
                            <input
                              value={editingEvidenceReference}
                              onChange={(event) => setEditingEvidenceReference(event.target.value)}
                              maxLength={1000}
                              style={{ ...inputStyle, marginTop: "7px" }}
                              disabled={evidenceSaving}
                            />
                            <div style={{ display: "flex", gap: "7px", marginTop: "7px" }}>
                              <button
                                type="button"
                                onClick={() => void handleUpdateEvidence(evidence.id)}
                                disabled={evidenceSaving}
                                style={primaryButtonStyle}
                              >
                                {evidenceSaving ? "Saving..." : "Save Changes"}
                              </button>
                              <button
                                type="button"
                                onClick={cancelEditingEvidence}
                                disabled={evidenceSaving}
                                style={secondaryButtonStyle}
                              >
                                Cancel
                              </button>
                            </div>
                          </>
                        ) : (
                          <>
                            <div style={{ display: "flex", justifyContent: "space-between", gap: "8px", alignItems: "flex-start" }}>
                              <div style={{ minWidth: 0 }}>
                                <div style={{ display: "flex", gap: "7px", alignItems: "center", flexWrap: "wrap" }}>
                                  <strong style={{ color: "#f8fafc", fontSize: "12px", wordBreak: "break-word" }}>
                                    {evidence.title}
                                  </strong>
                                  <span style={analyticsSeverityStyle}>
                                    {evidence.evidence_type}
                                  </span>
                                </div>
                                {evidence.description && (
                                  <div style={{ marginTop: "6px", color: "#cbd5e1", fontSize: "10px", lineHeight: 1.5, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                                    {evidence.description}
                                  </div>
                                )}
                                {evidence.reference && (
                                  <div style={{ marginTop: "7px", color: "#60a5fa", fontSize: "9px", lineHeight: 1.45, wordBreak: "break-all" }}>
                                    Reference: {evidence.reference}
                                  </div>
                                )}
                                <div style={{ marginTop: "7px", color: "#64748b", fontSize: "8px" }}>
                                  Added {new Date(evidence.created_at).toLocaleString()}
                                  {evidence.updated_at !== evidence.created_at ? ` · Updated ${new Date(evidence.updated_at).toLocaleString()}` : ""}
                                </div>
                              </div>

                              <div style={{ display: "flex", gap: "5px", flexShrink: 0 }}>
                                <button
                                  type="button"
                                  onClick={() => startEditingEvidence(evidence)}
                                  disabled={evidenceSaving}
                                  style={secondaryButtonStyle}
                                >
                                  Edit
                                </button>
                                <button
                                  type="button"
                                  onClick={() => void handleDeleteEvidence(evidence.id)}
                                  disabled={evidenceSaving}
                                  style={{ ...secondaryButtonStyle, color: "#fca5a5", borderColor: "#7f1d1d" }}
                                >
                                  Delete
                                </button>
                              </div>
                            </div>
                          </>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}

          {/* ML / AML ASSESSMENT */}

          {selectedWallet && investigationTab === "ml-aml" && (
            <>
              <div style={panelSectionStyle}>
                <div style={sectionTitleStyle}>ML Risk + AML Assessment</div>
                <div style={{ marginTop: "7px", fontSize: "10px", color: "#94a3b8", lineHeight: 1.5 }}>
                  Research-stage machine-learning output and structured behavioral evidence for analyst review.
                </div>
                {!selectedWalletId ? (
                  <div style={analyticsWarningStyle}>
                    This traced wallet is not saved in the selected case. Select a case wallet to load ML and AML assessment.
                  </div>
                ) : (
                  <button type="button" onClick={() => void handleLoadMlAml()} disabled={mlAmlLoading} style={{ ...primaryButtonStyle, marginTop: "10px" }}>
                    {mlAmlLoading ? "Loading ML / AML..." : "Refresh ML / AML"}
                  </button>
                )}
              </div>

              {mlAmlLoading && <div style={analyticsLoadingStyle}>Loading ML risk and AML evidence assessment...</div>}

              {mlRisk && (
                <div style={panelSectionStyle}>
                  <div style={sectionTitleStyle}>ML Risk</div>
                  <div style={{ marginTop: "8px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px" }}>
                    <div style={analyticsStatStyle}><span>Prediction</span><strong>{mlRisk.prediction}</strong></div>
                    <div style={analyticsStatStyle}><span>Model output</span><strong>{(mlRisk.probability * 100).toFixed(1)}%</strong></div>
                    <div style={analyticsStatStyle}><span>Model version</span><strong>{mlRisk.model_version}</strong></div>
                    <div style={analyticsStatStyle}><span>Schema version</span><strong>{mlRisk.schema_version}</strong></div>
                  </div>
                  <div style={mlNoticeStyle}>
                    <strong>{mlRisk.status}</strong>
                    <div style={{ marginTop: "4px", lineHeight: 1.5 }}>{mlRisk.notice}</div>
                  </div>
                  <div style={{ marginTop: "12px" }}>
                    <div style={sectionTitleStyle}>Model Features</div>
                    <div style={{ marginTop: "7px" }}>
                      {Object.entries(mlRisk.features).map(([name, value]) => (
                        <div key={name} style={featureRowStyle}>
                          <span style={{ color: "#94a3b8", wordBreak: "break-word" }}>{name}</span>
                          <strong style={{ textAlign: "right", wordBreak: "break-word" }}>{formatMlValue(value)}</strong>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {amlAssessment && (
                <div style={panelSectionStyle}>
                  <div style={sectionTitleStyle}>AML Evidence Assessment</div>
                  <div style={{ marginTop: "8px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px" }}>
                    <div style={analyticsStatStyle}><span>Review status</span><strong>{amlAssessment.review_status}</strong></div>
                    <div style={analyticsStatStyle}><span>Assessment type</span><strong>{amlAssessment.assessment_type}</strong></div>
                    <div style={analyticsStatStyle}><span>Indicators</span><strong>{amlAssessment.indicator_count}</strong></div>
                    <div style={analyticsStatStyle}><span>High severity</span><strong>{amlAssessment.high_severity_indicator_count}</strong></div>
                  </div>
                  <div style={{ marginTop: "12px" }}>
                    <div style={sectionTitleStyle}>Behavioral Indicators</div>
                    {amlAssessment.signals.length === 0 ? (
                      <div style={analyticsEmptyStyle}>No AML indicators returned.</div>
                    ) : (
                      amlAssessment.signals.map((signal, index) => (
                        <div
                          key={`aml-signal-${index}`}
                          style={{
                            ...amlIndicatorStyle,
                            color: "#f8fafc",
                            minHeight: "70px",
                          }}
                        >
                          <div
                            style={{
                              display: "flex",
                              justifyContent: "space-between",
                              gap: "8px",
                              alignItems: "center",
                            }}
                          >
                            <strong
                              style={{
                                color: "#f8fafc",
                                fontSize: "12px",
                                wordBreak: "break-word",
                              }}
                            >
                              {signal.signal}
                            </strong>

                            <span
                              style={{
                                ...analyticsSeverityStyle,
                                color: "#fbbf24",
                                flexShrink: 0,
                              }}
                            >
                              {signal.severity}
                            </span>
                          </div>

                          <div
                            style={{
                              marginTop: "4px",
                              color: "#64748b",
                              fontSize: "9px",
                              textTransform: "uppercase",
                            }}
                          >
                            Source: {signal.source}
                          </div>

                          <div
                            style={{
                              marginTop: "6px",
                              color: "#cbd5e1",
                              lineHeight: 1.45,
                              fontSize: "11px",
                            }}
                          >
                            {signal.reason}
                          </div>

                          {Object.keys(signal.evidence ?? {}).length > 0 && (
                            <details
                              style={{
                                marginTop: "8px",
                                color: "#94a3b8",
                              }}
                            >
                              <summary
                                style={{
                                  cursor: "pointer",
                                  color: "#60a5fa",
                                }}
                              >
                                Evidence
                              </summary>

                              <pre
                                style={{
                                  ...evidencePreStyle,
                                  marginTop: "6px",
                                  whiteSpace: "pre-wrap",
                                  overflowX: "auto",
                                }}
                              >
                                {JSON.stringify(signal.evidence, null, 2)}
                              </pre>
                            </details>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                  <div style={amlDisclaimerStyle}>
                    AML assessment is a structured research-stage evidence assessment. It does not by itself establish illicit activity or constitute a definitive AML determination.
                  </div>
                </div>
              )}
            </>
          )}

          {/* TRANSACTION DETAILS */}

          {selectedTransfer && investigationTab === "transaction" && (
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
        className="cg-graph"
        style={{
          width: "100%",
          height:
            "calc(100vh - 70px)",
          position: "relative",
        }}
      >
        {token && trace && nodes.length > 0 && (
          <>
            <div
              className="cg-filter"
              style={{
                position: "absolute",
                top: "16px",
                left: "430px",
                zIndex: 10,
                width: "270px",
                padding: "12px",
                background: "rgba(23, 26, 35, 0.96)",
                border: "1px solid #2f3545",
                borderRadius: "8px",
                boxShadow: "0 8px 24px rgba(0,0,0,0.3)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "8px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <strong style={{ fontSize: "12px" }}>
                    Graph Filters
                  </strong>
                  <span style={filterCountBadgeStyle}>
                    {filteredEdges.length}/{edges.length}
                  </span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                  <button
                    type="button"
                    onClick={() => setGraphFiltersOpen((current) => !current)}
                    style={filterIconButtonStyle}
                    title={graphFiltersOpen ? "Collapse filters" : "Expand filters"}
                  >
                    {graphFiltersOpen ? "−" : "+"}
                  </button>
                  <button
                    type="button"
                    onClick={clearGraphFilters}
                  style={{
                    background: "transparent",
                    color: "#94a3b8",
                    border: "none",
                    cursor: "pointer",
                    fontSize: "10px",
                  }}
                >
                  Clear
                  </button>
                </div>
              </div>

              {graphFiltersOpen && (
                <>
              <input
                value={transactionSearch}
                onChange={(event) =>
                  setTransactionSearch(event.target.value)
                }
                placeholder="Transaction hash"
                style={{ ...graphFilterInputStyle, marginBottom: "6px" }}
              />

              <select
                value={assetFilter}
                onChange={(event) => setAssetFilter(event.target.value)}
                style={{ ...graphFilterInputStyle, marginBottom: "6px" }}
              >
                <option value="all">All assets</option>
                {availableAssets.map((asset) => (
                  <option key={asset} value={asset}>
                    {asset}
                  </option>
                ))}
              </select>

              <select
                value={directionFilter}
                onChange={(event) =>
                  setDirectionFilter(event.target.value)
                }
                style={{ ...graphFilterInputStyle, marginBottom: "6px" }}
              >
                <option value="all">All directions</option>
                <option value="outgoing">Outgoing</option>
                <option value="incoming">Incoming</option>
              </select>

              <div style={{ display: "flex", gap: "6px" }}>
                <input
                  type="number"
                  min="0"
                  value={minValueFilter}
                  onChange={(event) => setMinValueFilter(event.target.value)}
                  placeholder="Min value"
                  style={{ ...graphFilterInputStyle, marginBottom: 0 }}
                />
                <input
                  type="number"
                  min="0"
                  value={maxValueFilter}
                  onChange={(event) => setMaxValueFilter(event.target.value)}
                  placeholder="Max value"
                  style={{ ...graphFilterInputStyle, marginBottom: 0 }}
                />
              </div>

              <div
                style={{
                  marginTop: "8px",
                  color: "#94a3b8",
                  fontSize: "10px",
                }}
              >
                Showing {filteredEdges.length} of {edges.length} connections
              </div>
                </>
              )}
            </div>

            <div
              className="cg-graph-actions"
              style={{
                position: "absolute",
                top: "16px",
                right: "20px",
                zIndex: 10,
              display: "flex",
              gap: "8px",
              padding: "8px",
              background: "rgba(23, 26, 35, 0.94)",
              border: "1px solid #2f3545",
              borderRadius: "8px",
              boxShadow: "0 8px 24px rgba(0,0,0,0.3)",
            }}
          >
            <button
              type="button"
              onClick={handleAutoLayout}
              style={graphControlButtonStyle}
            >
              Auto Layout
            </button>
            <button
              type="button"
              onClick={handleResetLayout}
              style={graphControlButtonStyle}
            >
              Reset Layout
            </button>
            <button
              type="button"
              onClick={handleFitGraph}
              style={graphControlButtonStyle}
            >
              Fit Graph
            </button>
          </div>
          </>
        )}

        <ReactFlow
          nodes={filteredNodes}
          edges={filteredEdges}
          fitView
          onInit={setReactFlowInstance}
          minZoom={0.2}
          maxZoom={2}
          onNodesChange={
            handleNodesChange
          }
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

        {token && (
          <>
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
          </>
        )}
      </ReactFlow>
    </div>
  </main>
);
}


const responsiveCss = `
  * { box-sizing: border-box; }
  html, body, #root { margin: 0; width: 100%; height: 100%; overflow: hidden; }
  button, input, select, textarea { font: inherit; }

  .cg-header {
    height: 58px !important;
    padding: 0 16px !important;
  }
  .cg-header h1 { font-size: 18px !important; }
  .cg-header > div:first-child { min-width: 0; }

  .cg-sidebar {
    top: 68px !important;
    left: 12px !important;
    width: 310px !important;
    max-height: calc(100vh - 80px) !important;
    padding: 12px !important;
    border-radius: 12px !important;
    font-size: 11px !important;
  }
  .cg-sidebar h3 { font-size: 14px !important; }
  .cg-sidebar input,
  .cg-sidebar select,
  .cg-sidebar textarea {
    padding: 8px !important;
    font-size: 11px !important;
  }
  .cg-sidebar label {
    font-size: 10px !important;
    margin-top: 8px !important;
    margin-bottom: 4px !important;
  }
  .cg-sidebar button {
    font-size: 10px !important;
  }

  .cg-investigation {
    top: 68px !important;
    right: 12px !important;
    width: 320px !important;
    max-height: calc(100vh - 80px) !important;
    padding: 12px !important;
    border-radius: 12px !important;
  }
  .cg-investigation h3 { font-size: 15px !important; }
  .cg-investigation h4 { font-size: 12px !important; }

  .cg-filter {
    top: 12px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: 290px !important;
    padding: 10px !important;
    border-radius: 10px !important;
  }

  .cg-graph-actions {
    top: 12px !important;
    right: 12px !important;
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 6px !important;
    padding: 6px !important;
    max-width: 230px !important;
  }
  .cg-graph-actions button {
    padding: 6px 8px !important;
    font-size: 10px !important;
    white-space: nowrap !important;
  }

  .cg-graph {
    height: calc(100vh - 58px) !important;
  }

  @media (max-width: 1150px) {
    .cg-sidebar { width: 270px !important; }
    .cg-filter { left: 54% !important; }
    .cg-investigation { width: 290px !important; }
  }

  @media (max-width: 850px) {
    .cg-sidebar { width: 250px !important; left: 8px !important; }
    .cg-filter {
      left: auto !important;
      right: 8px !important;
      transform: none !important;
      width: 260px !important;
    }
    .cg-investigation {
      left: 268px !important;
      right: 8px !important;
      width: auto !important;
      max-height: 46vh !important;
      top: auto !important;
      bottom: 8px !important;
    }
    .cg-graph-actions { top: 72px !important; right: 8px !important; }
  }

  @media (max-width: 650px) {
    .cg-sidebar {
      width: calc(100vw - 16px) !important;
      left: 8px !important;
      max-height: 42vh !important;
    }
    .cg-filter {
      left: 8px !important;
      right: 8px !important;
      width: auto !important;
      transform: none !important;
      top: 52px !important;
    }
    .cg-graph-actions {
      top: 8px !important;
      right: 8px !important;
      max-width: 190px !important;
    }
    .cg-investigation {
      left: 8px !important;
      right: 8px !important;
      bottom: 8px !important;
      max-height: 42vh !important;
    }
  }
`;

const workspaceToggleButtonStyle: React.CSSProperties = {
  background: "#202636",
  color: "#cbd5e1",
  border: "1px solid #39445a",
  borderRadius: "6px",
  padding: "7px 9px",
  cursor: "pointer",
  fontSize: "11px",
  fontWeight: 600,
};

const investigationTabsStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "1fr 1fr",
  gap: "4px",
  padding: "3px",
  marginBottom: "10px",
  background: "#0f1117",
  border: "1px solid #2f3545",
  borderRadius: "7px",
};

const investigationTabStyle = (active: boolean): React.CSSProperties => ({
  border: "none",
  borderRadius: "5px",
  padding: "7px 8px",
  cursor: "pointer",
  background: active ? "#2563eb" : "transparent",
  color: active ? "#ffffff" : "#94a3b8",
  fontSize: "10px",
  fontWeight: 700,
});

const filterCountBadgeStyle: React.CSSProperties = {
  padding: "2px 6px",
  borderRadius: "999px",
  background: "#202a3d",
  color: "#93c5fd",
  fontSize: "9px",
  fontWeight: 700,
};

const filterIconButtonStyle: React.CSSProperties = {
  width: "22px",
  height: "22px",
  padding: 0,
  border: "1px solid #3b4254",
  borderRadius: "5px",
  background: "#202636",
  color: "#cbd5e1",
  cursor: "pointer",
  fontSize: "14px",
  lineHeight: 1,
};

const graphFilterInputStyle = {
  width: "100%",
  boxSizing: "border-box" as const,
  padding: "7px 8px",
  background: "#0f1117",
  color: "#ffffff",
  border: "1px solid #3b4254",
  borderRadius: "5px",
  outline: "none",
  fontSize: "10px",
};

const graphControlButtonStyle = {
  background: "#272d3a",
  color: "#ffffff",
  border: "1px solid #475569",
  borderRadius: "5px",
  padding: "7px 10px",
  cursor: "pointer",
  fontSize: "11px",
  fontWeight: 600,
} as const;

function formatSeconds(seconds: number | null): string {
  if (seconds === null || !Number.isFinite(seconds)) {
    return "—";
  }

  if (seconds < 60) {
    return `${seconds.toFixed(0)}s`;
  }

  const minutes = seconds / 60;
  if (minutes < 60) {
    return `${minutes.toFixed(1)}m`;
  }

  const hours = minutes / 60;
  if (hours < 24) {
    return `${hours.toFixed(1)}h`;
  }

  return `${(hours / 24).toFixed(1)}d`;
}

const analyticsStatStyle: React.CSSProperties = {
  padding: "8px",
  background: "#0f1117",
  border: "1px solid #3b4254",
  borderRadius: "6px",
  display: "flex",
  flexDirection: "column",
  gap: "3px",
};

const analyticsEmptyStyle: React.CSSProperties = {
  marginTop: "7px",
  padding: "8px",
  color: "#64748b",
  fontSize: "10px",
  background: "#0f1117",
  borderRadius: "5px",
};

const analyticsListItemStyle: React.CSSProperties = {
  marginTop: "7px",
  padding: "9px",
  background: "#0f1117",
  border: "1px solid #3b4254",
  borderRadius: "6px",
  fontSize: "10px",
  lineHeight: 1.45,
};

const analyticsSignalStyle: React.CSSProperties = {
  marginTop: "7px",
  padding: "9px",
  background: "#172033",
  border: "1px solid #334155",
  borderRadius: "6px",
  fontSize: "10px",
  lineHeight: 1.45,
};

const analyticsSeverityStyle: React.CSSProperties = {
  marginLeft: "7px",
  padding: "2px 5px",
  borderRadius: "999px",
  background: "#202a3d",
  color: "#93c5fd",
  fontSize: "8px",
  textTransform: "uppercase",
};

function formatMlValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") return Number.isFinite(value) ? formatNumber(value) : "—";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "string") return value;
  return JSON.stringify(value);
}

const analyticsWarningStyle: React.CSSProperties = { marginTop: "10px", padding: "10px", background: "#2a1f0b", border: "1px solid #92400e", borderRadius: "6px", color: "#fcd34d", fontSize: "11px", lineHeight: 1.5 };
const analyticsLoadingStyle: React.CSSProperties = { padding: "14px", color: "#94a3b8", fontSize: "11px", textAlign: "center" };
const mlNoticeStyle: React.CSSProperties = { marginTop: "10px", padding: "10px", background: "#172033", border: "1px solid #334155", borderRadius: "6px", color: "#cbd5e1", fontSize: "10px", lineHeight: 1.45 };
const featureRowStyle: React.CSSProperties = { display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: "8px", padding: "6px 0", borderBottom: "1px solid #242b39", fontSize: "9px" };
const amlIndicatorStyle: React.CSSProperties = { marginTop: "7px", padding: "9px", background: "#172033", border: "1px solid #3b4254", borderRadius: "6px", fontSize: "10px", lineHeight: 1.45 };
const noteCardStyle: React.CSSProperties = { marginTop: "8px", padding: "10px", background: "#0f1117", border: "1px solid #3b4254", borderRadius: "6px" };
const noteMetaStyle: React.CSSProperties = { display: "flex", justifyContent: "space-between", gap: "8px", marginTop: "8px", color: "#64748b", fontSize: "8px", lineHeight: 1.4, flexWrap: "wrap" };
const noteActionsStyle: React.CSSProperties = { display: "flex", justifyContent: "flex-end", gap: "6px", marginTop: "8px" };
const notePrimaryActionStyle: React.CSSProperties = { border: "1px solid #2563eb", borderRadius: "5px", padding: "5px 8px", background: "#2563eb", color: "#ffffff", cursor: "pointer", fontSize: "9px", fontWeight: 700 };
const noteSecondaryActionStyle: React.CSSProperties = { border: "1px solid #475569", borderRadius: "5px", padding: "5px 8px", background: "#272d3a", color: "#cbd5e1", cursor: "pointer", fontSize: "9px", fontWeight: 700 };
const noteDangerActionStyle: React.CSSProperties = { border: "1px solid #7f1d1d", borderRadius: "5px", padding: "5px 8px", background: "#2a1518", color: "#fca5a5", cursor: "pointer", fontSize: "9px", fontWeight: 700 };
const evidencePreStyle: React.CSSProperties = { margin: "6px 0 0", padding: "8px", maxHeight: "180px", overflow: "auto", background: "#0f1117", borderRadius: "5px", color: "#cbd5e1", fontSize: "9px", whiteSpace: "pre-wrap", wordBreak: "break-word" };
const amlDisclaimerStyle: React.CSSProperties = { marginTop: "12px", padding: "9px", background: "#0f1117", border: "1px solid #3b4254", borderRadius: "6px", color: "#94a3b8", fontSize: "9px", lineHeight: 1.5 };

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

const secondaryButtonStyle: React.CSSProperties =
  {
    width: "auto",
    marginTop: 0,
    padding: "7px 10px",
    background: "#111827",
    color: "#cbd5e1",
    border: "1px solid #334155",
    borderRadius: "6px",
    cursor: "pointer",
    fontWeight: 600,
    fontSize: "10px",
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










