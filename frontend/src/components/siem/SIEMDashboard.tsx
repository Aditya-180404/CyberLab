"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  FileSearch,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Flame,
  Radio,
  RefreshCw,
  Search,
  Crosshair,
  Terminal,
  Activity,
  Layers,
  Clock,
  Eye,
  Play,
  X,
  CheckCircle2,
} from "lucide-react";
import {
  SecurityEventItem,
  SecurityAlertItem,
  SecurityIncidentItem,
  MitreMatrixSummaryItem,
  SIEMKPIsItem,
} from "../../lib/types";
import {
  fetchSecurityEvents,
  fetchSecurityAlerts,
  fetchSecurityIncidents,
  fetchMitreMatrix,
  fetchSIEMKPIs,
  simulateAttackScenario,
} from "../../lib/api";

interface SIEMDashboardProps {
  authToken: string | null;
}

export function SIEMDashboard({ authToken }: SIEMDashboardProps) {
  const [activeTab, setActiveTab] = useState<"MITRE" | "ALERTS" | "EVENTS">("MITRE");
  const [kpis, setKpis] = useState<SIEMKPIsItem | null>(null);
  const [mitreMatrix, setMitreMatrix] = useState<MitreMatrixSummaryItem | null>(null);
  const [alerts, setAlerts] = useState<SecurityAlertItem[]>([]);
  const [incidents, setIncidents] = useState<SecurityIncidentItem[]>([]);
  const [events, setEvents] = useState<SecurityEventItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [selectedScenario, setSelectedScenario] = useState("brute_force");
  const [showSimModal, setShowSimModal] = useState(false);

  // Event stream filters
  const [eventCategory, setEventCategory] = useState("ALL");
  const [eventSearch, setEventSearch] = useState("");

  const loadAll = useCallback(async () => {
    if (!authToken) return;
    setLoading(true);
    try {
      const [kpiRes, mitreRes, alertRes, incRes, evtRes] = await Promise.all([
        fetchSIEMKPIs(authToken),
        fetchMitreMatrix(authToken),
        fetchSecurityAlerts(authToken),
        fetchSecurityIncidents(authToken),
        fetchSecurityEvents(authToken, {
          category: eventCategory !== "ALL" ? eventCategory : undefined,
          search: eventSearch || undefined,
          limit: 100,
        }),
      ]);
      setKpis(kpiRes);
      setMitreMatrix(mitreRes);
      setAlerts(alertRes);
      setIncidents(incRes);
      setEvents(evtRes);
    } catch (err: any) {
      console.error("SIEM data load error:", err);
    } finally {
      setLoading(false);
    }
  }, [authToken, eventCategory, eventSearch]);

  useEffect(() => {
    loadAll();
    const interval = setInterval(loadAll, 10000);
    return () => clearInterval(interval);
  }, [loadAll]);

  const handleSimulate = async () => {
    if (!authToken) return;
    setSimulating(true);
    try {
      await simulateAttackScenario(authToken, selectedScenario, "metasploitable2", "192.168.1.120");
      setShowSimModal(false);
      await loadAll();
      alert(`Simulation '${selectedScenario}' executed successfully! Check the MITRE Matrix and Alerts tabs.`);
    } catch (err: any) {
      alert("Attack simulation failed: " + err.message);
    } finally {
      setSimulating(false);
    }
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case "CRITICAL":
        return "bg-rose-500/20 text-rose-300 border-rose-500/40 font-bold";
      case "HIGH":
        return "bg-orange-500/20 text-orange-300 border-orange-500/40";
      case "MEDIUM":
        return "bg-amber-500/20 text-amber-300 border-amber-500/40";
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
              <FileSearch className="w-5 h-5 text-cyan-400" />
              <span>SIEM, Alert Correlation & MITRE ATT&CK</span>
            </h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              PHASE 6 ACTIVE
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
            Real-time security log normalization, stateful rule engine, threat correlation, and interactive ATT&CK framework telemetry mapping.
          </p>
        </div>

        <div className="flex items-center space-x-3 shrink-0">
          <button
            onClick={() => setShowSimModal(true)}
            className="px-3.5 py-2 rounded-lg bg-rose-950/80 hover:bg-rose-900 text-rose-300 border border-rose-500/40 text-xs font-semibold font-mono flex items-center space-x-2 shadow-md transition"
          >
            <Flame className="w-4 h-4 text-rose-400 animate-pulse" />
            <span>Simulate Attack Scenario</span>
          </button>
          <button
            onClick={loadAll}
            disabled={loading}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 transition"
            title="Refresh SIEM"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-cyan-400" : ""}`} />
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <div className="text-[11px] uppercase tracking-wider text-slate-400 font-mono">Ingested Events</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">{kpis?.total_events ?? 0}</div>
          <div className="text-[11px] text-slate-400 mt-1">Normalized stream volume</div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <div className="text-[11px] uppercase tracking-wider text-slate-400 font-mono">Open Security Alerts</div>
          <div className="text-2xl font-bold font-mono text-amber-400 mt-1">{kpis?.open_alerts ?? 0}</div>
          <div className="text-[11px] text-amber-400/80 mt-1">Rule engine detections</div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <div className="text-[11px] uppercase tracking-wider text-slate-400 font-mono">Correlated Incidents</div>
          <div className="text-2xl font-bold font-mono text-rose-400 mt-1 flex items-center space-x-2">
            <span>{kpis?.active_incidents ?? 0}</span>
            {kpis && kpis.active_incidents > 0 && (
              <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping"></span>
            )}
          </div>
          <div className="text-[11px] text-rose-400/80 mt-1">Multi-vector threats</div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <div className="text-[11px] uppercase tracking-wider text-slate-400 font-mono">MITRE ATT&CK Triggers</div>
          <div className="text-2xl font-bold font-mono text-cyan-300 mt-1">
            {mitreMatrix?.active_techniques_triggered ?? 0}{" "}
            <span className="text-xs font-normal text-slate-500">
              / {mitreMatrix?.total_techniques_mapped ?? 0}
            </span>
          </div>
          <div className="text-[11px] text-cyan-400/80 mt-1">Active mapped techniques</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
        <button
          onClick={() => setActiveTab("MITRE")}
          className={`px-4 py-2 rounded-lg text-xs font-medium font-mono transition flex items-center space-x-2 ${
            activeTab === "MITRE"
              ? "bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 shadow-sm"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <Crosshair className="w-4 h-4" />
          <span>MITRE ATT&CK Matrix Heatmap</span>
        </button>
        <button
          onClick={() => setActiveTab("ALERTS")}
          className={`px-4 py-2 rounded-lg text-xs font-medium font-mono transition flex items-center space-x-2 ${
            activeTab === "ALERTS"
              ? "bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 shadow-sm"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <ShieldAlert className="w-4 h-4" />
          <span>Alerts & Correlated Incidents ({alerts.length})</span>
        </button>
        <button
          onClick={() => setActiveTab("EVENTS")}
          className={`px-4 py-2 rounded-lg text-xs font-medium font-mono transition flex items-center space-x-2 ${
            activeTab === "EVENTS"
              ? "bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 shadow-sm"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <Activity className="w-4 h-4" />
          <span>Live Normalized Events ({events.length})</span>
        </button>
      </div>

      {/* Tab 1: MITRE ATT&CK Matrix */}
      {activeTab === "MITRE" && mitreMatrix && (
        <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="text-xs font-mono text-slate-300">
              Interactive MITRE Enterprise Tactics &amp; Automated Detection Coverage
            </div>
            <div className="flex items-center space-x-4 text-[11px] font-mono">
              <span className="flex items-center space-x-1.5 text-rose-400">
                <span className="w-2.5 h-2.5 rounded bg-rose-500 shadow-sm shadow-rose-500"></span>
                <span>Active Threat Detected</span>
              </span>
              <span className="flex items-center space-x-1.5 text-slate-500">
                <span className="w-2.5 h-2.5 rounded bg-slate-800 border border-slate-700"></span>
                <span>Monitored Baseline</span>
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3 overflow-x-auto">
            {Object.entries(mitreMatrix.tactics).map(([tacticName, techniques]) => (
              <div key={tacticName} className="rounded-lg border border-slate-800 bg-slate-900/60 p-3 space-y-2">
                <div className="text-[11px] font-bold font-mono text-cyan-400 uppercase tracking-wider pb-1.5 border-b border-slate-800">
                  {tacticName}
                </div>
                <div className="space-y-1.5">
                  {techniques.map((tech) => {
                    const isTriggered = tech.alert_count > 0 || tech.event_count > 0;
                    return (
                      <div
                        key={tech.technique_id}
                        className={`p-2 rounded border text-xs transition ${
                          isTriggered
                            ? "bg-rose-950/40 border-rose-500/50 text-rose-200 shadow-sm shadow-rose-950"
                            : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                        }`}
                      >
                        <div className="flex items-center justify-between font-mono text-[10px]">
                          <span className={isTriggered ? "text-rose-400 font-bold" : "text-cyan-400/80"}>
                            {tech.technique_id}
                          </span>
                          {isTriggered && (
                            <span className="px-1 py-0.2 rounded bg-rose-500/30 text-rose-300 font-bold">
                              {tech.alert_count > 0 ? `${tech.alert_count} Alerts` : `${tech.event_count} Evt`}
                            </span>
                          )}
                        </div>
                        <div className="font-medium text-[11px] mt-0.5 leading-tight text-slate-200">
                          {tech.technique_name}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 2: Alerts & Incidents */}
      {activeTab === "ALERTS" && (
        <div className="space-y-6">
          {/* Correlated Incidents Section */}
          {incidents.length > 0 && (
            <div className="rounded-xl border border-rose-500/30 bg-rose-950/20 p-5 space-y-3">
              <div className="flex items-center space-x-2 text-rose-400 font-bold text-sm font-mono">
                <AlertTriangle className="w-4 h-4 text-rose-400" />
                <span>Correlated Security Incidents (Root Cause Analysis)</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {incidents.map((inc) => (
                  <div key={inc.id} className="rounded-lg border border-rose-500/40 bg-slate-950 p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-sm text-white">{inc.title}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-bold border border-rose-500/30">
                        {inc.severity}
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed">{inc.summary}</p>
                    <div className="flex flex-wrap gap-1.5 pt-2 border-t border-slate-800 text-[10px] font-mono">
                      {inc.mitre_tactics.map((t) => (
                        <span key={t} className="px-1.5 py-0.5 rounded bg-slate-800 text-cyan-300 border border-slate-700">
                          {t}
                        </span>
                      ))}
                      {inc.mitre_techniques.map((tid) => (
                        <span key={tid} className="px-1.5 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-500/40">
                          {tid}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Alerts Table */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/80 overflow-hidden shadow-lg">
            <div className="p-4 border-b border-slate-800 font-semibold text-sm text-slate-200 flex items-center justify-between bg-slate-950">
              <div className="flex items-center space-x-2">
                <ShieldAlert className="w-4 h-4 text-cyan-400" />
                <span>Security Alerts Stream</span>
              </div>
            </div>

            {alerts.length === 0 ? (
              <div className="p-12 text-center text-slate-400 text-xs font-mono">
                No active security alerts. The environment is currently quiet.
              </div>
            ) : (
              <div className="divide-y divide-slate-800/60">
                {alerts.map((alert) => (
                  <div key={alert.id} className="p-4 hover:bg-slate-900/40 transition flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${getSeverityBadge(alert.severity)}`}>
                          {alert.severity}
                        </span>
                        <span className="font-bold text-sm text-white">{alert.title}</span>
                        {alert.evidence_count > 1 && (
                          <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-300">
                            x{alert.evidence_count} events
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-400">{alert.description}</p>
                      <div className="text-[11px] font-mono text-slate-500 flex items-center space-x-3 pt-1">
                        <span>Target: <strong className="text-slate-300">{alert.hostname || "unknown"}</strong></span>
                        {alert.mitre_technique_id && (
                          <span>ATT&amp;CK: <strong className="text-cyan-400">{alert.mitre_technique_id} ({alert.mitre_technique_name})</strong></span>
                        )}
                        <span>First seen: {new Date(alert.first_seen).toLocaleTimeString()}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 3: Normalized Event Stream */}
      {activeTab === "EVENTS" && (
        <div className="rounded-xl border border-slate-800 bg-slate-950/80 overflow-hidden shadow-lg space-y-4 p-4">
          {/* Filter Bar */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3 border-b border-slate-800">
            <div className="flex items-center space-x-1 bg-slate-900 p-1 rounded-lg border border-slate-800 text-[11px] font-mono">
              {["ALL", "AUTHENTICATION", "PROCESS_EXECUTION", "FILE_INTEGRITY", "NETWORK_CONNECTION", "SYSTEM_LOG"].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setEventCategory(cat)}
                  className={`px-2.5 py-1 rounded transition ${
                    eventCategory === cat
                      ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  {cat.replace("_", " ")}
                </button>
              ))}
            </div>

            <div className="relative w-72">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search event message or IP..."
                value={eventSearch}
                onChange={(e) => setEventSearch(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>
          </div>

          {/* Event Stream Console */}
          <div className="divide-y divide-slate-800/40 font-mono text-xs max-h-[600px] overflow-y-auto">
            {events.map((evt) => (
              <div key={evt.id} className="p-2.5 hover:bg-slate-900/60 transition flex items-start space-x-3">
                <span className="text-slate-500 text-[11px] shrink-0">
                  {new Date(evt.timestamp).toLocaleTimeString()}
                </span>
                <span className={`text-[9px] px-1.5 py-0.2 rounded border uppercase shrink-0 ${getSeverityBadge(evt.severity)}`}>
                  {evt.severity}
                </span>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-900 text-cyan-400 border border-slate-800 shrink-0">
                  {evt.category}
                </span>
                <div className="flex-1 min-w-0">
                  <span className="text-slate-200">{evt.message}</span>
                  <div className="text-[10px] text-slate-500 flex items-center space-x-2 mt-0.5">
                    {evt.hostname && <span>Host: {evt.hostname}</span>}
                    {evt.source_ip && <span>Src: {evt.source_ip}</span>}
                    {evt.mitre_technique_id && (
                      <span className="text-rose-400">[{evt.mitre_technique_id} {evt.mitre_technique_name}]</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Simulation Modal */}
      {showSimModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2 text-rose-400 font-bold text-sm font-mono">
                <Flame className="w-4 h-4" />
                <span>Simulate Offensive Threat Vector</span>
              </div>
              <button onClick={() => setShowSimModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              Inject synthetic multi-stage attack events against your registered target VM (<span className="text-cyan-300 font-mono">Metasploitable2</span>) to validate detection rules and correlate incident alarms.
            </p>

            <div className="space-y-2">
              <label className="text-xs font-mono text-slate-400">Attack Scenario:</label>
              <select
                value={selectedScenario}
                onChange={(e) => setSelectedScenario(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white font-mono focus:outline-none focus:border-cyan-500"
              >
                <option value="brute_force">1. SSH Credential Brute Force (T1110)</option>
                <option value="privilege_escalation">2. Unauthorized Sudo Privilege Escalation (T1548.003)</option>
                <option value="credential_dumping">3. FIM Integrity Tampering on /etc/shadow (T1003.008)</option>
                <option value="reverse_shell">4. Interactive Reverse Shell Execution (T1059.004)</option>
              </select>
            </div>

            <div className="pt-2 flex items-center justify-end space-x-3">
              <button
                onClick={() => setShowSimModal(false)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-medium transition"
              >
                Cancel
              </button>
              <button
                onClick={handleSimulate}
                disabled={simulating}
                className="px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold font-mono flex items-center space-x-2 transition shadow-md shadow-rose-950"
              >
                <Play className={`w-3.5 h-3.5 ${simulating ? "animate-spin" : ""}`} />
                <span>{simulating ? "Injecting Attack..." : "Execute Simulation"}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
