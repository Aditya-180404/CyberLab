"use client";

import React, { useState, useEffect } from "react";
import { Sidebar } from "../components/layout/Sidebar";
import { Header } from "../components/layout/Header";
import { SystemHealthCard } from "../components/dashboard/SystemHealthCard";
import { QuickAuthCard } from "../components/dashboard/QuickAuthCard";
import { ModuleMatrixCard } from "../components/dashboard/ModuleMatrixCard";
import { RecentAuditCard } from "../components/dashboard/RecentAuditCard";
import { NetworkStudio } from "../components/network/NetworkStudio";
import { EndpointFleet } from "../components/agent/EndpointFleet";
import { AssetInventory } from "../components/inventory/AssetInventory";
import { SIEMDashboard } from "../components/siem/SIEMDashboard";
import { IncidentResponseSOAR } from "../components/soar/IncidentResponseSOAR";
import { DigitalTwinView } from "../components/digital_twin/DigitalTwinView";
import { PurpleTeamStudio } from "../components/purple_team/PurpleTeamStudio";
import { VulnerabilityManagement } from "../components/vulnerability/VulnerabilityManagement";
import { EnterpriseSitesView } from "../components/enterprise/EnterpriseSitesView";
import { ThreatIntelDeceptionView } from "../components/threat_intel/ThreatIntelDeceptionView";
import { fetchSystemHealth, fetchAuditLogs, fetchCurrentUser } from "../lib/api";
import { HealthResponse, UserProfile, AuditLogItem } from "../lib/types";

export default function SOCDashboard() {
  const [currentTab, setCurrentTab] = useState("SOC Dashboard");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState(false);
  const [healthError, setHealthError] = useState<string | null>(null);

  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [auditLoading, setAuditLoading] = useState(false);

  const loadHealth = async () => {
    setHealthLoading(true);
    setHealthError(null);
    try {
      const data = await fetchSystemHealth();
      setHealth(data);
    } catch (err: any) {
      setHealthError(err.message || "Could not connect to backend");
    } finally {
      setHealthLoading(false);
    }
  };

  const loadAudit = async (token: string) => {
    setAuditLoading(true);
    try {
      const logs = await fetchAuditLogs(token, 10);
      setAuditLogs(logs);
    } catch (err) {
      // Non-fatal if unauthenticated
    } finally {
      setAuditLoading(false);
    }
  };

  useEffect(() => {
    loadHealth();
    const savedToken = localStorage.getItem("cyberlab_token");
    if (savedToken) {
      fetchCurrentUser(savedToken)
        .then((user) => {
          setCurrentUser(user);
          setAuthToken(savedToken);
          loadAudit(savedToken);
        })
        .catch(() => {
          localStorage.removeItem("cyberlab_token");
        });
    }
    const interval = setInterval(loadHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleLoginSuccess = (user: UserProfile, token: string) => {
    setCurrentUser(user);
    setAuthToken(token);
    loadAudit(token);
  };

  const handleLogout = () => {
    setCurrentUser(null);
    setAuthToken(null);
    localStorage.removeItem("cyberlab_token");
    setAuditLogs([]);
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 bg-grid-cyber">
      {/* Sidebar Navigation */}
      <Sidebar currentTab={currentTab} onSelectTab={setCurrentTab} />

      {/* Main Content Area */}
      <div className="flex flex-col flex-1 min-w-0 overflow-y-auto">
        <Header currentUser={currentUser} onLogout={handleLogout} />

        {currentTab === "Network Studio" ? (
          <NetworkStudio authToken={authToken} />
        ) : currentTab === "Endpoint Fleet" ? (
          <EndpointFleet authToken={authToken} />
        ) : currentTab === "Asset Inventory" ? (
          <AssetInventory authToken={authToken} />
        ) : currentTab === "SIEM & Correlation" ? (
          <SIEMDashboard authToken={authToken} />
        ) : currentTab === "Threat Intel & NDR" ? (
          <ThreatIntelDeceptionView authToken={authToken} />
        ) : currentTab === "Incident Response" ? (
          <IncidentResponseSOAR authToken={authToken} />
        ) : currentTab === "Digital Twin" ? (
          <DigitalTwinView authToken={authToken} />
        ) : currentTab === "Purple-Team Studio" ? (
          <PurpleTeamStudio authToken={authToken} />
        ) : currentTab === "Vulnerabilities" ? (
          <VulnerabilityManagement authToken={authToken} />
        ) : currentTab === "Multi-Site Fleet" ? (
          <EnterpriseSitesView authToken={authToken} />
        ) : currentTab === "Audit Trail" ? (
          <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
            <div className="cyber-card rounded-xl p-5">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-lg font-bold text-white">Security Audit Trail</h1>
                  <p className="text-xs text-slate-400 mt-1">
                    Immutable record of logins, agent enrollments, topology changes, and SOAR containment actions.
                  </p>
                </div>
                {authToken && (
                  <button
                    onClick={() => loadAudit(authToken)}
                    className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-mono text-cyan-300 transition"
                  >
                    Refresh Logs
                  </button>
                )}
              </div>
            </div>
            <RecentAuditCard logs={auditLogs} loading={auditLoading} />
          </main>
        ) : currentTab === "Settings & RBAC" ? (
          <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <QuickAuthCard onLoginSuccess={handleLoginSuccess} currentUsername={currentUser?.username} />
              <SystemHealthCard
                health={health}
                loading={healthLoading}
                error={healthError}
                onRefresh={loadHealth}
              />
            </div>
          </main>
        ) : (
          <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
            {/* Welcome Banner */}
            <div className="rounded-2xl border border-cyan-500/20 bg-gradient-to-br from-slate-950 via-slate-900/95 to-cyan-950/35 p-6 flex flex-col lg:flex-row lg:items-center justify-between gap-5 shadow-xl shadow-black/50">
              <div>
                <div className="flex flex-wrap items-center gap-2.5">
                  <h1 className="text-xl font-bold tracking-tight text-white">
                    CyberLab Security Operations Center
                  </h1>
                  <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                    UNIFIED CONTROL PLANE • v1.0
                  </span>
                </div>
                <p className="text-xs text-slate-300/80 mt-2 max-w-2xl leading-relaxed">
                  Centralized enterprise SOC for multi-OS EDR telemetry, firewall/NDR syslog ingestion, threat intelligence IOC matching, deception traps, SOAR containment, topological attack-path modeling, and purple-team validation.
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2.5 shrink-0">
                <button
                  onClick={() => setCurrentTab("Endpoint Fleet")}
                  className="px-3.5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold font-mono shadow-lg shadow-cyan-950/60 transition"
                >
                  Endpoint Fleet →
                </button>
                <button
                  onClick={() => setCurrentTab("SIEM & Correlation")}
                  className="px-3 py-2 rounded-lg bg-slate-900/90 hover:bg-slate-800 text-slate-200 border border-slate-700/80 hover:border-cyan-500/40 text-xs font-mono transition"
                >
                  SIEM Alerts
                </button>
                <button
                  onClick={() => setCurrentTab("Threat Intel & NDR")}
                  className="px-3 py-2 rounded-lg bg-slate-900/90 hover:bg-slate-800 text-slate-200 border border-slate-700/80 hover:border-cyan-500/40 text-xs font-mono transition"
                >
                  Threat Intel & NDR
                </button>
                <button
                  onClick={() => setCurrentTab("Network Studio")}
                  className="px-3 py-2 rounded-lg bg-slate-900/90 hover:bg-slate-800 text-slate-200 border border-slate-700/80 hover:border-cyan-500/40 text-xs font-mono transition"
                >
                  Network Graph
                </button>
              </div>
            </div>

            {/* Core Row 1: System Health & RBAC Tester */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <SystemHealthCard
                  health={health}
                  loading={healthLoading}
                  error={healthError}
                  onRefresh={loadHealth}
                />
              </div>
              <div>
                <QuickAuthCard onLoginSuccess={handleLoginSuccess} currentUsername={currentUser?.username} />
              </div>
            </div>

            {/* Core Row 2: Architecture Roadmap Matrix */}
            <ModuleMatrixCard />

            {/* Core Row 3: Audit Trail Log Stream */}
            <RecentAuditCard logs={auditLogs} loading={auditLoading} />
          </main>
        )}
      </div>
    </div>
  );
}
