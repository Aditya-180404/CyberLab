"use client";

import React, { useState, useEffect } from "react";
import { Shield, Clock, Terminal, User } from "lucide-react";
import { UserProfile } from "../../lib/types";

export function Header({ currentUser, onLogout }: { currentUser: UserProfile | null; onLogout: () => void }) {
  const [time, setTime] = useState<string>("");

  useEffect(() => {
    const update = () => {
      setTime(new Date().toUTCString().replace("GMT", "UTC"));
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-20 h-16 border-b border-slate-800/90 bg-slate-950/80 backdrop-blur-md px-6 flex items-center justify-between shrink-0 shadow-sm shadow-black/40">
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2 text-xs font-mono text-slate-300 bg-slate-900/70 px-3 py-1.5 rounded-lg border border-slate-800/80">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          <Terminal className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-slate-400">CONTROL PLANE:</span>
          <span className="text-emerald-400 font-semibold">ACTIVE</span>
        </div>
        <div className="hidden md:inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-mono tracking-wider bg-cyan-950/60 text-cyan-300 border border-cyan-500/30">
          ENTERPRISE UNIFIED SOC
        </div>
      </div>

      <div className="flex items-center space-x-3">
        {/* Real-time Clock */}
        <div className="flex items-center space-x-1.5 text-xs font-mono text-slate-300 bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800">
          <Clock className="w-3.5 h-3.5 text-cyan-400" />
          <span>{time || "Synchronizing..."}</span>
        </div>

        {/* User Badge */}
        {currentUser ? (
          <div className="flex items-center space-x-2 bg-slate-900/90 border border-slate-800 px-3 py-1.5 rounded-lg text-xs shadow-inner">
            <User className="w-3.5 h-3.5 text-cyan-400" />
            <span className="font-semibold text-slate-100">{currentUser.username}</span>
            <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
              {currentUser.role}
            </span>
            <button
              onClick={onLogout}
              className="ml-1 pl-2 border-l border-slate-800 text-[10px] font-mono text-slate-400 hover:text-rose-400 transition"
            >
              Sign out
            </button>
          </div>
        ) : (
          <div className="text-xs font-mono px-2.5 py-1.5 rounded-lg bg-slate-900/60 border border-slate-800 text-slate-400">
            Session Unauthenticated
          </div>
        )}
      </div>
    </header>
  );
}
