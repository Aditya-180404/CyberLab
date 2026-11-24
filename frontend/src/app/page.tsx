"use client";

import React, { useState, useEffect } from "react";
import { Sidebar } from "../components/layout/Sidebar";
import { Header } from "../components/layout/Header";
import { SystemHealthCard } from "../components/dashboard/SystemHealthCard";
import { QuickAuthCard } from "../components/dashboard/QuickAuthCard";
import { ModuleMatrixCard } from "../components/dashboard/ModuleMatrixCard";
import { RecentAuditCard } from "../components/dashboard/RecentAuditCard";
import { NetworkStudio } from "../components/network/NetworkStudio";
import { VMManagement } from "../components/vm/VMManagement";
import { EndpointFleet } from "../components/agent/EndpointFleet";
import { AssetInventory } from "../components/inventory/AssetInventory";
import { SIEMDashboard } from "../components/siem/SIEMDashboard";
import { IncidentResponseSOAR } from "../components/soar/IncidentResponseSOAR";
import { DigitalTwinView } from "../components/digital_twin/DigitalTwinView";
import { PurpleTeamStudio } from "../components/purple_team/PurpleTeamStudio";
import { VulnerabilityManagement } from "../components/vulnerability/VulnerabilityManagement";
import { fetchSystemHealth, fetchAuditLogs } from "../lib/api";
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
        ) : currentTab === "Virtual Machines" ? (
          <VMManagement authToken={authToken} />
        ) : currentTab === "Endpoint Fleet" ? (
          <EndpointFleet authToken={authToken} />
        ) : currentTab === "Asset Inventory" ? (
          <AssetInventory authToken={authToken} />
        ) : currentTab === "SIEM & Correlation" ? (
          <SIEMDashboard authToken={authToken} />
        ) : currentTab === "Incident Response" ? (
          <IncidentResponseSOAR authToken={authToken} />
        ) : currentTab === "Digital Twin" ? (
          <DigitalTwinView authToken={authToken} />
        ) : currentTab === "Purple-Team Studio" ? (
          <PurpleTeamStudio authToken={authToken} />
        ) : currentTab === "Vulnerabilities" ? (
          <VulnerabilityManagement authToken={authToken} />
        ) : (
          <main className="p-6 space-y-6 max-w-7xl mx-auto w-full">
            {/* Welcome Banner */}
            <div className="rounded-xl border border-slate-800 bg-gradient-to-r from-slate-950 via-slate-900 to-cyan-950/30 p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-lg">
              <div>
                <div className="flex items-center space-x-2">
                  <h1 className="text-xl font-bold tracking-tight text-white">
                    CyberLab Security Operations Center
                  </h1>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    PHASE 3 VM INTEGRATION ACTIVE
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
                  Central management control plane for isolated Linux network namespaces, VMware virtual machines, distributed EDR agents, SIEM telemetry, and purple-team attack simulations.
                </p>
              </div>
              <div className="flex items-center space-x-3 shrink-0">
                <button
                  onClick={() => setCurrentTab("Virtual Machines")}
                  className="px-3.5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold font-mono shadow-md shadow-cyan-950 transition"
                >
                  Manage Real VMs →
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
                <QuickAuthCard onLoginSuccess={handleLoginSuccess} />
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
