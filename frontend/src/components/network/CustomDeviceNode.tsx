"use client";

import React, { memo } from "react";
import { Handle, Position } from "@xyflow/react";
import { Network, Server, Shield, Radio, Terminal } from "lucide-react";

interface DeviceNodeData {
  label: string;
  deviceType: "router" | "switch" | "firewall" | "server" | "endpoint";
  ipAddress?: string;
  status: "STOPPED" | "RUNNING" | "ERROR";
  vlanId?: number;
  namespace?: string;
}

const ICONS = {
  router: Network,
  switch: Network,
  firewall: Shield,
  server: Server,
  endpoint: Terminal,
};

const TYPE_COLORS = {
  router: "border-cyan-500/50 bg-cyan-950/40 text-cyan-400",
  switch: "border-purple-500/50 bg-purple-950/40 text-purple-400",
  firewall: "border-rose-500/50 bg-rose-950/40 text-rose-400",
  server: "border-emerald-500/50 bg-emerald-950/40 text-emerald-400",
  endpoint: "border-amber-500/50 bg-amber-950/40 text-amber-400",
};

export const CustomDeviceNode = memo(({ data, selected }: { data: DeviceNodeData; selected?: boolean }) => {
  const Icon = ICONS[data.deviceType] || Terminal;
  const colorClass = TYPE_COLORS[data.deviceType] || TYPE_COLORS.endpoint;
  const isRunning = data.status === "RUNNING";

  return (
    <div
      className={`min-w-[170px] rounded-xl border-2 p-3 shadow-xl backdrop-blur transition-all ${colorClass} ${
        selected ? "ring-2 ring-cyan-400 scale-105" : ""
      }`}
    >
      <Handle type="target" position={Position.Top} className="!bg-cyan-400 !w-3 !h-3" />

      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <Icon className="w-4 h-4 shrink-0" />
          <span className="font-bold text-xs tracking-tight text-white">{data.label}</span>
        </div>
        <span
          className={`h-2.5 w-2.5 rounded-full ${
            isRunning ? "bg-emerald-400 shadow-md shadow-emerald-500 animate-pulse" : "bg-slate-600"
          }`}
          title={`Status: ${data.status}`}
        />
      </div>

      <div className="space-y-1 font-mono text-[10px]">
        {data.ipAddress && (
          <div className="flex justify-between text-slate-300">
            <span className="text-slate-400">IP:</span>
            <span>{data.ipAddress}</span>
          </div>
        )}
        {data.vlanId && (
          <div className="flex justify-between text-slate-300">
            <span className="text-slate-400">VLAN:</span>
            <span className="text-cyan-300">ID {data.vlanId}</span>
          </div>
        )}
        <div className="flex justify-between text-slate-400 text-[9px] pt-1 border-t border-slate-700/50">
          <span className="uppercase">{data.deviceType}</span>
          <span>{data.status}</span>
        </div>
      </div>

      <Handle type="source" position={Position.Bottom} className="!bg-cyan-400 !w-3 !h-3" />
    </div>
  );
});

CustomDeviceNode.displayName = "CustomDeviceNode";
