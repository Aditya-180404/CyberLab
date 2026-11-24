"use client";

import React, { useState } from "react";
import { KeyRound, Shield, AlertCircle, CheckCircle2 } from "lucide-react";
import { loginUser } from "../../lib/api";
import { UserProfile } from "../../lib/types";

const SEED_ACCOUNTS = [
  { username: "admin", role: "super_admin", pass: "CyberLab@Admin2026!", label: "Super Admin" },
  { username: "analyst", role: "soc_analyst", pass: "Analyst@CyberLab2026!", label: "SOC Analyst" },
  { username: "engineer", role: "network_engineer", pass: "Engineer@CyberLab2026!", label: "Net Engineer" },
  { username: "auditor", role: "auditor", pass: "Auditor@CyberLab2026!", label: "Auditor" },
];

export function QuickAuthCard({ onLoginSuccess }: { onLoginSuccess: (user: UserProfile, token: string) => void }) {
  const [loading, setLoading] = useState(false);
  const [activeUser, setActiveUser] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleQuickLogin = async (acc: typeof SEED_ACCOUNTS[0]) => {
    setLoading(true);
    setError(null);
    try {
      const res = await loginUser(acc.username, acc.pass);
      localStorage.setItem("cyberlab_token", res.access_token);
      setActiveUser(acc.username);
      onLoginSuccess(res.user, res.access_token);
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur shadow-sm">
      <div className="flex items-center space-x-2 mb-3 border-b border-slate-800 pb-3">
        <KeyRound className="w-4 h-4 text-cyan-400" />
        <h2 className="text-sm font-semibold tracking-wide text-slate-100 uppercase font-mono">
          RBAC Session & Authentication
        </h2>
      </div>

      <p className="text-xs text-slate-400 mb-3">
        Select a seeded role to test authenticated endpoints, permission guards, and audit trail generation:
      </p>

      {error && (
        <div className="mb-3 p-2.5 rounded bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid grid-cols-2 gap-2.5">
        {SEED_ACCOUNTS.map((acc) => {
          const isCurrent = activeUser === acc.username;
          return (
            <button
              key={acc.username}
              onClick={() => handleQuickLogin(acc)}
              disabled={loading}
              className={`p-3 rounded-lg border text-left transition ${
                isCurrent
                  ? "bg-cyan-500/15 border-cyan-500/40 text-cyan-200"
                  : "bg-slate-950 border-slate-800 hover:border-slate-700 text-slate-300 hover:bg-slate-900/80"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-xs text-slate-100">{acc.label}</span>
                {isCurrent ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />
                ) : (
                  <Shield className="w-3.5 h-3.5 text-slate-400" />
                )}
              </div>
              <div className="text-[11px] font-mono text-slate-400 mt-1">
                user: <span className="text-slate-300">{acc.username}</span>
              </div>
              <div className="text-[10px] font-mono text-cyan-400/80 mt-0.5">
                role: {acc.role}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
