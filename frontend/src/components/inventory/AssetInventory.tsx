"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Layers,
  Server,
  Radio,
  Network,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  RefreshCw,
  Search,
  Filter,
  Activity,
  HardDrive,
  Cpu,
  Lock,
  Tag,
  CheckCircle2,
  X,
  ChevronDown,
  Info,
  ExternalLink,
} from "lucide-react";
import { AssetItem, AssetDetailItem, AssetKPIs } from "../../lib/types";
import { fetchAssets, fetchAssetKPIs, syncAssets, fetchAssetDetail, updateAssetCriticality } from "../../lib/api";

interface AssetInventoryProps {
  authToken: string | null;
}

export function AssetInventory({ authToken }: AssetInventoryProps) {
  const [assets, setAssets] = useState<AssetItem[]>([]);
  const [kpis, setKpis] = useState<AssetKPIs | null>(null);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedType, setSelectedType] = useState<string>("ALL");
  const [selectedCrit, setSelectedCrit] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Inspection modal
  const [selectedAsset, setSelectedAsset] = useState<AssetDetailItem | null>(null);
  const [inspectLoading, setInspectLoading] = useState(false);

  const loadData = useCallback(async () => {
    if (!authToken) return;
    setLoading(true);
    setError(null);
    try {
      const [assetList, kpiData] = await Promise.all([
        fetchAssets(authToken, {
          asset_type: selectedType,
          criticality: selectedCrit,
          search: searchQuery || undefined,
        }),
        fetchAssetKPIs(authToken),
      ]);
      setAssets(assetList);
      setKpis(kpiData);
    } catch (err: any) {
      setError(err.message || "Failed to load asset inventory");
    } finally {
      setLoading(false);
    }
  }, [authToken, selectedType, selectedCrit, searchQuery]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSync = async () => {
    if (!authToken) return;
    setSyncing(true);
    try {
      const res = await syncAssets(authToken);
      await loadData();
      alert(`Asset sync complete: ${res.total_synced} entities cataloged.`);
    } catch (err: any) {
      alert("Asset sync failed: " + err.message);
    } finally {
      setSyncing(false);
    }
  };

  const handleInspect = async (assetId: string) => {
    if (!authToken) return;
    setInspectLoading(true);
    try {
      const detail = await fetchAssetDetail(authToken, assetId);
      setSelectedAsset(detail);
    } catch (err: any) {
      alert("Could not load asset details: " + err.message);
    } finally {
      setInspectLoading(false);
    }
  };

  const handleCriticalityChange = async (assetId: string, newCrit: string) => {
    if (!authToken) return;
    try {
      await updateAssetCriticality(authToken, assetId, newCrit);
      await loadData();
      if (selectedAsset && selectedAsset.id === assetId) {
        setSelectedAsset({ ...selectedAsset, criticality: newCrit as any });
      }
    } catch (err: any) {
      alert("Failed to update criticality: " + err.message);
    }
  };

  const getRiskColor = (score: number) => {
    if (score >= 70) return "text-rose-400 bg-rose-500/10 border-rose-500/30";
    if (score >= 40) return "text-amber-400 bg-amber-500/10 border-amber-500/30";
    return "text-emerald-400 bg-emerald-500/10 border-emerald-500/30";
  };

  const getRiskBarColor = (score: number) => {
    if (score >= 70) return "bg-rose-500";
    if (score >= 40) return "bg-amber-500";
    return "bg-emerald-500";
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "VIRTUAL_MACHINE":
        return <Server className="w-4 h-4 text-cyan-400" />;
      case "AGENT_HOST":
        return <Radio className="w-4 h-4 text-purple-400" />;
      case "SIMULATED_DEVICE":
        return <Network className="w-4 h-4 text-emerald-400" />;
      default:
        return <Layers className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <div className="flex-1 flex flex-col p-6 space-y-6 max-w-7xl mx-auto w-full">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center space-x-2">
              <Layers className="w-5 h-5 text-cyan-400" />
              <span>Unified Asset Inventory & Posture</span>
            </h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              INVENTORY SYNC ACTIVE
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
            Multi-source asset catalog harmonizing VMware virtual machines, distributed Linux agents, and simulated network nodes with continuous risk scoring.
          </p>
        </div>

        <div className="flex items-center space-x-3 shrink-0">
          <button
            onClick={handleSync}
            disabled={syncing}
            className="px-3.5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold font-mono flex items-center space-x-2 shadow-md shadow-cyan-950 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${syncing ? "animate-spin" : ""}`} />
            <span>{syncing ? "Syncing..." : "Sync Multi-Source Assets"}</span>
          </button>
          <button
            onClick={loadData}
            disabled={loading}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 transition"
            title="Refresh View"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-cyan-400" : ""}`} />
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <div className="text-[11px] uppercase tracking-wider text-slate-400 font-mono">Cataloged Assets</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">{kpis?.total_assets ?? 0}</div>
          <div className="text-[11px] text-slate-400 mt-1">Cross-platform entities</div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <div className="text-[11px] uppercase tracking-wider text-slate-400 font-mono">Average Fleet Risk</div>
          <div className="text-2xl font-bold font-mono mt-1 flex items-center space-x-2">
            <span className={kpis ? (kpis.average_risk_score >= 50 ? "text-amber-400" : "text-emerald-400") : "text-white"}>
              {kpis?.average_risk_score ?? 0}
            </span>
            <span className="text-xs font-normal text-slate-400">/ 100</span>
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Normalized posture score</div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <div className="text-[11px] uppercase tracking-wider text-slate-400 font-mono">High Risk Assets</div>
          <div className="text-2xl font-bold font-mono text-rose-400 mt-1">{kpis?.high_risk_count ?? 0}</div>
          <div className="text-[11px] text-rose-400/80 mt-1">Risk score &ge; 60</div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <div className="text-[11px] uppercase tracking-wider text-slate-400 font-mono">Critical Assets</div>
          <div className="text-2xl font-bold font-mono text-purple-400 mt-1">{kpis?.critical_assets_count ?? 0}</div>
          <div className="text-[11px] text-purple-400/80 mt-1">Tier-1 business impact</div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl border border-slate-800 bg-slate-950/80">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search by hostname, IP address, or OS..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Asset Type Pills */}
          <div className="flex items-center space-x-1 bg-slate-900 p-1 rounded-lg border border-slate-800 text-[11px]">
            {["ALL", "VIRTUAL_MACHINE", "AGENT_HOST", "SIMULATED_DEVICE"].map((t) => (
              <button
                key={t}
                onClick={() => setSelectedType(t)}
                className={`px-2.5 py-1 rounded font-medium transition ${
                  selectedType === t
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {t === "ALL" ? "All Types" : t === "VIRTUAL_MACHINE" ? "VMs" : t === "AGENT_HOST" ? "Agents" : "Simulated"}
              </button>
            ))}
          </div>

          {/* Criticality Pills */}
          <div className="flex items-center space-x-1 bg-slate-900 p-1 rounded-lg border border-slate-800 text-[11px]">
            {["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"].map((c) => (
              <button
                key={c}
                onClick={() => setSelectedCrit(c)}
                className={`px-2.5 py-1 rounded font-medium transition ${
                  selectedCrit === c
                    ? "bg-purple-500/20 text-purple-300 border border-purple-500/40"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {c === "ALL" ? "All Tier" : c}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Asset Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-950/80 overflow-hidden shadow-lg">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950">
          <div className="flex items-center space-x-2 font-semibold text-sm text-slate-200">
            <Layers className="w-4 h-4 text-cyan-400" />
            <span>Asset Inventory</span>
            <span className="text-xs font-mono text-slate-400">({assets.length})</span>
          </div>
          {loading && <span className="text-xs font-mono text-cyan-400 animate-pulse">Scanning assets...</span>}
        </div>

        {error ? (
          <div className="p-8 text-center text-rose-400 text-xs font-mono">
            <AlertTriangle className="w-6 h-6 mx-auto mb-2 text-rose-400" />
            <span>{error}</span>
          </div>
        ) : assets.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <Layers className="w-8 h-8 mx-auto text-slate-600 animate-pulse" />
            <div className="text-sm font-semibold text-slate-300">No Assets Found</div>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              Click &quot;Sync Multi-Source Assets&quot; to aggregate all discovered VMware virtual machines, connected agents, and simulated network topologies.
            </p>
            <button
              onClick={handleSync}
              className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold font-mono shadow-md shadow-cyan-950 transition"
            >
              Run Asset Sync Now
            </button>
          </div>
        ) : (
          <div className="divide-y divide-slate-800/60">
            {assets.map((asset) => {
              const riskColor = getRiskColor(asset.risk_score);
              const barColor = getRiskBarColor(asset.risk_score);

              return (
                <div
                  key={asset.id}
                  className="p-4.5 hover:bg-slate-900/40 transition flex flex-col lg:flex-row lg:items-center justify-between gap-4"
                >
                  {/* Left: Identity */}
                  <div className="flex items-start space-x-3.5">
                    <div className="h-10 w-10 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center shrink-0">
                      {getTypeIcon(asset.asset_type)}
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-sm text-white tracking-wide">{asset.name}</span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-800">
                          {asset.asset_type.replace("_", " ")}
                        </span>
                        {asset.ip_addresses.length > 0 && (
                          <span className="text-[11px] font-mono text-cyan-400">{asset.ip_addresses[0]}</span>
                        )}
                      </div>

                      <div className="text-xs text-slate-400 flex flex-wrap items-center gap-x-3 gap-y-1">
                        <span>{asset.os_version}</span>
                        {asset.kernel_version && (
                          <>
                            <span>•</span>
                            <span className="font-mono text-[11px]">{asset.kernel_version}</span>
                          </>
                        )}
                        <span>•</span>
                        <span className="font-mono text-[11px] text-slate-400">{asset.id}</span>
                      </div>

                      {/* Security Tags */}
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {asset.security_tags.map((tag) => (
                          <span
                            key={tag}
                            className={`text-[9px] font-mono px-1.5 py-0.5 rounded border uppercase ${
                              tag === "VULNERABLE_TARGET"
                                ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                                : tag === "BRIDGED_ADAPTER" || tag === "FIM_ALERT_ACTIVE"
                                ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                                : tag === "EDR_MONITORED"
                                ? "bg-cyan-500/10 text-cyan-400 border-cyan-500/30"
                                : "bg-slate-800 text-slate-300 border-slate-700"
                            }`}
                          >
                            {tag.replace(/_/g, " ")}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Middle: Risk Gauge */}
                  <div className="w-48 space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400 font-mono text-[11px]">Security Risk</span>
                      <span className={`font-mono font-bold px-1.5 py-0.5 rounded border text-[10px] ${riskColor}`}>
                        {asset.risk_score} / 100
                      </span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                      <div className={`h-full rounded-full ${barColor}`} style={{ width: `${asset.risk_score}%` }}></div>
                    </div>
                  </div>

                  {/* Right: Criticality & Action */}
                  <div className="flex items-center space-x-3 shrink-0">
                    {/* Criticality Dropdown */}
                    <select
                      value={asset.criticality}
                      onChange={(e) => handleCriticalityChange(asset.id, e.target.value)}
                      className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 font-mono focus:outline-none focus:border-cyan-500"
                    >
                      <option value="LOW">LOW</option>
                      <option value="MEDIUM">MEDIUM</option>
                      <option value="HIGH">HIGH</option>
                      <option value="CRITICAL">CRITICAL</option>
                    </select>

                    <button
                      onClick={() => handleInspect(asset.id)}
                      disabled={inspectLoading}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium flex items-center space-x-1.5 transition"
                    >
                      <Info className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Posture Details</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Posture Details Modal */}
      {selectedAsset && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-3xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950">
              <div className="flex items-center space-x-2.5">
                {getTypeIcon(selectedAsset.asset_type)}
                <span className="font-bold text-white text-sm">Asset Security Posture: {selectedAsset.name}</span>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase ${getRiskColor(selectedAsset.risk_score)}`}>
                  Risk: {selectedAsset.risk_score}/100
                </span>
              </div>
              <button
                onClick={() => setSelectedAsset(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-6 text-xs">
              {/* Quick Specs Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <div className="text-slate-400 font-mono text-[10px] uppercase">Asset Class</div>
                  <div className="font-semibold text-slate-200 mt-1">{selectedAsset.asset_type}</div>
                </div>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <div className="text-slate-400 font-mono text-[10px] uppercase">Business Criticality</div>
                  <div className="font-semibold text-purple-400 mt-1">{selectedAsset.criticality}</div>
                </div>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <div className="text-slate-400 font-mono text-[10px] uppercase">Network Exposure</div>
                  <div className="font-semibold text-cyan-400 mt-1">{selectedAsset.exposure}</div>
                </div>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <div className="text-slate-400 font-mono text-[10px] uppercase">Operational State</div>
                  <div className="font-semibold text-emerald-400 mt-1">{selectedAsset.status}</div>
                </div>
              </div>

              {/* Hardware Specifications */}
              {selectedAsset.hardware_specs && (
                <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
                  <div className="font-semibold font-mono text-slate-300 flex items-center space-x-2">
                    <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Hardware Profile</span>
                  </div>
                  <div className="grid grid-cols-3 gap-3 text-slate-400 font-mono">
                    <div>vCPUs: <span className="text-slate-200">{selectedAsset.hardware_specs.vcpus || selectedAsset.hardware_specs.cpu_cores || 1}</span></div>
                    <div>RAM: <span className="text-slate-200">{Math.round((selectedAsset.hardware_specs.memory_mb || 1024) / 1024)} GB</span></div>
                    <div>Hypervisor: <span className="text-slate-200">{selectedAsset.hardware_specs.hypervisor || "N/A"}</span></div>
                  </div>
                </div>
              )}

              {/* Discovered Listening Services */}
              {selectedAsset.services && selectedAsset.services.length > 0 && (
                <div className="space-y-2">
                  <div className="font-semibold font-mono text-slate-300 flex items-center space-x-2">
                    <Radio className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Discovered Listening Services & Open Ports</span>
                  </div>
                  <div className="rounded-lg border border-slate-800 bg-slate-950 overflow-hidden font-mono text-[11px]">
                    <div className="grid grid-cols-3 p-2 border-b border-slate-800 text-slate-400 uppercase">
                      <div>Port</div>
                      <div>Protocol</div>
                      <div>State</div>
                    </div>
                    <div className="divide-y divide-slate-800/60 max-h-40 overflow-y-auto">
                      {selectedAsset.services.map((svc, idx) => (
                        <div key={idx} className="grid grid-cols-3 p-2 text-slate-300">
                          <div className="text-cyan-400">{svc.port}</div>
                          <div className="uppercase">{svc.protocol}</div>
                          <div className="text-emerald-400">{svc.state}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Source-Specific Linkage Details */}
              {selectedAsset.vm_details && (
                <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
                  <div className="font-semibold font-mono text-cyan-400 flex items-center space-x-2">
                    <Server className="w-3.5 h-3.5" />
                    <span>VMware Hypervisor Linkage</span>
                  </div>
                  <div className="text-slate-400 font-mono space-y-1">
                    <div>Config Path: <span className="text-slate-300">{selectedAsset.vm_details.config_path}</span></div>
                    <div>Power State: <span className="text-emerald-400">{selectedAsset.vm_details.power_state}</span></div>
                    <div>Vulnerable Target: <span className={selectedAsset.vm_details.is_vulnerable_target ? "text-rose-400 font-bold" : "text-slate-400"}>{selectedAsset.vm_details.is_vulnerable_target ? "YES" : "NO"}</span></div>
                  </div>
                </div>
              )}

              {selectedAsset.agent_details && (
                <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
                  <div className="font-semibold font-mono text-purple-400 flex items-center space-x-2">
                    <Radio className="w-3.5 h-3.5" />
                    <span>Autonomous Agent Linkage</span>
                  </div>
                  <div className="text-slate-400 font-mono space-y-1">
                    <div>Agent ID: <span className="text-slate-300">{selectedAsset.agent_details.id}</span></div>
                    <div>Agent Status: <span className="text-emerald-400">{selectedAsset.agent_details.status}</span></div>
                    <div>Agent Version: <span className="text-slate-300">{selectedAsset.agent_details.agent_version}</span></div>
                    <div>Last Heartbeat: <span className="text-slate-300">{selectedAsset.agent_details.last_heartbeat || "N/A"}</span></div>
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-800 bg-slate-950 flex items-center justify-between text-xs">
              <span className="text-slate-400 font-mono">Last Synchronized: {new Date(selectedAsset.last_seen).toLocaleString()}</span>
              <button
                onClick={() => setSelectedAsset(null)}
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
