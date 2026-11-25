"use client";

import React from "react";
import { CheckCircle2, Clock } from "lucide-react";

interface ModuleItem {
  id: number;
  name: string;
  status: "COMPLETE" | "PLANNED";
  summary: string;
}

const MODULES: ModuleItem[] = [
  { id: 1, name: "Core Foundation", status: "COMPLETE", summary: "FastAPI, Next.js, SQLite WAL, RBAC, Health, Audit" },
  { id: 2, name: "Network Simulation Engine", status: "COMPLETE", summary: "Linux netns, veth pairs, Linux bridges, nftables, React Flow" },
  { id: 3, name: "Real VM Integration", status: "COMPLETE", summary: "VMware Workstation CLI adapter, VM power states, vNIC bridging" },
  { id: 4, name: "Distributed Linux Agent", status: "COMPLETE", summary: "Standalone Python agent, TLS heartbeat, policy enforcement" },
  { id: 5, name: "Asset Inventory & Monitoring", status: "COMPLETE", summary: "Cross-platform asset sync, dynamic risk scoring, posture inspection" },
  { id: 6, name: "SIEM & Detection Engine", status: "COMPLETE", summary: "Event normalization, MITRE ATT&CK mapping, alert correlation" },
  { id: 7, name: "Incident Response (SOAR)", status: "COMPLETE", summary: "Playbook execution, approval gates, verified containment, rollback" },
  { id: 8, name: "Digital Twin & Attack Paths", status: "COMPLETE", summary: "NetworkX topological graphs, reachability, blast-radius analysis" },
  { id: 9, name: "Attack Simulation Studio", status: "COMPLETE", summary: "Safe, bounded offensive scenarios against authorized targets" },
  { id: 10, name: "Purple-Team Validation", status: "COMPLETE", summary: "Continuous control validation, defensive efficacy scoring" },
  { id: 11, name: "Vulnerability Management", status: "COMPLETE", summary: "CVE ingestion, CVSS asset risk scoring, remediation tracking" },
  { id: 12, name: "Multi-Site Enterprise Fleet", status: "COMPLETE", summary: "Multi-site isolation, PostgreSQL migration, hardened fleet control, compliance reporting" },
];

export function ModuleMatrixCard() {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur shadow-sm">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <h2 className="text-sm font-semibold tracking-wide text-slate-100 uppercase font-mono">
          Architecture & Platform Module Matrix
        </h2>
        <span className="text-xs font-mono text-emerald-400">
          All 12 Modules Active (12/12) - Production Release v1.0
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {MODULES.map((mod) => {
          const isComplete = mod.status === "COMPLETE";
          return (
            <div
              key={mod.id}
              className={`p-3 rounded-lg border text-xs transition ${
                isComplete
                  ? "bg-cyan-950/20 border-cyan-500/40 text-slate-200"
                  : "bg-slate-950 border-slate-800 text-slate-400"
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-mono text-[11px] font-semibold text-slate-300">
                  Module {mod.id}
                </span>
                {isComplete ? (
                  <span className="flex items-center space-x-1 text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                    <CheckCircle2 className="w-3 h-3" />
                    <span>ACTIVE</span>
                  </span>
                ) : (
                  <span className="flex items-center space-x-1 text-[10px] font-mono text-slate-400 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">
                    <Clock className="w-3 h-3" />
                    <span>PLANNED</span>
                  </span>
                )}
              </div>
              <div className="font-medium text-slate-100 mb-1">{mod.name}</div>
              <p className="text-[11px] text-slate-400 leading-relaxed">{mod.summary}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
