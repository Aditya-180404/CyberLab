"use client";

import React, { useState, useEffect } from "react";
import {
  Server,
  Play,
  Square,
  RotateCcw,
  Search,
  ShieldAlert,
  ShieldCheck,
  Cpu,
  Layers,
  Network,
  AlertTriangle,
  HardDrive,
} from "lucide-react";
import { fetchVMs, discoverVMs, powerVM } from "../../lib/api";
import { VirtualMachineItem } from "../../lib/types";

export function VMManagement({ authToken }: { authToken: string | null }) {
  const [vms, setVms] = useState<VirtualMachineItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const loadVMs = async () => {
    setLoading(true);
    try {
      const data = await fetchVMs(authToken || "demo-token");
      setVms(data);
    } catch (err: any) {
      // Non-fatal if unauthenticated or empty
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVMs();
  }, [authToken]);

  const handleDiscover = async () => {
    setLoading(true);
    setMessage("Scanning VMware Workstation inventory and host drives for .vmx files...");
    try {
      const res = await discoverVMs(authToken || "demo-token");
      setVms(res.registered_vms);
      setMessage(`Discovery complete! Successfully inventoried ${res.discovered_count} virtual machines.`);
    } catch (err: any) {
      setMessage(`Discovery failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handlePowerAction = async (vmId: string, action: "start" | "stop" | "reset") => {
    setActionLoading(vmId);
    try {
      const updated = await powerVM(authToken || "demo-token", vmId, action, "soft");
      setVms((prev) => prev.map((v) => (v.id === updated.id ? updated : v)));
      setMessage(`Power action '${action}' dispatched successfully to ${updated.name}.`);
    } catch (err: any) {
      setMessage(`Power operation failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const runningCount = vms.filter((v) => v.power_state === "RUNNING").length;
  const vulnerableCount = vms.filter((v) => v.is_vulnerable_target).length;

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto w-full">
      {/* Top Banner */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Server className="w-5 h-5 text-cyan-400" />
            <h1 className="text-xl font-bold tracking-tight text-white font-mono">
              VMware Workstation Hypervisor Control
            </h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              PHASE 3 ACTIVE
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
            Manage real virtual machines (Parrot OS, Metasploitable 2, Stapler), inspect VMware network adapter bindings, enforce host-only isolation, and control VM power states.
          </p>
        </div>

        <button
          onClick={handleDiscover}
          disabled={loading}
          className="flex items-center space-x-2 px-4 py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold font-mono shadow-md shadow-cyan-950 transition disabled:opacity-50 shrink-0"
        >
          <Search className="w-4 h-4" />
          <span>{loading ? "Scanning Disks..." : "Discover Local VMs on Host"}</span>
        </button>
      </div>

      {/* Message Banner */}
      {message && (
        <div className="bg-cyan-950/40 border border-cyan-800/40 p-3 rounded-lg text-xs font-mono text-cyan-300 flex items-center justify-between">
          <span>{message}</span>
          <button onClick={() => setMessage(null)} className="text-slate-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 font-mono">
          <div className="text-[10px] text-slate-400 uppercase">Registered VMs</div>
          <div className="text-2xl font-bold text-slate-100 mt-1">{vms.length}</div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 font-mono">
          <div className="text-[10px] text-slate-400 uppercase">Running Instances</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{runningCount}</div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 font-mono">
          <div className="text-[10px] text-slate-400 uppercase">Target Vulnerable Assets</div>
          <div className="text-2xl font-bold text-rose-400 mt-1">{vulnerableCount}</div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 font-mono">
          <div className="text-[10px] text-slate-400 uppercase">Hypervisor Backend</div>
          <div className="text-sm font-bold text-cyan-400 mt-2 truncate">VMware Workstation (vmrun)</div>
        </div>
      </div>

      {/* VM Grid */}
      <div className="space-y-4">
        <h2 className="text-sm font-semibold tracking-wide text-slate-200 uppercase font-mono">
          Discovered Virtual Machine Inventory
        </h2>

        {vms.length === 0 ? (
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-8 text-center space-y-3">
            <Server className="w-8 h-8 text-slate-500 mx-auto" />
            <p className="text-xs text-slate-400">
              No virtual machines currently registered in the CyberLab database.
            </p>
            <button
              onClick={handleDiscover}
              className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold font-mono"
            >
              Scan Host for Installed VMs
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {vms.map((vm) => {
              const isRunning = vm.power_state === "RUNNING";
              const hasBridgeWarning = vm.safety_warning !== null;

              return (
                <div
                  key={vm.id}
                  className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 space-y-4 backdrop-blur shadow-sm hover:border-slate-700 transition"
                >
                  {/* Card Header */}
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <h3 className="font-bold text-sm text-white font-mono">{vm.name}</h3>
                        {vm.is_vulnerable_target && (
                          <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30">
                            VULNERABLE ASSET
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] font-mono text-slate-400 mt-0.5">
                        {vm.os_type} • {vm.vcpus} vCPU • {vm.memory_mb} MB RAM
                      </div>
                    </div>

                    {/* Power State Badge */}
                    <div className="flex items-center space-x-1.5 font-mono text-[11px] bg-slate-950 px-2.5 py-1 rounded-md border border-slate-800">
                      <span
                        className={`h-2 w-2 rounded-full ${
                          isRunning ? "bg-emerald-400 animate-pulse" : "bg-slate-600"
                        }`}
                      />
                      <span className={isRunning ? "text-emerald-400 font-semibold" : "text-slate-400"}>
                        {vm.power_state}
                      </span>
                    </div>
                  </div>

                  {/* Config Path */}
                  <div className="p-2 rounded bg-slate-950 border border-slate-800/80 font-mono text-[10px] text-slate-400 truncate" title={vm.config_path}>
                    <span className="text-slate-500">PATH:</span> {vm.config_path}
                  </div>

                  {/* Network Adapter Inspection */}
                  <div className="space-y-1.5 font-mono text-xs">
                    <div className="text-[10px] uppercase text-slate-400 flex items-center space-x-1">
                      <Network className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Network Adapter Inspection</span>
                    </div>

                    {vm.network_adapters && vm.network_adapters.length > 0 ? (
                      <div className="space-y-1">
                        {vm.network_adapters.map((ad, idx) => (
                          <div
                            key={idx}
                            className="p-2 rounded bg-slate-950/80 border border-slate-800 text-[11px] flex items-center justify-between"
                          >
                            <div>
                              <span className="text-slate-200 font-semibold">{ad.name}</span>
                              <span className="text-slate-400 ml-2">({ad.virtual_dev})</span>
                              {ad.mac_address && (
                                <span className="text-slate-500 ml-2 text-[10px]">[{ad.mac_address}]</span>
                              )}
                            </div>
                            <span
                              className={`text-[10px] px-2 py-0.5 rounded border ${
                                ad.is_bridged
                                  ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                                  : "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                              }`}
                            >
                              {ad.connection_type} ({ad.vnet || "NAT"})
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-[11px] text-slate-500 italic">No virtual adapters parsed</div>
                    )}
                  </div>

                  {/* Safety Alert if bridged */}
                  {hasBridgeWarning ? (
                    <div className="p-2.5 rounded bg-rose-950/30 border border-rose-500/30 text-rose-300 text-[11px] flex items-start space-x-2">
                      <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                      <span>{vm.safety_warning}</span>
                    </div>
                  ) : (
                    <div className="p-2 rounded bg-emerald-950/15 border border-emerald-500/20 text-emerald-400 text-[10px] font-mono flex items-center space-x-1.5">
                      <ShieldCheck className="w-3.5 h-3.5" />
                      <span>Isolated Host-Only (vmnet1) — Protected from host Wi-Fi/LAN</span>
                    </div>
                  )}

                  {/* Power Control Buttons */}
                  <div className="pt-2 border-t border-slate-800/80 flex items-center justify-end space-x-2">
                    {!isRunning ? (
                      <button
                        onClick={() => handlePowerAction(vm.id, "start")}
                        disabled={actionLoading === vm.id}
                        className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition disabled:opacity-50"
                      >
                        <Play className="w-3.5 h-3.5" />
                        <span>Power On</span>
                      </button>
                    ) : (
                      <>
                        <button
                          onClick={() => handlePowerAction(vm.id, "reset")}
                          disabled={actionLoading === vm.id}
                          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold transition disabled:opacity-50"
                        >
                          <RotateCcw className="w-3.5 h-3.5" />
                          <span>Reset</span>
                        </button>
                        <button
                          onClick={() => handlePowerAction(vm.id, "stop")}
                          disabled={actionLoading === vm.id}
                          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold transition disabled:opacity-50"
                        >
                          <Square className="w-3.5 h-3.5" />
                          <span>Shut Down</span>
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
    </div>
  );
}
