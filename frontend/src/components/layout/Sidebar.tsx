"use client";

import React from "react";
import {
  ShieldAlert,
  Network,
  Radio,
  Layers,
  FileSearch,
  Crosshair,
  GitBranch,
  ShieldCheck,
  History,
  Settings,
  Cpu,
  AlertTriangle,
  Globe,
  Radar,
} from "lucide-react";

interface NavItem {
  name: string;
  icon: React.ComponentType<{ className?: string }>;
  status: "ACTIVE" | "PLANNED";
}

const NAV_ITEMS: NavItem[] = [
  { name: "SOC Dashboard", icon: ShieldAlert, status: "ACTIVE" },
  { name: "Network Studio", icon: Network, status: "ACTIVE" },
  { name: "Endpoint Fleet", icon: Radio, status: "ACTIVE" },
  { name: "Asset Inventory", icon: Layers, status: "ACTIVE" },
  { name: "SIEM & Correlation", icon: FileSearch, status: "ACTIVE" },
  { name: "Threat Intel & NDR", icon: Radar, status: "ACTIVE" },
  { name: "Incident Response", icon: Crosshair, status: "ACTIVE" },
  { name: "Digital Twin", icon: GitBranch, status: "ACTIVE" },
  { name: "Purple-Team Studio", icon: ShieldCheck, status: "ACTIVE" },
  { name: "Vulnerabilities", icon: AlertTriangle, status: "ACTIVE" },
  { name: "Multi-Site Fleet", icon: Globe, status: "ACTIVE" },
  { name: "Audit Trail", icon: History, status: "ACTIVE" },
  { name: "Settings & RBAC", icon: Settings, status: "ACTIVE" },
];

export function Sidebar({ currentTab, onSelectTab }: { currentTab: string; onSelectTab: (tab: string) => void }) {
  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-950/80 backdrop-blur flex flex-col justify-between shrink-0 h-screen sticky top-0">
      <div>
        {/* Brand */}
        <div className="p-5 border-b border-slate-800/90 flex items-center space-x-3 bg-gradient-to-b from-cyan-950/20 to-transparent">
          <div className="h-9 w-9 rounded-lg bg-cyan-950/80 border border-cyan-500/40 flex items-center justify-center text-cyan-400 font-bold shadow-lg shadow-cyan-950/60">
            <Cpu className="w-5 h-5 text-cyan-400 animate-pulse" />
          </div>
          <div>
            <div className="font-bold tracking-wider text-slate-100 flex items-center space-x-2">
              <span>CYBERLAB</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 font-mono">
                v1.0
              </span>
            </div>
            <p className="text-[11px] text-slate-400 tracking-tight">Unified Security Operations</p>
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
                {isSelected && (
                  <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 shadow-[0_0_6px_rgba(34,211,238,0.8)]" />
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* System Status Footer */}
      <div className="p-4 border-t border-slate-800/90 bg-slate-950/70">
        <div className="flex items-center justify-between text-[11px] text-slate-400">
          <span className="flex items-center space-x-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping"></span>
            <span className="text-slate-300 font-mono">SOC ENGINE ONLINE</span>
          </span>
          <span className="font-mono text-cyan-400/90">Unified v1.0</span>
        </div>
      </div>
    </aside>
  );
}
