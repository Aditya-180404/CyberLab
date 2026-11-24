"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Crosshair,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  RotateCcw,
  CheckCircle2,
  XCircle,
  Play,
  RefreshCw,
  Lock,
  Unlock,
  Ban,
  Clock,
  Terminal,
  Server,
  Radio,
  FileCheck,
  X,
  Check,
} from "lucide-react";
import { SOARPlaybookItem, SOARActionItem, SOARKPIsItem } from "../../lib/types";
import {
  fetchSOARPlaybooks,
  fetchSOARActions,
  fetchSOARKPIs,
  executeSOARPlaybook,
  approveSOARAction,
  rejectSOARAction,
  rollbackSOARAction,
} from "../../lib/api";

interface IncidentResponseSOARProps {
  authToken: string | null;
}

export function IncidentResponseSOAR({ authToken }: IncidentResponseSOARProps) {
  const [playbooks, setPlaybooks] = useState<SOARPlaybookItem[]>([]);
  const [actions, setActions] = useState<SOARActionItem[]>([]);
  const [kpis, setKpis] = useState<SOARKPIsItem | null>(null);
  const [loading, setLoading] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);

  // Execution Modal
  const [showRunModal, setShowRunModal] = useState(false);
  const [selectedPlaybook, setSelectedPlaybook] = useState<SOARPlaybookItem | null>(null);
  const [targetId, setTargetId] = useState("metasploitable2");
  const [targetType, setTargetType] = useState("ASSET");

  const loadData = useCallback(async () => {
    if (!authToken) return;
    setLoading(true);
    try {
      const [pbList, actList, kpiData] = await Promise.all([
        fetchSOARPlaybooks(authToken),
        fetchSOARActions(authToken),
        fetchSOARKPIs(authToken),
      ]);
      setPlaybooks(pbList);
      setActions(actList);
      setKpis(kpiData);
    } catch (err: any) {
      console.error("Failed to load SOAR data:", err);
    } finally {
      setLoading(false);
    }
  }, [authToken]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 8000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleApprove = async (actionId: string) => {
    if (!authToken) return;
    setActionLoadingId(actionId);
    try {
      await approveSOARAction(authToken, actionId);
      await loadData();
    } catch (err: any) {
      alert("Failed to approve action: " + err.message);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleReject = async (actionId: string) => {
    if (!authToken) return;
    const reason = prompt("Enter reason for rejecting this response action:", "Manual SOC analyst override");
    if (!reason) return;
    setActionLoadingId(actionId);
    try {
      await rejectSOARAction(authToken, actionId, reason);
      await loadData();
    } catch (err: any) {
      alert("Failed to reject action: " + err.message);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleRollback = async (actionId: string) => {
    if (!authToken) return;
    if (!confirm("Are you sure you want to rollback this containment action and restore the previous state?")) {
      return;
    }
    setActionLoadingId(actionId);
    try {
      await rollbackSOARAction(authToken, actionId);
      await loadData();
      alert("Containment action rolled back successfully.");
    } catch (err: any) {
      alert("Rollback failed: " + err.message);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleRunPlaybook = async () => {
    if (!authToken || !selectedPlaybook) return;
    setActionLoadingId(selectedPlaybook.id);
    try {
      await executeSOARPlaybook(authToken, selectedPlaybook.id, {
        target_id: targetId,
        target_name: targetId,
        target_type: targetType,
        action_type: selectedPlaybook.action_type,
      });
      setShowRunModal(false);
      await loadData();
      alert(`Playbook '${selectedPlaybook.name}' dispatched.`);
    } catch (err: any) {
      alert("Failed to execute playbook: " + err.message);
    } finally {
      setActionLoadingId(null);
    }
  };

  const pendingActions = actions.filter((a) => a.status === "PENDING_APPROVAL");

  const getStatusBadge = (st: string) => {
    switch (st) {
      case "COMPLETED":
        return "bg-emerald-500/20 text-emerald-300 border-emerald-500/40";
      case "PENDING_APPROVAL":
        return "bg-amber-500/20 text-amber-300 border-amber-500/40 animate-pulse";
      case "ROLLED_BACK":
        return "bg-purple-500/20 text-purple-300 border-purple-500/40";
      case "REJECTED":
        return "bg-slate-800 text-slate-400 border-slate-700";
      case "FAILED":
        return "bg-rose-500/20 text-rose-300 border-rose-500/40 font-bold";
      default:
        return "bg-slate-800 text-slate-300 border-slate-700";
    }
  };

  return (
    <div className="flex-1 flex flex-col p-6 space-y-6 max-w-7xl mx-auto w-full">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center space-x-2">
              <Crosshair className="w-5 h-5 text-cyan-400" />
              <span>SOAR &amp; Automated Incident Response</span>
            </h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              PHASE 7 ACTIVE
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
            Automated containment playbooks, human-in-the-loop authorization gates, verified post-action states, and instant rollback controls.
          </p>
        </div>

        <div className="flex items-center space-x-3 shrink-0">
          <button
            onClick={loadData}
            disabled={loading}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 transition"
            title="Refresh SOAR Queue"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-cyan-400" : ""}`} />
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <div className="text-[11px] uppercase tracking-wider text-slate-400 font-mono">Response Actions</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">{kpis?.total_actions ?? 0}</div>
          <div className="text-[11px] text-slate-400 mt-1">Total playbook dispatches</div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <div className="text-[11px] uppercase tracking-wider text-slate-400 font-mono">Pending Approvals</div>
          <div className="text-2xl font-bold font-mono text-amber-400 mt-1 flex items-center space-x-2">
            <span>{kpis?.pending_approval ?? 0}</span>
            {kpis && kpis.pending_approval > 0 && (
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping"></span>
            )}
          </div>
          <div className="text-[11px] text-amber-400/80 mt-1">Awaiting SOC Tier-2 signoff</div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <div className="text-[11px] uppercase tracking-wider text-slate-400 font-mono">Verified Actions</div>
          <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">{kpis?.completed_actions ?? 0}</div>
          <div className="text-[11px] text-emerald-400/80 mt-1">Post-execution checks passed</div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <div className="text-[11px] uppercase tracking-wider text-slate-400 font-mono">Rolled-Back Actions</div>
          <div className="text-2xl font-bold font-mono text-purple-400 mt-1">{kpis?.rolled_back ?? 0}</div>
          <div className="text-[11px] text-purple-400/80 mt-1">Safely reversed states</div>
        </div>
      </div>

      {/* Section 1: Pending Authorization Queue */}
      {pendingActions.length > 0 && (
        <div className="rounded-xl border border-amber-500/40 bg-amber-950/20 p-5 space-y-4 shadow-lg animate-in fade-in">
          <div className="flex items-center space-x-2 text-amber-300 font-bold text-sm font-mono">
            <AlertTriangle className="w-4 h-4 text-amber-400 animate-bounce" />
            <span>Human-in-the-Loop Authorization Gate ({pendingActions.length} Pending)</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            High-impact containment operations require explicit SOC Analyst or Administrator approval before mutating network access or virtual machine power states.
          </p>

          <div className="divide-y divide-amber-500/20 rounded-lg border border-amber-500/30 bg-slate-950 overflow-hidden">
            {pendingActions.map((act) => (
              <div key={act.id} className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 font-bold">
                      {act.action_type}
                    </span>
                    <span className="font-bold text-sm text-white">Target: {act.target_name || act.target_id}</span>
                  </div>
                  <div className="text-xs text-slate-400 flex items-center space-x-3 font-mono">
                    <span>Requested by: <strong className="text-slate-200">{act.requested_by}</strong></span>
                    <span>•</span>
                    <span>Queued at: {new Date(act.created_at).toLocaleTimeString()}</span>
                  </div>
                </div>

                <div className="flex items-center space-x-2 shrink-0">
                  <button
                    onClick={() => handleReject(act.id)}
                    disabled={actionLoadingId === act.id}
                    className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-rose-300 border border-rose-500/30 text-xs font-semibold flex items-center space-x-1.5 transition"
                  >
                    <XCircle className="w-3.5 h-3.5" />
                    <span>Reject</span>
                  </button>
                  <button
                    onClick={() => handleApprove(act.id)}
                    disabled={actionLoadingId === act.id}
                    className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold font-mono flex items-center space-x-1.5 shadow-md shadow-emerald-950 transition"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Authorize &amp; Execute</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Section 2: Automated Playbook Library */}
      <div className="space-y-3">
        <div className="text-xs font-semibold uppercase font-mono tracking-wider text-slate-300 flex items-center space-x-2">
          <Terminal className="w-3.5 h-3.5 text-cyan-400" />
          <span>Automated Containment Playbook Catalog</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {playbooks.map((pb) => (
            <div
              key={pb.id}
              className="rounded-xl border border-slate-800 bg-slate-950/80 p-4 space-y-3 flex flex-col justify-between hover:border-slate-700 transition"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 text-cyan-400 border border-slate-800">
                    {pb.action_type}
                  </span>
                  <span
                    className={`text-[9px] font-mono px-1.5 py-0.2 rounded border ${
                      pb.requires_approval
                        ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                        : "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                    }`}
                  >
                    {pb.requires_approval ? "Approval Gate" : "Autonomous"}
                  </span>
                </div>
                <div className="font-bold text-sm text-white">{pb.name}</div>
                <p className="text-xs text-slate-400 leading-relaxed">{pb.description}</p>
              </div>

              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
                <span className="text-[10px] font-mono text-slate-500">Trigger: {pb.trigger_event}</span>
                <button
                  onClick={() => {
                    setSelectedPlaybook(pb);
                    setShowRunModal(true);
                  }}
                  className="px-2.5 py-1 rounded-lg bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 border border-cyan-500/30 text-xs font-mono font-medium flex items-center space-x-1.5 transition"
                >
                  <Play className="w-3 h-3 text-cyan-400" />
                  <span>Execute</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Section 3: Response Action History & Rollback Console */}
      <div className="rounded-xl border border-slate-800 bg-slate-950/80 overflow-hidden shadow-lg">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950">
          <div className="flex items-center space-x-2 font-semibold text-sm text-slate-200">
            <FileCheck className="w-4 h-4 text-cyan-400" />
            <span>Response Action History &amp; Rollback Console</span>
            <span className="text-xs font-mono text-slate-400">({actions.length})</span>
          </div>
        </div>

        {actions.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs font-mono">
            No response actions executed yet.
          </div>
        ) : (
          <div className="divide-y divide-slate-800/60">
            {actions.map((act) => (
              <div
                key={act.id}
                className="p-4 hover:bg-slate-900/40 transition flex flex-col lg:flex-row lg:items-center justify-between gap-4"
              >
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${getStatusBadge(act.status)}`}>
                      {act.status}
                    </span>
                    <span className="font-bold text-sm text-white">{act.action_type}</span>
                    <span className="text-xs font-mono text-cyan-400">Target: {act.target_name || act.target_id}</span>
                  </div>

                  <p className="text-xs text-slate-400">
                    {act.verification_details || act.rejection_reason || "Action registered in execution queue."}
                  </p>

                  <div className="text-[11px] font-mono text-slate-500 flex flex-wrap items-center gap-x-3 gap-y-1 pt-0.5">
                    <span>ID: {act.id}</span>
                    <span>•</span>
                    <span>Requested by: {act.requested_by}</span>
                    {act.approved_by && (
                      <>
                        <span>•</span>
                        <span>Approved by: {act.approved_by}</span>
                      </>
                    )}
                    <span>•</span>
                    <span>Created: {new Date(act.created_at).toLocaleTimeString()}</span>
                  </div>
                </div>

                {/* Rollback Button */}
                <div className="flex items-center space-x-2 shrink-0">
                  {act.status === "COMPLETED" && act.rollback_supported && !act.is_rolled_back && (
                    <button
                      onClick={() => handleRollback(act.id)}
                      disabled={actionLoadingId === act.id}
                      className="px-3 py-1.5 rounded-lg bg-purple-950/80 hover:bg-purple-900 border border-purple-500/40 text-purple-300 text-xs font-mono font-medium flex items-center space-x-1.5 transition shadow-sm"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                      <span>Rollback Action</span>
                    </button>
                  )}
                  {act.is_rolled_back && (
                    <span className="text-[11px] font-mono text-purple-400 px-2 py-1 rounded bg-purple-500/10 border border-purple-500/20">
                      Rolled Back
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Execution Modal */}
      {showRunModal && selectedPlaybook && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2 text-cyan-400 font-bold text-sm font-mono">
                <Play className="w-4 h-4" />
                <span>Execute Playbook: {selectedPlaybook.name}</span>
              </div>
              <button onClick={() => setShowRunModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              {selectedPlaybook.description}
            </p>

            <div className="space-y-3">
              <div className="space-y-1">
                <label className="text-xs font-mono text-slate-400">Target Type:</label>
                <select
                  value={targetType}
                  onChange={(e) => setTargetType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-white font-mono focus:outline-none focus:border-cyan-500"
                >
                  <option value="ASSET">Unified Asset (Metasploitable2 / Target VM)</option>
                  <option value="AGENT">Autonomous Linux Agent</option>
                  <option value="IP">Malicious IP Address</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-mono text-slate-400">Target Identifier (Hostname or IP):</label>
                <input
                  type="text"
                  value={targetId}
                  onChange={(e) => setTargetId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-white font-mono focus:outline-none focus:border-cyan-500"
                  placeholder="e.g. metasploitable2 or 192.168.1.120"
                />
              </div>
            </div>

            <div className="pt-2 flex items-center justify-end space-x-3">
              <button
                onClick={() => setShowRunModal(false)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-medium transition"
              >
                Cancel
              </button>
              <button
                onClick={handleRunPlaybook}
                disabled={actionLoadingId === selectedPlaybook.id}
                className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold font-mono flex items-center space-x-2 transition shadow-md shadow-cyan-950"
              >
                <Play className={`w-3.5 h-3.5 ${actionLoadingId === selectedPlaybook.id ? "animate-spin" : ""}`} />
                <span>Dispatch Playbook</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
