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
  { id: 1, name: "Core Foundation", status: "COMPLETE", summary: "FastAPI, Next.js, PostgreSQL/SQLite, RBAC, Health, Audit" },
  { id: 2, name: "Network & Topology Studio", status: "COMPLETE", summary: "Linux netns, veth pairs, Linux bridges, nftables, React Flow" },
  { id: 3, name: "Multi-System Onboarding", status: "COMPLETE", summary: "Cross-OS agents (Linux, Windows, macOS), syslog forwarders & enrollment keys" },
  { id: 4, name: "Distributed EDR Agents", status: "COMPLETE", summary: "FIM, auth log tailing, socket monitoring, TLS heartbeat, policy enforcement" },
  { id: 5, name: "Asset Inventory & Monitoring", status: "COMPLETE", summary: "Cross-platform asset sync, dynamic risk scoring, posture inspection" },
  { id: 6, name: "SIEM & Detection Engine", status: "COMPLETE", summary: "Event normalization, OPNsense/Suricata NDR, MITRE ATT&CK correlation" },
  { id: 7, name: "Incident Response (SOAR)", status: "COMPLETE", summary: "Playbook execution, approval gates, nftables containment, rollback" },
  { id: 8, name: "Digital Twin & Attack Paths", status: "COMPLETE", summary: "NetworkX topological graphs, reachability, blast-radius analysis" },
  { id: 9, name: "Threat Intel & Deception", status: "COMPLETE", summary: "IOC feed matching, honeypot canary traps, NDR telemetry correlation" },
  { id: 10, name: "Purple-Team Validation", status: "COMPLETE", summary: "Continuous control validation, defensive efficacy scoring" },
  { id: 11, name: "Vulnerability Management", status: "COMPLETE", summary: "Version-matched CVE scanning, CVSS risk scoring, remediation tracking" },
  { id: 12, name: "Multi-Site Enterprise Fleet", status: "COMPLETE", summary: "Multi-site isolation, PostgreSQL fleet control, executive & compliance reporting" },
];

export function ModuleMatrixCard() {
  return (
    <div className="cyber-card rounded-xl p-5 backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-4 border-b border-slate-800/80 pb-3">
        <h2 className="text-sm font-semibold tracking-wide text-slate-100 uppercase font-mono">
          Unified SOC Capabilities & Module Matrix
        </h2>
        <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
          All 12 Modules Active • v1.0
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {MODULES.map((mod) => {
          const isComplete = mod.status === "COMPLETE";
          return (
            <div
              key={mod.id}
              className={`p-3.5 rounded-lg border text-xs transition-all duration-200 ${
                isComplete
                  ? "bg-slate-950/75 border-cyan-500/25 hover:border-cyan-400/50 hover:bg-cyan-950/20 text-slate-200"
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
