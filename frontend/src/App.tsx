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

type PeelTransfer = {
  asset: string | null;
  block_number: number | null;
  category: string | null;
  chain: string | null;
  contract_address: string | null;
  from_address: string;
  from_chain: string | null;
  timestamp: string | null;
  to_address: string;
  to_chain: string | null;
  transaction_hash: string;
  value: number;
};

type PeelHopValue = {
  from_transaction: string;
  to_transaction: string;
  input_value: number;
  forwarded_value: number;
  value_difference: number;
  value_reduction: boolean;
  retained_amount: number;
  forward_ratio: number | null;
  retention_ratio: number | null;
};

type PeelCandidate = {
  wallets: { address: string; chain: string }[];
  hop_count: number;
  wallet_count: number;
  transfers: PeelTransfer[];
  value_progression: {
    input_value: number | null;
    output_value: number | null;
    value_difference: number | null;
    value_ratio: number | null;
    values: number[];
    available: boolean;
    value_reduction: boolean;
    retained_amount: number | null;
    retention_ratio: number | null;
    forward_ratio: number | null;
  };
  hop_value_progression: PeelHopValue[];
  timing: {
    timestamps_available: boolean;
    timestamps: number[];
    gaps_seconds: number[];
    average_gap_seconds: number | null;
    minimum_gap_seconds: number | null;
    maximum_gap_seconds: number | null;
    chronological: boolean;
  };
  same_asset: boolean;
  evidence: string[];
};

type PeelChainResponse = {
  address: string;
  chain: string;
  max_hops: number;
  status: string;
  candidate_count: number;
  candidates: PeelCandidate[];
  notice: string;
};

type CrossChainEvent = {
  address?: string;
  receiver_address?: string;
  sender_address?: string;
  chain: string | null;
  transaction_hash: string;
  asset: string | null;
  value: number | null;
  category: string | null;
  block_number: number | null;
  timestamp: string | null;
  contract_address: string | null;
};

type CrossChainCandidate = {
  source: CrossChainEvent;
  destination: CrossChainEvent;
  time_gap_seconds: number | null;
  value_difference: number | null;
  value_ratio: number | null;
  asset_changed: boolean | null;
  signals: string[];
  signal_count: number;
  confidence: number;
  status: string;
  evidence: string[];
};

type CrossChainResponse = {
  address: string;
  source_chain: string;
  target_chain: string | null;
  time_window_minutes: number;
  value_tolerance: number;
  status: string;
  candidate_count: number;
  candidates: CrossChainCandidate[];
  notice: string;
};

type CandidateLinkCandidate = {
  name: string | null;
  address: string;
  chain: string;
  source: string | null;
  risk_category: string | null;
  confidence: number | null;
  hop: number | null;
  link_basis: string;
  link_strength: string;
  signals: string[];
  signal_count: number;
  evidence: string | null;
  wallets: string[];
  transfers: TraceTransfer[];
  reason: string | null;
};

type CandidateLinkingResponse = {
  address: string;
  chain: string;
  max_hops: number;
  status: string;
  candidate_count: number;
  candidates: CandidateLinkCandidate[];
  method: string;
  notice: string;
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
  hop_number?: number;
  source_type?: "trace" | "peel_chain" | "cross_chain";
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

type RiskEntity = {
  address: string;
  chain: string;
  entity_type: string;
  name: string | null;
  source: string | null;
  risk_category: string | null;
  confidence: number | null;
  evidence: string | null;
  updated_at: string | null;
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

  const [authMode, setAuthMode] =
    useState<"login" | "register" | "verify">("login");

  const [verificationEmail, setVerificationEmail] =
    useState("");

  const [verificationCode, setVerificationCode] =
    useState("");

  const [fullName, setFullName] =
    useState("");

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [confirmPassword, setConfirmPassword] =
    useState("");

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
     PEEL CHAIN STATE
  ========================= */

  const [peelMaxHops, setPeelMaxHops] =
    useState("5");

  const [peelChain, setPeelChain] =
    useState<PeelChainResponse | null>(null);

  const [peelLoading, setPeelLoading] =
    useState(false);

  const [peelFilter, setPeelFilter] =
    useState("all");

  const [peelSort, setPeelSort] =
    useState("strongest");

  const [selectedPeelCandidateKey, setSelectedPeelCandidateKey] =
    useState<string | null>(null);

  const [peelExpanded, setPeelExpanded] =
    useState(false);

  /* =========================
     CROSS-CHAIN STATE
  ========================= */

  const [crossChainTarget, setCrossChainTarget] =
    useState("all");

  const [crossChainWindow, setCrossChainWindow] =
    useState("120");

  const [crossChainTolerance, setCrossChainTolerance] =
    useState("20");

  const [crossChain, setCrossChain] =
    useState<CrossChainResponse | null>(null);

  const [crossChainLoading, setCrossChainLoading] =
    useState(false);

  const [crossChainExpanded, setCrossChainExpanded] =
    useState(false);

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
     INTELLIGENCE STATE
  ========================= */

  const [riskEntities, setRiskEntities] =
    useState<RiskEntity[]>([]);

  const [intelligenceLoading, setIntelligenceLoading] =
    useState(false);

  const [intelligenceChainFilter, setIntelligenceChainFilter] =
    useState("all");

  const [intelligenceTypeFilter, setIntelligenceTypeFilter] =
    useState("all");

  const [intelligenceSourceFilter, setIntelligenceSourceFilter] =
    useState("all");

  const [intelligenceRiskFilter, setIntelligenceRiskFilter] =
    useState("all");

  const [newRiskEntityAddress, setNewRiskEntityAddress] =
    useState("");

  const [newRiskEntityChain, setNewRiskEntityChain] =
    useState("ethereum");

  const [newRiskEntityType, setNewRiskEntityType] =
    useState("vasp");

  const [newRiskEntityName, setNewRiskEntityName] =
    useState("");

  const [newRiskEntitySource, setNewRiskEntitySource] =
    useState("");

  const [newRiskEntityRiskCategory, setNewRiskEntityRiskCategory] =
    useState("");

  const [newRiskEntityConfidence, setNewRiskEntityConfidence] =
    useState("0.95");

  const [newRiskEntityEvidence, setNewRiskEntityEvidence] =
    useState("");

  const [riskEntitySaving, setRiskEntitySaving] =
    useState(false);

  const [editingRiskEntityKey, setEditingRiskEntityKey] =
    useState<string | null>(null);

  const [editingRiskEntityName, setEditingRiskEntityName] =
    useState("");

  const [editingRiskEntityType, setEditingRiskEntityType] =
    useState("");

  const [editingRiskEntitySource, setEditingRiskEntitySource] =
    useState("");

  const [editingRiskEntityRiskCategory, setEditingRiskEntityRiskCategory] =
    useState("");

  const [editingRiskEntityConfidence, setEditingRiskEntityConfidence] =
    useState("");

  const [editingRiskEntityEvidence, setEditingRiskEntityEvidence] =
    useState("");

  /* =========================
     CANDIDATE LINKING STATE
  ========================= */

  const [candidateLinking, setCandidateLinking] =
    useState<CandidateLinkingResponse | null>(null);

  const [candidateLinkingLoading, setCandidateLinkingLoading] =
    useState(false);

  const [candidateLinkingMaxHops, setCandidateLinkingMaxHops] =
    useState("2");

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

  const [highlightPathEnabled, setHighlightPathEnabled] =
    useState(false);

  const [selectedTransfer, setSelectedTransfer] =
    useState<WalletTransaction | null>(null);

  const [investigationTab, setInvestigationTab] =
    useState<
      "wallet"
      | "transaction"
      | "analytics"
      | "ml-aml"
      | "vasp"
      | "intelligence"
      | "candidate-linking"
      | "notes"
      | "evidence"
    >("wallet");

  const [investigationMenuOpen, setInvestigationMenuOpen] =
    useState(true);

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

  const [authNotice, setAuthNotice] =
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
     AUTHENTICATION
  ========================= */

  async function readAuthError(
    response: Response,
    fallback: string,
  ) {
    const raw = await response.text();

    if (!raw) {
      return fallback;
    }

    try {
      const parsed = JSON.parse(raw) as {
        detail?: unknown;
        message?: unknown;
      };

      if (typeof parsed.detail === "string") {
        return parsed.detail;
      }

      if (typeof parsed.message === "string") {
        return parsed.message;
      }
    } catch {
      // Fall back to the raw response when it is not JSON.
    }

    return raw;
  }

  async function handleLogin(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const trimmedEmail = email.trim();

    setLoginLoading(true);
    setError(null);
    setAuthNotice(null);

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
            email: trimmedEmail,
            password,
          }),
        },
      );

      if (!response.ok) {
        const message = await readAuthError(
          response,
          `Login failed with status ${response.status}`,
        );

        // An existing account may have been created but not verified yet.
        // Move the user directly to the verification flow instead of
        // leaving them at a dead-end login error.
        if (
          response.status === 403 &&
          message.toLowerCase().includes("verify")
        ) {
          setVerificationEmail(trimmedEmail);
          setVerificationCode("");
          setAuthMode("verify");
          setError(message);
          return;
        }

        throw new Error(message);
      }

      const data: LoginResponse =
        await response.json();

      localStorage.setItem(
        "access_token",
        data.access_token,
      );

      setToken(data.access_token);
      setPassword("");
      setConfirmPassword("");
      setAuthNotice(null);
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

  async function handleRegister(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const trimmedFullName = fullName.trim();
    const trimmedEmail = email.trim();

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (!password) {
      setError("Password is required.");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setLoginLoading(true);
    setError(null);
    setAuthNotice(null);

    try {
      const registerResponse = await fetch(
        `${API_URL}/users/`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            email: trimmedEmail,
            password,
            full_name:
              trimmedFullName || null,
          }),
        },
      );

      if (!registerResponse.ok) {
        const message = await readAuthError(
          registerResponse,
          `Account creation failed with status ${registerResponse.status}`,
        );

        // The backend intentionally returns 409 for an existing email.
        // For an unverified account, the resend endpoint can safely issue
        // another code and lets the user continue the verification flow.
        if (registerResponse.status === 409) {
          setVerificationEmail(trimmedEmail);
          setVerificationCode("");

          try {
            const resendResponse = await fetch(
              `${API_URL}/users/resend-verification`,
              {
                method: "POST",
                headers: {
                  "Content-Type":
                    "application/json",
                },
                body: JSON.stringify({
                  email: trimmedEmail,
                }),
              },
            );

            if (!resendResponse.ok) {
              throw new Error(
                await readAuthError(
                  resendResponse,
                  "This email is already registered.",
                ),
              );
            }

            setFullName("");
            setPassword("");
            setConfirmPassword("");
            setAuthMode("verify");
            setError(null);
            setAuthNotice(
              "This email is already registered. If it still needs verification, a new code has been sent.",
            );
            return;
          } catch {
            // Keep the original registration conflict if the resend
            // request itself cannot be completed.
          }
        }

        throw new Error(message);
      }

      setVerificationEmail(trimmedEmail);
      setVerificationCode("");
      setFullName("");
      setPassword("");
      setConfirmPassword("");
      setAuthMode("verify");
      setError(null);
      setAuthNotice(
        "Account created. Check your email for the 6-digit verification code.",
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Account creation failed",
      );
    } finally {
      setLoginLoading(false);
    }
  }

  async function handleVerifyEmail(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const trimmedEmail = verificationEmail.trim();
    const trimmedCode = verificationCode.trim();

    if (!trimmedEmail) {
      setError("Verification email is required.");
      return;
    }

    if (!/^\d{6}$/.test(trimmedCode)) {
      setError("Enter the 6-digit verification code.");
      return;
    }

    setLoginLoading(true);
    setError(null);
    setAuthNotice(null);

    try {
      const response = await fetch(
        `${API_URL}/users/verify-email`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            email: trimmedEmail,
            code: trimmedCode,
          }),
        },
      );

      if (!response.ok) {
        throw new Error(
          await readAuthError(
            response,
            `Email verification failed with status ${response.status}`,
          ),
        );
      }

      setEmail(trimmedEmail);
      setVerificationCode("");
      setAuthMode("login");
      setError(null);
      setAuthNotice(
        "Email verified successfully. You can now sign in.",
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Email verification failed",
      );
    } finally {
      setLoginLoading(false);
    }
  }

  async function handleResendVerification() {
    const trimmedEmail = verificationEmail.trim();

    if (!trimmedEmail) {
      setError("Verification email is required.");
      return;
    }

    setLoginLoading(true);
    setError(null);
    setAuthNotice(null);

    try {
      const response = await fetch(
        `${API_URL}/users/resend-verification`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            email: trimmedEmail,
          }),
        },
      );

      if (!response.ok) {
        throw new Error(
          await readAuthError(
            response,
            `Could not resend verification code (status ${response.status})`,
          ),
        );
      }

      setVerificationCode("");
      setAuthNotice(
        "If this account requires verification, a new code has been sent to your email.",
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not resend verification code",
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
    setPeelChain(null);
    setSelectedPeelCandidateKey(null);
    setCrossChain(null);
    setRisk(null);
    setGraphAnalytics(null);
    setTimelineAnalytics(null);
    setMlRisk(null);
    setAmlAssessment(null);
    setVaspAttribution(null);
    setRiskEntities([]);
    cancelEditingRiskEntity();
    setCandidateLinking(null);
    setNotes([]);
    setNewNoteContent("");
    setEditingNoteId(null);
    setEditingNoteContent("");

    setNodes([]);
    setEdges([]);

    setSelectedWallet(null);
    setSelectedTransfer(null);

    setError(null);
    setAuthNotice(null);
    setAuthMode("login");
    setVerificationEmail("");
    setVerificationCode("");
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
      setPeelChain(null);
      setSelectedPeelCandidateKey(null);
      setCrossChain(null);
      setRisk(null);
      setGraphAnalytics(null);
      setTimelineAnalytics(null);
      setMlRisk(null);
      setAmlAssessment(null);
      setVaspAttribution(null);
      setRiskEntities([]);
      cancelEditingRiskEntity();
      setCandidateLinking(null);
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
    setRiskEntities([]);
    cancelEditingRiskEntity();
    setCandidateLinking(null);
    setSelectedWallet(null);
    setHighlightPathEnabled(false);
    setSelectedTransfer(null);
    setSelectedPeelCandidateKey(null);

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

          // Vertical hop layout: target at the top, then each hop below it.
          // Wallets in the same hop spread horizontally so dense levels grow
          // wider instead of compressing or overlapping.
          const horizontalSpacing = 300;
          const verticalSpacing = 300;

          const levelWidth =
            (levelWallets.length - 1) *
            horizontalSpacing;

          const x =
            levelIndex *
            horizontalSpacing -
            levelWidth / 2;

          const y = level * verticalSpacing;

          return {
            id: wallet,

            position: {
              x,
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
                ? "2px solid #FF5E68"
                : "1px solid #789BA0",

              background:
                isTarget
                  ? "#281316"
                  : "#08181D",

              color: "#F3FAFA",

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
                fill: "#F3FAFA",
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
     PEEL CHAIN ANALYSIS
  ========================= */

  async function handlePeelChainAnalysis() {
    if (!token) {
      setError("Please login first.");
      return;
    }

    if (!selectedCase) {
      setError("Create or select a case first.");
      return;
    }

    const hops = Number(peelMaxHops);
    if (!Number.isInteger(hops) || hops < 2 || hops > 5) {
      setError("Peel Chain max hops must be between 2 and 5.");
      return;
    }

    setPeelLoading(true);
    setPeelExpanded(true);
    setError(null);
    setSelectedPeelCandidateKey(null);

    try {
      const response = await fetch(
        `${API_URL}/wallets/peel-chain/${address}?chain=${encodeURIComponent(chain)}&max_hops=${hops}`,
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
          message || `Peel Chain API returned ${response.status}`,
        );
      }

      const data: PeelChainResponse = await response.json();
      setPeelChain(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Peel Chain analysis failed",
      );
    } finally {
      setPeelLoading(false);
    }
  }

  /* =========================
     CROSS-CHAIN ANALYSIS
  ========================= */

  async function handleCrossChainAnalysis() {
    if (!token) {
      setError("Please login first.");
      return;
    }

    if (!selectedCase) {
      setError("Create or select a case first.");
      return;
    }

    const windowMinutes = Number(crossChainWindow);
    const tolerancePercent = Number(crossChainTolerance);

    if (
      !Number.isInteger(windowMinutes) ||
      windowMinutes < 1 ||
      windowMinutes > 1440
    ) {
      setError("Cross-Chain time window must be between 1 and 1440 minutes.");
      return;
    }

    if (
      !Number.isFinite(tolerancePercent) ||
      tolerancePercent < 0 ||
      tolerancePercent > 100
    ) {
      setError("Cross-Chain value tolerance must be between 0 and 100%.");
      return;
    }

    setCrossChainLoading(true);
    setCrossChainExpanded(true);
    setError(null);

    try {
      const target =
        crossChainTarget !== "all"
          ? `&target_chain=${encodeURIComponent(crossChainTarget)}`
          : "";

      const response = await fetch(
        `${API_URL}/wallets/cross-chain/${address}?source_chain=${encodeURIComponent(
          chain,
        )}&time_window_minutes=${windowMinutes}&value_tolerance=${
          tolerancePercent / 100
        }${target}`,
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
          message ||
            `Cross-Chain API returned ${response.status}`,
        );
      }

      const data: CrossChainResponse = await response.json();
      setCrossChain(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Cross-Chain analysis failed",
      );
    } finally {
      setCrossChainLoading(false);
    }
  }

  function handleInspectCrossChainTransfer(
    event: CrossChainEvent,
    side: "source" | "destination",
  ) {
    const sourceAddress =
      side === "source"
        ? event.address ?? ""
        : event.sender_address ?? "";

    const targetAddress =
      side === "source"
        ? event.receiver_address ?? ""
        : event.address ?? "";

    setSelectedWallet(null);
    setSelectedTransfer({
      source: sourceAddress,
      target: targetAddress,
      transfer: {
        transaction_hash: event.transaction_hash,
        asset: event.asset,
        value: event.value,
        category: event.category,
        block_number: event.block_number,
        timestamp: event.timestamp,
        contract_address: event.contract_address,
      },
      hop_count: 1,
      hop_number: side === "source" ? 1 : 2,
      source_type: "cross_chain",
    });
    setInvestigationTab("transaction");
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

  /* =========================
     INTELLIGENCE REGISTRY
  ========================= */

  async function handleLoadRiskEntities() {
    if (!token) {
      setError("Please login first.");
      return;
    }

    setIntelligenceLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();

      if (intelligenceChainFilter !== "all") {
        params.set("chain", intelligenceChainFilter);
      }
      if (intelligenceTypeFilter !== "all") {
        params.set("entity_type", intelligenceTypeFilter);
      }
      if (intelligenceSourceFilter !== "all") {
        params.set("source", intelligenceSourceFilter);
      }
      if (intelligenceRiskFilter !== "all") {
        params.set("risk_category", intelligenceRiskFilter);
      }

      const query = params.toString();
      const response = await fetch(
        `${API_URL}/intelligence/risk-entities${query ? `?${query}` : ""}`,
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
          message || `Intelligence registry returned ${response.status}`,
        );
      }

      const data: RiskEntity[] = await response.json();
      setRiskEntities(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load intelligence registry",
      );
    } finally {
      setIntelligenceLoading(false);
    }
  }

  function resetRiskEntityForm() {
    setNewRiskEntityAddress(selectedWallet ?? "");
    setNewRiskEntityChain(chain);
    setNewRiskEntityType("vasp");
    setNewRiskEntityName("");
    setNewRiskEntitySource("");
    setNewRiskEntityRiskCategory("centralized_exchange");
    setNewRiskEntityConfidence("0.95");
    setNewRiskEntityEvidence("");
  }

  async function handleCreateRiskEntity(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!token) {
      setError("Please login first.");
      return;
    }

    const addressValue = newRiskEntityAddress.trim();
    const chainValue = newRiskEntityChain.trim();
    const typeValue = newRiskEntityType.trim();
    const nameValue = newRiskEntityName.trim();
    const sourceValue = newRiskEntitySource.trim();
    const riskCategoryValue = newRiskEntityRiskCategory.trim();
    const evidenceValue = newRiskEntityEvidence.trim();
    const confidenceValue = Number(newRiskEntityConfidence);

    if (!addressValue) {
      setError("Risk entity address is required.");
      return;
    }
    if (!chainValue) {
      setError("Risk entity chain is required.");
      return;
    }
    if (!typeValue) {
      setError("Entity type is required.");
      return;
    }
    if (!nameValue) {
      setError("Risk entity name is required.");
      return;
    }
    if (!sourceValue) {
      setError("Intelligence source is required.");
      return;
    }
    if (
      !Number.isFinite(confidenceValue) ||
      confidenceValue < 0 ||
      confidenceValue > 1
    ) {
      setError("Confidence must be between 0 and 1.");
      return;
    }

    setRiskEntitySaving(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/intelligence/risk-entities`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          address: addressValue,
          chain: chainValue,
          entity_type: typeValue,
          name: nameValue,
          source: sourceValue,
          risk_category: riskCategoryValue || undefined,
          confidence: confidenceValue,
          evidence: evidenceValue || undefined,
        }),
      });

      if (response.status === 401) {
        localStorage.removeItem("access_token");
        setToken(null);
        throw new Error("Session expired. Please login again.");
      }

      if (!response.ok) {
        const message = await response.text();
        throw new Error(
          message || `Create risk entity returned ${response.status}`,
        );
      }

      resetRiskEntityForm();
      await handleLoadRiskEntities();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to create risk entity",
      );
    } finally {
      setRiskEntitySaving(false);
    }
  }

  function startEditingRiskEntity(entity: RiskEntity) {
    setEditingRiskEntityKey(`${entity.chain}:${entity.address.toLowerCase()}`);
    setEditingRiskEntityName(entity.name ?? "");
    setEditingRiskEntityType(entity.entity_type);
    setEditingRiskEntitySource(entity.source ?? "");
    setEditingRiskEntityRiskCategory(entity.risk_category ?? "");
    setEditingRiskEntityConfidence(
      entity.confidence !== null ? String(entity.confidence) : "",
    );
    setEditingRiskEntityEvidence(entity.evidence ?? "");
    setError(null);
  }

  function cancelEditingRiskEntity() {
    setEditingRiskEntityKey(null);
    setEditingRiskEntityName("");
    setEditingRiskEntityType("");
    setEditingRiskEntitySource("");
    setEditingRiskEntityRiskCategory("");
    setEditingRiskEntityConfidence("");
    setEditingRiskEntityEvidence("");
  }

  async function handleUpdateRiskEntity(entity: RiskEntity) {
    if (!token) {
      setError("Please login first.");
      return;
    }

    const nameValue = editingRiskEntityName.trim();
    const typeValue = editingRiskEntityType.trim();
    const sourceValue = editingRiskEntitySource.trim();
    const riskCategoryValue = editingRiskEntityRiskCategory.trim();
    const evidenceValue = editingRiskEntityEvidence.trim();
    const confidenceValue = Number(editingRiskEntityConfidence);

    if (!nameValue) {
      setError("Risk entity name is required.");
      return;
    }
    if (!typeValue) {
      setError("Entity type is required.");
      return;
    }
    if (!sourceValue) {
      setError("Intelligence source is required.");
      return;
    }
    if (
      !Number.isFinite(confidenceValue) ||
      confidenceValue < 0 ||
      confidenceValue > 1
    ) {
      setError("Confidence must be between 0 and 1.");
      return;
    }

    setRiskEntitySaving(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/intelligence/risk-entities/${encodeURIComponent(entity.address)}?chain=${encodeURIComponent(entity.chain)}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            entity_type: typeValue,
            name: nameValue,
            source: sourceValue,
            risk_category: riskCategoryValue || undefined,
            confidence: confidenceValue,
            evidence: evidenceValue || undefined,
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
        throw new Error(
          message || `Update risk entity returned ${response.status}`,
        );
      }

      cancelEditingRiskEntity();
      await handleLoadRiskEntities();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to update risk entity",
      );
    } finally {
      setRiskEntitySaving(false);
    }
  }

  async function handleDeleteRiskEntity(entity: RiskEntity) {
    if (!token) {
      setError("Please login first.");
      return;
    }

    const confirmed = window.confirm(
      `Delete the intelligence record "${entity.name ?? entity.address}"? This action cannot be undone.`,
    );

    if (!confirmed) {
      return;
    }

    setRiskEntitySaving(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/intelligence/risk-entities/${encodeURIComponent(entity.address)}?chain=${encodeURIComponent(entity.chain)}`,
        {
          method: "DELETE",
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
          message || `Delete risk entity returned ${response.status}`,
        );
      }

      if (
        editingRiskEntityKey ===
        `${entity.chain}:${entity.address.toLowerCase()}`
      ) {
        cancelEditingRiskEntity();
      }

      await handleLoadRiskEntities();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to delete risk entity",
      );
    } finally {
      setRiskEntitySaving(false);
    }
  }

  async function handleCandidateLinking() {
    if (!token) {
      setError("Please login first.");
      return;
    }

    if (!selectedWallet) {
      setError("Select a wallet from the investigation graph first.");
      return;
    }

    const hops = Number(candidateLinkingMaxHops);
    if (!Number.isInteger(hops) || hops < 0 || hops > 2) {
      setError("Candidate Linking max hops must be between 0 and 2.");
      return;
    }

    setCandidateLinkingLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/wallets/candidate-linking/${selectedWallet}?chain=${encodeURIComponent(
          chain,
        )}&max_hops=${hops}`,
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
          message ||
            `Candidate Linking API returned ${response.status}`,
        );
      }

      const data: CandidateLinkingResponse =
        await response.json();

      setCandidateLinking(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Candidate Linking failed",
      );
    } finally {
      setCandidateLinkingLoading(false);
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
    // When path highlighting is active, only nodes that belong to the
    // highlighted investigation path may be moved. Everything else stays
    // fixed so the investigator can reposition the active path without
    // disturbing the surrounding graph.
    const allowedChanges =
      highlightPathEnabled && selectedWallet
        ? changes.filter((change) => {
            if (change.type !== "position") {
              return true;
            }

            return highlightedPathNodes.has(change.id);
          })
        : changes;

    if (allowedChanges.length === 0) {
      return;
    }

    setNodes((currentNodes) =>
      applyNodeChanges(allowedChanges, currentNodes),
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

    const nodesByLevel = new Map<number, Node[]>();

    nodes.forEach((node) => {
      const level = levels.get(node.id) ?? 0;
      const levelNodes = nodesByLevel.get(level) ?? [];
      levelNodes.push(node);
      nodesByLevel.set(level, levelNodes);
    });

    setNodes((currentNodes) =>
      currentNodes.map((node) => {
        const level = levels.get(node.id) ?? 0;
        const levelNodes = nodesByLevel.get(level) ?? [];
        const index = levelNodes.findIndex((item) => item.id === node.id);
        const horizontalSpacing = 300;
        const verticalSpacing = 300;
        const levelWidth = (levelNodes.length - 1) * horizontalSpacing;

        return {
          ...node,
          position: {
            x: index * horizontalSpacing - levelWidth / 2,
            y: level * verticalSpacing,
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
    setHighlightPathEnabled(false);
    setSelectedWallet(node.id);
    const savedWallet = wallets.find(
      (wallet) => wallet.address.toLowerCase() === node.id.toLowerCase(),
    );
    setSelectedWalletId(savedWallet?.id ?? null);
    setInvestigationTab("wallet");
    setInvestigationMenuOpen(true);
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
      // Keep the selected wallet/path active when a highlighted edge is
      // clicked. Opening transaction details should not clear the
      // investigation highlight.
      const clickedEdgeIsHighlighted =
        highlightPathEnabled &&
        highlightedPathEdges.has(edge.id);

      if (!clickedEdgeIsHighlighted) {
        setSelectedWallet(null);
        setHighlightPathEnabled(false);
      }

      setSelectedTransfer(
        matchingTransfer,
      );
      setInvestigationTab("transaction");
      setInvestigationMenuOpen(false);
    }
  }

  /* =========================
     CLOSE INVESTIGATION
  ========================= */

  function closeInvestigationPanel() {
    setSelectedWallet(null);
    setHighlightPathEnabled(false);
    setSelectedTransfer(null);
    setInvestigationTab("wallet");
    setInvestigationMenuOpen(true);
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
     PEEL CHAIN GRAPH HIGHLIGHTING
  ========================= */

  function getPeelCandidateKey(candidate: PeelCandidate): string {
    const firstTransaction =
      candidate.transfers[0]?.transaction_hash ??
      candidate.wallets[0]?.address ??
      "";

    const lastTransaction =
      candidate.transfers[candidate.transfers.length - 1]?.transaction_hash ??
      candidate.wallets[candidate.wallets.length - 1]?.address ??
      "";

    return `${firstTransaction}:${lastTransaction}`.toLowerCase();
  }

  function handleSelectPeelCandidate(candidate: PeelCandidate) {
    setSelectedPeelCandidateKey(
      getPeelCandidateKey(candidate),
    );
  }

  function handleInspectPeelTransfer(
    candidate: PeelCandidate,
    transfer: PeelTransfer,
    transferIndex: number,
  ) {
    setSelectedWallet(null);
    setSelectedTransfer({
      source: transfer.from_address,
      target: transfer.to_address,
      transfer: {
        transaction_hash: transfer.transaction_hash,
        asset: transfer.asset,
        value: transfer.value,
        category: transfer.category,
        block_number: transfer.block_number,
        timestamp: transfer.timestamp,
        contract_address: transfer.contract_address,
      },
      hop_count: candidate.hop_count,
      hop_number: transferIndex + 1,
      source_type: "peel_chain",
    });
    setInvestigationTab("transaction");
  }

  function clearPeelCandidateSelection() {
    setSelectedPeelCandidateKey(null);
  }

  /* =========================
     RENDER
  ========================= */

  const filteredPeelCandidates = (() => {
    if (!peelChain) {
      return [];
    }

    const filtered = peelChain.candidates.filter((candidate) => {
      const pattern = getPeelPatternAssessment(candidate);

      switch (peelFilter) {
        case "strong":
          return pattern.label === "Strong pattern";
        case "same-asset":
          return candidate.same_asset;
        case "value-reduced":
          return candidate.value_progression.value_reduction;
        case "chronological":
          return candidate.timing.chronological;
        default:
          return true;
      }
    });

    return [...filtered].sort((left, right) => {
      const leftPattern = getPeelPatternAssessment(left);
      const rightPattern = getPeelPatternAssessment(right);

      switch (peelSort) {
        case "hops":
          return right.hop_count - left.hop_count;
        case "retained":
          return (right.value_progression.retained_amount ?? 0) -
            (left.value_progression.retained_amount ?? 0);
        case "gap":
          return (left.timing.average_gap_seconds ?? Number.POSITIVE_INFINITY) -
            (right.timing.average_gap_seconds ?? Number.POSITIVE_INFINITY);
        case "strongest":
        default:
          return rightPattern.signalCount - leftPattern.signalCount ||
            right.hop_count - left.hop_count;
      }
    });
  })();

  const highlightedPeelCandidate =
    peelChain?.candidates.find(
      (candidate) =>
        getPeelCandidateKey(candidate) ===
        selectedPeelCandidateKey,
    ) ?? null;

  const highlightedPeelWallets = new Set(
    (highlightedPeelCandidate?.wallets ?? []).map(
      (wallet) => wallet.address.toLowerCase(),
    ),
  );

  const highlightedPeelConnections = new Set(
    (highlightedPeelCandidate?.wallets ?? [])
      .slice(0, -1)
      .map((wallet, index) => {
        const nextWallet =
          highlightedPeelCandidate?.wallets[index + 1];

        return nextWallet
          ? `${wallet.address.toLowerCase()}->${nextWallet.address.toLowerCase()}`
          : null;
      })
      .filter((value): value is string => Boolean(value)),
  );

  /* =========================
     GRAPH PATH HIGHLIGHTING
  ========================= */

  const highlightedPathNodes = new Set<string>();
  const highlightedPathEdges = new Set<string>();

  if (highlightPathEnabled && selectedWallet && filteredNodes.length > 0) {
    const targetNode =
      filteredNodes.find((node) =>
        String(node.data?.label ?? "").startsWith("TARGET"),
      ) ??
      filteredNodes.find(
        (node) =>
          String(node.id).toLowerCase() === address.toLowerCase(),
      );

    if (targetNode) {
      const adjacency = new Map<
        string,
        Array<{ neighbor: string; edgeId: string }>
      >();

      filteredNodes.forEach((node) => {
        adjacency.set(node.id, []);
      });

      filteredEdges.forEach((edge) => {
        adjacency.get(edge.source)?.push({
          neighbor: edge.target,
          edgeId: edge.id,
        });
        adjacency.get(edge.target)?.push({
          neighbor: edge.source,
          edgeId: edge.id,
        });
      });

      const startId = targetNode.id;
      const goalId = selectedWallet;
      const previous = new Map<
        string,
        { nodeId: string; edgeId: string } | null
      >();
      const queue: string[] = [startId];
      previous.set(startId, null);

      let queueIndex = 0;
      while (queueIndex < queue.length && !previous.has(goalId)) {
        const current = queue[queueIndex++];

        for (const connection of adjacency.get(current) ?? []) {
          if (previous.has(connection.neighbor)) {
            continue;
          }

          previous.set(connection.neighbor, {
            nodeId: current,
            edgeId: connection.edgeId,
          });
          queue.push(connection.neighbor);

          if (connection.neighbor === goalId) {
            break;
          }
        }
      }

      if (previous.has(goalId)) {
        let current = goalId;
        highlightedPathNodes.add(current);

        while (current !== startId) {
          const step = previous.get(current);
          if (!step) {
            break;
          }

          highlightedPathEdges.add(step.edgeId);
          highlightedPathNodes.add(step.nodeId);
          current = step.nodeId;
        }
      } else if (startId === goalId) {
        highlightedPathNodes.add(startId);
      }

      // Also highlight every DIRECT OUTGOING transaction from the
      // selected wallet. The path above shows Target -> selected wallet;
      // this adds selected wallet -> its outgoing destinations so the
      // investigator can see where funds continue to flow.
      filteredEdges.forEach((edge) => {
        if (
          String(edge.source).toLowerCase() ===
          goalId.toLowerCase()
        ) {
          highlightedPathEdges.add(edge.id);
          highlightedPathNodes.add(edge.target);
        }
      });

      highlightedPathNodes.add(goalId);
    }
  }

  const graphNodes = filteredNodes.map((node) => {
    if (highlightPathEnabled && selectedWallet) {
      const isHighlighted = highlightedPathNodes.has(node.id);

      return {
        ...node,
        draggable: isHighlighted,
        selectable: isHighlighted,
        style: {
          ...(node.style ?? {}),
          pointerEvents: isHighlighted ? "auto" : "none",
          border: isHighlighted
            ? "2px solid #00F7FF"
            : "1px solid #143038",
          background: isHighlighted
            ? "#04181B"
            : "#02090C",
          boxShadow: isHighlighted
            ? "0 0 0 2px rgba(217,154,43,0.16), 0 0 22px rgba(217,154,43,0.38)"
            : "none",
          opacity: isHighlighted ? 1 : 0.22,
        },
      };
    }

    if (!highlightedPeelCandidate) {
      return node;
    }

    const isHighlighted = highlightedPeelWallets.has(
      String(node.id).toLowerCase(),
    );

    return {
      ...node,
      style: {
        ...(node.style ?? {}),
        border: isHighlighted
          ? "3px solid #00DCE6"
          : "1px solid #174047",
        background: isHighlighted
          ? "#102126"
          : "#02090C",
        boxShadow: isHighlighted
          ? "0 0 18px rgba(94,234,212,0.35)"
          : "none",
        opacity: isHighlighted ? 1 : 0.35,
      },
    };
  });

  const graphEdges = filteredEdges.map((edge) => {
    if (highlightPathEnabled && selectedWallet) {
      const isHighlighted = highlightedPathEdges.has(edge.id);

      return {
        ...edge,
        animated: false,
        selectable: isHighlighted,
        deletable: isHighlighted,
        className: isHighlighted
          ? "cg-path-highlight"
          : "cg-path-dim",
        style: {
          ...(edge.style ?? {}),
          strokeWidth: isHighlighted ? 4 : 1,
          stroke: isHighlighted ? "#00F7FF" : "#14333A",
          opacity: isHighlighted ? 1 : 0.14,
          strokeDasharray: isHighlighted ? "8 6" : undefined,
          filter: isHighlighted
            ? "drop-shadow(0 0 5px rgba(217,154,43,0.85))"
            : "none",
          pointerEvents: isHighlighted ? "auto" : "none",
        },
        labelStyle: {
          ...(edge.labelStyle ?? {}),
          opacity: isHighlighted ? 1 : 0.12,
          fontWeight: isHighlighted ? 800 : 600,
          pointerEvents: isHighlighted ? "auto" : "none",
        },
      };
    }

    if (!highlightedPeelCandidate) {
      return edge;
    }

    const connectionKey =
      `${String(edge.source).toLowerCase()}->${String(edge.target).toLowerCase()}`;
    const reverseConnectionKey =
      `${String(edge.target).toLowerCase()}->${String(edge.source).toLowerCase()}`;

    const isHighlighted =
      highlightedPeelConnections.has(connectionKey) ||
      highlightedPeelConnections.has(reverseConnectionKey);

    return {
      ...edge,
      animated: isHighlighted,
      style: {
        ...(edge.style ?? {}),
        strokeWidth: isHighlighted ? 5 : 1,
        stroke: isHighlighted ? "#00DCE6" : "#34545A",
        opacity: isHighlighted ? 1 : 0.2,
      },
      labelStyle: {
        ...(edge.labelStyle ?? {}),
        opacity: isHighlighted ? 1 : 0.25,
        fontWeight: isHighlighted ? 800 : 600,
      },
    };
  });


  return (
    <main
      style={{
        width: "100vw",
        height: "100vh",
        margin: 0,
        padding: 0,
        background: "#02090C",
        color: "#EAF7F8",
        overflow: "hidden",
        fontFamily:
          "Inter, Arial, sans-serif",
      }}
    >
      <style>{responsiveCss}</style>
      <style>{`
        /* GRAPHITE + AMBER TYPOGRAPHY POLISH */
        .cg-header,
        .cg-sidebar,
        .cg-investigation,
        .cg-graph {
          -webkit-font-smoothing: antialiased;
          text-rendering: optimizeLegibility;
        }

        .cg-header button,
        .cg-sidebar button,
        .cg-investigation button,
        .cg-graph button {
          font-weight: 600 !important;
        }

        .cg-sidebar input,
        .cg-sidebar select,
        .cg-sidebar textarea,
        .cg-investigation input,
        .cg-investigation select,
        .cg-investigation textarea {
          font-weight: 500 !important;
        }

        .cg-graph .react-flow__node {
          font-weight: 500;
        }

        .cg-graph .react-flow__edge-text {
          font-weight: 600 !important;
        }

        /* During path highlighting, locked graph elements must not capture
           the mouse so the React Flow pane can still be panned freely. */
        .cg-graph .cg-path-dim,
        .cg-graph .cg-path-dim * {
          pointer-events: none !important;
        }

        .cg-graph .react-flow__node {
          touch-action: none;
        }
      `}</style>

      {/* =====================
          TOP BAR
      ===================== */}

      <header
        className="cg-header"
        style={{
          height: "64px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 18px 0 24px",
          background: "rgba(7, 20, 22, 0.97)",
          borderBottom: "1px solid #123039",
          boxSizing: "border-box",
          position: "relative",
          zIndex: 50,
          gap: "20px",
        }}
      >
        {/* BRAND */}
        <div
          style={{
            minWidth: 0,
            display: "flex",
            alignItems: "center",
            gap: "10px",
            justifyContent: "center",
          }}
        >
          {/* Crypto Guard logo */}
          <div
            aria-hidden="true"
            style={{
              width: "30px",
              height: "34px",
              flex: "0 0 auto",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <svg
              width="30"
              height="34"
              viewBox="0 0 30 34"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M15 2L27 9V23L15 30L3 23V9L15 2Z"
                stroke="#00F7FF"
                strokeWidth="1.7"
                strokeLinejoin="round"
              />
              <path
                d="M3 9L15 16L27 9M15 16V30"
                stroke="#00F7FF"
                strokeWidth="1.7"
                strokeLinejoin="round"
              />
              <path
                d="M9 12.5L15 9L21 12.5V19.5L15 23L9 19.5V12.5Z"
                stroke="#00F7FF"
                strokeWidth="1.4"
                strokeLinejoin="round"
              />
            </svg>
          </div>

          <div
            style={{
              minWidth: 0,
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
            }}
          >
          <h1
            style={{
              margin: 0,
              fontSize: "18px",
              lineHeight: 1.1,
              fontWeight: 800,
              letterSpacing: "-0.3px",
              color: "#F3FAFA",
              whiteSpace: "nowrap",
            }}
          >
            Crypto Guard V2
          </h1>

          <div
            style={{
              marginTop: "4px",
              fontSize: "10px",
              lineHeight: 1.2,
              color: "#8EADB1",
              letterSpacing: "0.2px",
              whiteSpace: "nowrap",
              fontWeight: 500,
            }}
          >
            Cryptocurrency Investigation & Intelligence Platform
          </div>
          </div>
        </div>

        {/* INVESTIGATION CONTEXT */}
        {token && (
          <div
            className="cg-header-context"
            style={{
              flex: 1,
              minWidth: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "7px 11px",
                background: "#07171C",
                border: "1px solid #14333A",
                borderRadius: "8px",
                minWidth: 0,
                maxWidth: "100%",
              }}
            >
              <span style={{
                fontSize: "10px",
                color: "#8EADB1",
                textTransform: "uppercase",
                letterSpacing: "0.6px",
                fontWeight: 700,
              }}>
                Case
              </span>

              <span style={{
                color: "#EAF7F8",
                fontSize: "12px",
                fontWeight: 700,
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}>
                {selectedCase?.title ?? "No case selected"}
              </span>

              <span style={{ color: "#174047", fontSize: "13px" }}>•</span>

              <span style={{
                fontSize: "10px",
                color: "#8EADB1",
                textTransform: "uppercase",
                letterSpacing: "0.6px",
                fontWeight: 700,
              }}>
                Chain
              </span>

              <span style={{
                color: "#49D6A0",
                fontSize: "12px",
                fontWeight: 700,
                textTransform: "capitalize",
              }}>
                {chain}
              </span>

              {selectedWallet && (
                <>
                  <span style={{ color: "#174047", fontSize: "13px" }}>•</span>

                  <span style={{
                    fontSize: "10px",
                    color: "#8EADB1",
                    textTransform: "uppercase",
                    letterSpacing: "0.6px",
                    fontWeight: 700,
                  }}>
                    Wallet
                  </span>

                  <span
                    style={{
                      color: "#B8D4D7",
                      fontSize: "11px",
                      fontFamily: "monospace",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                      maxWidth: "180px",
                    }}
                    title={selectedWallet}
                  >
                    {selectedWallet.slice(0, 8)}...
                    {selectedWallet.slice(-6)}
                  </span>
                </>
              )}
            </div>
          </div>
        )}

        {/* ACTIONS */}
        {token && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              flexShrink: 0,
            }}
          >
            {/* LIVE INDICATOR */}
            <div
              title="Investigation workspace active"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "7px 9px",
                border: "1px solid #14333A",
                borderRadius: "8px",
                background: "#071418",
              }}
            >
              <span style={{
                width: "7px",
                height: "7px",
                borderRadius: "50%",
                background: "#00F7FF",
                boxShadow: "0 0 8px rgba(74, 222, 128, 0.45)",
              }} />
              <span style={{
                fontSize: "10px",
                color: "#B8D4D7",
                fontWeight: 700,
                letterSpacing: "0.4px",
              }}>
                LIVE
              </span>
            </div>

            {/* REPORT */}
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
                background: reportLoading ? "#063A40" : "#00F7FF",
                color: reportLoading ? "#D8EAEC" : "#02090C",
                borderColor: "#00F7FF",
                opacity: reportLoading || !selectedCase ? 0.65 : 1,
                cursor:
                  reportLoading || !selectedCase ? "not-allowed" : "pointer",
                fontWeight: 700,
                fontSize: "16px",
              }}
            >
              {reportLoading ? "Generating..." : "📄 Report"}
            </button>

            {/* WORKSPACE */}
            <button
              type="button"
              onClick={() => {
                setSidebarCollapsed((current) => {
                  const next = !current;
                  window.setTimeout(() => {
                    reactFlowInstance?.fitView({ padding: 0.18 });
                  }, 120);
                  return next;
                });
              }}
              title={
                sidebarCollapsed
                  ? "Open workspace panel"
                  : "Collapse workspace panel"
              }
              style={workspaceToggleButtonStyle}
            >
              {sidebarCollapsed ? "☰ Workspace" : "☰"}
            </button>

            {/* LOGOUT */}
            <button
              type="button"
              onClick={handleLogout}
              style={{
                background: "#14323A",
                color: "#F3FAFA",
                border: "1px solid #3D5B5F",
                borderRadius: "8px",
                padding: "8px 14px",
                cursor: "pointer",
                fontWeight: 700,
              }}
            >
              Logout
            </button>
          </div>
        )}
      </header>

      {/* =====================
          AUTHENTICATION
      ===================== */}

      {!token && (
        <section
          style={{
            position: "absolute",
            zIndex: 100,
            top: "78px",
            left: "50%",
            transform: "translateX(-50%)",
            width: "390px",
            maxWidth: "calc(100vw - 32px)",
            maxHeight: "calc(100vh - 94px)",
            overflowY: "auto",
            background: "#071418",
            border: "1px solid #174047",
            borderRadius: "16px",
            padding: "28px",
            boxSizing: "border-box",
            boxShadow:
              "0 20px 50px rgba(0,0,0,0.45)",
          }}
        >
          <div
            style={{
              textAlign: "center",
              marginBottom: "22px",
            }}
          >
            <div
              style={{
                width: "44px",
                height: "44px",
                margin: "0 auto 12px",
                borderRadius: "12px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                background:
                  "rgba(0,247,255,0.08)",
                border:
                  "1px solid rgba(0,247,255,0.35)",
                color: "#00F7FF",
                fontSize: "20px",
                fontWeight: 800,
              }}
            >
              CG
            </div>

            <h2
              style={{
                margin: 0,
                marginBottom: "7px",
                fontSize: "24px",
                letterSpacing: "-0.02em",
              }}
            >
              Crypto Guard
            </h2>

            <p
              style={{
                color: "#A9C5C8",
                fontSize: "13px",
                margin: 0,
              }}
            >
              {authMode === "login"
                ? "Sign in to access blockchain tracing."
                : authMode === "register"
                  ? "Create your analyst account to get started."
                  : "Verify your email to activate your analyst account."}
            </p>
          </div>

          {authMode !== "verify" && (
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: "6px",
                padding: "4px",
                marginBottom: "20px",
                background: "#02090C",
                border: "1px solid #122F35",
                borderRadius: "10px",
              }}
            >
              <button
                type="button"
                onClick={() => {
                  setAuthMode("login");
                  setError(null);
                  setAuthNotice(null);
                }}
                style={{
                  border:
                    "1px solid " +
                    (authMode === "login"
                      ? "#00F7FF"
                      : "transparent"),
                  borderRadius: "7px",
                  padding: "9px 10px",
                  background:
                    authMode === "login"
                      ? "rgba(0,247,255,0.10)"
                      : "transparent",
                  color:
                    authMode === "login"
                      ? "#00F7FF"
                      : "#A9C5C8",
                  cursor: "pointer",
                  fontWeight: 700,
                  fontSize: "14px",
                }}
              >
                Sign In
              </button>

              <button
                type="button"
                onClick={() => {
                  setAuthMode("register");
                  setError(null);
                  setAuthNotice(null);
                }}
                style={{
                  border:
                    "1px solid " +
                    (authMode === "register"
                      ? "#00F7FF"
                      : "transparent"),
                  borderRadius: "7px",
                  padding: "9px 10px",
                  background:
                    authMode === "register"
                      ? "rgba(0,247,255,0.10)"
                      : "transparent",
                  color:
                    authMode === "register"
                      ? "#00F7FF"
                      : "#A9C5C8",
                  cursor: "pointer",
                  fontWeight: 700,
                  fontSize: "14px",
                }}
              >
                Create Account
              </button>
            </div>
          )}

          <form
            onSubmit={
              authMode === "login"
                ? handleLogin
                : authMode === "register"
                  ? handleRegister
                  : handleVerifyEmail
            }
          >
            {authMode === "verify" ? (
              <>
                <label style={labelStyle}>
                  Verification Email
                </label>

                <input
                  type="email"
                  value={verificationEmail}
                  onChange={(event) =>
                    setVerificationEmail(
                      event.target.value,
                    )
                  }
                  placeholder="you@example.com"
                  autoComplete="email"
                  required
                  style={inputStyle}
                />

                <label
                  style={{
                    ...labelStyle,
                    marginTop: "14px",
                  }}
                >
                  Verification Code
                </label>

                <input
                  type="text"
                  inputMode="numeric"
                  value={verificationCode}
                  onChange={(event) =>
                    setVerificationCode(
                      event.target.value
                        .replace(/\D/g, "")
                        .slice(0, 6),
                    )
                  }
                  placeholder="Enter 6-digit code"
                  autoComplete="one-time-code"
                  maxLength={6}
                  required
                  style={{
                    ...inputStyle,
                    letterSpacing: "0.22em",
                    textAlign: "center",
                    fontSize: "18px",
                    fontWeight: 700,
                  }}
                />
              </>
            ) : (
              <>
                {authMode === "register" && (
                  <>
                    <label style={labelStyle}>
                      Full Name
                    </label>

                    <input
                      type="text"
                      value={fullName}
                      onChange={(event) =>
                        setFullName(
                          event.target.value,
                        )
                      }
                      placeholder="Your full name"
                      autoComplete="name"
                      style={inputStyle}
                    />
                  </>
                )}

                <label style={labelStyle}>
                  Email
                </label>

                <input
                  type="email"
                  value={email}
                  onChange={(event) =>
                    setEmail(
                      event.target.value,
                    )
                  }
                  placeholder="you@example.com"
                  autoComplete="email"
                  required
                  style={inputStyle}
                />

                <label style={labelStyle}>
                  Password
                </label>

                <input
                  type="password"
                  value={password}
                  onChange={(event) =>
                    setPassword(
                      event.target.value,
                    )
                  }
                  placeholder="Enter your password"
                  autoComplete={
                    authMode === "login"
                      ? "current-password"
                      : "new-password"
                  }
                  required
                  style={inputStyle}
                />

                {authMode === "register" && (
                  <>
                    <label style={labelStyle}>
                      Confirm Password
                    </label>

                    <input
                      type="password"
                      value={confirmPassword}
                      onChange={(event) =>
                        setConfirmPassword(
                          event.target.value,
                        )
                      }
                      placeholder="Re-enter your password"
                      autoComplete="new-password"
                      required
                      style={inputStyle}
                    />
                  </>
                )}
              </>
            )}

            {authNotice && (
              <div
                role="status"
                style={{
                  marginTop: "14px",
                  padding: "10px 12px",
                  borderRadius: "8px",
                  border:
                    "1px solid rgba(58,214,141,0.38)",
                  background:
                    "rgba(58,214,141,0.08)",
                  color: "#8DE8B8",
                  fontSize: "13px",
                  lineHeight: 1.4,
                }}
              >
                {authNotice}
              </div>
            )}

            {error && (
              <div
                role="alert"
                style={{
                  marginTop: "14px",
                  padding: "10px 12px",
                  borderRadius: "8px",
                  border:
                    "1px solid rgba(255,129,127,0.45)",
                  background:
                    "rgba(255,129,127,0.08)",
                  color: "#FFAAA7",
                  fontSize: "13px",
                  lineHeight: 1.4,
                }}
              >
                {error}
              </div>
            )}

            {authMode === "verify" ? (
              <>
                <button
                  type="submit"
                  disabled={loginLoading}
                  style={{
                    ...primaryButtonStyle,
                    marginTop: "18px",
                    opacity:
                      loginLoading ? 0.65 : 1,
                    cursor:
                      loginLoading
                        ? "not-allowed"
                        : "pointer",
                  }}
                >
                  {loginLoading
                    ? "Verifying..."
                    : "Verify Email"}
                </button>

                <button
                  type="button"
                  disabled={loginLoading}
                  onClick={handleResendVerification}
                  style={{
                    width: "100%",
                    marginTop: "9px",
                    padding: "11px 14px",
                    borderRadius: "8px",
                    border:
                      "1px solid #24484F",
                    background: "#0B1E23",
                    color: "#B9D3D6",
                    cursor:
                      loginLoading
                        ? "not-allowed"
                        : "pointer",
                    opacity:
                      loginLoading ? 0.65 : 1,
                    fontWeight: 700,
                  }}
                >
                  {loginLoading
                    ? "Sending..."
                    : "Resend Code"}
                </button>

                <button
                  type="button"
                  disabled={loginLoading}
                  onClick={() => {
                    setAuthMode("login");
                    setVerificationCode("");
                    setError(null);
                    setAuthNotice(null);
                    setEmail(
                      verificationEmail.trim(),
                    );
                  }}
                  style={{
                    width: "100%",
                    marginTop: "9px",
                    padding: "10px 14px",
                    border: "none",
                    background: "transparent",
                    color: "#6FBFC5",
                    cursor:
                      loginLoading
                        ? "not-allowed"
                        : "pointer",
                    fontWeight: 700,
                    fontSize: "13px",
                  }}
                >
                  ← Back to Sign In
                </button>
              </>
            ) : (
              <button
                type="submit"
                disabled={loginLoading}
                style={{
                  ...primaryButtonStyle,
                  marginTop: "18px",
                  opacity:
                    loginLoading ? 0.65 : 1,
                  cursor:
                    loginLoading
                      ? "not-allowed"
                      : "pointer",
                }}
              >
                {loginLoading
                  ? authMode === "login"
                    ? "Signing in..."
                    : "Creating account..."
                  : authMode === "login"
                    ? "Sign In"
                    : "Create Account"}
              </button>
            )}
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
            top: "78px",
            left: "16px",
            width: "380px",
            maxHeight:
              "calc(100vh - 94px)",
            overflowY:
              "auto",
            background:
              "rgba(11, 16, 24, 0.98)",
            border:
              "1px solid #12262B",
            borderRadius:
              "16px",
            padding:
              "14px",
            boxSizing:
              "border-box",
            boxShadow:
              "0 16px 42px rgba(0,0,0,0.42)",
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
                "1px solid #12252A",
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
                    "13px",
                  letterSpacing:
                    "0.08em",
                  textTransform:
                    "uppercase",
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
                    "#00F7FF",
                  color:
                    "#02090C",
                  border:
                    "none",
                  borderRadius:
                    "5px",
                  padding:
                    "6px 10px",
                  cursor:
                    "pointer",
                  fontSize:
                    "14px",
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
                    "#02090C",
                  border:
                    "1px solid #174047",
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
                      "#A9C5C8",
                    fontSize:
                      "12px",
                    border:
                      "1px dashed #174047",
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
                              ? "#0B1D22"
                              : "#02090C",
                          border:
                            isSelected
                              ? "1px solid #00F7FF"
                              : "1px solid #174047",
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
                                  ? "#00F7FF"
                                  : "#A9C5C8",
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
                                "#A9C5C8",
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
                                "#281316",
                              color:
                                "#FFC1BE",
                              border:
                                "1px solid #FF5E68",
                              borderRadius:
                                "5px",
                              padding:
                                "5px 8px",
                              cursor:
                                "pointer",
                              fontSize:
                                "14px",
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
                  "1px solid #12252A",
              }}
            >
              <div
                style={{
                  fontSize:
                    "10px",
                  color:
                    "#A9C5C8",
                  textTransform:
                    "uppercase",
                }}
              >
                Active Case
              </div>

              <div
                style={{
                  marginTop:
                    "5px",
                  fontSize:
                    "14px",
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
                    "#A9C5C8",
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
                className="cg-generate-report"
                style={{
                  marginTop: "10px",
                  width: "100%",
                  padding: "8px 10px",
                  border: "1px solid #49D6A0",
                  borderRadius: "6px",
                  background: reportLoading ? "#163A32" : "#49D6A0",
                  color: "#02090C",
                  cursor: reportLoading ? "not-allowed" : "pointer",
                  fontSize: "16px",
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
                  "1px solid #12252A",
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
                      "13px",
                    letterSpacing:
                      "0.06em",
                    textTransform:
                      "uppercase",
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
                      "#00F7FF",
                    color:
                      "#02090C",
                    border:
                      "none",
                    borderRadius:
                      "5px",
                    padding:
                      "6px 9px",
                    cursor:
                      "pointer",
                    fontSize:
                      "14px",
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
                      "#02090C",
                    border:
                      "1px solid #174047",
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
                        "#A9C5C8",
                      fontSize:
                        "11px",
                      border:
                        "1px dashed #174047",
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
                                ? "#0B1D22"
                                : "#02090C",
                            border:
                              selected
                                ? "1px solid #00F7FF"
                                : "1px solid #174047",
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
                                  "#281316",
                                color:
                                  "#FFC1BE",
                                border:
                                  "1px solid #FF5E68",
                                borderRadius:
                                  "4px",
                                padding:
                                  "3px 6px",
                                cursor:
                                  "pointer",
                                fontSize:
                                  "14px",
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
                                "#C9E0E3",
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
                                "#789BA0",
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
                    "16px 0 12px",
                  fontSize:
                    "13px",
                  letterSpacing:
                    "0.08em",
                  textTransform:
                    "uppercase",
                  color:
                    "#EAF7F8",
                  textAlign:
                    "left",
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
                      "1px solid #12252A",
                    fontSize:
                      "12px",
                    color:
                      "#C9E0E3",
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

              {/* PEEL CHAIN ANALYSIS */}

              <div
                style={{
                  marginTop: "14px",
                  paddingTop: "14px",
                  borderTop: "1px solid #12252A",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: "8px",
                  }}
                >
                  <div style={{ minWidth: 0, textAlign: "left" }}>
                    <h3
                      style={{
                        margin: 0,
                        fontSize: "15px",
                        fontWeight: 700,
                        lineHeight: 1.25,
                        letterSpacing: "0.02em",
                        textAlign: "left",
                      }}
                    >
                      Peel Chain Analysis
                    </h3>
                    <div
                      style={{
                        marginTop: "4px",
                        fontSize: "9px",
                        color: "#8EADB1",
                        lineHeight: 1.4,
                      }}
                    >
                      Sequential outgoing transfer analysis from stored Neo4j data.
                    </div>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    {peelChain && (
                      <button
                        type="button"
                        onClick={() => {
                          setPeelChain(null);
                          setSelectedPeelCandidateKey(null);
                          setPeelFilter("all");
                          setPeelSort("strongest");
                        }}
                        style={{
                          ...secondaryButtonStyle,
                          width: "auto",
                          marginTop: 0,
                          padding: "5px 7px",
                          fontSize: "16px",
                        }}
                      >
                        Clear
                      </button>
                    )}
                    <button
                      type="button"
                      aria-expanded={peelExpanded}
                      onClick={() => setPeelExpanded((current) => !current)}
                      style={{
                        width: "30px",
                        height: "30px",
                        padding: 0,
                        borderRadius: "8px",
                        border: "1px solid #174047",
                        background: peelExpanded ? "#13272C" : "#061116",
                        color: peelExpanded ? "#65F9FF" : "#A9C5C8",
                        cursor: "pointer",
                        fontSize: "16px",
                        lineHeight: 1,
                      }}
                    >
                      {peelExpanded ? "−" : "+"}
                    </button>
                  </div>
                </div>

                {peelExpanded && (
                  <>
                    <label style={labelStyle}>Max Hops</label>
                <select
                  value={peelMaxHops}
                  onChange={(event) => setPeelMaxHops(event.target.value)}
                  style={inputStyle}
                >
                  <option value="2">2 Hops</option>
                  <option value="3">3 Hops</option>
                  <option value="4">4 Hops</option>
                  <option value="5">5 Hops</option>
                </select>

                <button
                  type="button"
                  onClick={handlePeelChainAnalysis}
                  disabled={peelLoading}
                  style={{
                    ...primaryButtonStyle,
                    background: "#0A6E73",
                  }}
                >
                  {peelLoading ? "Analyzing Peel Chain..." : "Analyze Peel Chain"}
                </button>

                {peelChain && (
                  <div style={{ marginTop: "14px" }}>
                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
                        gap: "8px",
                      }}
                    >
                      <div style={miniStatStyle}>
                        <span>Status</span>
                        <strong style={{ color: "#00F7FF" }}>{peelChain.status}</strong>
                      </div>
                      <div style={miniStatStyle}>
                        <span>Candidates</span>
                        <strong>{peelChain.candidate_count}</strong>
                      </div>
                      <div style={miniStatStyle}>
                        <span>Chain</span>
                        <strong>{peelChain.chain}</strong>
                      </div>
                      <div style={miniStatStyle}>
                        <span>Max Hops</span>
                        <strong>{peelChain.max_hops}</strong>
                      </div>
                    </div>

                    <div
                      style={{
                        marginTop: "10px",
                        padding: "9px",
                        border: "1px solid #174047",
                        borderRadius: "7px",
                        background: "#061116",
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          gap: "8px",
                          marginBottom: "7px",
                        }}
                      >
                        <span style={{ fontSize: "10px", color: "#D8EAEC" }}>Candidates</span>
                        <span style={{ fontSize: "9px", color: "#B8D4D7" }}>
                          Showing {filteredPeelCandidates.length} of {peelChain.candidates.length}
                        </span>
                      </div>

                      <div
                        style={{
                          display: "grid",
                          gridTemplateColumns: "1fr 1fr",
                          gap: "6px",
                        }}
                      >
                        <select
                          value={peelFilter}
                          onChange={(event) => setPeelFilter(event.target.value)}
                          style={{ ...inputStyle, marginBottom: 0, padding: "7px", fontSize: "10px" }}
                        >
                          <option value="all">All candidates</option>
                          <option value="strong">Strong pattern</option>
                          <option value="same-asset">Same asset</option>
                          <option value="value-reduced">Value reduced</option>
                          <option value="chronological">Chronological</option>
                        </select>

                        <select
                          value={peelSort}
                          onChange={(event) => setPeelSort(event.target.value)}
                          style={{ ...inputStyle, marginBottom: 0, padding: "7px", fontSize: "10px" }}
                        >
                          <option value="strongest">Strongest pattern</option>
                          <option value="hops">Most hops</option>
                          <option value="retained">Highest retained amount</option>
                          <option value="gap">Shortest average gap</option>
                        </select>
                      </div>

                      {selectedPeelCandidateKey && (
                        <button
                          type="button"
                          onClick={clearPeelCandidateSelection}
                          style={{
                            ...secondaryButtonStyle,
                            width: "100%",
                            marginTop: "7px",
                            padding: "7px",
                            fontSize: "16px",
                          }}
                        >
                          Clear Graph Highlight
                        </button>
                      )}
                    </div>

                    {filteredPeelCandidates.length === 0 ? (
                      <div
                        style={{
                          marginTop: "10px",
                          padding: "12px",
                          border: "1px solid #174047",
                          borderRadius: "7px",
                          color: "#B8D4D7",
                          fontSize: "10px",
                          textAlign: "center",
                        }}
                      >
                        No candidates match the selected filter.
                      </div>
                    ) : (
                      filteredPeelCandidates.map((candidate, index) => {
                      const firstValue = candidate.value_progression.input_value;
                      const finalValue = candidate.value_progression.output_value;
                      const firstAsset = candidate.transfers[0]?.asset ?? "Unknown";
                      const gap = candidate.timing.average_gap_seconds;
                      const pattern = getPeelPatternAssessment(candidate);

                      return (
                        <div
                          key={`${candidate.transfers[0]?.transaction_hash ?? index}-${candidate.transfers[candidate.transfers.length - 1]?.transaction_hash ?? index}`}
                          style={{
                            marginTop: "10px",
                            padding: "10px",
                            background: "#02090C",
                            border: "1px solid #174047",
                            borderRadius: "7px",
                          }}
                        >
                          <div
                            style={{
                              display: "flex",
                              justifyContent: "space-between",
                              alignItems: "center",
                              gap: "8px",
                            }}
                          >
                            <strong style={{ fontSize: "12px" }}>Candidate #{index + 1}</strong>
                            <span
                              style={{
                                fontSize: "9px",
                                padding: "3px 6px",
                                borderRadius: "999px",
                                background: "#102126",
                                color: "#00DCE6",
                              }}
                            >
                              {candidate.hop_count} hops
                            </span>
                          </div>

                          <button
                            type="button"
                            onClick={() =>
                              handleSelectPeelCandidate(candidate)
                            }
                            style={{
                              width: "100%",
                              marginTop: "7px",
                              padding: "6px 8px",
                              borderRadius: "5px",
                              border: getPeelCandidateKey(candidate) === selectedPeelCandidateKey
                                ? "1px solid #00DCE6"
                                : "1px solid #174047",
                              background: getPeelCandidateKey(candidate) === selectedPeelCandidateKey
                                ? "#102126"
                                : "#061116",
                              color: getPeelCandidateKey(candidate) === selectedPeelCandidateKey
                                ? "#00DCE6"
                                : "#C9E0E3",
                              fontSize: "16px",
                              cursor: "pointer",
                            }}
                          >
                            {getPeelCandidateKey(candidate) === selectedPeelCandidateKey
                              ? "Highlighted on Graph"
                              : "Highlight on Graph"}
                          </button>

                          <div
                            style={{
                              marginTop: "8px",
                              padding: "7px 8px",
                              border: "1px solid #174047",
                              borderRadius: "6px",
                              display: "flex",
                              justifyContent: "space-between",
                              alignItems: "center",
                              gap: "8px",
                              background: "#061116",
                            }}
                          >
                            <span style={{ fontSize: "9px", color: "#B8D4D7" }}>Pattern signals</span>
                            <strong style={{ fontSize: "10px", color: pattern.color }}>
                              {pattern.label} · {pattern.signalCount}/5
                            </strong>
                          </div>

                          <div
                            style={{
                              marginTop: "9px",
                              display: "flex",
                              flexDirection: "column",
                              gap: "0",
                            }}
                          >
                            {candidate.wallets.map((wallet, walletIndex) => {
                              const transfer = candidate.transfers[walletIndex];
                              const shortAddress =
                                wallet.address.length > 22
                                  ? `${wallet.address.slice(0, 10)}...${wallet.address.slice(-8)}`
                                  : wallet.address;

                              return (
                                <div key={`${wallet.address}-${walletIndex}`}>
                                  <div
                                    title={wallet.address}
                                    style={{
                                      padding: "8px 9px",
                                      border: "1px solid #174047",
                                      borderRadius: "6px",
                                      background: walletIndex === 0 ? "#061116" : "#02090C",
                                      fontSize: "9px",
                                      color: "#EAF7F8",
                                      overflow: "hidden",
                                    }}
                                  >
                                    <div
                                      style={{
                                        color: "#8EADB1",
                                        fontSize: "8px",
                                        marginBottom: "4px",
                                        letterSpacing: "0.04em",
                                      }}
                                    >
                                      {walletIndex === 0 ? "SOURCE" : `HOP ${walletIndex}`}
                                    </div>
                                    <div
                                      style={{
                                        whiteSpace: "nowrap",
                                        overflow: "hidden",
                                        textOverflow: "ellipsis",
                                        fontFamily: "monospace",
                                      }}
                                    >
                                      {shortAddress}
                                    </div>
                                  </div>

                                  {transfer && (
                                    <button
                                      type="button"
                                      onClick={() =>
                                        handleInspectPeelTransfer(
                                          candidate,
                                          transfer,
                                          walletIndex,
                                        )
                                      }
                                      title={`Inspect transaction ${transfer.transaction_hash}`}
                                      style={{
                                        width: "100%",
                                        border: "none",
                                        background: "transparent",
                                        cursor: "pointer",
                                        display: "flex",
                                        flexDirection: "column",
                                        alignItems: "center",
                                        padding: "4px 0",
                                        color: "inherit",
                                      }}
                                    >
                                      <span
                                        style={{
                                          fontSize: "16px",
                                          lineHeight: 1,
                                          color: "#00DCE6",
                                        }}
                                      >
                                        ↓
                                      </span>
                                      <span
                                        style={{
                                          marginTop: "2px",
                                          fontSize: "16px",
                                          color: "#00DCE6",
                                          whiteSpace: "nowrap",
                                        }}
                                      >
                                        {formatNumber(transfer.value)} {transfer.asset ?? ""}
                                      </span>
                                      <span
                                        style={{
                                          marginTop: "3px",
                                          fontSize: "16px",
                                          color: "#49D6A0",
                                        }}
                                      >
                                        Inspect transaction
                                      </span>
                                    </button>
                                  )}
                                </div>
                              );
                            })}
                          </div>

                          {candidate.hop_value_progression.length > 0 && (
                            <div
                              style={{
                                marginTop: "9px",
                                padding: "8px",
                                border: "1px solid #174047",
                                borderRadius: "6px",
                                background: "#061116",
                              }}
                            >
                              <div style={{ ...sectionTitleStyle, fontSize: "10px" }}>Value per Hop</div>
                              <div style={{ marginTop: "6px", display: "flex", flexDirection: "column", gap: "6px" }}>
                                {candidate.hop_value_progression.map((hop, hopIndex) => (
                                  <div
                                    key={`${hop.from_transaction}-${hop.to_transaction}-${hopIndex}`}
                                    style={{
                                      padding: "7px",
                                      border: "1px solid #274D50",
                                      borderRadius: "5px",
                                    }}
                                  >
                                    <div style={{ display: "flex", justifyContent: "space-between", gap: "8px", fontSize: "9px" }}>
                                      <strong>Hop {hopIndex + 1} → {hopIndex + 2}</strong>
                                      <span style={{ color: hop.value_reduction ? "#00F7FF" : "#2DEAF2" }}>
                                        {hop.value_reduction ? "Reduced" : "No reduction"}
                                      </span>
                                    </div>
                                    <div
                                      style={{
                                        marginTop: "5px",
                                        display: "grid",
                                        gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
                                        gap: "5px",
                                      }}
                                    >
                                      <div style={miniStatStyle}>
                                        <span>Input</span>
                                        <strong>{formatNumber(hop.input_value)}</strong>
                                      </div>
                                      <div style={miniStatStyle}>
                                        <span>Forwarded</span>
                                        <strong>{formatNumber(hop.forwarded_value)}</strong>
                                      </div>
                                      <div style={miniStatStyle}>
                                        <span>Retained</span>
                                        <strong>{formatNumber(hop.retained_amount)}</strong>
                                      </div>
                                    </div>
                                    <div style={{ marginTop: "5px", fontSize: "9px", color: "#B8D4D7" }}>
                                      Forward ratio: {
                                        hop.forward_ratio === null || hop.forward_ratio === undefined
                                          ? "—"
                                          : `${(hop.forward_ratio * 100).toFixed(2)}%`
                                      }
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          <div
                            style={{
                              marginTop: "8px",
                              display: "grid",
                              gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
                              gap: "5px",
                            }}
                          >
                            <div style={miniStatStyle}>
                              <span>Asset</span>
                              <strong>{firstAsset}</strong>
                            </div>
                            <div style={miniStatStyle}>
                              <span>Value</span>
                              <strong>{formatNumber(firstValue)} → {formatNumber(finalValue)}</strong>
                            </div>
                            <div style={miniStatStyle}>
                              <span>Reduction</span>
                              <strong>{formatNumber(candidate.value_progression.retained_amount)}</strong>
                            </div>
                            <div style={miniStatStyle}>
                              <span>Forward Ratio</span>
                              <strong>
                                {candidate.value_progression.forward_ratio === null ||
                                candidate.value_progression.forward_ratio === undefined
                                  ? "—"
                                  : `${(candidate.value_progression.forward_ratio * 100).toFixed(2)}%`}
                              </strong>
                            </div>
                            <div style={miniStatStyle}>
                              <span>Average Gap</span>
                              <strong>{gap === null ? "Unknown" : formatDuration(gap)}</strong>
                            </div>
                            <div style={miniStatStyle}>
                              <span>Same Asset</span>
                              <strong style={{ color: candidate.same_asset ? "#00F7FF" : "#FF817F" }}>
                                {candidate.same_asset ? "Yes" : "No"}
                              </strong>
                            </div>
                          </div>

                          <div style={{ marginTop: "9px" }}>
                            <div style={sectionTitleStyle}>Evidence</div>
                            <div style={{ marginTop: "5px" }}>
                              {candidate.evidence.map((item, evidenceIndex) => (
                                <div
                                  key={`${index}-${evidenceIndex}`}
                                  style={{
                                    fontSize: "9px",
                                    color: "#D8EAEC",
                                    lineHeight: 1.5,
                                  }}
                                >
                                  ✓ {item}
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      );
                    })
                    )}

                    {peelChain.candidate_count === 0 && (
                      <div
                        style={{
                          marginTop: "10px",
                          padding: "10px",
                          background: "#02090C",
                          border: "1px solid #174047",
                          borderRadius: "6px",
                          fontSize: "11px",
                          color: "#B8D4D7",
                        }}
                      >
                        No validated peel-chain candidates were found in the stored graph data.
                      </div>
                    )}

                    <div
                      style={{
                        marginTop: "10px",
                        fontSize: "9px",
                        color: "#8EADB1",
                        lineHeight: 1.5,
                      }}
                    >
                      {peelChain.notice}
                    </div>
                  </div>
                )}
                  </>
                )}
              </div>

              {/* CROSS-CHAIN ANALYSIS */}

              <div
                style={{
                  marginTop: "14px",
                  paddingTop: "14px",
                  borderTop: "1px solid #12252A",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: "8px",
                  }}
                >
                  <div style={{ minWidth: 0, textAlign: "left" }}>
                    <h3
                      style={{
                        margin: 0,
                        fontSize: "15px",
                        fontWeight: 700,
                        lineHeight: 1.25,
                        letterSpacing: "0.02em",
                        textAlign: "left",
                      }}
                    >
                      Cross-Chain Analysis
                    </h3>
                    <div
                      style={{
                        marginTop: "4px",
                        fontSize: "9px",
                        color: "#8EADB1",
                      }}
                    >
                      Detect candidate links across supported chains.
                    </div>
                  </div>
                  <button
                    type="button"
                    aria-expanded={crossChainExpanded}
                    onClick={() => setCrossChainExpanded((current) => !current)}
                    style={{
                      width: "30px",
                      height: "30px",
                      padding: 0,
                      borderRadius: "8px",
                      border: "1px solid #174047",
                      background: crossChainExpanded ? "#13272C" : "#061116",
                      color: crossChainExpanded ? "#65F9FF" : "#A9C5C8",
                      cursor: "pointer",
                      fontSize: "16px",
                      lineHeight: 1,
                    }}
                  >
                    {crossChainExpanded ? "−" : "+"}
                  </button>
                </div>

                {crossChainExpanded && (
                  <>
                  <label
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "4px",
                      fontSize: "9px",
                      color: "#B8D4D7",
                    }}
                  >
                    Target Chain
                    <select
                      value={crossChainTarget}
                      onChange={(event) =>
                        setCrossChainTarget(event.target.value)
                      }
                      style={{
                        padding: "7px",
                        borderRadius: "5px",
                        border: "1px solid #174047",
                        background: "#061116",
                        color: "#EAF7F8",
                        fontSize: "10px",
                      }}
                    >
                      <option value="all">All Other Chains</option>
                      <option value="ethereum">Ethereum</option>
                      <option value="polygon">Polygon</option>
                      <option value="arbitrum">Arbitrum</option>
                      <option value="base">Base</option>
                      <option value="bsc">BSC</option>
                      <option value="optimism">Optimism</option>
                    </select>
                  </label>

                  <label
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "4px",
                      fontSize: "9px",
                      color: "#B8D4D7",
                    }}
                  >
                    Time Window (min)
                    <input
                      type="number"
                      min={1}
                      max={1440}
                      value={crossChainWindow}
                      onChange={(event) =>
                        setCrossChainWindow(event.target.value)
                      }
                      style={{
                        padding: "7px",
                        borderRadius: "5px",
                        border: "1px solid #174047",
                        background: "#061116",
                        color: "#EAF7F8",
                        fontSize: "10px",
                      }}
                    />
                  </label>

                <label
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "4px",
                    marginTop: "8px",
                    fontSize: "9px",
                    color: "#B8D4D7",
                  }}
                >
                  Value Tolerance (%)
                  <input
                    type="number"
                    min={0}
                    max={100}
                    value={crossChainTolerance}
                    onChange={(event) =>
                      setCrossChainTolerance(event.target.value)
                    }
                    style={{
                      padding: "7px",
                      borderRadius: "5px",
                      border: "1px solid #174047",
                      background: "#061116",
                      color: "#EAF7F8",
                      fontSize: "10px",
                    }}
                  />
                </label>

                <button
                  type="button"
                  onClick={handleCrossChainAnalysis}
                  disabled={crossChainLoading}
                  style={{
                    width: "100%",
                    marginTop: "9px",
                    padding: "8px",
                    borderRadius: "5px",
                    border: "1px solid #00F7FF",
                    background: crossChainLoading ? "#102126" : "#13272C",
                    color: "#65F9FF",
                    fontSize: "16px",
                    fontWeight: 700,
                    cursor: crossChainLoading ? "not-allowed" : "pointer",
                  }}
                >
                  {crossChainLoading
                    ? "Analyzing Cross-Chain..."
                    : "Analyze Cross-Chain"}
                </button>

                {crossChain && (
                  <div
                    style={{
                      marginTop: "10px",
                      padding: "8px",
                      border: "1px solid #174047",
                      borderRadius: "6px",
                      background: "#02090C",
                    }}
                  >
                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(3, 1fr)",
                        gap: "6px",
                      }}
                    >
                      <div>
                        <div style={{ fontSize: "8px", color: "#8EADB1" }}>
                          STATUS
                        </div>
                        <strong style={{ fontSize: "9px", color: "#65F9FF" }}>
                          {crossChain.status}
                        </strong>
                      </div>

                      <div>
                        <div style={{ fontSize: "8px", color: "#8EADB1" }}>
                          CANDIDATES
                        </div>
                        <strong style={{ fontSize: "9px", color: "#EAF7F8" }}>
                          {crossChain.candidate_count}
                        </strong>
                      </div>

                      <div>
                        <div style={{ fontSize: "8px", color: "#8EADB1" }}>
                          SOURCE
                        </div>
                        <strong style={{ fontSize: "9px", color: "#EAF7F8" }}>
                          {crossChain.source_chain}
                        </strong>
                      </div>
                    </div>

                    <div
                      style={{
                        marginTop: "7px",
                        fontSize: "8px",
                        color: "#B8D4D7",
                      }}
                    >
                      Window: {crossChain.time_window_minutes} min · Tolerance:{" "}
                      {(crossChain.value_tolerance * 100).toFixed(0)}%
                    </div>
                  </div>
                )}

                {crossChain?.candidates.map((candidate, index) => (
                  <div
                    key={`${candidate.source.transaction_hash}-${candidate.destination.transaction_hash}-${index}`}
                    style={{
                      marginTop: "9px",
                      padding: "9px",
                      background: "#02090C",
                      border: "1px solid #174047",
                      borderRadius: "7px",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        gap: "8px",
                      }}
                    >
                      <strong style={{ fontSize: "11px" }}>
                        Candidate #{index + 1}
                      </strong>

                      <span
                        style={{
                          fontSize: "8px",
                          padding: "3px 6px",
                          borderRadius: "999px",
                          background: "#13272C",
                          color: "#65F9FF",
                        }}
                      >
                        {(candidate.confidence * 100).toFixed(0)}% signal
                      </span>
                    </div>

                    <div
                      style={{
                        marginTop: "7px",
                        fontSize: "8px",
                        color: "#B8D4D7",
                      }}
                    >
                      {candidate.source.chain ?? "Unknown"} →{" "}
                      {candidate.destination.chain ?? "Unknown"} ·{" "}
                      {candidate.time_gap_seconds !== null
                        ? `${candidate.time_gap_seconds.toFixed(0)}s gap`
                        : "time unavailable"}
                    </div>

                    <div
                      style={{
                        marginTop: "7px",
                        display: "flex",
                        flexWrap: "wrap",
                        gap: "4px",
                      }}
                    >
                      {candidate.signals.map((signal) => (
                        <span
                          key={signal}
                          style={{
                            padding: "3px 5px",
                            borderRadius: "999px",
                            background: "#102126",
                            color: "#D8EAEC",
                            fontSize: "7px",
                          }}
                        >
                          {signal}
                        </span>
                      ))}
                    </div>

                    <div
                      style={{
                        marginTop: "8px",
                        display: "grid",
                        gridTemplateColumns: "1fr 1fr",
                        gap: "5px",
                      }}
                    >
                      <button
                        type="button"
                        onClick={() =>
                          handleInspectCrossChainTransfer(
                            candidate.source,
                            "source",
                          )
                        }
                        style={{
                          padding: "6px",
                          borderRadius: "5px",
                          border: "1px solid #174047",
                          background: "#061116",
                          color: "#65F9FF",
                          fontSize: "16px",
                          cursor: "pointer",
                        }}
                      >
                        Inspect Source TX
                      </button>

                      <button
                        type="button"
                        onClick={() =>
                          handleInspectCrossChainTransfer(
                            candidate.destination,
                            "destination",
                          )
                        }
                        style={{
                          padding: "6px",
                          borderRadius: "5px",
                          border: "1px solid #174047",
                          background: "#061116",
                          color: "#65F9FF",
                          fontSize: "16px",
                          cursor: "pointer",
                        }}
                      >
                        Inspect Destination TX
                      </button>
                    </div>
                  </div>
                ))}

                {crossChain && (
                  <div
                    style={{
                      marginTop: "9px",
                      padding: "7px 8px",
                      border: "1px solid #174047",
                      borderRadius: "6px",
                      background: "#061116",
                      color: "#B8D4D7",
                      fontSize: "8px",
                      lineHeight: 1.5,
                    }}
                  >
                    {crossChain.notice}
                  </div>
                )}
                  </>
                )}
              </div>

              {/* RISK BUTTON */}

              <button
                type="button"
                onClick={
                  handleRiskAnalysis
                }
                disabled={
                  riskLoading
                }
                style={{
                  ...riskButtonStyle,
                  marginTop: "10px",
                  padding: "9px 10px",
                  borderRadius: "9px",
                  fontSize: "16px",
                  letterSpacing: "0.02em",
                }}
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
            top: "78px",
            right: "16px",
            width: "390px",
            maxHeight:
              "calc(100vh - 94px)",
            overflowY:
              "auto",
            background:
              "rgba(17, 21, 31, 0.99)",
            border:
              "1px solid #1C3438",
            borderRadius:
              "14px",
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
                  "#0B1D22",
                color:
                  "#F3FAFA",
                border:
                  "1px solid #34545A",
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
            <>
              {investigationMenuOpen ? (
                <div style={investigationMenuStyle}>
                  <button
                    type="button"
                    onClick={() => {
                      setInvestigationTab("wallet");
                      setInvestigationMenuOpen(false);
                    }}
                    style={investigationMenuButtonStyle}
                  >
                    <span>Wallet</span>
                    <span style={investigationMenuArrowStyle}>›</span>
                  </button>

                  {selectedTransfer && (
                    <button
                      type="button"
                      onClick={() => {
                        setInvestigationTab("transaction");
                        setInvestigationMenuOpen(false);
                      }}
                      style={investigationMenuButtonStyle}
                    >
                      <span>Transaction</span>
                      <span style={investigationMenuArrowStyle}>›</span>
                    </button>
                  )}

                  <button
                    type="button"
                    onClick={() => {
                      setInvestigationTab("analytics");
                      setInvestigationMenuOpen(false);
                      if (!graphAnalytics || !timelineAnalytics) {
                        void handleLoadWalletAnalytics();
                      }
                    }}
                    style={investigationMenuButtonStyle}
                  >
                    <span>Analytics</span>
                    <span style={investigationMenuArrowStyle}>›</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setInvestigationTab("ml-aml");
                      setInvestigationMenuOpen(false);
                      if (!mlRisk || !amlAssessment) {
                        void handleLoadMlAml();
                      }
                    }}
                    style={investigationMenuButtonStyle}
                  >
                    <span>ML / AML</span>
                    <span style={investigationMenuArrowStyle}>›</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setInvestigationTab("vasp");
                      setInvestigationMenuOpen(false);
                      if (!vaspAttribution) {
                        void handleLoadVaspAttribution();
                      }
                    }}
                    style={investigationMenuButtonStyle}
                  >
                    <span>VASP Attribution</span>
                    <span style={investigationMenuArrowStyle}>›</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setInvestigationTab("intelligence");
                      setInvestigationMenuOpen(false);
                      if (!intelligenceLoading) {
                        void handleLoadRiskEntities();
                      }
                      if (!newRiskEntityAddress && selectedWallet) {
                        resetRiskEntityForm();
                      }
                    }}
                    style={investigationMenuButtonStyle}
                  >
                    <span>Intelligence</span>
                    <span style={investigationMenuArrowStyle}>›</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setInvestigationTab("candidate-linking");
                      setInvestigationMenuOpen(false);
                    }}
                    style={investigationMenuButtonStyle}
                  >
                    <span>Candidate Linking</span>
                    <span style={investigationMenuArrowStyle}>›</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setInvestigationTab("notes");
                      setInvestigationMenuOpen(false);
                      if (selectedCase && notes.length === 0 && !notesLoading) {
                        void loadNotes(selectedCase.id);
                      }
                    }}
                    style={investigationMenuButtonStyle}
                  >
                    <span>Notes</span>
                    <span style={investigationMenuArrowStyle}>›</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setInvestigationTab("evidence");
                      setInvestigationMenuOpen(false);
                      if (selectedCase && !evidenceLoading) {
                        void loadEvidence(selectedCase.id);
                      }
                    }}
                    style={investigationMenuButtonStyle}
                  >
                    <span>Evidence</span>
                    <span style={investigationMenuArrowStyle}>›</span>
                  </button>
                </div>
              ) : (
                <div style={investigationBackBarStyle}>
                  <button
                    type="button"
                    aria-label="Back to investigation sections"
                    onClick={() => setInvestigationMenuOpen(true)}
                    style={investigationBackButtonStyle}
                  >
                    ←
                  </button>
                  <div style={investigationBackTitleStyle}>
                    {
                      {
                        wallet: "Wallet",
                        transaction: "Transaction",
                        analytics: "Analytics",
                        "ml-aml": "ML / AML",
                        vasp: "VASP Attribution",
                        intelligence: "Intelligence",
                        "candidate-linking": "Candidate Linking",
                        notes: "Notes",
                        evidence: "Evidence",
                      }[investigationTab]
                    }
                  </div>
                </div>
              )}
            </>
          )}



          {/* VASP ATTRIBUTION */}

          {!investigationMenuOpen && selectedWallet && investigationTab === "vasp" && (
            <>
              <div style={panelSectionStyle}>
                <div style={sectionTitleStyle}>VASP Attribution</div>
                <div style={{ marginTop: "7px", fontSize: "10px", color: "#B8D4D7", lineHeight: 1.5 }}>
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
                    <div style={{ marginTop: "10px", color: "#8EADB1", fontSize: "9px", lineHeight: 1.5 }}>
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
                            <div style={{ marginTop: "5px", color: "#B8D4D7", fontSize: "9px", wordBreak: "break-all" }}>{candidate.address}</div>
                          </div>
                          <span style={{ ...analyticsSeverityStyle, color: "#58F7FF", flexShrink: 0 }}>
                            {candidate.confidence !== null ? `${(candidate.confidence * 100).toFixed(1)}%` : "N/A"}
                          </span>
                        </div>
                        <div style={{ marginTop: "9px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px" }}>
                          <div style={analyticsStatStyle}><span>Hop</span><strong>{candidate.hop ?? "N/A"}</strong></div>
                          <div style={analyticsStatStyle}><span>Basis</span><strong>{candidate.attribution_basis}</strong></div>
                          <div style={analyticsStatStyle}><span>Source</span><strong>{candidate.source ?? "N/A"}</strong></div>
                          <div style={analyticsStatStyle}><span>Category</span><strong>{candidate.risk_category ?? "N/A"}</strong></div>
                        </div>
                        <div style={{ marginTop: "9px", color: "#D8EAEC", fontSize: "10px", lineHeight: 1.5 }}>
                          <strong>Reason:</strong> {candidate.reason}
                        </div>
                        {candidate.evidence && (
                          <div style={{ marginTop: "8px", color: "#B8D4D7", fontSize: "10px", lineHeight: 1.5 }}>
                            <strong style={{ color: "#D8EAEC" }}>Evidence:</strong> {candidate.evidence}
                          </div>
                        )}
                        <details style={{ marginTop: "9px", color: "#B8D4D7" }}>
                          <summary style={{ cursor: "pointer", color: "#49D6A0", fontSize: "10px" }}>Transaction Path Evidence</summary>
                          <div style={{ marginTop: "8px", fontSize: "9px", color: "#D8EAEC", lineHeight: 1.5 }}>
                            <div><strong>Wallet path:</strong></div>
                            <div style={{ marginTop: "4px", wordBreak: "break-all" }}>{candidate.wallets.join(" → ")}</div>
                            {candidate.transfers.map((transfer, transferIndex) => (
                              <div key={`${transfer.transaction_hash}-${transferIndex}`} style={{ marginTop: "8px", padding: "8px", background: "#02090C", border: "1px solid #12252A", borderRadius: "6px" }}>
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
                <div style={{ marginTop: "6px", color: "#8EADB1", fontSize: "9px", lineHeight: 1.45 }}>
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

          {/* INTELLIGENCE REGISTRY */}

          {!investigationMenuOpen && selectedWallet && investigationTab === "intelligence" && (
            <>
              <div style={panelSectionStyle}>
                <div style={sectionTitleStyle}>Risk Entity Intelligence</div>
                <div
                  style={{
                    marginTop: "7px",
                    fontSize: "10px",
                    color: "#B8D4D7",
                    lineHeight: 1.5,
                  }}
                >
                  Manage documented intelligence entities used by VASP
                  attribution, candidate linking, and risk exposure analysis.
                  Records are stored in the backend intelligence registry and
                  Neo4j.
                </div>

                <div
                  style={{
                    marginTop: "10px",
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "6px",
                  }}
                >
                  <select
                    value={intelligenceChainFilter}
                    onChange={(event) =>
                      setIntelligenceChainFilter(event.target.value)
                    }
                    style={inputStyle}
                    disabled={intelligenceLoading}
                  >
                    <option value="all">All chains</option>
                    <option value="ethereum">Ethereum</option>
                    <option value="polygon">Polygon</option>
                    <option value="arbitrum">Arbitrum</option>
                    <option value="optimism">Optimism</option>
                    <option value="base">Base</option>
                  </select>

                  <select
                    value={intelligenceTypeFilter}
                    onChange={(event) =>
                      setIntelligenceTypeFilter(event.target.value)
                    }
                    style={inputStyle}
                    disabled={intelligenceLoading}
                  >
                    <option value="all">All entity types</option>
                    <option value="vasp">VASP</option>
                    <option value="exchange">Exchange</option>
                    <option value="mixer">Mixer</option>
                    <option value="sanctions">Sanctions</option>
                    <option value="scam">Scam</option>
                    <option value="risk_entity">Risk Entity</option>
                  </select>

                  <select
                    value={intelligenceSourceFilter}
                    onChange={(event) =>
                      setIntelligenceSourceFilter(event.target.value)
                    }
                    style={inputStyle}
                    disabled={intelligenceLoading}
                  >
                    <option value="all">All sources</option>
                    {Array.from(
                      new Set(
                        riskEntities
                          .map((entity) => entity.source)
                          .filter(
                            (value): value is string =>
                              Boolean(value && value.trim()),
                          ),
                      ),
                    )
                      .sort()
                      .map((source) => (
                        <option key={source} value={source}>
                          {source}
                        </option>
                      ))}
                  </select>

                  <select
                    value={intelligenceRiskFilter}
                    onChange={(event) =>
                      setIntelligenceRiskFilter(event.target.value)
                    }
                    style={inputStyle}
                    disabled={intelligenceLoading}
                  >
                    <option value="all">All risk categories</option>
                    <option value="centralized_exchange">
                      Centralized Exchange
                    </option>
                    <option value="decentralized_exchange">
                      Decentralized Exchange
                    </option>
                    <option value="mixer">Mixer</option>
                    <option value="sanctions">Sanctions</option>
                    <option value="scam">Scam</option>
                    <option value="stolen_funds">Stolen Funds</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <button
                  type="button"
                  onClick={() => void handleLoadRiskEntities()}
                  disabled={intelligenceLoading}
                  style={{ ...primaryButtonStyle, marginTop: "8px" }}
                >
                  {intelligenceLoading
                    ? "Loading Intelligence..."
                    : "Refresh Intelligence Registry"}
                </button>
              </div>

              <div style={panelSectionStyle}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    gap: "8px",
                  }}
                >
                  <div style={sectionTitleStyle}>Registered Risk Entities</div>
                  <span style={filterCountBadgeStyle}>
                    {riskEntities.length} record
                    {riskEntities.length === 1 ? "" : "s"}
                  </span>
                </div>

                {intelligenceLoading ? (
                  <div style={analyticsLoadingStyle}>
                    Loading documented intelligence records...
                  </div>
                ) : riskEntities.length === 0 ? (
                  <div style={analyticsEmptyStyle}>
                    No risk entities matched the current filters.
                  </div>
                ) : (
                  <div style={{ marginTop: "9px" }}>
                    {riskEntities.map((entity, index) => {
                      const entityKey = `${entity.chain}:${entity.address.toLowerCase()}`;
                      const isEditing = editingRiskEntityKey === entityKey;

                      return (
                        <div
                          key={`${entityKey}-${index}`}
                          style={{
                            ...analyticsListItemStyle,
                            marginBottom: "7px",
                          }}
                        >
                          {isEditing ? (
                            <>
                              <div
                                style={{
                                  color: "#D8EAEC",
                                  fontSize: "9px",
                                  wordBreak: "break-all",
                                }}
                              >
                                <strong>Address:</strong> {entity.address}
                              </div>
                              <div
                                style={{
                                  marginTop: "3px",
                                  color: "#8EADB1",
                                  fontSize: "9px",
                                }}
                              >
                                Chain: {entity.chain}
                              </div>

                              <input
                                value={editingRiskEntityName}
                                onChange={(event) =>
                                  setEditingRiskEntityName(event.target.value)
                                }
                                placeholder="Entity name"
                                style={{ ...inputStyle, marginTop: "7px" }}
                                disabled={riskEntitySaving}
                              />
                              <input
                                value={editingRiskEntityType}
                                onChange={(event) =>
                                  setEditingRiskEntityType(event.target.value)
                                }
                                placeholder="Entity type"
                                style={{ ...inputStyle, marginTop: "6px" }}
                                disabled={riskEntitySaving}
                              />
                              <input
                                value={editingRiskEntitySource}
                                onChange={(event) =>
                                  setEditingRiskEntitySource(event.target.value)
                                }
                                placeholder="Intelligence source"
                                style={{ ...inputStyle, marginTop: "6px" }}
                                disabled={riskEntitySaving}
                              />
                              <input
                                value={editingRiskEntityRiskCategory}
                                onChange={(event) =>
                                  setEditingRiskEntityRiskCategory(
                                    event.target.value,
                                  )
                                }
                                placeholder="Risk category"
                                style={{ ...inputStyle, marginTop: "6px" }}
                                disabled={riskEntitySaving}
                              />
                              <input
                                value={editingRiskEntityConfidence}
                                onChange={(event) =>
                                  setEditingRiskEntityConfidence(
                                    event.target.value,
                                  )
                                }
                                placeholder="Confidence 0-1"
                                inputMode="decimal"
                                style={{ ...inputStyle, marginTop: "6px" }}
                                disabled={riskEntitySaving}
                              />
                              <textarea
                                value={editingRiskEntityEvidence}
                                onChange={(event) =>
                                  setEditingRiskEntityEvidence(
                                    event.target.value,
                                  )
                                }
                                placeholder="Evidence"
                                rows={3}
                                style={{
                                  ...inputStyle,
                                  marginTop: "6px",
                                  resize: "vertical",
                                  lineHeight: 1.5,
                                }}
                                disabled={riskEntitySaving}
                              />

                              <div
                                style={{
                                  display: "flex",
                                  gap: "6px",
                                  marginTop: "7px",
                                }}
                              >
                                <button
                                  type="button"
                                  onClick={() =>
                                    void handleUpdateRiskEntity(entity)
                                  }
                                  disabled={riskEntitySaving}
                                  style={primaryButtonStyle}
                                >
                                  {riskEntitySaving ? "Saving..." : "Save"}
                                </button>
                                <button
                                  type="button"
                                  onClick={cancelEditingRiskEntity}
                                  disabled={riskEntitySaving}
                                  style={secondaryButtonStyle}
                                >
                                  Cancel
                                </button>
                              </div>
                            </>
                          ) : (
                            <>
                              <div
                                style={{
                                  display: "flex",
                                  justifyContent: "space-between",
                                  gap: "8px",
                                  alignItems: "flex-start",
                                }}
                              >
                                <div style={{ minWidth: 0 }}>
                                  <div style={sectionTitleStyle}>
                                    {entity.name ?? "Unnamed Risk Entity"}
                                  </div>
                                  <div
                                    style={{
                                      marginTop: "4px",
                                      color: "#B8D4D7",
                                      fontSize: "9px",
                                      wordBreak: "break-all",
                                    }}
                                  >
                                    {entity.address}
                                  </div>
                                </div>

                                <span
                                  style={{
                                    ...analyticsSeverityStyle,
                                    flexShrink: 0,
                                  }}
                                >
                                  {entity.confidence !== null
                                    ? `${(entity.confidence * 100).toFixed(1)}%`
                                    : "N/A"}
                                </span>
                              </div>

                              <div
                                style={{
                                  marginTop: "8px",
                                  display: "grid",
                                  gridTemplateColumns: "1fr 1fr",
                                  gap: "6px",
                                }}
                              >
                                <div style={analyticsStatStyle}>
                                  <span>Chain</span>
                                  <strong>{entity.chain}</strong>
                                </div>
                                <div style={analyticsStatStyle}>
                                  <span>Type</span>
                                  <strong>{entity.entity_type}</strong>
                                </div>
                                <div style={analyticsStatStyle}>
                                  <span>Source</span>
                                  <strong>{entity.source ?? "N/A"}</strong>
                                </div>
                                <div style={analyticsStatStyle}>
                                  <span>Risk</span>
                                  <strong>
                                    {entity.risk_category ?? "N/A"}
                                  </strong>
                                </div>
                              </div>

                              {entity.evidence && (
                                <div
                                  style={{
                                    marginTop: "8px",
                                    color: "#B8D4D7",
                                    fontSize: "9px",
                                    lineHeight: 1.5,
                                  }}
                                >
                                  <strong style={{ color: "#D8EAEC" }}>
                                    Evidence:
                                  </strong>{" "}
                                  {entity.evidence}
                                </div>
                              )}

                              {entity.updated_at && (
                                <div
                                  style={{
                                    marginTop: "5px",
                                    color: "#8EADB1",
                                    fontSize: "8px",
                                  }}
                                >
                                  Updated: {entity.updated_at}
                                </div>
                              )}

                              <div
                                style={{
                                  display: "flex",
                                  gap: "6px",
                                  marginTop: "8px",
                                }}
                              >
                                <button
                                  type="button"
                                  onClick={() => startEditingRiskEntity(entity)}
                                  disabled={riskEntitySaving}
                                  style={secondaryButtonStyle}
                                >
                                  Edit
                                </button>
                                <button
                                  type="button"
                                  onClick={() =>
                                    void handleDeleteRiskEntity(entity)
                                  }
                                  disabled={riskEntitySaving}
                                  style={{
                                    ...secondaryButtonStyle,
                                    borderColor: "#6A292D",
                                    color: "#E6A3A0",
                                  }}
                                >
                                  Delete
                                </button>
                              </div>
                            </>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              <div style={panelSectionStyle}>
                <div style={sectionTitleStyle}>Add Risk Entity</div>
                <div
                  style={{
                    marginTop: "6px",
                    color: "#8EADB1",
                    fontSize: "9px",
                    lineHeight: 1.45,
                  }}
                >
                  Add a documented intelligence entity to the registry. The
                  address is also linked to the Neo4j intelligence graph by
                  the backend.
                </div>

                <form
                  onSubmit={handleCreateRiskEntity}
                  style={{ marginTop: "10px" }}
                >
                  <input
                    value={newRiskEntityAddress}
                    onChange={(event) =>
                      setNewRiskEntityAddress(event.target.value)
                    }
                    placeholder="Wallet / risk entity address"
                    style={inputStyle}
                    disabled={riskEntitySaving}
                    required
                  />

                  <select
                    value={newRiskEntityChain}
                    onChange={(event) =>
                      setNewRiskEntityChain(event.target.value)
                    }
                    style={{ ...inputStyle, marginTop: "6px" }}
                    disabled={riskEntitySaving}
                  >
                    <option value="ethereum">Ethereum</option>
                    <option value="polygon">Polygon</option>
                    <option value="arbitrum">Arbitrum</option>
                    <option value="optimism">Optimism</option>
                    <option value="base">Base</option>
                  </select>

                  <input
                    value={newRiskEntityType}
                    onChange={(event) =>
                      setNewRiskEntityType(event.target.value)
                    }
                    placeholder="Entity type, e.g. vasp"
                    style={{ ...inputStyle, marginTop: "6px" }}
                    disabled={riskEntitySaving}
                    required
                  />

                  <input
                    value={newRiskEntityName}
                    onChange={(event) =>
                      setNewRiskEntityName(event.target.value)
                    }
                    placeholder="Entity name, e.g. Coinbase"
                    style={{ ...inputStyle, marginTop: "6px" }}
                    disabled={riskEntitySaving}
                    required
                  />

                  <input
                    value={newRiskEntitySource}
                    onChange={(event) =>
                      setNewRiskEntitySource(event.target.value)
                    }
                    placeholder="Intelligence source"
                    style={{ ...inputStyle, marginTop: "6px" }}
                    disabled={riskEntitySaving}
                    required
                  />

                  <input
                    value={newRiskEntityRiskCategory}
                    onChange={(event) =>
                      setNewRiskEntityRiskCategory(event.target.value)
                    }
                    placeholder="Risk category"
                    style={{ ...inputStyle, marginTop: "6px" }}
                    disabled={riskEntitySaving}
                  />

                  <input
                    value={newRiskEntityConfidence}
                    onChange={(event) =>
                      setNewRiskEntityConfidence(event.target.value)
                    }
                    placeholder="Confidence 0-1"
                    inputMode="decimal"
                    style={{ ...inputStyle, marginTop: "6px" }}
                    disabled={riskEntitySaving}
                    required
                  />

                  <textarea
                    value={newRiskEntityEvidence}
                    onChange={(event) =>
                      setNewRiskEntityEvidence(event.target.value)
                    }
                    placeholder="Evidence / source description"
                    rows={3}
                    style={{
                      ...inputStyle,
                      marginTop: "6px",
                      resize: "vertical",
                      lineHeight: 1.5,
                    }}
                    disabled={riskEntitySaving}
                  />

                  <button
                    type="submit"
                    disabled={
                      riskEntitySaving ||
                      !newRiskEntityAddress.trim() ||
                      !newRiskEntityName.trim()
                    }
                    style={{ ...primaryButtonStyle, marginTop: "7px" }}
                  >
                    {riskEntitySaving ? "Saving..." : "Add Risk Entity"}
                  </button>
                </form>
              </div>
            </>
          )}

          {/* CANDIDATE LINKING */}

          {!investigationMenuOpen && selectedWallet && investigationTab === "candidate-linking" && (
            <>
              <div style={panelSectionStyle}>
                <div style={sectionTitleStyle}>Candidate Linking</div>
                <div
                  style={{
                    marginTop: "7px",
                    fontSize: "10px",
                    color: "#B8D4D7",
                    lineHeight: 1.5,
                  }}
                >
                  Links the investigated wallet to known VASP intelligence
                  using existing transaction-path evidence. This is a
                  research-stage candidate assessment.
                </div>

                <div
                  style={{
                    marginTop: "10px",
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "6px",
                  }}
                >
                  <label style={labelStyle}>
                    Max Hops
                    <select
                      value={candidateLinkingMaxHops}
                      onChange={(event) =>
                        setCandidateLinkingMaxHops(event.target.value)
                      }
                      style={{ ...inputStyle, marginTop: "5px" }}
                      disabled={candidateLinkingLoading}
                    >
                      <option value="0">0</option>
                      <option value="1">1</option>
                      <option value="2">2</option>
                    </select>
                  </label>

                  <div
                    style={{
                      padding: "8px",
                      border: "1px solid #174047",
                      borderRadius: "6px",
                      background: "#061116",
                      color: "#B8D4D7",
                      fontSize: "8px",
                      lineHeight: 1.5,
                      alignSelf: "end",
                    }}
                  >
                    Source: existing VASP intelligence + Neo4j
                    transaction-path evidence
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => void handleCandidateLinking()}
                  disabled={candidateLinkingLoading}
                  style={{
                    ...primaryButtonStyle,
                    marginTop: "10px",
                  }}
                >
                  {candidateLinkingLoading
                    ? "Linking Candidates..."
                    : "Analyze Candidate Links"}
                </button>
              </div>

              {candidateLinkingLoading && (
                <div style={analyticsLoadingStyle}>
                  Evaluating known VASP intelligence and transaction-path
                  evidence...
                </div>
              )}

              {candidateLinking && (
                <>
                  <div style={panelSectionStyle}>
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        gap: "8px",
                      }}
                    >
                      <div style={sectionTitleStyle}>Linking Summary</div>
                      <span style={filterCountBadgeStyle}>
                        {candidateLinking.candidate_count} candidate
                        {candidateLinking.candidate_count === 1 ? "" : "s"}
                      </span>
                    </div>

                    <div
                      style={{
                        marginTop: "8px",
                        display: "grid",
                        gridTemplateColumns: "1fr 1fr",
                        gap: "6px",
                      }}
                    >
                      <div style={analyticsStatStyle}>
                        <span>Status</span>
                        <strong>{candidateLinking.status}</strong>
                      </div>
                      <div style={analyticsStatStyle}>
                        <span>Max hops</span>
                        <strong>{candidateLinking.max_hops}</strong>
                      </div>
                      <div style={analyticsStatStyle}>
                        <span>Chain</span>
                        <strong>{candidateLinking.chain}</strong>
                      </div>
                      <div style={analyticsStatStyle}>
                        <span>Candidates</span>
                        <strong>{candidateLinking.candidate_count}</strong>
                      </div>
                    </div>

                    <div
                      style={{
                        marginTop: "10px",
                        color: "#8EADB1",
                        fontSize: "9px",
                        lineHeight: 1.5,
                      }}
                    >
                      {candidateLinking.method}
                    </div>
                  </div>

                  {candidateLinking.candidates.length === 0 ? (
                    <div style={analyticsEmptyStyle}>
                      No candidate links were found within the configured
                      transaction path depth.
                    </div>
                  ) : (
                    candidateLinking.candidates.map((candidate, index) => (
                      <div
                        key={`${candidate.address}-${candidate.name ?? "candidate"}-${index}`}
                        style={panelSectionStyle}
                      >
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            gap: "8px",
                            alignItems: "flex-start",
                          }}
                        >
                          <div style={{ minWidth: 0 }}>
                            <div style={sectionTitleStyle}>
                              {candidate.name ?? "Known VASP"}
                            </div>
                            <div
                              style={{
                                marginTop: "5px",
                                color: "#B8D4D7",
                                fontSize: "9px",
                                wordBreak: "break-all",
                              }}
                            >
                              {candidate.address}
                            </div>
                          </div>

                          <span
                            style={{
                              ...analyticsSeverityStyle,
                              color: "#58F7FF",
                              flexShrink: 0,
                            }}
                          >
                            {candidate.confidence !== null
                              ? `${(candidate.confidence * 100).toFixed(1)}%`
                              : "N/A"}
                          </span>
                        </div>

                        <div
                          style={{
                            marginTop: "9px",
                            display: "grid",
                            gridTemplateColumns: "1fr 1fr",
                            gap: "6px",
                          }}
                        >
                          <div style={analyticsStatStyle}>
                            <span>Hop</span>
                            <strong>{candidate.hop ?? "N/A"}</strong>
                          </div>
                          <div style={analyticsStatStyle}>
                            <span>Link Basis</span>
                            <strong>{candidate.link_basis}</strong>
                          </div>
                          <div style={analyticsStatStyle}>
                            <span>Link Strength</span>
                            <strong>{candidate.link_strength}</strong>
                          </div>
                          <div style={analyticsStatStyle}>
                            <span>Source</span>
                            <strong>{candidate.source ?? "N/A"}</strong>
                          </div>
                        </div>

                        {candidate.risk_category && (
                          <div
                            style={{
                              marginTop: "7px",
                              color: "#B8D4D7",
                              fontSize: "9px",
                            }}
                          >
                            Risk category:{" "}
                            <strong style={{ color: "#D8EAEC" }}>
                              {candidate.risk_category}
                            </strong>
                          </div>
                        )}

                        {candidate.reason && (
                          <div
                            style={{
                              marginTop: "9px",
                              color: "#D8EAEC",
                              fontSize: "10px",
                              lineHeight: 1.5,
                            }}
                          >
                            <strong>Reason:</strong> {candidate.reason}
                          </div>
                        )}

                        {candidate.signals.length > 0 && (
                          <div
                            style={{
                              marginTop: "8px",
                              display: "flex",
                              flexWrap: "wrap",
                              gap: "4px",
                            }}
                          >
                            {candidate.signals.map((signal) => (
                              <span
                                key={signal}
                                style={{
                                  padding: "3px 5px",
                                  borderRadius: "999px",
                                  background: "#102126",
                                  color: "#D8EAEC",
                                  fontSize: "7px",
                                }}
                              >
                                {signal}
                              </span>
                            ))}
                          </div>
                        )}

                        {candidate.evidence && (
                          <div
                            style={{
                              marginTop: "8px",
                              color: "#B8D4D7",
                              fontSize: "10px",
                              lineHeight: 1.5,
                            }}
                          >
                            <strong style={{ color: "#D8EAEC" }}>
                              Evidence:
                            </strong>{" "}
                            {candidate.evidence}
                          </div>
                        )}

                        <details
                          style={{
                            marginTop: "9px",
                            color: "#B8D4D7",
                          }}
                        >
                          <summary
                            style={{
                              cursor: "pointer",
                              color: "#49D6A0",
                              fontSize: "10px",
                            }}
                          >
                            Linked Transaction Evidence
                          </summary>

                          <div
                            style={{
                              marginTop: "8px",
                              fontSize: "9px",
                              color: "#D8EAEC",
                              lineHeight: 1.5,
                            }}
                          >
                            {candidate.wallets.length > 0 && (
                              <>
                                <div>
                                  <strong>Wallet path:</strong>
                                </div>
                                <div
                                  style={{
                                    marginTop: "4px",
                                    wordBreak: "break-all",
                                  }}
                                >
                                  {candidate.wallets.join(" → ")}
                                </div>
                              </>
                            )}

                            {candidate.transfers.map(
                              (transfer, transferIndex) => (
                                <div
                                  key={`${transfer.transaction_hash}-${transferIndex}`}
                                  style={{
                                    marginTop: "8px",
                                    padding: "8px",
                                    background: "#02090C",
                                    border: "1px solid #12252A",
                                    borderRadius: "6px",
                                  }}
                                >
                                  <div>
                                    <strong>Transaction:</strong>{" "}
                                    <span style={{ wordBreak: "break-all" }}>
                                      {transfer.transaction_hash}
                                    </span>
                                  </div>
                                  <div style={{ marginTop: "4px" }}>
                                    <strong>Asset:</strong>{" "}
                                    {transfer.asset ?? "N/A"} ·{" "}
                                    <strong>Value:</strong>{" "}
                                    {transfer.value ?? "N/A"}
                                  </div>
                                  <div style={{ marginTop: "4px" }}>
                                    <strong>Category:</strong>{" "}
                                    {transfer.category ?? "N/A"} ·{" "}
                                    <strong>Block:</strong>{" "}
                                    {transfer.block_number ?? "N/A"}
                                  </div>
                                  <div style={{ marginTop: "4px" }}>
                                    <strong>Timestamp:</strong>{" "}
                                    {transfer.timestamp ?? "N/A"}
                                  </div>
                                </div>
                              ),
                            )}
                          </div>
                        </details>
                      </div>
                    ))
                  )}

                  <div style={amlDisclaimerStyle}>
                    {candidateLinking.notice}
                  </div>
                </>
              )}
            </>
          )}

          {/* CASE NOTES */}

          {!investigationMenuOpen && selectedWallet && investigationTab === "notes" && (
            <>
              <div style={panelSectionStyle}>
                <div style={sectionTitleStyle}>Analyst Notes</div>
                <div style={{ marginTop: "6px", color: "#8EADB1", fontSize: "9px", lineHeight: 1.45 }}>
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
                          <div style={{ color: "#EAF7F8", fontSize: "11px", lineHeight: 1.55, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
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

          {!investigationMenuOpen && selectedWallet && investigationTab === "wallet" && (
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
                      "#02090C",
                    border:
                      "1px solid #174047",
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

              <div
                style={{
                  marginTop: "12px",
                  display: "flex",
                  gap: "8px",
                }}
              >
                <button
                  type="button"
                  onClick={() => {
                    setHighlightPathEnabled((current) => !current);
                  }}
                  disabled={
                    selectedWallet.toLowerCase() ===
                    address.toLowerCase()
                  }
                  style={{
                    flex: 1,
                    border: highlightPathEnabled
                      ? "1px solid #00F7FF"
                      : "1px solid #34545A",
                    borderRadius: "6px",
                    padding: "9px 10px",
                    background: highlightPathEnabled
                      ? "#04181B"
                      : "#0B1D22",
                    color: highlightPathEnabled
                      ? "#F3FAFA"
                      : "#D8EAEC",
                    cursor:
                      selectedWallet.toLowerCase() ===
                      address.toLowerCase()
                        ? "not-allowed"
                        : "pointer",
                    fontSize: "16px",
                    fontWeight: 700,
                    boxShadow: highlightPathEnabled
                      ? "0 0 12px rgba(217,154,43,0.18)"
                      : "none",
                  }}
                >
                  {highlightPathEnabled
                    ? "Clear Path Highlight"
                    : "Highlight Path"}
                </button>
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
                        "#A9C5C8",
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
                            "#02090C",
                          border:
                            "1px solid #174047",
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

          {!investigationMenuOpen && selectedWallet && investigationTab === "analytics" && (
            <>
              <div style={panelSectionStyle}>
                <div style={sectionTitleStyle}>
                  Graph & Timeline Analytics
                </div>
                <div
                  style={{
                    marginTop: "7px",
                    fontSize: "10px",
                    color: "#B8D4D7",
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
                      background: "#10282C",
                      border: "1px solid #12434A",
                      borderRadius: "6px",
                      color: "#2DEAF2",
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
                    color: "#B8D4D7",
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
                          <div style={{ color: "#B8D4D7", marginTop: "3px" }}>
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
                            <div style={{ marginTop: "4px", color: "#D8EAEC", lineHeight: 1.45 }}>
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
                          <div style={{ marginTop: "3px", color: "#B8D4D7", wordBreak: "break-all" }}>
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
                            <div style={{ marginTop: "4px", color: "#D8EAEC", lineHeight: 1.45 }}>
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
                          <div style={{ marginTop: "3px", color: "#B8D4D7", wordBreak: "break-all" }}>
                            {shortenAddress(tx.counterparty)}
                          </div>
                          <div style={{ marginTop: "3px", color: "#8EADB1" }}>
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
                          <div style={{ marginTop: "3px", color: "#B8D4D7" }}>
                            {burst.start_time} → {burst.end_time}
                          </div>
                          <div style={{ marginTop: "3px", color: "#8EADB1" }}>
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

          {!investigationMenuOpen && selectedWallet && investigationTab === "evidence" && (
            <>
              <div style={panelSectionStyle}>
                <div style={sectionTitleStyle}>Case Evidence</div>
                <div style={{ marginTop: "6px", color: "#8EADB1", fontSize: "9px", lineHeight: 1.45 }}>
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
                          border: "1px solid #174047",
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
                                  <strong style={{ color: "#F3FAFA", fontSize: "12px", wordBreak: "break-word" }}>
                                    {evidence.title}
                                  </strong>
                                  <span style={analyticsSeverityStyle}>
                                    {evidence.evidence_type}
                                  </span>
                                </div>
                                {evidence.description && (
                                  <div style={{ marginTop: "6px", color: "#D8EAEC", fontSize: "10px", lineHeight: 1.5, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                                    {evidence.description}
                                  </div>
                                )}
                                {evidence.reference && (
                                  <div style={{ marginTop: "7px", color: "#49D6A0", fontSize: "9px", lineHeight: 1.45, wordBreak: "break-all" }}>
                                    Reference: {evidence.reference}
                                  </div>
                                )}
                                <div style={{ marginTop: "7px", color: "#8EADB1", fontSize: "8px" }}>
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
                                  style={{ ...secondaryButtonStyle, color: "#E6A3A0", borderColor: "#6A292D" }}
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

          {!investigationMenuOpen && selectedWallet && investigationTab === "ml-aml" && (
            <>
              <div style={panelSectionStyle}>
                <div style={sectionTitleStyle}>ML Risk + AML Assessment</div>
                <div style={{ marginTop: "7px", fontSize: "10px", color: "#B8D4D7", lineHeight: 1.5 }}>
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
                          <span style={{ color: "#B8D4D7", wordBreak: "break-word" }}>{name}</span>
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
                            color: "#F3FAFA",
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
                                color: "#F3FAFA",
                                fontSize: "12px",
                                wordBreak: "break-word",
                              }}
                            >
                              {signal.signal}
                            </strong>

                            <span
                              style={{
                                ...analyticsSeverityStyle,
                                color: "#2DEAF2",
                                flexShrink: 0,
                              }}
                            >
                              {signal.severity}
                            </span>
                          </div>

                          <div
                            style={{
                              marginTop: "4px",
                              color: "#8EADB1",
                              fontSize: "9px",
                              textTransform: "uppercase",
                            }}
                          >
                            Source: {signal.source}
                          </div>

                          <div
                            style={{
                              marginTop: "6px",
                              color: "#D8EAEC",
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
                                color: "#B8D4D7",
                              }}
                            >
                              <summary
                                style={{
                                  cursor: "pointer",
                                  color: "#49D6A0",
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

          {!investigationMenuOpen && selectedTransfer && investigationTab === "transaction" && (
            <>
              <div
                style={
                  panelSectionStyle
                }
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: "8px",
                  }}
                >
                  <div style={sectionTitleStyle}>Transaction</div>
                  {selectedTransfer.source_type === "peel_chain" && (
                    <span
                      style={{
                        fontSize: "8px",
                        padding: "3px 6px",
                        borderRadius: "999px",
                        background: "#13272C",
                        color: "#65F9FF",
                        border: "1px solid #00DCE6",
                      }}
                    >
                      Peel Chain
                    </span>
                  )}
                </div>

                <div
                  style={{
                    marginTop:
                      "8px",
                    padding:
                      "10px",
                    background:
                      "#02090C",
                    border:
                      "1px solid #174047",
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
                      selectedTransfer.hop_number
                        ? `Hop ${selectedTransfer.hop_number} of ${selectedTransfer.hop_count}`
                        : selectedTransfer.hop_count
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
                      "#C9E0E3",
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
                      "#A9C5C8",
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
              "#281316",
            border:
              "1px solid #FF5E68",
            borderRadius:
              "8px",
            color:
              "#FFC1BE",
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

      {token && sidebarCollapsed && (
        <button
          type="button"
          onClick={() => {
            setSidebarCollapsed(false);
            window.setTimeout(() => {
              reactFlowInstance?.fitView({ padding: 0.18 });
            }, 120);
          }}
          title="Show case workspace"
          aria-label="Show case workspace"
          style={{
            position: "absolute",
            top: "80px",
            left: "14px",
            zIndex: 30,
            display: "flex",
            alignItems: "center",
            gap: "7px",
            height: "34px",
            padding: "0 11px",
            borderRadius: "8px",
            border: "1px solid #34545A",
            background: "rgba(15, 17, 19, 0.96)",
            color: "#F3FAFA",
            boxShadow: "0 8px 24px rgba(0,0,0,0.32)",
            cursor: "pointer",
            fontSize: "16px",
            fontWeight: 700,
          }}
        >
          <span style={{ fontSize: "16px", lineHeight: 1 }}>☰</span>
          Show Workspace
        </button>
      )}

      <div
        className="cg-graph"
        style={{
          width: "100%",
          height:
            "calc(100vh - 64px)",
          position: "relative",
          background: "#061116",
        }}
      >
        {token && trace && nodes.length > 0 && (
          <>
            <div
              className="cg-filter"
              style={{
                position: "absolute",
                top: "16px",
                left: sidebarCollapsed ? "16px" : "430px",
                zIndex: 10,
                width: "270px",
                padding: "12px",
                background: "rgba(11, 29, 31, 0.96)",
                border: "1px solid #12252A",
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
                    color: "#B8D4D7",
                    border: "none",
                    cursor: "pointer",
                    fontSize: "16px",
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
                  color: "#B8D4D7",
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
              background: "rgba(11, 29, 31, 0.94)",
              border: "1px solid #12252A",
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
          nodes={graphNodes}
          edges={graphEdges}
          fitView
          onInit={setReactFlowInstance}
          minZoom={0.2}
          maxZoom={2}
          panOnDrag={true}
          selectionOnDrag={false}
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
        <Background
          color="#12252A"
          gap={18}
          size={1}
        />

        {token && (
          <>
            <Controls
              showInteractive={false}
            />

            <MiniMap
              style={{
                background: "#02090C",
                border: "1px solid #174047",
                borderRadius: "10px",
                boxShadow: "0 10px 30px rgba(0,0,0,0.35)",
              }}
              nodeStrokeWidth={2}
              nodeColor={(node) => {
                const label =
                  String(
                    node.data?.label ??
                      "",
                  );

                return label.startsWith(
                  "TARGET",
                )
                  ? "#FF5E68"
                  : "#789BA0";
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
  /* DEEP TEAL VISUAL SYSTEM */
  @keyframes cg-path-flow {
    to { stroke-dashoffset: -28px; }
  }

  .cg-graph .react-flow__edge.cg-path-highlight .react-flow__edge-path {
    stroke: #00F7FF !important;
    stroke-width: 4px !important;
    stroke-dasharray: 8 6 !important;
    filter: drop-shadow(0 0 5px rgba(217,154,43,0.85));
    animation: cg-path-flow 1.15s linear infinite;
  }

  .cg-graph .react-flow__edge.cg-path-dim,
  .cg-graph .react-flow__edge.cg-path-dim * {
    pointer-events: none !important;
    cursor: default !important;
  }

  .cg-graph .react-flow__edge.cg-path-dim .react-flow__edge-path {
    opacity: 0.14 !important;
  }

  .cg-graph .react-flow__edge.cg-path-highlight .react-flow__edge-text {
    fill: #F3FAFA !important;
  }

  .cg-graph .react-flow__edge.cg-path-highlight .react-flow__edge-textbg {
    fill: #04181B !important;
    stroke: #00F7FF !important;
  }

  .cg-graph .react-flow__attribution { display: none !important; }
  .cg-graph .react-flow__controls {
    box-shadow: 0 10px 28px rgba(5, 24, 27, 0.18) !important;
  }
  .cg-graph .react-flow__controls-button {
    width: 30px !important;
    height: 30px !important;
    background: #061116 !important;
    color: #C9E0E3 !important;
    border-color: #174047 !important;
  }
  .cg-graph .react-flow__controls-button:hover {
    background: #08181D !important;
    color: #EAF7F8 !important;
  }
  .cg-graph .react-flow__minimap {
    background: #061116 !important;
    border: 1px solid #174047 !important;
    box-shadow: 0 10px 28px rgba(5, 24, 27, 0.18) !important;
  }
  .cg-graph .react-flow__minimap-mask {
    fill: rgba(21, 154, 156, 0.10) !important;
  }
  .cg-graph .react-flow__node {
    font-family: Arial, sans-serif;
  }
  .cg-graph .react-flow__edge-textbg {
    fill: #061116 !important;
  }
  .cg-graph .react-flow__edge-text {
    fill: #C9E0E3 !important;
  }

  /* =========================
     DEEP TEAL THEME
     Technical teal surfaces + restrained cyan-green accent.
  ========================= */
  :root {
    color-scheme: dark;
    --cg-bg: #02090C;
    --cg-panel: #061116;
    --cg-card: #08181D;
    --cg-border: #12252A;
    --cg-border-soft: #174047;
    --cg-text: #EAF7F8;
    --cg-muted: #A9C5C8;
    --cg-accent: #00F7FF;
    --cg-accent-hover: #35F9FF;
    --cg-success: #49D6A0;
    --cg-warning: #2DEAF2;
    --cg-danger: #FF5E68;
  }

  .cg-graph .react-flow {
    background: #061116 !important;
  }

  .cg-graph .react-flow__minimap {
    background: #061116 !important;
    border: 1px solid #12252A !important;
  }

  .cg-graph .react-flow__controls-button {
    background: #061116 !important;
    color: #C9E0E3 !important;
    border-color: #174047 !important;
  }

  .cg-graph .react-flow__controls-button:hover {
    background: #08181D !important;
    color: #EAF7F8 !important;
  }

  .cg-sidebar,
  .cg-investigation {
    scrollbar-color: #174047 transparent;
  }

  * { box-sizing: border-box; }
  html, body, #root { margin: 0; width: 100%; height: 100%; overflow: hidden; }
  button, input, select, textarea { font: inherit; }

  .cg-header {
    height: 64px !important;
    padding: 0 20px !important;
  }
  .cg-header h1 { font-size: 20px !important; }
  .cg-header > div:first-child { min-width: 0; }

  .cg-sidebar {
    top: 78px !important;
    left: 16px !important;
    width: 380px !important;
    max-height: calc(100vh - 94px) !important;
    padding: 14px !important;
    border-radius: 16px !important;
    font-size: 11px !important;
  }
  .cg-sidebar h3 { font-size: 15px !important; }
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
    top: 78px !important;
    right: 16px !important;
    width: 390px !important;
    max-height: calc(100vh - 94px) !important;
    padding: 16px !important;
    border-radius: 14px !important;
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
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 6px !important;
    width: max-content !important;
    max-width: none !important;
    padding: 6px !important;
    box-sizing: border-box !important;
  }
  .cg-graph-actions button {
    flex: 0 0 auto !important;
    height: 32px !important;
    padding: 0 10px !important;
    font-size: 10px !important;
    white-space: nowrap !important;
  }

  .cg-graph {
    height: calc(100vh - 64px) !important;
  }

  .cg-graph .react-flow__controls {
    overflow: hidden;
    border: 1px solid #174047;
    border-radius: 10px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.35);
  }

  .cg-graph .react-flow__controls-button {
    width: 30px;
    height: 30px;
    background: #061116;
    color: #C9E0E3;
    border-bottom: 1px solid #174047;
  }

  .cg-graph .react-flow__controls-button:hover {
    background: #08181D;
  }

  .cg-graph .react-flow__minimap-mask {
    fill: rgba(0, 247, 255, 0.06);
  }

  .cg-graph .react-flow__attribution {
    display: none;
  }

  .cg-empty-state {
    animation: cg-fade-in 220ms ease-out;
  }

  /* GRAPHITE + AMBER FINAL POLISH */
  .cg-graph .react-flow {
    background: #02090C !important;
  }
  .cg-graph .react-flow__pane {
    background: #02090C !important;
  }
  .cg-graph .react-flow__edge-textbg {
    fill: #08181D !important;
    stroke: #174047 !important;
  }
  .cg-graph .react-flow__edge-text {
    fill: #C9E0E3 !important;
  }
  .cg-graph .react-flow__minimap {
    background: #061116 !important;
    border-color: #174047 !important;
  }
  .cg-graph-actions {
    background: rgba(15, 17, 19, 0.96) !important;
    border-color: #174047 !important;
  }
  .cg-filter {
    background: rgba(15, 17, 19, 0.96) !important;
    border-color: #174047 !important;
  }

  @keyframes cg-fade-in {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .cg-sidebar::-webkit-scrollbar { width: 7px; }
  .cg-sidebar::-webkit-scrollbar-track { background: transparent; }
  .cg-sidebar::-webkit-scrollbar-thumb { background: #24494C; border-radius: 999px; }
  .cg-sidebar form { border-radius: 10px !important; }
  .cg-sidebar input,
  .cg-sidebar select,
  .cg-sidebar textarea {
    border-color: #174047 !important;
    background: #071418 !important;
    border-radius: 8px !important;
  }
  .cg-sidebar button { transition: filter 120ms ease, transform 120ms ease; }
  .cg-sidebar button:hover:not(:disabled) { filter: brightness(1.08); }

  /* Investigation report CTA: green success treatment with the same strong
     border/glow language used by the danger/target treatment. */
  .cg-generate-report {
    color: #02090C !important;
    text-shadow: none !important;
    box-shadow:
      0 0 0 1px rgba(73, 214, 160, 0.18),
      0 0 14px rgba(73, 214, 160, 0.30),
      0 5px 18px rgba(0, 0, 0, 0.24) !important;
    transition:
      background 140ms ease,
      border-color 140ms ease,
      box-shadow 140ms ease,
      transform 140ms ease,
      filter 140ms ease !important;
  }

  .cg-generate-report:hover:not(:disabled) {
    background: #63E6B1 !important;
    border-color: #63E6B1 !important;
    color: #02090C !important;
    box-shadow:
      0 0 0 1px rgba(99, 230, 177, 0.24),
      0 0 20px rgba(73, 214, 160, 0.48),
      0 7px 22px rgba(0, 0, 0, 0.28) !important;
    transform: translateY(-1px);
  }

  .cg-generate-report:disabled {
    color: #8FB7AA !important;
    box-shadow: 0 0 0 1px rgba(73, 214, 160, 0.10) !important;
  }

  @media (max-width: 1150px) {
    .cg-sidebar { width: 300px !important; }
    .cg-filter { left: 52% !important; }
    .cg-investigation { width: 330px !important; }
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
      max-width: calc(100vw - 16px) !important;
      overflow-x: auto !important;
      justify-content: flex-start !important;
    }
    .cg-graph-actions button {
      flex: 0 0 auto !important;
    }
    .cg-investigation {
      left: 8px !important;
      right: 8px !important;
      bottom: 8px !important;
      max-height: 42vh !important;
    }
  }

  /* FINAL BUTTON READABILITY */
  .cg-header button,
  .cg-sidebar button,
  .cg-investigation button,
  .cg-graph-actions button {
    font-size: 16px !important;
    line-height: 1.2 !important;
    box-sizing: border-box !important;
    white-space: nowrap !important;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .cg-graph-actions button {
    min-height: 32px;
  }

  /* Align analysis section titles with their descriptions. */
  .cg-sidebar h3 {
    text-align: left !important;
  }
`;

const workspaceToggleButtonStyle: React.CSSProperties = {
  background: "#061116",
  color: "#D8EAEC",
  border: "1px solid #174047",
  borderRadius: "8px",
  padding: "8px 11px",
  cursor: "pointer",
  fontSize: "16px",
  fontWeight: 700,
  transition: "background 140ms ease, border-color 140ms ease",
};

const investigationMenuStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: "8px",
  marginBottom: "10px",
};

const investigationMenuButtonStyle: React.CSSProperties = {
  width: "100%",
  minHeight: "46px",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: "12px",
  padding: "10px 13px",
  boxSizing: "border-box",
  border: "1px solid #174047",
  borderRadius: "8px",
  background: "#07151A",
  color: "#E9FAFB",
  cursor: "pointer",
  fontFamily: "Inter, Arial, sans-serif",
  fontSize: "15px",
  fontWeight: 600,
  textAlign: "left",
  transition: "background 140ms ease, border-color 140ms ease, transform 140ms ease",
};

const investigationMenuArrowStyle: React.CSSProperties = {
  color: "#00F7FF",
  fontSize: "24px",
  lineHeight: 1,
  fontWeight: 400,
  flex: "0 0 auto",
};

const investigationBackBarStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "10px",
  marginBottom: "12px",
  paddingBottom: "10px",
  borderBottom: "1px solid #15363B",
};

const investigationBackButtonStyle: React.CSSProperties = {
  width: "34px",
  height: "34px",
  minWidth: "34px",
  padding: 0,
  display: "grid",
  placeItems: "center",
  border: "1px solid #174047",
  borderRadius: "7px",
  background: "#07151A",
  color: "#00F7FF",
  cursor: "pointer",
  fontFamily: "Inter, Arial, sans-serif",
  fontSize: "22px",
  lineHeight: 1,
  fontWeight: 500,
};

const investigationBackTitleStyle: React.CSSProperties = {
  minWidth: 0,
  color: "#F3FAFA",
  fontSize: "16px",
  fontWeight: 700,
  lineHeight: 1.2,
};

const investigationTabsStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "1fr 1fr",
  gap: "4px",
  padding: "3px",
  marginBottom: "10px",
  background: "#02090C",
  border: "1px solid #12252A",
  borderRadius: "7px",
};

const investigationTabStyle = (active: boolean): React.CSSProperties => ({
  border: "none",
  borderRadius: "5px",
  padding: "7px 8px",
  cursor: "pointer",
  background: active ? "#00F7FF" : "transparent",
  color: active ? "#02090C" : "#A9C5C8",
  fontSize: "12px",
  fontWeight: 700,
});

const filterCountBadgeStyle: React.CSSProperties = {
  padding: "2px 6px",
  borderRadius: "999px",
  background: "#0B1D22",
  color: "#65F9FF",
  fontSize: "9px",
  fontWeight: 700,
};

const filterIconButtonStyle: React.CSSProperties = {
  width: "22px",
  height: "22px",
  padding: 0,
  border: "1px solid #174047",
  borderRadius: "5px",
  background: "#153033",
  color: "#D8EAEC",
  cursor: "pointer",
  fontSize: "16px",
  lineHeight: 1,
};

const graphFilterInputStyle = {
  width: "100%",
  boxSizing: "border-box" as const,
  padding: "7px 8px",
  background: "#02090C",
  color: "#F3FAFA",
  border: "1px solid #174047",
  borderRadius: "5px",
  outline: "none",
  fontSize: "10px",
};

const graphControlButtonStyle = {
  background: "#0B1D22",
  color: "#F3FAFA",
  border: "1px solid #34545A",
  borderRadius: "6px",
  padding: "0 11px",
  height: "32px",
  minWidth: "76px",
  cursor: "pointer",
  fontSize: "11px",
  fontWeight: 600,
  whiteSpace: "nowrap",
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  boxSizing: "border-box",
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
  background: "#02090C",
  border: "1px solid #174047",
  borderRadius: "6px",
  display: "flex",
  flexDirection: "column",
  gap: "3px",
};

const analyticsEmptyStyle: React.CSSProperties = {
  marginTop: "7px",
  padding: "8px",
  color: "#8EADB1",
  fontSize: "10px",
  background: "#02090C",
  borderRadius: "5px",
};

const analyticsListItemStyle: React.CSSProperties = {
  marginTop: "7px",
  padding: "9px",
  background: "#02090C",
  border: "1px solid #174047",
  borderRadius: "6px",
  fontSize: "10px",
  lineHeight: 1.45,
};

const analyticsSignalStyle: React.CSSProperties = {
  marginTop: "7px",
  padding: "9px",
  background: "#08181D",
  border: "1px solid #174047",
  borderRadius: "6px",
  fontSize: "10px",
  lineHeight: 1.45,
};

const analyticsSeverityStyle: React.CSSProperties = {
  marginLeft: "7px",
  padding: "2px 5px",
  borderRadius: "999px",
  background: "#0B1D22",
  color: "#65F9FF",
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

const analyticsWarningStyle: React.CSSProperties = { marginTop: "10px", padding: "10px", background: "#10282C", border: "1px solid #12434A", borderRadius: "6px", color: "#2DEAF2", fontSize: "11px", lineHeight: 1.5 };
const analyticsLoadingStyle: React.CSSProperties = { padding: "14px", color: "#B8D4D7", fontSize: "11px", textAlign: "center" };
const mlNoticeStyle: React.CSSProperties = { marginTop: "10px", padding: "10px", background: "#08181D", border: "1px solid #174047", borderRadius: "6px", color: "#D8EAEC", fontSize: "10px", lineHeight: 1.45 };
const featureRowStyle: React.CSSProperties = { display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: "8px", padding: "6px 0", borderBottom: "1px solid #293629", fontSize: "9px" };
const amlIndicatorStyle: React.CSSProperties = { marginTop: "7px", padding: "9px", background: "#08181D", border: "1px solid #174047", borderRadius: "6px", fontSize: "10px", lineHeight: 1.45 };
const noteCardStyle: React.CSSProperties = { marginTop: "8px", padding: "10px", background: "#02090C", border: "1px solid #174047", borderRadius: "6px" };
const noteMetaStyle: React.CSSProperties = { display: "flex", justifyContent: "space-between", gap: "8px", marginTop: "8px", color: "#8EADB1", fontSize: "8px", lineHeight: 1.4, flexWrap: "wrap" };
const noteActionsStyle: React.CSSProperties = { display: "flex", justifyContent: "flex-end", gap: "6px", marginTop: "8px" };
const notePrimaryActionStyle: React.CSSProperties = { border: "1px solid #00F7FF", borderRadius: "5px", padding: "5px 8px", background: "#00F7FF", color: "#02090C", cursor: "pointer", fontSize: "16px", fontWeight: 700 };
const noteSecondaryActionStyle: React.CSSProperties = { border: "1px solid #34545A", borderRadius: "5px", padding: "5px 8px", background: "#0B1D22", color: "#D8EAEC", cursor: "pointer", fontSize: "16px", fontWeight: 700 };
const noteDangerActionStyle: React.CSSProperties = { border: "1px solid #6A292D", borderRadius: "5px", padding: "5px 8px", background: "#2a1518", color: "#E6A3A0", cursor: "pointer", fontSize: "9px", fontWeight: 700 };
const evidencePreStyle: React.CSSProperties = { margin: "6px 0 0", padding: "8px", maxHeight: "180px", overflow: "auto", background: "#02090C", borderRadius: "5px", color: "#D8EAEC", fontSize: "9px", whiteSpace: "pre-wrap", wordBreak: "break-word" };
const amlDisclaimerStyle: React.CSSProperties = { marginTop: "12px", padding: "9px", background: "#02090C", border: "1px solid #174047", borderRadius: "6px", color: "#B8D4D7", fontSize: "9px", lineHeight: 1.5 };

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
          "1px solid #12252A",
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
                  "#A9C5C8",
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
            "#02090C",
          border:
            "1px solid #174047",
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
                  "#02090C",
                border:
                  "1px solid #174047",
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
                    "#C9E0E3",
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
                    "#02090C",
                  border:
                    "1px solid #174047",
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
  value: number | null | undefined,
): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "—";
  }

  return value.toLocaleString(
    undefined,
    {
      maximumFractionDigits: 6,
    },
  );
}

function getPeelPatternAssessment(candidate: PeelCandidate): {
  label: string;
  color: string;
  signalCount: number;
} {
  const hopProgression = candidate.hop_value_progression ?? [];
  const nonIncreasing =
    hopProgression.length > 0 &&
    hopProgression.every(
      (hop) =>
        Number.isFinite(hop.input_value) &&
        Number.isFinite(hop.forwarded_value) &&
        hop.forwarded_value <= hop.input_value,
    );

  const signals = [
    candidate.same_asset,
    candidate.timing.chronological,
    candidate.value_progression.available,
    candidate.value_progression.value_reduction,
    nonIncreasing,
  ];

  const signalCount = signals.filter(Boolean).length;

  if (signalCount >= 5) {
    return {
      label: "Strong pattern",
      color: "#00F7FF",
      signalCount,
    };
  }

  if (signalCount >= 4) {
    return {
      label: "Moderate pattern",
      color: "#2DEAF2",
      signalCount,
    };
  }

  return {
    label: "Limited pattern",
    color: "#FF817F",
    signalCount,
  };
}

function formatDuration(seconds: number): string {
  if (!Number.isFinite(seconds)) {
    return "Unknown";
  }

  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
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

function riskLevelColor(
  level: RiskResponse["risk_level"],
) {
  switch (level) {
    case "critical":
      return "#FF817F";

    case "high":
      return "#00AAB2";

    case "moderate":
      return "#2DEAF2";

    case "low":
      return "#00F7FF";

    default:
      return "#F3FAFA";
  }
}

function riskSeverityColor(
  severity: RiskIndicator["severity"],
) {
  switch (severity) {
    case "critical":
      return "#FF817F";

    case "high":
      return "#00AAB2";

    case "medium":
      return "#2DEAF2";

    case "low":
      return "#00F7FF";

    default:
      return "#C9E0E3";
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
      "#02090C",
    color:
      "#F3FAFA",
    border:
      "1px solid #174047",
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
      "#C9E0E3",
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
    background: "#061116",
    color: "#D8EAEC",
    border: "1px solid #174047",
    borderRadius: "6px",
    cursor: "pointer",
    fontWeight: 600,
    fontSize: "16px",
  };

const primaryButtonStyle: React.CSSProperties =
  {
    width: "100%",
    marginTop:
      "16px",
    padding:
      "10px 12px",
    background:
      "#00F7FF",
    color:
      "#02090C",
    border:
      "1px solid #00F7FF",
    borderRadius:
      "8px",
    cursor:
      "pointer",
    fontWeight:
      700,
    fontSize:
      "16px",
  };

const riskButtonStyle: React.CSSProperties =
  {
    width: "100%",
    marginTop:
      "10px",
    padding:
      "10px",
    background:
      "#00F7FF",
    color:
      "#02090C",
    border:
      "none",
    borderRadius:
      "6px",
    cursor:
      "pointer",
    fontWeight:
      700,
    fontSize:
      "16px",
  };

const statCardStyle: React.CSSProperties =
  {
    padding:
      "12px",
    background:
      "#02090C",
    borderRadius:
      "6px",
    border:
      "1px solid #174047",
  };

const miniStatStyle: React.CSSProperties =
  {
    padding:
      "8px",
    background:
      "#02090C",
    borderRadius:
      "6px",
    border:
      "1px solid #174047",
    display:
      "flex",
    flexDirection:
      "column",
    gap:
      "3px",
    fontSize:
      "10px",
    color:
      "#A9C5C8",
  };

const behaviorCardStyle: React.CSSProperties =
  {
    padding:
      "8px",
    background:
      "#02090C",
    border:
      "1px solid #174047",
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
      "#A9C5C8",
  };

const smallTitleStyle: React.CSSProperties =
  {
    fontSize:
      "11px",
    color:
      "#A9C5C8",
  };

const panelSectionStyle: React.CSSProperties =
  {
    marginTop:
      "14px",
    paddingTop:
      "12px",
    borderTop:
      "1px solid #12252A",
  };

const sectionTitleStyle: React.CSSProperties =
  {
    fontSize:
      "12px",
    fontWeight:
      700,
    color:
      "#F3FAFA",
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
      "#C9E0E3",
  };


export default App;













