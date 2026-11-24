"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  Play,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Clock,
  Layers,
  Terminal,
  Server,
  Zap,
  Target,
  FileSearch,
  Crosshair,
  TrendingUp,
  Cpu,
} from "lucide-react";
import {
  SimulationScenarioItem,
  SimulationExecutionItem,
  MitreCoverageResponse,
  PurpleTeamKPIsItem,
  AssetItem,
} from "../../lib/types";
import {
  fetchSimulationScenarios,
  executeSimulationScenario,
  runPurpleTeamCampaign,
  fetchSimulationExecutions,
  fetchMitreCoverage,
  fetchPurpleTeamKPIs,
  fetchAssets,
} from "../../lib/api";

interface PurpleTeamStudioProps {
  authToken: string | null;
}

export function PurpleTeamStudio({ authToken }: PurpleTeamStudioProps) {
  const [activeTab, setActiveTab] = useState<"catalog" | "history" | "coverage">("catalog");
  const [selectedTactic, setSelectedTactic] = useState<string>("ALL");

  // Data states
  const [scenarios, setScenarios] = useState<SimulationScenarioItem[]>([]);
  const [executions, setExecutions] = useState<SimulationExecutionItem[]>([]);
  const [coverage, setCoverage] = useState<MitreCoverageResponse | null>(null);
  const [kpis, setKpis] = useState<PurpleTeamKPIsItem | null>(null);
  const [assets, setAssets] = useState<AssetItem[]>([]);

  // Selection states
  const [selectedAssetId, setSelectedAssetId] = useState<string>("");
  const [selectedExecution, setSelectedExecution] = useState<SimulationExecutionItem | null>(null);

  // Loading states
  const [loading, setLoading] = useState(false);
  const [executingId, setExecutingId] = useState<string | null>(null);
  const [runningCampaign, setRunningCampaign] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const loadData = async () => {
    if (!authToken) return;
    setLoading(true);
    setError(null);
    try {
      const [scens, execs, cov, kpiData, assetList] = await Promise.all([
        fetchSimulationScenarios(authToken),
        fetchSimulationExecutions(authToken, 25),
        fetchMitreCoverage(authToken),
        fetchPurpleTeamKPIs(authToken),
        fetchAssets(authToken).catch(() => []),
      ]);
      setScenarios(scens);
      setExecutions(execs);
      setCoverage(cov);
      setKpis(kpiData);
      setAssets(assetList || []);
      if (execs.length > 0 && !selectedExecution) {
        setSelectedExecution(execs[0]);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load Purple-Team data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (authToken) {
      loadData();
    }
  }, [authToken]);

  const handleExecuteScenario = async (scenarioId: string) => {
    if (!authToken) return;
    setExecutingId(scenarioId);
    setError(null);
    setSuccessMessage(null);
    try {
      const result = await executeSimulationScenario(authToken, scenarioId, selectedAssetId || undefined);
      setSuccessMessage(
        `Simulation '${result.scenario_name || scenarioId}' completed: ${result.validation_result?.detection_status}`
      );
      await loadData();
      setSelectedExecution(result);
    } catch (err: any) {
      setError(err.message || "Failed to execute atomic simulation");
    } finally {
      setExecutingId(null);
    }
  };

  const handleRunCampaign = async () => {
    if (!authToken) return;
    setRunningCampaign(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const res = await runPurpleTeamCampaign(authToken, selectedAssetId || undefined);
      setSuccessMessage(
        `Automated Purple-Team Campaign complete: ${res.total_scenarios_executed} scenarios executed with ${res.efficacy_rate_pct}% detection efficacy.`
      );
      await loadData();
      setActiveTab("coverage");
    } catch (err: any) {
      setError(err.message || "Campaign execution failed");
    } finally {
      setRunningCampaign(false);
    }
  };

  if (!authToken) {
    return (
      <div className="p-8 text-center bg-slate-900/60 border border-slate-800 rounded-xl m-6">
        <ShieldCheck className="w-12 h-12 text-slate-500 mx-auto mb-3" />
        <h3 className="text-lg font-semibold text-slate-300">Authentication Required</h3>
        <p className="text-sm text-slate-500 mt-1">Please sign in from the SOC Dashboard to access Purple-Team Validation Studio.</p>
      </div>
    );
  }

  const tactics = ["ALL", "Discovery", "Credential Access", "Privilege Escalation", "Execution"];
  const filteredScenarios = selectedTactic === "ALL"
    ? scenarios
    : scenarios.filter((s) => s.mitre_tactic.toLowerCase() === selectedTactic.toLowerCase());

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto w-full">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-slate-950 via-slate-900 to-purple-950/40 p-6 rounded-xl border border-slate-800 shadow-xl">
        <div>
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-lg bg-purple-500/10 border border-purple-500/30 text-purple-400 shadow-md">
              <Crosshair className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-xl font-bold tracking-tight text-slate-100">Purple-Team Validation Studio</h1>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
                  Continuous Control Validation v0.9
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Atomic attack simulation, automated detection validation, efficacy scoring, and MITRE ATT&CK defensive gap analysis.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleRunCampaign}
            disabled={runningCampaign}
            className="px-4 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold text-xs flex items-center space-x-2 shadow-lg shadow-purple-950/50 transition-all"
          >
            <Play className={`w-3.5 h-3.5 ${runningCampaign ? "animate-spin" : ""}`} />
            <span>{runningCampaign ? "Executing Campaign..." : "Run Full Campaign"}</span>
          </button>

          <button
            onClick={loadData}
            disabled={loading}
            className="px-3.5 py-2 rounded-lg border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-xs font-medium flex items-center space-x-1.5 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-purple-400" : ""}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3.5 bg-red-950/40 border border-red-500/30 rounded-lg text-xs text-red-300 flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 shrink-0 text-red-400" />
          <span>{error}</span>
        </div>
      )}

      {successMessage && (
        <div className="p-3.5 bg-emerald-950/40 border border-emerald-500/30 rounded-lg text-xs text-emerald-300 flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* KPI Dial Bar */}
      {kpis && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-[11px] font-medium uppercase tracking-wider">Simulations Run</span>
              <Play className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-slate-100 mt-2">{kpis.total_simulations}</div>
            <div className="text-[10px] text-slate-500 mt-1">Atomic scenario dispatches</div>
          </div>

          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-[11px] font-medium uppercase tracking-wider">Detection Efficacy</span>
              <TrendingUp className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="flex items-baseline space-x-2 mt-2">
              <span className="text-2xl font-bold font-mono text-emerald-400">{kpis.overall_efficacy_rate}%</span>
              <span className="text-[10px] font-mono text-slate-400">
                ({kpis.total_detected} / {kpis.total_simulations})
              </span>
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Validated by SIEM & EDR</div>
          </div>

          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-[11px] font-medium uppercase tracking-wider">Mean Time To Detect</span>
              <Clock className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-cyan-400 mt-2">
              {kpis.mean_time_to_detect_seconds}s
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Average detection latency</div>
          </div>

          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-[11px] font-medium uppercase tracking-wider">Coverage Gaps</span>
              <AlertTriangle className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-amber-400 mt-2">
              {coverage ? coverage.gap_techniques : kpis.total_missed}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Techniques needing SIEM rules</div>
          </div>
        </div>
      )}

      {/* Navigation Sub-Tabs */}
      <div className="flex border-b border-slate-800 space-x-1">
        <button
          onClick={() => setActiveTab("catalog")}
          className={`flex items-center space-x-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-all ${
            activeTab === "catalog"
              ? "border-purple-500 text-purple-400 bg-purple-500/5"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Zap className="w-4 h-4" />
          <span>Atomic Test Catalog</span>
          <span className="px-1.5 py-0.2 rounded text-[10px] bg-purple-500/20 text-purple-300 font-mono">
            {scenarios.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab("history")}
          className={`flex items-center space-x-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-all ${
            activeTab === "history"
              ? "border-purple-500 text-purple-400 bg-purple-500/5"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Terminal className="w-4 h-4" />
          <span>Validation Runs & Log</span>
          <span className="px-1.5 py-0.2 rounded text-[10px] bg-slate-800 text-slate-300 font-mono">
            {executions.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab("coverage")}
          className={`flex items-center space-x-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-all ${
            activeTab === "coverage"
              ? "border-purple-500 text-purple-400 bg-purple-500/5"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          <span>MITRE ATT&CK Coverage & Gaps</span>
          {coverage && (
            <span className="px-1.5 py-0.2 rounded text-[10px] bg-emerald-500/20 text-emerald-300 font-mono">
              {coverage.overall_coverage_pct}%
            </span>
          )}
        </button>
      </div>

      {/* Target Asset Selector Bar */}
      <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-3 w-full md:w-auto flex-1">
          <Server className="w-5 h-5 text-purple-400 shrink-0" />
          <div className="w-full max-w-md">
            <label className="text-[10px] uppercase font-mono text-slate-400 mb-1 block">
              Authorized Target Asset for Simulation
            </label>
            <select
              value={selectedAssetId}
              onChange={(e) => setSelectedAssetId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-purple-500"
            >
              <option value="">Default Synthetic Lab Endpoint (Safe In-Memory)</option>
              {assets.map((ast) => (
                <option key={ast.id} value={ast.id}>
                  {ast.name} ({ast.asset_type}) - Risk: {ast.risk_score}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="text-right text-[11px] text-slate-400">
          Safety Constraint: <span className="text-emerald-400 font-semibold font-mono">Bounded Atomic Telemetry</span>
        </div>
      </div>

      {/* Sub-Tab 1: Atomic Test Catalog */}
      {activeTab === "catalog" && (
        <div className="space-y-4">
          {/* Tactic Filter Buttons */}
          <div className="flex flex-wrap gap-1.5">
            {tactics.map((tac) => (
              <button
                key={tac}
                onClick={() => setSelectedTactic(tac)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  selectedTactic === tac
                    ? "bg-purple-600 text-white shadow-md shadow-purple-950/40"
                    : "bg-slate-900/80 text-slate-400 hover:text-slate-200 border border-slate-800"
                }`}
              >
                {tac}
              </button>
            ))}
          </div>

          {/* Scenario Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredScenarios.map((scen) => {
              const isExecuting = executingId === scen.id;
              return (
                <div
                  key={scen.id}
                  className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 flex flex-col justify-between space-y-4 hover:border-slate-700 transition-all"
                >
                  <div className="space-y-2.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 font-bold">
                        {scen.mitre_technique_id}
                      </span>
                      <span
                        className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                          scen.severity === "CRITICAL"
                            ? "bg-red-500/20 text-red-400 border border-red-500/30"
                            : scen.severity === "HIGH"
                            ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                            : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {scen.severity}
                      </span>
                    </div>

                    <div>
                      <h4 className="text-sm font-bold text-slate-100">{scen.name}</h4>
                      <span className="text-[11px] font-mono text-slate-400">{scen.mitre_tactic}</span>
                    </div>

                    <p className="text-xs text-slate-400">{scen.description}</p>

                    {scen.command_template && (
                      <div className="p-2.5 rounded bg-slate-950 border border-slate-800 text-[11px] font-mono text-cyan-300 overflow-x-auto">
                        {scen.command_template}
                      </div>
                    )}
                  </div>

                  <div className="pt-3 border-t border-slate-800/80 space-y-3">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-slate-500 font-mono">Expected SIEM Rule:</span>
                      <span className="font-mono text-indigo-400 truncate max-w-[160px]">
                        {scen.expected_detection_rule || "None (Baseline Discovery)"}
                      </span>
                    </div>

                    <button
                      onClick={() => handleExecuteScenario(scen.id)}
                      disabled={isExecuting}
                      className="w-full py-2 rounded-lg bg-slate-800 hover:bg-purple-600 text-slate-200 hover:text-white font-semibold text-xs flex items-center justify-center space-x-2 transition-all border border-slate-700 hover:border-purple-500"
                    >
                      <Play className={`w-3.5 h-3.5 ${isExecuting ? "animate-spin" : ""}`} />
                      <span>{isExecuting ? "Dispatching..." : "Execute Atomic Test"}</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Sub-Tab 2: Validation Runs & Telemetry Log */}
      {activeTab === "history" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Execution History Table */}
          <div className="lg:col-span-2 p-5 rounded-xl border border-slate-800 bg-slate-900/60 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Execution Stream & Detection Outcomes ({executions.length})
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-slate-800 text-[10px] font-mono uppercase text-slate-400 bg-slate-950/50">
                  <tr>
                    <th className="p-2.5">Technique / Scenario</th>
                    <th className="p-2.5">Target</th>
                    <th className="p-2.5">Outcome</th>
                    <th className="p-2.5">Latency</th>
                    <th className="p-2.5">Executed</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {executions.map((ex) => {
                    const isSelected = selectedExecution?.id === ex.id;
                    const detStatus = ex.validation_result?.detection_status;
                    return (
                      <tr
                        key={ex.id}
                        onClick={() => setSelectedExecution(ex)}
                        className={`cursor-pointer transition-colors ${
                          isSelected ? "bg-purple-950/40" : "hover:bg-slate-800/30"
                        }`}
                      >
                        <td className="p-2.5">
                          <div className="font-bold text-slate-200">{ex.scenario_name || ex.scenario_id}</div>
                          <span className="text-[10px] text-slate-400">{ex.mitre_technique_id}</span>
                        </td>
                        <td className="p-2.5 text-slate-300">{ex.target_name || "Synthetic"}</td>
                        <td className="p-2.5">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold inline-flex items-center space-x-1 ${
                              detStatus === "DETECTED"
                                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                                : "bg-red-500/20 text-red-400 border border-red-500/30"
                            }`}
                          >
                            {detStatus === "DETECTED" ? (
                              <CheckCircle2 className="w-3 h-3" />
                            ) : (
                              <XCircle className="w-3 h-3" />
                            )}
                            <span>{detStatus}</span>
                          </span>
                        </td>
                        <td className="p-2.5 text-slate-300">{ex.validation_result?.detection_latency_seconds}s</td>
                        <td className="p-2.5 text-[10px] text-slate-500">
                          {new Date(ex.executed_at).toLocaleTimeString()}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Execution Log & Inspection Drawer */}
          <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">Run Telemetry & Details</h4>
            {selectedExecution ? (
              <div className="space-y-3 text-xs">
                <div>
                  <span className="text-[10px] font-mono text-slate-500 block">Scenario:</span>
                  <div className="font-bold text-slate-100">{selectedExecution.scenario_name}</div>
                  <div className="text-[10px] font-mono text-purple-400">
                    {selectedExecution.mitre_tactic} ({selectedExecution.mitre_technique_id})
                  </div>
                </div>

                <div className="border-t border-slate-800/80 pt-2 space-y-1 text-slate-400 text-[11px]">
                  <div>Target: <span className="text-slate-200 font-mono">{selectedExecution.target_name}</span></div>
                  <div>Operator: <span className="text-slate-200 font-mono">{selectedExecution.executed_by}</span></div>
                  <div>Status: <span className="text-slate-200 font-mono">{selectedExecution.status}</span></div>
                </div>

                {selectedExecution.validation_result && (
                  <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono uppercase text-slate-500">Detection Result:</span>
                      <span
                        className={`text-[10px] font-mono font-bold ${
                          selectedExecution.validation_result.detection_status === "DETECTED"
                            ? "text-emerald-400"
                            : "text-red-400"
                        }`}
                      >
                        {selectedExecution.validation_result.detection_status}
                      </span>
                    </div>
                    {selectedExecution.validation_result.matched_rule_id && (
                      <div className="text-[10px] font-mono text-cyan-300">
                        Rule: {selectedExecution.validation_result.matched_rule_id}
                      </div>
                    )}
                    <p className="text-[11px] text-slate-400">{selectedExecution.validation_result.verification_details}</p>
                  </div>
                )}

                {selectedExecution.execution_log && (
                  <div>
                    <span className="text-[10px] font-mono text-slate-500 block mb-1">Execution Terminal Log:</span>
                    <pre className="p-3 rounded bg-slate-950 border border-slate-800 text-[10px] font-mono text-slate-300 overflow-x-auto whitespace-pre-wrap max-h-48">
                      {selectedExecution.execution_log}
                    </pre>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-6 text-center text-slate-500 text-xs">Select an execution from the left to inspect logs.</div>
            )}
          </div>
        </div>
      )}

      {/* Sub-Tab 3: MITRE ATT&CK Defensive Heatmap & Gap Matrix */}
      {activeTab === "coverage" && coverage && (
        <div className="space-y-6">
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-100">MITRE ATT&CK Defensive Coverage & Blind Spots</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Technique coverage mapping indicating covered detection rules versus unmonitored defensive gaps.
              </p>
            </div>
            <div className="flex items-center space-x-3 text-xs font-mono">
              <span className="text-emerald-400 bg-emerald-950/40 border border-emerald-500/30 px-2 py-0.5 rounded">
                Covered: {coverage.covered_techniques}
              </span>
              <span className="text-red-400 bg-red-950/40 border border-red-500/30 px-2 py-0.5 rounded">
                Gaps: {coverage.gap_techniques}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {coverage.coverage_items.map((item) => (
              <div
                key={item.technique_id}
                className={`p-4 rounded-xl border space-y-3 transition-all ${
                  item.coverage_status === "COVERED"
                    ? "border-emerald-500/40 bg-emerald-950/10 shadow-sm"
                    : item.coverage_status === "PARTIAL"
                    ? "border-amber-500/40 bg-amber-950/10"
                    : "border-red-500/30 bg-red-950/10 border-dashed"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-200 font-bold">
                    {item.technique_id}
                  </span>
                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                      item.coverage_status === "COVERED"
                        ? "bg-emerald-500/20 text-emerald-400"
                        : item.coverage_status === "PARTIAL"
                        ? "bg-amber-500/20 text-amber-400"
                        : "bg-red-500/20 text-red-400"
                    }`}
                  >
                    {item.coverage_status === "COVERED" ? "COVERED (100%)" : item.coverage_status}
                  </span>
                </div>

                <div>
                  <h4 className="text-sm font-bold text-slate-100">{item.technique_name}</h4>
                  <span className="text-[10px] font-mono text-slate-400">{item.tactic}</span>
                </div>

                <div className="text-[11px] font-mono pt-2 border-t border-slate-800/80 space-y-1">
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Simulations: {item.total_simulated}</span>
                    <span>Detected: {item.detected_count}</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Efficacy:</span>
                    <span className="font-bold text-slate-200">{item.detection_efficacy_pct}%</span>
                  </div>
                  {item.rule_name ? (
                    <div className="text-[10px] text-emerald-400 font-semibold truncate pt-1">
                      Rule: {item.rule_name}
                    </div>
                  ) : (
                    <div className="text-[10px] text-amber-400 font-semibold pt-1">
                      ⚠️ Detection Gap: SIEM Rule Required
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
