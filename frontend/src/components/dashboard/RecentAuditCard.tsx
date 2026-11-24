"use client";

import React from "react";
import { History } from "lucide-react";
import { AuditLogItem } from "../../lib/types";

export function RecentAuditCard({ logs, loading }: { logs: AuditLogItem[]; loading: boolean }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur shadow-sm">
      <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2">
          <History className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-semibold tracking-wide text-slate-100 uppercase font-mono">
            Immutable Audit Trail Stream
          </h2>
        </div>
        <span className="text-xs font-mono text-slate-400">
          Latest {logs.length} Operations
        </span>
      </div>

      {loading ? (
        <div className="text-xs text-slate-400 py-3">Fetching audit records...</div>
      ) : logs.length === 0 ? (
        <div className="text-xs text-slate-400 py-3">
          No audit records available. Authenticate with an account to view or record events.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-[10px] font-mono text-slate-400 uppercase">
                <th className="pb-2">Timestamp</th>
                <th className="pb-2">User</th>
                <th className="pb-2">Action</th>
                <th className="pb-2">Resource</th>
                <th className="pb-2">Status</th>
                <th className="pb-2">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50 font-mono text-[11px]">
              {logs.map((log) => {
                const isSuccess = log.status === "SUCCESS";
                return (
                  <tr key={log.id} className="hover:bg-slate-800/30 transition">
                    <td className="py-2 text-slate-400">
                      {new Date(log.created_at).toLocaleTimeString()}
                    </td>
                    <td className="py-2 text-slate-200 font-semibold">{log.username}</td>
                    <td className="py-2 text-cyan-400">{log.action}</td>
                    <td className="py-2 text-slate-400">{log.resource_type}</td>
                    <td className="py-2">
                      <span
                        className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] border ${
                          isSuccess
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                            : "bg-rose-500/10 text-rose-400 border-rose-500/20"
                        }`}
                      >
                        {log.status}
                      </span>
                    </td>
                    <td className="py-2 text-slate-400 max-w-xs truncate" title={log.details || ""}>
                      {log.details || "-"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
