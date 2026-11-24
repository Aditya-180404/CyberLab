"use client";

import React from "react";
import {
  ShieldAlert,
  Network,
  Server,
  Radio,
  Layers,
  FileSearch,
  Crosshair,
  GitBranch,
  ShieldCheck,
  History,
  Settings,
  Cpu,
} from "lucide-react";

interface NavItem {
  name: string;
  phase: string;
  icon: React.ComponentType<{ className?: string }>;
  status: "ACTIVE" | "PLANNED";
}

const NAV_ITEMS: NavItem[] = [
  { name: "SOC Dashboard", phase: "Phase 1", icon: ShieldAlert, status: "ACTIVE" },
  { name: "Network Studio", phase: "Phase 2", icon: Network, status: "ACTIVE" },
  { name: "Virtual Machines", phase: "Phase 3", icon: Server, status: "ACTIVE" },
  { name: "Endpoint Fleet", phase: "Phase 4", icon: Radio, status: "ACTIVE" },
  { name: "Asset Inventory", phase: "Phase 5", icon: Layers, status: "ACTIVE" },
  { name: "SIEM & Correlation", phase: "Phase 6", icon: FileSearch, status: "ACTIVE" },
  { name: "Incident Response", phase: "Phase 7", icon: Crosshair, status: "PLANNED" },
  { name: "Digital Twin", phase: "Phase 8", icon: GitBranch, status: "PLANNED" },
  { name: "Purple-Team Studio", phase: "Phase 9-10", icon: ShieldCheck, status: "PLANNED" },
  { name: "Audit Trail", phase: "Phase 1", icon: History, status: "ACTIVE" },
  { name: "Settings & RBAC", phase: "Phase 1", icon: Settings, status: "ACTIVE" },
];

export function Sidebar({ currentTab, onSelectTab }: { currentTab: string; onSelectTab: (tab: string) => void }) {
  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-950/80 backdrop-blur flex flex-col justify-between shrink-0 h-screen sticky top-0">
      <div>
        {/* Brand */}
        <div className="p-5 border-b border-slate-800 flex items-center space-x-3">
          <div className="h-9 w-9 rounded-lg bg-cyan-950 border border-cyan-500/30 flex items-center justify-center text-cyan-400 font-bold shadow-lg shadow-cyan-950/50">
            <Cpu className="w-5 h-5 text-cyan-400 animate-pulse" />
          </div>
          <div>
            <div className="font-bold tracking-wider text-slate-100 flex items-center space-x-2">
              <span>CYBERLAB</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-mono">
                v0.6
              </span>
            </div>
            <p className="text-[11px] text-slate-400 tracking-tight">Security Platform</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="p-3 space-y-1">
          <div className="text-[10px] uppercase font-mono tracking-wider text-slate-400 px-3 py-2">
            Platform Modules
          </div>
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isSelected = currentTab === item.name;
            const isActive = item.status === "ACTIVE";

            return (
              <button
                key={item.name}
                onClick={() => onSelectTab(item.name)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                  isSelected
                    ? "bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent"
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <Icon className={`w-4 h-4 ${isSelected ? "text-cyan-400" : "text-slate-400"}`} />
                  <span>{item.name}</span>
                </div>
                <span
                  className={`text-[9px] font-mono px-1.5 py-0.5 rounded border ${
                    isActive
                      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                      : "bg-slate-800/60 text-slate-400 border-slate-700/50"
                  }`}
                >
                  {item.phase}
                </span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* System Status Footer */}
      <div className="p-4 border-t border-slate-800 bg-slate-950/60">
        <div className="flex items-center justify-between text-[11px] text-slate-400">
          <span className="flex items-center space-x-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping"></span>
            <span className="text-slate-300 font-mono">HYPERVISOR ACTIVE</span>
          </span>
          <span className="font-mono text-slate-400">Kali Linux</span>
        </div>
      </div>
    </aside>
  );
}
