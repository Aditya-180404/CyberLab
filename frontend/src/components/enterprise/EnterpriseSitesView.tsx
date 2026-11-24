"use client";

import React, { useState, useEffect } from "react";
import {
  Globe,
  Building2,
  Server,
  Radio,
  ShieldAlert,
  FileText,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  RefreshCw,
  Plus,
  Trash2,
  Copy,
  Check,
  Download,
  Award,
  Layers,
  MapPin,
  Activity,
  ArrowUpRight,
  TrendingUp,
} from "lucide-react";
import {
  SiteItem,
  SiteStatsItem,
  ExecutiveReportItem,
  ComplianceReportItem,
} from "../../lib/types";
import {
  fetchSites,
  fetchSiteStats,
  createSite,
  deleteSite,
  fetchExecutiveReport,
  fetchComplianceReport,
} from "../../lib/api";

interface EnterpriseSitesViewProps {
  authToken: string | null;
}

export function EnterpriseSitesView({ authToken }: EnterpriseSitesViewProps) {
  const [activeTab, setActiveTab] = useState<"sites" | "executive" | "compliance">("sites");

  // Sites state
  const [siteStats, setSiteStats] = useState<SiteStatsItem[]>([]);
  const [sitesLoading, setSitesLoading] = useState(false);
  const [sitesError, setSitesError] = useState<string | null>(null);

  // New site form state
  const [showAddSiteModal, setShowAddSiteModal] = useState(false);
  const [newSiteName, setNewSiteName] = useState("");
  const [newSiteLocation, setNewSiteLocation] = useState("");
  const [newSiteIpRange, setNewSiteIpRange] = useState("");
  const [newSiteDescription, setNewSiteDescription] = useState("");
  const [siteSubmitting, setSiteSubmitting] = useState(false);
  const [siteActionMsg, setSiteActionMsg] = useState<string | null>(null);

  // Executive Report state
  const [execReport, setExecReport] = useState<ExecutiveReportItem | null>(null);
  const [execLoading, setExecLoading] = useState(false);
  const [execError, setExecError] = useState<string | null>(null);

  // Compliance Report state
  const [complianceReport, setComplianceReport] = useState<ComplianceReportItem | null>(null);
  const [selectedStandard, setSelectedStandard] = useState("NIST CSF 2.0");
  const [compLoading, setCompLoading] = useState(false);
  const [compError, setCompError] = useState<string | null>(null);

  // Copy feedback state
  const [copiedMd, setCopiedMd] = useState(false);

  // Load site stats
  const loadSiteStats = async () => {
    if (!authToken) return;
    setSitesLoading(true);
    setSitesError(null);
    try {
      const data = await fetchSiteStats(authToken);
      setSiteStats(data);
    } catch (err: any) {
      setSitesError(err.message || "Failed to load multi-site statistics");
    } finally {
      setSitesLoading(false);
    }
  };

  // Load executive report
  const loadExecutiveReport = async () => {
    if (!authToken) return;
    setExecLoading(true);
    setExecError(null);
    try {
      const data = await fetchExecutiveReport(authToken);
      setExecReport(data);
    } catch (err: any) {
      setExecError(err.message || "Failed to generate executive report");
    } finally {
      setExecLoading(false);
    }
  };

  // Load compliance report
  const loadComplianceReport = async (standard = selectedStandard) => {
    if (!authToken) return;
    setCompLoading(true);
    setCompError(null);
    try {
      const data = await fetchComplianceReport(authToken, standard);
      setComplianceReport(data);
    } catch (err: any) {
      setCompError(err.message || "Failed to generate compliance report");
    } finally {
      setCompLoading(false);
    }
  };

  useEffect(() => {
    if (authToken) {
      loadSiteStats();
    }
  }, [authToken]);

  useEffect(() => {
    if (authToken && activeTab === "executive" && !execReport) {
      loadExecutiveReport();
    } else if (authToken && activeTab === "compliance" && !complianceReport) {
      loadComplianceReport(selectedStandard);
    }
  }, [activeTab, authToken]);

  const handleCreateSite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!authToken || !newSiteName.trim()) return;
    setSiteSubmitting(true);
    setSiteActionMsg(null);
    try {
      await createSite(authToken, {
        name: newSiteName.trim(),
        location: newSiteLocation.trim() || undefined,
        ip_range: newSiteIpRange.trim() || undefined,
        description: newSiteDescription.trim() || undefined,
      });
      setSiteActionMsg(`Site "${newSiteName}" successfully registered.`);
      setNewSiteName("");
      setNewSiteLocation("");
      setNewSiteIpRange("");
      setNewSiteDescription("");
      setShowAddSiteModal(false);
      await loadSiteStats();
    } catch (err: any) {
      setSiteActionMsg(`Error creating site: ${err.message}`);
    } finally {
      setSiteSubmitting(false);
    }
  };

  const handleDeleteSite = async (siteId: string, siteName: string) => {
    if (!authToken) return;
    if (!confirm(`Are you sure you want to remove site "${siteName}"? Associated assets will be preserved.`)) return;
    try {
      await deleteSite(authToken, siteId);
      setSiteActionMsg(`Site "${siteName}" removed.`);
      await loadSiteStats();
    } catch (err: any) {
      setSiteActionMsg(`Error removing site: ${err.message}`);
    }
  };

  const handleCopyMarkdown = (markdown: string) => {
    navigator.clipboard.writeText(markdown);
    setCopiedMd(true);
    setTimeout(() => setCopiedMd(false), 2500);
  };

  const handleDownloadMarkdown = (filename: string, content: string) => {
    const element = document.createElement("a");
    const file = new Blob([content], { type: "text/markdown;charset=utf-8" });
    element.href = URL.createObjectURL(file);
    element.download = filename;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  // Fleet Totals Calculations
  const totalFleetAssets = siteStats.reduce((sum, s) => sum + s.total_assets, 0);
  const totalActiveAgents = siteStats.reduce((sum, s) => sum + s.active_agents, 0);
  const totalOpenIncidents = siteStats.reduce((sum, s) => sum + s.open_incidents, 0);
  const totalCriticalVulns = siteStats.reduce((sum, s) => sum + s.critical_vulnerabilities, 0);
  const avgFleetRisk = siteStats.length > 0
    ? Math.round(siteStats.reduce((sum, s) => sum + s.average_risk_score, 0) / siteStats.length)
    : 0;

  if (!authToken) {
    return (
      <div className="p-8 max-w-5xl mx-auto">
        <div className="rounded-xl border border-amber-500/30 bg-amber-950/20 p-6 text-center">
          <AlertTriangle className="w-10 h-10 text-amber-400 mx-auto mb-3" />
          <h2 className="text-lg font-semibold text-amber-200">Authentication Required</h2>
          <p className="text-xs text-amber-400/80 mt-1">
            Please log in from the SOC Dashboard to access Multi-Site Fleet Operations and Enterprise Compliance Reports.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto w-full">
      {/* Header Banner */}
      <div className="rounded-xl border border-slate-800 bg-gradient-to-r from-slate-950 via-slate-900 to-indigo-950/30 p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-lg">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center space-x-2">
              <Globe className="w-6 h-6 text-indigo-400" />
              <span>Multi-Site Enterprise Fleet & Governance</span>
            </h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              PHASE 12 v1.0 PRODUCTION
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
            Centralized multi-site telemetry aggregation, distributed agent fleet operations, executive board reporting, and NIST CSF 2.0 / CIS Controls compliance auditing.
          </p>
        </div>
        <div className="flex items-center space-x-3 shrink-0">
          <button
            onClick={() => {
              if (activeTab === "sites") loadSiteStats();
              else if (activeTab === "executive") loadExecutiveReport();
              else if (activeTab === "compliance") loadComplianceReport();
            }}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-900 hover:bg-slate-800 text-xs font-medium text-slate-300 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${(sitesLoading || execLoading || compLoading) ? "animate-spin text-cyan-400" : ""}`} />
            <span>Refresh</span>
          </button>
          {activeTab === "sites" && (
            <button
              onClick={() => setShowAddSiteModal(true)}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold font-mono shadow-md shadow-indigo-950 transition"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Register Site</span>
            </button>
          )}
        </div>
      </div>

      {/* Fleet KPI Banner */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3.5">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Sites</span>
            <Building2 className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-white">{siteStats.length}</div>
          <p className="text-[10px] text-slate-500 mt-0.5">Distributed zones</p>
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3.5">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Total Assets</span>
            <Server className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-cyan-400">{totalFleetAssets}</div>
          <p className="text-[10px] text-slate-500 mt-0.5">Physical, VM & Netns</p>
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3.5">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Active Agents</span>
            <Radio className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-emerald-400">{totalActiveAgents}</div>
          <p className="text-[10px] text-slate-500 mt-0.5">Live EDR Heartbeats</p>
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3.5">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Incidents</span>
            <ShieldAlert className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-amber-400">{totalOpenIncidents}</div>
          <p className="text-[10px] text-slate-500 mt-0.5">Open SOAR cases</p>
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3.5">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Critical CVEs</span>
            <AlertCircle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-rose-400">{totalCriticalVulns}</div>
          <p className="text-[10px] text-slate-500 mt-0.5">Unmitigated flaws</p>
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3.5">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Fleet Posture</span>
            <Activity className="w-4 h-4 text-purple-400" />
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-purple-400">{avgFleetRisk}/100</div>
          <p className="text-[10px] text-slate-500 mt-0.5">Avg Risk Exposure</p>
        </div>
      </div>

      {siteActionMsg && (
        <div className="p-3 rounded-lg border border-indigo-500/30 bg-indigo-950/20 text-indigo-300 text-xs flex items-center justify-between">
          <span>{siteActionMsg}</span>
          <button onClick={() => setSiteActionMsg(null)} className="text-indigo-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Sub-view Navigation Tabs */}
      <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
        <button
          onClick={() => setActiveTab("sites")}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-medium transition ${
            activeTab === "sites"
              ? "bg-indigo-600/10 text-indigo-300 border border-indigo-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent"
          }`}
        >
          <Building2 className="w-4 h-4" />
          <span>Multi-Site Fleet ({siteStats.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("executive")}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-medium transition ${
            activeTab === "executive"
              ? "bg-indigo-600/10 text-indigo-300 border border-indigo-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent"
          }`}
        >
          <TrendingUp className="w-4 h-4" />
          <span>Executive Posture Scorecard</span>
        </button>

        <button
          onClick={() => setActiveTab("compliance")}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-medium transition ${
            activeTab === "compliance"
              ? "bg-indigo-600/10 text-indigo-300 border border-indigo-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent"
          }`}
        >
          <Award className="w-4 h-4" />
          <span>Compliance & Audit Readiness</span>
        </button>
      </div>

      {/* TAB 1: SITES & FLEET MANAGEMENT */}
      {activeTab === "sites" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold tracking-wide text-slate-200 uppercase font-mono">
              Distributed Enterprise Sites
            </h2>
            <span className="text-xs text-slate-400">
              Each site isolates or aggregates telemetry, endpoints, and detection pipelines
            </span>
          </div>

          {sitesLoading && siteStats.length === 0 ? (
            <div className="p-12 text-center text-slate-500 text-xs">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-400" />
              Loading distributed sites...
            </div>
          ) : siteStats.length === 0 ? (
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-8 text-center text-slate-400 text-xs">
              No enterprise sites registered. Click "Register Site" above to establish your primary security operations center.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {siteStats.map((site) => (
                <div
                  key={site.site_id}
                  className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 hover:border-slate-700 transition space-y-4 shadow-sm"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <h3 className="font-semibold text-slate-100 text-sm">{site.name}</h3>
                        <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded border ${
                          site.status === "ACTIVE"
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                            : "bg-slate-800 text-slate-400 border-slate-700"
                        }`}>
                          {site.status}
                        </span>
                      </div>
                      <div className="flex items-center space-x-1.5 text-xs text-slate-400 mt-1">
                        <MapPin className="w-3.5 h-3.5 text-slate-500" />
                        <span>{site.location || "Global Data Center"}</span>
                      </div>
                    </div>
                    {site.name !== "Primary CyberLab HQ" && (
                      <button
                        onClick={() => handleDeleteSite(site.site_id, site.name)}
                        className="text-slate-500 hover:text-rose-400 transition p-1"
                        title="Remove site"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-slate-800/80">
                    <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
                      <div className="text-slate-400 text-[11px]">Assets Bound</div>
                      <div className="text-base font-bold font-mono text-cyan-400 mt-0.5">
                        {site.total_assets}
                      </div>
                    </div>
                    <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
                      <div className="text-slate-400 text-[11px]">Active Agents</div>
                      <div className="text-base font-bold font-mono text-emerald-400 mt-0.5">
                        {site.active_agents}
                      </div>
                    </div>
                    <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
                      <div className="text-slate-400 text-[11px]">Open Incidents</div>
                      <div className="text-base font-bold font-mono text-amber-400 mt-0.5">
                        {site.open_incidents}
                      </div>
                    </div>
                    <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
                      <div className="text-slate-400 text-[11px]">Critical CVEs</div>
                      <div className="text-base font-bold font-mono text-rose-400 mt-0.5">
                        {site.critical_vulnerabilities}
                      </div>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
                    <span className="text-slate-400">Risk Score:</span>
                    <span className={`font-mono font-semibold ${
                      site.average_risk_score >= 70
                        ? "text-rose-400"
                        : site.average_risk_score >= 40
                        ? "text-amber-400"
                        : "text-emerald-400"
                    }`}>
                      {site.average_risk_score} / 100
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: EXECUTIVE REPORT */}
      {activeTab === "executive" && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold tracking-wide text-slate-200 uppercase font-mono">
                Executive Security Posture Scorecard
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Board-grade summary synthesized from live telemetry, simulation efficacy, and vulnerability posture
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={loadExecutiveReport}
                disabled={execLoading}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${execLoading ? "animate-spin" : ""}`} />
                <span>Regenerate Scorecard</span>
              </button>
              {execReport && (
                <>
                  <button
                    onClick={() => handleCopyMarkdown(execReport.report_markdown)}
                    className="flex items-center space-x-1 px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs font-medium transition"
                    title="Copy Markdown Report"
                  >
                    {copiedMd ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedMd ? "Copied" : "Copy MD"}</span>
                  </button>
                  <button
                    onClick={() => handleDownloadMarkdown(`CyberLab_Executive_Report_${new Date().toISOString().slice(0, 10)}.md`, execReport.report_markdown)}
                    className="flex items-center space-x-1 px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs font-medium transition"
                    title="Download Markdown Report"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download</span>
                  </button>
                </>
              )}
            </div>
          </div>

          {execLoading ? (
            <div className="p-12 text-center text-slate-500 text-xs">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-400" />
              Generating executive posture report...
            </div>
          ) : execReport ? (
            <div className="space-y-6">
              {/* Scorecard Hero */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="md:col-span-1 rounded-xl border border-slate-800 bg-slate-900/60 p-6 flex flex-col justify-between">
                  <div>
                    <span className="text-xs uppercase font-mono text-slate-400 tracking-wider">
                      Overall Posture Score
                    </span>
                    <div className="mt-2 flex items-baseline space-x-2">
                      <span className="text-5xl font-black font-mono text-white">
                        {execReport.overall_posture_score}
                      </span>
                      <span className="text-slate-500 font-mono text-lg">/ 100</span>
                    </div>
                  </div>
                  <div className="mt-4 pt-4 border-t border-slate-800 flex items-center justify-between">
                    <span className="text-xs text-slate-400">Posture Tier:</span>
                    <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded border ${
                      execReport.posture_level === "EXCELLENT"
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                        : execReport.posture_level === "ACCEPTABLE"
                        ? "bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
                        : execReport.posture_level === "AT_RISK"
                        ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                        : "bg-rose-500/10 text-rose-400 border-rose-500/20"
                    }`}>
                      {execReport.posture_level}
                    </span>
                  </div>
                </div>

                <div className="md:col-span-2 rounded-xl border border-slate-800 bg-slate-900/60 p-6 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center space-x-2 text-indigo-400 text-xs font-mono mb-1.5">
                      <FileText className="w-4 h-4" />
                      <span>EXECUTIVE SUMMARY</span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {execReport.executive_summary}
                    </p>
                  </div>
                  <div className="mt-4 pt-4 border-t border-slate-800 text-[11px] text-slate-500 flex items-center justify-between font-mono">
                    <span>Target Org: {execReport.organization_name}</span>
                    <span>Generated: {new Date(execReport.generated_at).toLocaleString()}</span>
                  </div>
                </div>
              </div>

              {/* Top Strategic Risks */}
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-200 font-mono">
                    Top Strategic Risks ({execReport.top_risks.length})
                  </h3>
                </div>

                {execReport.top_risks.length === 0 ? (
                  <p className="text-xs text-emerald-400">No elevated security risks detected across monitored assets.</p>
                ) : (
                  <div className="space-y-3">
                    {execReport.top_risks.map((risk, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-lg border border-slate-800 bg-slate-950/60 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center space-x-2">
                            <span className="font-semibold text-slate-200">{risk.item_name}</span>
                            <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded border ${
                              risk.severity === "CRITICAL"
                                ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                                : risk.severity === "HIGH"
                                ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                                : "bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
                            }`}>
                              {risk.severity}
                            </span>
                            <span className="text-[10px] text-slate-500 font-mono">({risk.category})</span>
                          </div>
                          <p className="text-slate-400 text-[11px]">{risk.impact}</p>
                        </div>
                        <div className="shrink-0 text-right md:max-w-xs">
                          <div className="text-[10px] uppercase font-mono text-slate-500">Action</div>
                          <div className="text-cyan-400 text-[11px]">{risk.recommended_action}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Prioritized Recommendations */}
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-200 font-mono">
                    Prioritized Remediation Roadmap
                  </h3>
                </div>
                <ul className="space-y-2 text-xs text-slate-300">
                  {execReport.remediation_recommendations.map((rec, idx) => (
                    <li key={idx} className="flex items-start space-x-2">
                      <span className="text-cyan-400 font-mono font-bold">{idx + 1}.</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Raw Markdown Report Preview */}
              <div className="rounded-xl border border-slate-800 bg-slate-950 p-5 space-y-2">
                <div className="flex items-center justify-between text-xs font-mono text-slate-400 border-b border-slate-800 pb-2">
                  <span>MARKDOWN EXPORT PREVIEW</span>
                  <button
                    onClick={() => handleCopyMarkdown(execReport.report_markdown)}
                    className="text-cyan-400 hover:text-cyan-300 flex items-center space-x-1"
                  >
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copy Full Markdown</span>
                  </button>
                </div>
                <pre className="text-[11px] font-mono text-slate-300 overflow-x-auto whitespace-pre-wrap max-h-80 leading-relaxed bg-slate-900/50 p-3 rounded-lg border border-slate-800">
                  {execReport.report_markdown}
                </pre>
              </div>
            </div>
          ) : null}
        </div>
      )}

      {/* TAB 3: COMPLIANCE AUDIT */}
      {activeTab === "compliance" && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold tracking-wide text-slate-200 uppercase font-mono">
                Regulatory & Framework Compliance Audit
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Automated continuous evidence collection against NIST CSF 2.0 and CIS Controls benchmarks
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <select
                value={selectedStandard}
                onChange={(e) => {
                  setSelectedStandard(e.target.value);
                  loadComplianceReport(e.target.value);
                }}
                className="bg-slate-900 border border-slate-700 text-xs text-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-indigo-500"
              >
                <option value="NIST CSF 2.0">NIST CSF 2.0</option>
                <option value="CIS Controls v8">CIS Controls v8</option>
              </select>

              <button
                onClick={() => loadComplianceReport(selectedStandard)}
                disabled={compLoading}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${compLoading ? "animate-spin" : ""}`} />
                <span>Re-Audit</span>
              </button>

              {complianceReport && (
                <button
                  onClick={() => handleDownloadMarkdown(`CyberLab_${selectedStandard.replace(/\s+/g, "_")}_Audit_${new Date().toISOString().slice(0, 10)}.md`, complianceReport.report_markdown)}
                  className="flex items-center space-x-1 px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs font-medium transition"
                  title="Download Audit Report"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download MD</span>
                </button>
              )}
            </div>
          </div>

          {compLoading ? (
            <div className="p-12 text-center text-slate-500 text-xs">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-400" />
              Auditing telemetry against {selectedStandard}...
            </div>
          ) : complianceReport ? (
            <div className="space-y-6">
              {/* Compliance Header */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 flex flex-col justify-between">
                  <div>
                    <span className="text-xs uppercase font-mono text-slate-400 tracking-wider">
                      Compliance Readiness
                    </span>
                    <div className="mt-2 flex items-baseline space-x-2">
                      <span className="text-5xl font-black font-mono text-emerald-400">
                        {complianceReport.compliance_score_pct}%
                      </span>
                    </div>
                  </div>
                  <div className="mt-4 pt-4 border-t border-slate-800 flex items-center justify-between">
                    <span className="text-xs text-slate-400">Audit Status:</span>
                    <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded border ${
                      complianceReport.certification_status === "AUDIT_READY"
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                        : complianceReport.certification_status === "CONDITIONALLY_COMPLIANT"
                        ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                        : "bg-rose-500/10 text-rose-400 border-rose-500/20"
                    }`}>
                      {complianceReport.certification_status}
                    </span>
                  </div>
                </div>

                <div className="md:col-span-2 rounded-xl border border-slate-800 bg-slate-900/60 p-6 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center space-x-2 text-indigo-400 text-xs font-mono mb-1.5">
                      <Award className="w-4 h-4" />
                      <span>AUDIT READINESS SUMMARY</span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {complianceReport.summary}
                    </p>
                  </div>
                  <div className="mt-4 pt-4 border-t border-slate-800 text-[11px] text-slate-500 flex items-center justify-between font-mono">
                    <span>Framework: {complianceReport.standard}</span>
                    <span>Evidence Controls Evaluated: {complianceReport.evidence_count}</span>
                  </div>
                </div>
              </div>

              {/* Evaluated Controls List */}
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-200 font-mono">
                    Control Families & Telemetry Verification ({complianceReport.controls.length})
                  </h3>
                </div>

                <div className="space-y-3">
                  {complianceReport.controls.map((control) => (
                    <div
                      key={control.control_id}
                      className="p-4 rounded-lg border border-slate-800 bg-slate-950/60 space-y-2 text-xs"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div className="flex items-center space-x-2">
                          <span className="font-mono text-cyan-400 font-semibold">{control.control_id}</span>
                          <span className="text-slate-400">|</span>
                          <span className="text-slate-200 font-medium">{control.title}</span>
                          <span className="text-[10px] text-slate-500 font-mono">({control.family})</span>
                        </div>
                        <div className="flex items-center space-x-3">
                          <span className="font-mono text-slate-400 text-[11px]">
                            {control.coverage_score_pct}% Score
                          </span>
                          <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                            control.status === "COMPLIANT"
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                              : control.status === "PARTIAL"
                              ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                              : "bg-rose-500/10 text-rose-400 border-rose-500/20"
                          }`}>
                            {control.status}
                          </span>
                        </div>
                      </div>

                      {/* Control progress bar */}
                      <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-300 ${
                            control.coverage_score_pct >= 80
                              ? "bg-emerald-500"
                              : control.coverage_score_pct >= 50
                              ? "bg-amber-500"
                              : "bg-rose-500"
                          }`}
                          style={{ width: `${control.coverage_score_pct}%` }}
                        />
                      </div>

                      <div className="text-[11px] text-slate-400 pt-1">
                        <span className="text-slate-500 font-mono">Evidence: </span>
                        {control.evidence}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : null}
        </div>
      )}

      {/* Modal: Register Enterprise Site */}
      {showAddSiteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-semibold text-slate-100 flex items-center space-x-2">
                <Building2 className="w-4 h-4 text-indigo-400" />
                <span>Register Distributed Enterprise Site</span>
              </h3>
              <button
                onClick={() => setShowAddSiteModal(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateSite} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-300 mb-1">Site / Branch Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Regional Branch A, AWS us-east-1"
                  value={newSiteName}
                  onChange={(e) => setNewSiteName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1">Physical / Cloud Location</label>
                <input
                  type="text"
                  placeholder="e.g., Frankfurt DC, Azure West US, On-Premises"
                  value={newSiteLocation}
                  onChange={(e) => setNewSiteLocation(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1">Assigned CIDR / IP Range</label>
                <input
                  type="text"
                  placeholder="e.g., 10.100.0.0/16 or 192.168.10.0/24"
                  value={newSiteIpRange}
                  onChange={(e) => setNewSiteIpRange(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1">Description / Purpose</label>
                <textarea
                  rows={2}
                  placeholder="Optional site notes or operational scope..."
                  value={newSiteDescription}
                  onChange={(e) => setNewSiteDescription(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="pt-3 border-t border-slate-800 flex items-center justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowAddSiteModal(false)}
                  className="px-3 py-1.5 rounded-lg border border-slate-700 hover:bg-slate-800 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={siteSubmitting || !newSiteName.trim()}
                  className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold shadow-md shadow-indigo-950 disabled:opacity-50"
                >
                  {siteSubmitting ? "Registering..." : "Register Site"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
