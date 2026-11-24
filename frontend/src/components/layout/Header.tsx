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
    <header className="h-16 border-b border-slate-800 bg-slate-950/60 backdrop-blur px-6 flex items-center justify-between shrink-0">
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2 text-xs font-mono text-slate-300">
          <Terminal className="w-4 h-4 text-cyan-400" />
          <span className="text-slate-400">API GATEWAY:</span>
          <span className="text-emerald-400 font-semibold">127.0.0.1:8000</span>
        </div>
        <div className="hidden md:inline-block px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-cyan-950/50 text-cyan-400 border border-cyan-800/40">
          LOCAL DEV HOST
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {/* Real-time Clock */}
        <div className="flex items-center space-x-1.5 text-xs font-mono text-slate-400 bg-slate-900/80 px-3 py-1.5 rounded-md border border-slate-800">
          <Clock className="w-3.5 h-3.5 text-cyan-400" />
          <span>{time || "Synchronizing..."}</span>
        </div>

        {/* User Badge */}
        {currentUser ? (
          <div className="flex items-center space-x-2 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-md text-xs">
            <User className="w-3.5 h-3.5 text-cyan-400" />
            <span className="font-semibold text-slate-200">{currentUser.username}</span>
            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
              {currentUser.role}
            </span>
            <button
              onClick={onLogout}
              className="ml-2 text-[10px] text-slate-400 hover:text-rose-400 transition"
            >
              Sign out
            </button>
          </div>
        ) : (
          <div className="text-xs font-mono text-slate-400">Not authenticated</div>
        )}
      </div>
    </header>
  );
}
