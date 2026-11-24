"use client";

import React, { useState, useEffect } from "react";
import {
  GitBranch,
  Target,
  ShieldAlert,
  AlertTriangle,
  RefreshCw,
  Search,
  CheckCircle2,
  Lock,
  Radio,
  Flame,
  ArrowRight,
  ShieldCheck,
  Server,
  Terminal,
  Activity,
  Layers,
  Zap,
  RotateCcw,
} from "lucide-react";
import {
  DigitalTwinGraphResponse,
  DigitalTwinNode,
  AttackPathResponse,
  AttackPathItem,
  BlastRadiusResponse,
  ChokePointResponse,
  ChokePointItem,
} from "../../lib/types";
import {
  fetchDigitalTwinGraph,
  discoverAttackPaths,
  fetchAssetBlastRadius,
  fetchDefensiveChokePoints,
  simulateNodeCompromise,
  resetDigitalTwinSimulation,
} from "../../lib/api";

interface DigitalTwinViewProps {
  authToken: string | null;
}

export function DigitalTwinView({ authToken }: DigitalTwinViewProps) {
  const [activeTab, setActiveTab] = useState<"paths" | "blast" | "choke" | "topology">("paths");

  // Graph state
  const [graphData, setGraphData] = useState<DigitalTwinGraphResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Attack Path state
  const [sourceNodeId, setSourceNodeId] = useState<string>("node-adversary-ext-01");
  const [targetNodeId, setTargetNodeId] = useState<string>("node-crown-jewel-db-vault");
  const [attackPathsResult, setAttackPathsResult] = useState<AttackPathResponse | null>(null);
  const [selectedPath, setSelectedPath] = useState<AttackPathItem | null>(null);
  const [analyzingPaths, setAnalyzingPaths] = useState(false);

  // Blast Radius state
  const [selectedBlastAssetId, setSelectedBlastAssetId] = useState<string>("node-dmz-web-proxy-01");
  const [blastResult, setBlastResult] = useState<BlastRadiusResponse | null>(null);
  const [loadingBlast, setLoadingBlast] = useState(false);

  // Choke Points state
  const [chokeResult, setChokeResult] = useState<ChokePointResponse | null>(null);
  const [loadingChoke, setLoadingChoke] = useState(false);

  // Inspected node
  const [inspectedNode, setInspectedNode] = useState<DigitalTwinNode | null>(null);

  const loadGraph = async () => {
    if (!authToken) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchDigitalTwinGraph(authToken);
      setGraphData(data);
      // Auto-select inspected node
      if (data.nodes.length > 0 && !inspectedNode) {
        setInspectedNode(data.nodes[0]);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load Digital Twin graph");
    } finally {
      setLoading(false);
    }
  };

  const handleRunAttackPathAnalysis = async () => {
    if (!authToken) return;
    setAnalyzingPaths(true);
    try {
      const res = await discoverAttackPaths(authToken, {
        source_node_id: sourceNodeId,
        target_node_id: targetNodeId,
        max_hops: 6,
      });
      setAttackPathsResult(res);
      if (res.paths.length > 0) {
        setSelectedPath(res.paths[0]);
      } else {
        setSelectedPath(null);
      }
    } catch (err: any) {
      setError(err.message || "Failed to discover attack paths");
    } finally {
      setAnalyzingPaths(false);
    }
  };

  const handleRunBlastAnalysis = async (assetId: string) => {
    if (!authToken) return;
    setSelectedBlastAssetId(assetId);
    setLoadingBlast(true);
    try {
      const res = await fetchAssetBlastRadius(authToken, assetId);
      setBlastResult(res);
    } catch (err: any) {
      setError(err.message || "Failed to analyze blast radius");
    } finally {
      setLoadingBlast(false);
    }
  };

  const handleLoadChokePoints = async () => {
    if (!authToken) return;
    setLoadingChoke(true);
    try {
      const res = await fetchDefensiveChokePoints(authToken);
      setChokeResult(res);
    } catch (err: any) {
      setError(err.message || "Failed to load choke points");
    } finally {
      setLoadingChoke(false);
    }
  };

  const handleToggleCompromise = async (nodeId: string, currentComp: boolean) => {
    if (!authToken) return;
    try {
      await simulateNodeCompromise(authToken, nodeId, !currentComp);
      await loadGraph();
      if (attackPathsResult) handleRunAttackPathAnalysis();
      if (selectedBlastAssetId === nodeId) handleRunBlastAnalysis(nodeId);
    } catch (err: any) {
      setError(err.message || "Failed to toggle compromise");
    }
  };

  const handleResetSimulation = async () => {
    if (!authToken) return;
    try {
      await resetDigitalTwinSimulation(authToken);
      await loadGraph();
      if (attackPathsResult) handleRunAttackPathAnalysis();
    } catch (err: any) {
      setError(err.message || "Failed to reset simulation");
    }
  };

  useEffect(() => {
    if (authToken) {
      loadGraph();
      handleLoadChokePoints();
    }
  }, [authToken]);

  useEffect(() => {
    if (authToken && graphData && !attackPathsResult) {
      handleRunAttackPathAnalysis();
      handleRunBlastAnalysis(selectedBlastAssetId);
    }
  }, [graphData]);

  if (!authToken) {
    return (
      <div className="p-8 text-center bg-slate-900/60 border border-slate-800 rounded-xl m-6">
        <GitBranch className="w-12 h-12 text-slate-500 mx-auto mb-3" />
        <h3 className="text-lg font-semibold text-slate-300">Authentication Required</h3>
        <p className="text-sm text-slate-500 mt-1">Please sign in from the SOC Dashboard to access Digital Twin & Attack-Path Analysis.</p>
      </div>
    );
  }

  const summary = graphData?.summary;
  const nodes = graphData?.nodes || [];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto w-full">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-slate-950 via-slate-900 to-indigo-950/40 p-6 rounded-xl border border-slate-800 shadow-xl">
        <div>
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 shadow-md">
              <GitBranch className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-xl font-bold tracking-tight text-slate-100">Digital Twin & Attack-Path Engine</h1>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  NetworkX Centrality v0.8
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Topological graph modeling, MITRE ATT&CK lateral path discovery, blast radius quantification, and choke-point defense.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {summary && summary.compromised_nodes > 0 && (
            <button
              onClick={handleResetSimulation}
              className="px-3 py-1.5 rounded-lg border border-amber-500/30 bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 text-xs font-medium flex items-center space-x-1.5 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset Simulations ({summary.compromised_nodes})</span>
            </button>
          )}

          <button
            onClick={() => {
              loadGraph();
              handleLoadChokePoints();
            }}
            disabled={loading}
            className="px-3.5 py-1.5 rounded-lg border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-xs font-medium flex items-center space-x-1.5 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-indigo-400" : ""}`} />
            <span>Refresh Model</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3.5 bg-red-950/40 border border-red-500/30 rounded-lg text-xs text-red-300 flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 shrink-0 text-red-400" />
          <span>{error}</span>
        </div>
      )}

      {/* KPI Dial Bar */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-[11px] font-medium uppercase tracking-wider">Total Nodes</span>
              <Layers className="w-4 h-4 text-indigo-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-slate-100 mt-2">{summary.total_nodes}</div>
            <div className="text-[10px] text-slate-500 mt-1">Cross-domain entities</div>
          </div>

          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-[11px] font-medium uppercase tracking-wider">Directed Edges</span>
              <Activity className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-cyan-400 mt-2">{summary.total_edges}</div>
            <div className="text-[10px] text-slate-500 mt-1">Traversable routes</div>
          </div>

          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-[11px] font-medium uppercase tracking-wider">Compromised</span>
              <ShieldAlert className="w-4 h-4 text-red-400" />
            </div>
            <div className="flex items-baseline space-x-2 mt-2">
              <span className={`text-2xl font-bold font-mono ${summary.compromised_nodes > 0 ? "text-red-400" : "text-emerald-400"}`}>
                {summary.compromised_nodes}
              </span>
              {summary.compromised_nodes > 0 && (
                <span className="text-[10px] text-red-400 font-mono animate-pulse">ELEVATED</span>
              )}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Active threat targets</div>
          </div>

          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-[11px] font-medium uppercase tracking-wider">Crown Jewels</span>
              <Lock className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-amber-400 mt-2">{summary.critical_nodes}</div>
            <div className="text-[10px] text-slate-500 mt-1">Critical Tier Targets</div>
          </div>

          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-[11px] font-medium uppercase tracking-wider">Avg Posture Risk</span>
              <Flame className="w-4 h-4 text-orange-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-orange-400 mt-2">{summary.average_risk_score}</div>
            <div className="text-[10px] text-slate-500 mt-1">Risk index / 100</div>
          </div>

          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-[11px] font-medium uppercase tracking-wider">Choke Points</span>
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-emerald-400 mt-2">{summary.choke_points_count}</div>
            <div className="text-[10px] text-slate-500 mt-1">Optimal cut-vertices</div>
          </div>
        </div>
      )}

      {/* Navigation Sub-Tabs */}
      <div className="flex border-b border-slate-800 space-x-1">
        <button
          onClick={() => setActiveTab("paths")}
          className={`flex items-center space-x-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-all ${
            activeTab === "paths"
              ? "border-indigo-500 text-indigo-400 bg-indigo-500/5"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Zap className="w-4 h-4" />
          <span>Attack Path Discovery</span>
          {attackPathsResult && (
            <span className="px-1.5 py-0.2 rounded text-[10px] bg-indigo-500/20 text-indigo-300 font-mono">
              {attackPathsResult.total_paths_found}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab("blast")}
          className={`flex items-center space-x-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-all ${
            activeTab === "blast"
              ? "border-indigo-500 text-indigo-400 bg-indigo-500/5"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Flame className="w-4 h-4" />
          <span>Blast Radius Analyzer</span>
        </button>

        <button
          onClick={() => setActiveTab("choke")}
          className={`flex items-center space-x-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-all ${
            activeTab === "choke"
              ? "border-indigo-500 text-indigo-400 bg-indigo-500/5"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          <span>Defensive Choke Points</span>
        </button>

        <button
          onClick={() => setActiveTab("topology")}
          className={`flex items-center space-x-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-all ${
            activeTab === "topology"
              ? "border-indigo-500 text-indigo-400 bg-indigo-500/5"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <GitBranch className="w-4 h-4" />
          <span>Topological Twin Map</span>
        </button>
      </div>

      {/* Sub-Tab 1: Attack Path Discovery */}
      {activeTab === "paths" && (
        <div className="space-y-6">
          {/* Query Bar */}
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
            <div className="flex flex-1 flex-col md:flex-row items-center gap-3">
              <div className="w-full md:w-1/2">
                <label className="text-[10px] uppercase font-mono text-slate-400 mb-1 block">Adversary Entrypoint (Source)</label>
                <select
                  value={sourceNodeId}
                  onChange={(e) => setSourceNodeId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  {nodes.map((n) => (
                    <option key={n.id} value={n.id}>
                      {n.label} ({n.zone}) {n.is_compromised ? "[COMPROMISED]" : ""}
                    </option>
                  ))}
                </select>
              </div>

              <div className="hidden md:flex items-center justify-center pt-5 text-slate-500">
                <ArrowRight className="w-5 h-5 text-indigo-400" />
              </div>

              <div className="w-full md:w-1/2">
                <label className="text-[10px] uppercase font-mono text-slate-400 mb-1 block">Target Asset (Crown Jewel)</label>
                <select
                  value={targetNodeId}
                  onChange={(e) => setTargetNodeId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  {nodes.map((n) => (
                    <option key={n.id} value={n.id}>
                      {n.label} ({n.zone}) [Criticality: {n.criticality}]
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex items-end pt-0 md:pt-4">
              <button
                onClick={handleRunAttackPathAnalysis}
                disabled={analyzingPaths}
                className="w-full md:w-auto px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs flex items-center justify-center space-x-2 shadow-lg shadow-indigo-900/30 transition-all"
              >
                <Search className={`w-4 h-4 ${analyzingPaths ? "animate-spin" : ""}`} />
                <span>{analyzingPaths ? "Analyzing..." : "Discover Vectors"}</span>
              </button>
            </div>
          </div>

          {/* Recommended Choke Point Alert */}
          {attackPathsResult && attackPathsResult.recommended_choke_point && (
            <div className="p-4 rounded-xl border border-indigo-500/30 bg-indigo-950/30 flex items-center justify-between gap-4">
              <div className="flex items-center space-x-3">
                <ShieldCheck className="w-6 h-6 text-indigo-400 shrink-0" />
                <div>
                  <div className="text-xs font-bold text-indigo-200">Optimal Defensive Choke Point Identified</div>
                  <div className="text-xs text-indigo-300/80 mt-0.5">
                    Enforcing zero-trust isolation at <span className="font-mono font-bold text-white bg-indigo-900/60 px-1.5 py-0.5 rounded">{attackPathsResult.recommended_choke_point}</span> eliminates all active attack paths to the target crown jewel.
                  </div>
                </div>
              </div>
              <button
                onClick={() => setActiveTab("choke")}
                className="px-3 py-1.5 rounded-lg bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 border border-indigo-500/30 text-xs font-medium whitespace-nowrap"
              >
                Inspect Choke Point
              </button>
            </div>
          )}

          {/* Paths List & Step Details */}
          {attackPathsResult && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left Column: Discovered Vectors */}
              <div className="space-y-3">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Viable Vectors ({attackPathsResult.total_paths_found})
                </h3>
                {attackPathsResult.paths.map((p, idx) => {
                  const isSelected = selectedPath?.path_id === p.path_id;
                  return (
                    <div
                      key={p.path_id}
                      onClick={() => setSelectedPath(p)}
                      className={`p-4 rounded-xl border cursor-pointer transition-all ${
                        isSelected
                          ? "border-indigo-500 bg-indigo-950/40 shadow-lg shadow-indigo-950/50"
                          : "border-slate-800 bg-slate-900/60 hover:bg-slate-900/90 hover:border-slate-700"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-200">Vector #{idx + 1}</span>
                        <span
                          className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                            p.viability === "HIGH"
                              ? "bg-red-500/20 text-red-400 border border-red-500/30"
                              : "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                          }`}
                        >
                          {p.viability} VIABILITY
                        </span>
                      </div>

                      <div className="flex items-center space-x-3 mt-3 text-xs text-slate-400">
                        <div>
                          Hops: <span className="font-mono text-slate-200">{p.hops}</span>
                        </div>
                        <div>
                          Risk Index: <span className="font-mono text-orange-400 font-bold">{p.cumulative_risk}%</span>
                        </div>
                      </div>

                      <div className="mt-3 pt-3 border-t border-slate-800/80 flex flex-wrap gap-1.5">
                        {p.node_labels.map((lbl, lIdx) => (
                          <React.Fragment key={lIdx}>
                            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                              {lbl.split(" ")[0]}
                            </span>
                            {lIdx < p.node_labels.length - 1 && <span className="text-slate-600 text-xs">→</span>}
                          </React.Fragment>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Right Column: Step-by-Step MITRE ATT&CK Breakdown */}
              <div className="lg:col-span-2 space-y-4">
                {selectedPath ? (
                  <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 space-y-4">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                      <div>
                        <h4 className="text-sm font-bold text-slate-100 flex items-center space-x-2">
                          <span>Attack Vector Progression</span>
                          <span className="text-xs font-normal text-slate-400">({selectedPath.hops} Hops)</span>
                        </h4>
                        <p className="text-xs text-slate-400 mt-0.5">{selectedPath.mitigation_summary}</p>
                      </div>
                      <div className="text-right">
                        <div className="text-[10px] uppercase font-mono text-slate-400">Vector Risk</div>
                        <div className="text-lg font-bold font-mono text-orange-400">{selectedPath.cumulative_risk}%</div>
                      </div>
                    </div>

                    {/* Step Cards */}
                    <div className="space-y-3">
                      {selectedPath.steps.map((st) => (
                        <div
                          key={st.hop_number}
                          className="p-3.5 rounded-lg border border-slate-800 bg-slate-950/80 flex flex-col md:flex-row md:items-center justify-between gap-3"
                        >
                          <div className="flex items-start space-x-3">
                            <div className="w-7 h-7 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center font-mono font-bold text-xs shrink-0 mt-0.5">
                              {st.hop_number}
                            </div>
                            <div>
                              <div className="flex items-center space-x-2">
                                <span className="text-xs font-semibold text-slate-200">{st.technique_name}</span>
                                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-indigo-500/20 text-indigo-300">
                                  {st.technique_id}
                                </span>
                                <span className="text-[10px] font-mono text-slate-400">({st.tactic})</span>
                              </div>
                              <p className="text-xs text-slate-400 mt-1">{st.description}</p>
                              <div className="flex items-center space-x-3 mt-2 text-[10px] font-mono text-slate-400">
                                <span>From: {st.source_label}</span>
                                <span>→</span>
                                <span>To: {st.target_label}</span>
                                {st.port && (
                                  <span className="px-1.5 py-0.5 bg-slate-800 rounded text-cyan-400">
                                    {st.protocol}:{st.port}
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>

                          <div className="text-right shrink-0">
                            <span className="text-[10px] font-mono text-slate-400 block">Hop Risk</span>
                            <span className="text-xs font-mono font-bold text-amber-400">+{st.risk_weight}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="p-8 text-center bg-slate-900/40 border border-slate-800 rounded-xl text-slate-500 text-xs">
                    No attack paths selected. Click a vector on the left to inspect its exploit sequence.
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Sub-Tab 2: Blast Radius Analyzer */}
      {activeTab === "blast" && (
        <div className="space-y-6">
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex-1 w-full">
              <label className="text-[10px] uppercase font-mono text-slate-400 mb-1 block">
                Select Compromised Pivot Asset to Evaluate
              </label>
              <select
                value={selectedBlastAssetId}
                onChange={(e) => handleRunBlastAnalysis(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                {nodes.map((n) => (
                  <option key={n.id} value={n.id}>
                    {n.label} ({n.zone}) [Criticality: {n.criticality}] {n.is_compromised ? "- CURRENTLY COMPROMISED" : ""}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {blastResult && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Blast Gauge Card */}
              <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">Blast Radius Posture</h4>
                  <Flame className="w-5 h-5 text-orange-400" />
                </div>

                <div className="text-center py-4">
                  <div className="text-5xl font-extrabold font-mono text-orange-400">{blastResult.blast_score}%</div>
                  <div className="text-xs text-slate-400 mt-1">Infrastructure Blast Score</div>
                </div>

                <div className="border-t border-slate-800 pt-3 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">Total Downstream Reachable:</span>
                    <span className="font-mono font-bold text-slate-200">{blastResult.total_reachable_nodes} Hosts</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">Critical Targets Reachable:</span>
                    <span className="font-mono font-bold text-red-400">
                      {blastResult.reachable_by_criticality["CRITICAL"] || 0}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">High Targets Reachable:</span>
                    <span className="font-mono font-bold text-amber-400">
                      {blastResult.reachable_by_criticality["HIGH"] || 0}
                    </span>
                  </div>
                </div>

                {blastResult.containment_recommendation && (
                  <div className="p-3 bg-red-950/30 border border-red-500/20 rounded-lg text-xs text-red-300 mt-4">
                    <span className="font-bold block mb-1">Recommended Containment:</span>
                    {blastResult.containment_recommendation}
                  </div>
                )}
              </div>

              {/* Reachable Targets Table */}
              <div className="lg:col-span-2 p-5 rounded-xl border border-slate-800 bg-slate-900/60 space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                  Downstream Reachable Assets ({blastResult.reachable_assets.length})
                </h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="border-b border-slate-800 text-[10px] font-mono uppercase text-slate-400 bg-slate-950/50">
                      <tr>
                        <th className="p-2.5">Asset / Node</th>
                        <th className="p-2.5">Zone</th>
                        <th className="p-2.5">Criticality</th>
                        <th className="p-2.5">Hops</th>
                        <th className="p-2.5">Impact</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono">
                      {blastResult.reachable_assets.map((ast) => (
                        <tr key={ast.node_id} className="hover:bg-slate-800/30">
                          <td className="p-2.5 font-bold text-slate-200">{ast.label}</td>
                          <td className="p-2.5">
                            <span className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-slate-300">
                              {ast.zone}
                            </span>
                          </td>
                          <td className="p-2.5">
                            <span
                              className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                                ast.criticality === "CRITICAL"
                                  ? "bg-red-500/20 text-red-400"
                                  : ast.criticality === "HIGH"
                                  ? "bg-amber-500/20 text-amber-400"
                                  : "bg-slate-800 text-slate-400"
                              }`}
                            >
                              {ast.criticality}
                            </span>
                          </td>
                          <td className="p-2.5 text-slate-300">{ast.hops_away} hop(s)</td>
                          <td className="p-2.5 font-sans text-slate-400 text-[11px]">{ast.impact_summary}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Sub-Tab 3: Defensive Choke Points */}
      {activeTab === "choke" && (
        <div className="space-y-4">
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-100">NetworkX Betweenness Centrality Choke Points</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Nodes with the highest centrality index through which the majority of lateral movement paths must traverse.
              </p>
            </div>
            <button
              onClick={handleLoadChokePoints}
              disabled={loadingChoke}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-xs text-slate-300 flex items-center space-x-1.5"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingChoke ? "animate-spin" : ""}`} />
              <span>Recalculate Centrality</span>
            </button>
          </div>

          {chokeResult && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {chokeResult.choke_points.map((cp, idx) => (
                <div key={cp.node_id} className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-bold">
                      RANK #{idx + 1}
                    </span>
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                        cp.risk_level === "CRITICAL"
                          ? "bg-red-500/20 text-red-400 border border-red-500/30"
                          : "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                      }`}
                    >
                      {cp.risk_level} BOTTLENECK
                    </span>
                  </div>

                  <div>
                    <h4 className="text-sm font-bold text-slate-100">{cp.label}</h4>
                    <span className="text-[10px] font-mono text-slate-400">Zone: {cp.zone}</span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs font-mono bg-slate-950 p-3 rounded-lg border border-slate-800/80">
                    <div>
                      <span className="text-[10px] text-slate-500 block">Centrality:</span>
                      <span className="text-indigo-400 font-bold">{cp.betweenness_centrality}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 block">Paths Cut:</span>
                      <span className="text-emerald-400 font-bold">{cp.paths_intercepted_pct}%</span>
                    </div>
                  </div>

                  <p className="text-xs text-slate-400">{cp.recommendation}</p>

                  <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
                    <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-800/40">
                      {cp.suggested_action}
                    </span>
                    <button
                      onClick={() => handleToggleCompromise(cp.node_id, false)}
                      className="text-xs text-slate-400 hover:text-slate-200 transition-colors"
                    >
                      Inspect Node
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Sub-Tab 4: Topological Twin Map */}
      {activeTab === "topology" && (
        <div className="p-6 rounded-xl border border-slate-800 bg-slate-950 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-100">Topological Digital Twin Map</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Visual breakdown by architectural security zones. Click any node to inspect telemetry and open services.
              </p>
            </div>
            <div className="flex items-center space-x-3 text-xs">
              <span className="flex items-center space-x-1.5 text-slate-400">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                <span>Normal</span>
              </span>
              <span className="flex items-center space-x-1.5 text-red-400">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse"></span>
                <span>Compromised</span>
              </span>
              <span className="flex items-center space-x-1.5 text-amber-400">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
                <span>Crown Jewel</span>
              </span>
            </div>
          </div>

          {/* Zones Architecture Layout */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {["EXTERNAL", "TRANSIT_ROUTER", "DMZ", "INTERNAL", "SECURE_VAULT"].map((zoneName) => {
              const zoneNodes = nodes.filter((n) => n.zone === zoneName);
              return (
                <div key={zoneName} className="p-3.5 rounded-xl border border-slate-800/80 bg-slate-900/40 space-y-3">
                  <div className="border-b border-slate-800 pb-2">
                    <span className="text-[10px] font-mono uppercase font-bold text-indigo-400 tracking-wider">
                      {zoneName.replace("_", " ")}
                    </span>
                    <span className="text-[10px] text-slate-500 ml-1.5">({zoneNodes.length})</span>
                  </div>

                  <div className="space-y-2.5">
                    {zoneNodes.map((n) => {
                      const isInspected = inspectedNode?.id === n.id;
                      return (
                        <div
                          key={n.id}
                          onClick={() => setInspectedNode(n)}
                          className={`p-3 rounded-lg border cursor-pointer transition-all ${
                            isInspected
                              ? "border-indigo-500 bg-indigo-950/40 shadow-md"
                              : n.is_compromised
                              ? "border-red-500/50 bg-red-950/20"
                              : n.criticality === "CRITICAL"
                              ? "border-amber-500/40 bg-amber-950/10"
                              : "border-slate-800 bg-slate-950/80 hover:border-slate-700"
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-slate-200 truncate">{n.label}</span>
                            {n.is_compromised && (
                              <span className="w-2 h-2 rounded-full bg-red-500 animate-ping shrink-0 ml-1"></span>
                            )}
                          </div>
                          <div className="text-[10px] font-mono text-slate-400 mt-1">
                            {n.ip_addresses[0] || "Dynamic IP"}
                          </div>
                          <div className="flex items-center justify-between mt-2 pt-1.5 border-t border-slate-800/60 text-[10px]">
                            <span className="text-slate-500 font-mono">Risk: {n.risk_score}</span>
                            <span
                              className={`font-mono font-bold ${
                                n.criticality === "CRITICAL"
                                  ? "text-red-400"
                                  : n.criticality === "HIGH"
                                  ? "text-amber-400"
                                  : "text-slate-400"
                              }`}
                            >
                              {n.criticality}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Node Inspector Drawer */}
          {inspectedNode && (
            <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/80 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div>
                <div className="flex items-center space-x-2">
                  <h4 className="text-sm font-bold text-slate-100">{inspectedNode.label}</h4>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                    ID: {inspectedNode.id}
                  </span>
                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                      inspectedNode.is_compromised
                        ? "bg-red-500/20 text-red-400 border border-red-500/30"
                        : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                    }`}
                  >
                    {inspectedNode.is_compromised ? "COMPROMISED" : "HEALTHY"}
                  </span>
                </div>
                <div className="flex flex-wrap gap-2 mt-2 text-xs text-slate-400">
                  <span>Zone: {inspectedNode.zone}</span>
                  <span>•</span>
                  <span>IP: {inspectedNode.ip_addresses.join(", ") || "None"}</span>
                  <span>•</span>
                  <span>Criticality: {inspectedNode.criticality}</span>
                  <span>•</span>
                  <span>Posture Risk: {inspectedNode.risk_score}/100</span>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <button
                  onClick={() => handleToggleCompromise(inspectedNode.id, inspectedNode.is_compromised)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 border transition-all ${
                    inspectedNode.is_compromised
                      ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30 hover:bg-emerald-500/30"
                      : "bg-red-500/20 text-red-300 border-red-500/30 hover:bg-red-500/30"
                  }`}
                >
                  <Activity className="w-3.5 h-3.5" />
                  <span>{inspectedNode.is_compromised ? "Mark As Disinfected" : "Simulate Compromise"}</span>
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
