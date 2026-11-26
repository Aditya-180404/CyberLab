"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Radio,
  ShieldAlert,
  ShieldCheck,
  RefreshCw,
  Terminal,
  Server,
  Activity,
  HardDrive,
  Cpu,
  Lock,
  Unlock,
  AlertTriangle,
  FileSearch,
  ExternalLink,
  Ban,
  CheckCircle2,
  Clock,
  X,
  Copy,
  Check,
} from "lucide-react";
import { AgentItem, AgentDetailItem } from "../../lib/types";
import { fetchAgents, fetchAgentDetail, isolateAgent, restoreAgent, revokeAgent } from "../../lib/api";

interface EndpointFleetProps {
  authToken: string | null;
}

export function EndpointFleet({ authToken }: EndpointFleetProps) {
  const [agents, setAgents] = useState<AgentItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<AgentDetailItem | null>(null);
  const [inspectLoading, setInspectLoading] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);
  const [showDeployGuide, setShowDeployGuide] = useState(false);
  const [deployOS, setDeployOS] = useState<"linux" | "windows" | "macos" | "syslog">("linux");
  const [copiedCmd, setCopiedCmd] = useState(false);

  const loadAgents = useCallback(async () => {
    if (!authToken) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchAgents(authToken);
      setAgents(data);
    } catch (err: any) {
      setError(err.message || "Failed to load agent fleet");
    } finally {
      setLoading(false);
    }
  }, [authToken]);

  useEffect(() => {
    loadAgents();
    const interval = setInterval(loadAgents, 8000);
    return () => clearInterval(interval);
  }, [loadAgents]);

  const handleInspect = async (agentId: string) => {
    if (!authToken) return;
    setInspectLoading(true);
    try {
      const detail = await fetchAgentDetail(authToken, agentId);
      setSelectedAgent(detail);
    } catch (err: any) {
      alert("Error inspecting agent: " + err.message);
    } finally {
      setInspectLoading(false);
    }
  };

  const handleIsolate = async (agentId: string) => {
    if (!authToken) return;
    if (!confirm(`Are you sure you want to isolate endpoint '${agentId}'? This will drop all ingress/egress except CyberLab management traffic.`)) {
      return;
    }
    setActionLoadingId(agentId);
    try {
      await isolateAgent(authToken, agentId);
      await loadAgents();
      if (selectedAgent && selectedAgent.id === agentId) {
        handleInspect(agentId);
      }
    } catch (err: any) {
      alert("Failed to isolate endpoint: " + err.message);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleRestore = async (agentId: string) => {
    if (!authToken) return;
    setActionLoadingId(agentId);
    try {
      await restoreAgent(authToken, agentId);
      await loadAgents();
      if (selectedAgent && selectedAgent.id === agentId) {
        handleInspect(agentId);
      }
    } catch (err: any) {
      alert("Failed to restore endpoint: " + err.message);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleRevoke = async (agentId: string) => {
    if (!authToken) return;
    if (!confirm(`CAUTION: Revoking credentials for '${agentId}' will permanently invalidate its authentication token. Proceed?`)) {
      return;
    }
    setActionLoadingId(agentId);
    try {
      await revokeAgent(authToken, agentId);
      await loadAgents();
      if (selectedAgent && selectedAgent.id === agentId) {
        setSelectedAgent(null);
      }
    } catch (err: any) {
      alert("Failed to revoke credentials: " + err.message);
    } finally {
      setActionLoadingId(null);
    }
  };

  const getDeployCommand = () => {
    if (deployOS === "linux") return "sudo ./deploy/install-agent.sh --server http://<SOC_SERVER_IP>:8000";
    if (deployOS === "windows") return "powershell -ExecutionPolicy Bypass -File .\\deploy\\install-agent.ps1 -ServerUrl http://<SOC_SERVER_IP>:8000";
    if (deployOS === "macos") return "python3 agent/cyberlab_agent.py --server http://<SOC_SERVER_IP>:8000 --interval 10";
    return "Send syslog UDP/TCP -> <SOC_SERVER_IP>:5514  |  POST /api/v1/siem/ingest/ndr";
  };

  const handleCopyCmd = () => {
    navigator.clipboard.writeText(getDeployCommand());
    setCopiedCmd(true);
    setTimeout(() => setCopiedCmd(false), 2000);
  };

  // Fleet stats
  const totalCount = agents.length;
  const onlineCount = agents.filter((a) => a.status === "ONLINE").length;
  const isolatedCount = agents.filter((a) => a.status === "ISOLATED").length;
  const offlineCount = agents.filter((a) => a.status === "OFFLINE").length;

  return (
    <div className="flex-1 flex flex-col p-6 space-y-6 max-w-7xl mx-auto w-full">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center space-x-2">
              <Radio className="w-5 h-5 text-cyan-400" />
              <span>Endpoint Fleet & Distributed EDR</span>
            </h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              EDR FLEET ACTIVE
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
            Real-time telemetry, host inventory, listening socket mapping, file integrity monitoring (FIM), and automated SOAR quarantine execution.
          </p>
        </div>

        <div className="flex items-center space-x-3 shrink-0">
          <button
            onClick={() => setShowDeployGuide(!showDeployGuide)}
            className="px-3.5 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-cyan-300 border border-cyan-500/30 text-xs font-semibold flex items-center space-x-2 transition"
          >
            <Terminal className="w-4 h-4 text-cyan-400" />
            <span>Deploy Agent</span>
          </button>
          <button
            onClick={loadAgents}
            disabled={loading}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 transition"
            title="Refresh Fleet"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-cyan-400" : ""}`} />
          </button>
        </div>
      </div>

      {/* Deployment Guide Banner */}
      {showDeployGuide && (
        <div className="rounded-xl border border-cyan-500/30 bg-cyan-950/20 p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-cyan-400 font-semibold text-sm">
              <Terminal className="w-4 h-4" />
              <span>Connect Company Systems (Linux, Windows, macOS &amp; Firewalls)</span>
            </div>
            <button
              onClick={() => setShowDeployGuide(false)}
              className="text-slate-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="flex flex-wrap gap-2 text-xs font-mono">
            {(["linux", "windows", "macos", "syslog"] as const).map((osKey) => (
              <button
                key={osKey}
                onClick={() => setDeployOS(osKey)}
                className={`px-3 py-1 rounded-lg border uppercase transition ${
                  deployOS === osKey
                    ? "bg-cyan-600/20 text-cyan-300 border-cyan-500/40"
                    : "bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200"
                }`}
              >
                {osKey === "syslog" ? "Firewall / Syslog" : osKey}
              </button>
            ))}
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Install the autonomous agent on employee laptops, production servers, or forward OPNsense / Suricata / Zeek logs to collect live processes, active connections, installed packages, auth logs, and SHA-256 FIM alerts.
          </p>
          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono text-xs text-cyan-300">
            <span className="select-all truncate">{getDeployCommand()}</span>
            <button
              onClick={handleCopyCmd}
              className="ml-3 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] flex items-center space-x-1.5 transition shrink-0"
            >
              {copiedCmd ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedCmd ? "Copied" : "Copy"}</span>
            </button>
          </div>
          <div className="text-[11px] text-slate-400 flex items-center space-x-2">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <span>Add <code className="text-slate-300">--enrollment-key &lt;KEY&gt;</code> when <code className="text-slate-300">AGENT_ENROLLMENT_KEY</code> is enforced in production.</span>
          </div>
        </div>
      )}

      {/* Fleet KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <div className="text-[11px] uppercase tracking-wider text-slate-400 font-mono">Total Endpoints</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">{totalCount}</div>
          <div className="text-[11px] text-slate-400 mt-1">Fleet assets registered</div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <div className="text-[11px] uppercase tracking-wider text-slate-400 font-mono">Online Endpoints</div>
          <div className="text-2xl font-bold font-mono text-emerald-400 mt-1 flex items-center space-x-2">
            <span>{onlineCount}</span>
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          </div>
          <div className="text-[11px] text-emerald-400/80 mt-1">Active heartbeats OK</div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <div className="text-[11px] uppercase tracking-wider text-slate-400 font-mono">Quarantined (Isolated)</div>
          <div className="text-2xl font-bold font-mono text-amber-400 mt-1">{isolatedCount}</div>
          <div className="text-[11px] text-amber-400/80 mt-1">Network egress blocked</div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <div className="text-[11px] uppercase tracking-wider text-slate-400 font-mono">Offline Endpoints</div>
          <div className="text-2xl font-bold font-mono text-slate-400 mt-1">{offlineCount}</div>
          <div className="text-[11px] text-slate-400 mt-1">Heartbeat missed &gt;35s</div>
        </div>
      </div>

      {/* Main Agent List */}
      <div className="rounded-xl border border-slate-800 bg-slate-950/80 overflow-hidden shadow-lg">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950">
          <div className="flex items-center space-x-2 font-semibold text-sm text-slate-200">
            <Server className="w-4 h-4 text-cyan-400" />
            <span>Registered Linux Endpoints</span>
            <span className="text-xs font-mono text-slate-400">({agents.length})</span>
          </div>
          {loading && <span className="text-xs font-mono text-cyan-400 animate-pulse">Refreshing telemetry...</span>}
        </div>

        {error ? (
          <div className="p-8 text-center text-rose-400 text-xs font-mono">
            <AlertTriangle className="w-6 h-6 mx-auto mb-2 text-rose-400" />
            <span>{error}</span>
          </div>
        ) : agents.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <Radio className="w-8 h-8 mx-auto text-slate-600 animate-pulse" />
            <div className="text-sm font-semibold text-slate-300">No Linux Agents Connected Yet</div>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              Deploy an agent by running the standalone script on your Kali machine or target VM to start streaming live telemetry.
            </p>
            <button
              onClick={() => setShowDeployGuide(true)}
              className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold font-mono shadow-md shadow-cyan-950 transition"
            >
              View Quick Deploy Command
            </button>
          </div>
        ) : (
          <div className="divide-y divide-slate-800/60">
            {agents.map((agent) => {
              const isIso = agent.status === "ISOLATED";
              const isRev = agent.status === "REVOKED";
              const isOnline = agent.status === "ONLINE";

              return (
                <div
                  key={agent.id}
                  className="p-4.5 hover:bg-slate-900/40 transition flex flex-col lg:flex-row lg:items-center justify-between gap-4"
                >
                  {/* Left: Endpoint Identity */}
                  <div className="flex items-start space-x-3.5">
                    <div
                      className={`h-10 w-10 rounded-lg flex items-center justify-center shrink-0 border ${
                        isIso
                          ? "bg-amber-950/40 border-amber-500/40 text-amber-400"
                          : isOnline
                          ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-400"
                          : isRev
                          ? "bg-rose-950/40 border-rose-500/40 text-rose-400"
                          : "bg-slate-900 border-slate-700 text-slate-400"
                      }`}
                    >
                      {isIso ? <Lock className="w-5 h-5" /> : <Radio className="w-5 h-5" />}
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-sm text-white tracking-wide">{agent.hostname}</span>
                        <span
                          className={`text-[9px] font-mono px-2 py-0.5 rounded border uppercase ${
                            isIso
                              ? "bg-amber-500/10 text-amber-400 border-amber-500/30 font-bold"
                              : isOnline
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                              : isRev
                              ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                              : "bg-slate-800 text-slate-400 border-slate-700"
                          }`}
                        >
                          {agent.status}
                        </span>
                        <span className="text-[10px] font-mono text-cyan-400/90">{agent.ip_address}</span>
                      </div>

                      <div className="text-xs text-slate-400 flex flex-wrap items-center gap-x-3 gap-y-1">
                        <span>{agent.os_release}</span>
                        <span>•</span>
                        <span className="font-mono text-[11px] text-slate-400">Kernel {agent.kernel_version}</span>
                        <span>•</span>
                        <span className="font-mono text-[11px] text-slate-400">ID: {agent.id}</span>
                      </div>
                    </div>
                  </div>

                  {/* Middle: Hardware Specs */}
                  <div className="flex items-center space-x-6 text-xs text-slate-400 font-mono">
                    {agent.hardware_specs && (
                      <>
                        <div className="flex items-center space-x-1.5" title="CPU Cores">
                          <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                          <span>{agent.hardware_specs.cpu_cores || "?"} vCPU</span>
                        </div>
                        <div className="flex items-center space-x-1.5" title="RAM Total">
                          <Activity className="w-3.5 h-3.5 text-purple-400" />
                          <span>{Math.round((agent.hardware_specs.memory_mb || 0) / 1024)} GB</span>
                        </div>
                        <div className="flex items-center space-x-1.5" title="Disk Total">
                          <HardDrive className="w-3.5 h-3.5 text-emerald-400" />
                          <span>{agent.hardware_specs.disk_total_gb || "?"} GB</span>
                        </div>
                      </>
                    )}
                  </div>

                  {/* Right: Actions */}
                  <div className="flex items-center space-x-2 shrink-0">
                    <button
                      onClick={() => handleInspect(agent.id)}
                      disabled={inspectLoading}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium flex items-center space-x-1.5 transition"
                    >
                      <FileSearch className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Telemetry</span>
                    </button>

                    {!isRev && (
                      <>
                        {isIso ? (
                          <button
                            onClick={() => handleRestore(agent.id)}
                            disabled={actionLoadingId === agent.id}
                            className="px-3 py-1.5 rounded-lg bg-emerald-950/60 hover:bg-emerald-900 border border-emerald-500/40 text-emerald-300 text-xs font-medium flex items-center space-x-1.5 transition"
                          >
                            <Unlock className="w-3.5 h-3.5" />
                            <span>Restore Network</span>
                          </button>
                        ) : (
                          <button
                            onClick={() => handleIsolate(agent.id)}
                            disabled={actionLoadingId === agent.id}
                            className="px-3 py-1.5 rounded-lg bg-amber-950/60 hover:bg-amber-900 border border-amber-500/40 text-amber-300 text-xs font-medium flex items-center space-x-1.5 transition"
                          >
                            <Lock className="w-3.5 h-3.5" />
                            <span>Quarantine</span>
                          </button>
                        )}

                        <button
                          onClick={() => handleRevoke(agent.id)}
                          disabled={actionLoadingId === agent.id}
                          className="p-1.5 rounded-lg bg-slate-900 hover:bg-rose-950 text-slate-500 hover:text-rose-400 border border-transparent hover:border-rose-500/30 transition"
                          title="Revoke Agent Credentials"
                        >
                          <Ban className="w-3.5 h-3.5" />
                        </button>
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Inspection Modal / Drawer */}
      {selectedAgent && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-3xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950">
              <div className="flex items-center space-x-2.5">
                <Radio className="w-4 h-4 text-cyan-400" />
                <span className="font-bold text-white text-sm">Telemetry Inspection: {selectedAgent.hostname}</span>
                <span className="text-xs font-mono text-cyan-400">({selectedAgent.ip_address})</span>
              </div>
              <button
                onClick={() => setSelectedAgent(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-6">
              {/* Telemetry Resource Gauges */}
              {selectedAgent.latest_telemetry ? (
                <>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800">
                      <div className="text-[11px] font-mono uppercase text-slate-400 flex items-center justify-between">
                        <span>CPU Utilization</span>
                        <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                      </div>
                      <div className="text-xl font-bold font-mono text-cyan-300 mt-1">
                        {selectedAgent.latest_telemetry.cpu_pct.toFixed(1)}%
                      </div>
                    </div>
                    <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800">
                      <div className="text-[11px] font-mono uppercase text-slate-400 flex items-center justify-between">
                        <span>Memory Utilization</span>
                        <Activity className="w-3.5 h-3.5 text-purple-400" />
                      </div>
                      <div className="text-xl font-bold font-mono text-purple-300 mt-1">
                        {selectedAgent.latest_telemetry.memory_pct.toFixed(1)}%
                      </div>
                    </div>
                    <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800">
                      <div className="text-[11px] font-mono uppercase text-slate-400 flex items-center justify-between">
                        <span>Disk Utilization</span>
                        <HardDrive className="w-3.5 h-3.5 text-emerald-400" />
                      </div>
                      <div className="text-xl font-bold font-mono text-emerald-300 mt-1">
                        {selectedAgent.latest_telemetry.disk_pct.toFixed(1)}%
                      </div>
                    </div>
                  </div>

                  {/* FIM File Integrity Alerts */}
                  <div className="space-y-2">
                    <div className="text-xs font-semibold uppercase font-mono tracking-wider text-slate-300 flex items-center space-x-2">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                      <span>File Integrity Monitoring (FIM) Events</span>
                    </div>
                    {selectedAgent.latest_telemetry.fim_alerts && selectedAgent.latest_telemetry.fim_alerts.length > 0 ? (
                      <div className="rounded-lg border border-amber-500/30 bg-amber-950/20 divide-y divide-amber-500/20 text-xs">
                        {selectedAgent.latest_telemetry.fim_alerts.map((alert, idx) => (
                          <div key={idx} className="p-2.5 flex items-center justify-between font-mono">
                            <div className="flex items-center space-x-2">
                              <span className="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 text-[10px] font-bold">
                                {alert.action}
                              </span>
                              <span className="text-slate-200">{alert.path}</span>
                            </div>
                            <span className="text-amber-400 text-[11px]">{alert.message}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-400 font-mono">
                        No integrity violations detected on monitored system paths.
                      </div>
                    )}
                  </div>

                  {/* Open Listening Sockets */}
                  <div className="space-y-2">
                    <div className="text-xs font-semibold uppercase font-mono tracking-wider text-slate-300 flex items-center space-x-2">
                      <Radio className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Active Listening Sockets / Network Ports</span>
                    </div>
                    <div className="rounded-lg border border-slate-800 bg-slate-950 overflow-hidden text-xs font-mono">
                      <div className="grid grid-cols-4 p-2 border-b border-slate-800 text-[11px] text-slate-400 uppercase">
                        <div>Protocol</div>
                        <div>Local Port</div>
                        <div>Remote Endpoint</div>
                        <div>State</div>
                      </div>
                      <div className="divide-y divide-slate-800/60 max-h-40 overflow-y-auto">
                        {selectedAgent.latest_telemetry.network_connections.map((conn, idx) => (
                          <div key={idx} className="grid grid-cols-4 p-2 text-slate-300">
                            <div className="uppercase text-cyan-400">{conn.protocol}</div>
                            <div>{conn.local_port}</div>
                            <div className="truncate text-slate-400">{(conn as any).remote || "-"}</div>
                            <div className="text-emerald-400 text-[11px]">{conn.state || "LISTEN"}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <div className="p-6 text-center text-slate-400 font-mono text-xs">
                  Awaiting first telemetry batch from agent...
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-800 bg-slate-950 flex items-center justify-between text-xs">
              <span className="text-slate-400 font-mono">
                Heartbeat Interval: {selectedAgent.heartbeat_interval_sec}s
              </span>
              <button
                onClick={() => setSelectedAgent(null)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-medium transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
