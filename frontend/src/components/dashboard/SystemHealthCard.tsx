"use client";

import React from "react";
import { Activity, Database, HardDrive, Cpu, Layers } from "lucide-react";
import { HealthResponse } from "../../lib/types";

export function SystemHealthCard({ health, loading, error, onRefresh }: {
  health: HealthResponse | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur shadow-sm">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2">
          <Activity className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-semibold tracking-wide text-slate-100 uppercase font-mono">
            Platform Engine Health
          </h2>
        </div>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="text-xs text-slate-400 hover:text-cyan-400 font-mono transition disabled:opacity-50"
        >
          {loading ? "Checking..." : "[ Refresh Probe ]"}
        </button>
      </div>

      {error ? (
        <div className="p-4 rounded-lg bg-rose-950/30 border border-rose-500/30 text-rose-400 text-xs">
          <strong>Backend Unreachable:</strong> {error}
          <div className="mt-1 text-[11px] text-slate-400">
            Ensure FastAPI is running on <code className="text-slate-300">127.0.0.1:8000</code>.
          </div>
        </div>
      ) : health ? (
        <div className="space-y-4">
          {/* Top Status Indicators */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
              <div className="text-[10px] font-mono text-slate-400 uppercase">Engine Status</div>
              <div className="text-sm font-bold text-emerald-400 mt-0.5 flex items-center space-x-1.5">
                <span className="h-2 w-2 rounded-full bg-emerald-400"></span>
                <span className="uppercase">{health.status}</span>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
              <div className="text-[10px] font-mono text-slate-400 uppercase">Database</div>
              <div className="text-sm font-bold text-cyan-400 mt-0.5 flex items-center space-x-1.5">
                <Database className="w-3.5 h-3.5" />
                <span className="uppercase">{health.database}</span>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
              <div className="text-[10px] font-mono text-slate-400 uppercase">OS & Kernel</div>
              <div className="text-xs font-mono text-slate-200 mt-1 truncate" title={health.platform.kernel}>
                {health.platform.os} {health.platform.kernel.split("-")[0]}
              </div>
            </div>

            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
              <div className="text-[10px] font-mono text-slate-400 uppercase">Python Runtime</div>
              <div className="text-xs font-mono text-slate-200 mt-1">
                v{health.platform.python}
              </div>
            </div>
          </div>

          {/* Telemetry Progress Bars */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            {/* CPU */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-slate-400 flex items-center space-x-1">
                  <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                  <span>CPU Utilization</span>
                </span>
                <span className="text-slate-200 font-semibold">{health.platform.cpu_usage_pct}%</span>
              </div>
              <div className="w-full bg-slate-950 rounded-full h-2 border border-slate-800 overflow-hidden">
                <div
                  className="bg-cyan-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(health.platform.cpu_usage_pct, 100)}%` }}
                ></div>
              </div>
            </div>

            {/* Memory */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-slate-400 flex items-center space-x-1">
                  <Layers className="w-3.5 h-3.5 text-purple-400" />
                  <span>RAM Usage</span>
                </span>
                <span className="text-slate-200 font-semibold">
                  {health.platform.memory_used_gb} / {health.platform.memory_total_gb} GB ({health.platform.memory_usage_pct}%)
                </span>
              </div>
              <div className="w-full bg-slate-950 rounded-full h-2 border border-slate-800 overflow-hidden">
                <div
                  className="bg-purple-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(health.platform.memory_usage_pct, 100)}%` }}
                ></div>
              </div>
            </div>

            {/* Disk */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-slate-400 flex items-center space-x-1">
                  <HardDrive className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Available Storage</span>
                </span>
                <span className="text-slate-200 font-semibold">
                  {health.platform.disk_free_gb} GB free ({health.platform.disk_usage_pct}% used)
                </span>
              </div>
              <div className="w-full bg-slate-950 rounded-full h-2 border border-slate-800 overflow-hidden">
                <div
                  className="bg-emerald-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(health.platform.disk_usage_pct, 100)}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-xs text-slate-400 py-3">Connecting to backend health probe...</div>
      )}
    </div>
  );
}
