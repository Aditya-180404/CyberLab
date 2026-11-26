"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Radar,
  ShieldAlert,
  Plus,
  Trash2,
  RefreshCw,
  AlertTriangle,
  Crosshair,
  Radio,
  Zap,
  CheckCircle2,
  FileCode2,
} from "lucide-react";
import { ThreatIOCItem, DeceptionTrapItem } from "../../lib/types";
import {
  fetchThreatIOCs,
  createThreatIOC,
  deleteThreatIOC,
  fetchDeceptionTraps,
  triggerDeceptionTrap,
  ingestSyslogLines,
  ingestNDREvents,
} from "../../lib/api";

interface ThreatIntelDeceptionViewProps {
  authToken: string | null;
}

export function ThreatIntelDeceptionView({ authToken }: ThreatIntelDeceptionViewProps) {
  const [iocs, setIocs] = useState<ThreatIOCItem[]>([]);
  const [traps, setTraps] = useState<DeceptionTrapItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  // Add IOC Form
  const [iocType, setIocType] = useState<"IP" | "DOMAIN" | "SHA256">("IP");
  const [iocValue, setIocValue] = useState("");
  const [threatActor, setThreatActor] = useState("");
  const [severity, setSeverity] = useState<"HIGH" | "CRITICAL" | "MEDIUM" | "LOW">("HIGH");

  // Syslog / NDR Test Ingestor
  const [syslogInput, setSyslogInput] = useState(
    "filterlog: 42,,,1000000103,em0,match,block,in,4,0x0,,64,1234,0,none,6,tcp,60,198.51.100.50,10.0.0.10,44444,22,0,S"
  );

  const loadData = useCallback(async () => {
    if (!authToken) return;
    setLoading(true);
    try {
      const [iocList, trapList] = await Promise.all([
        fetchThreatIOCs(authToken),
        fetchDeceptionTraps(authToken),
      ]);
      setIocs(iocList);
      setTraps(trapList);
    } catch (err: any) {
      setStatusMsg(`Error loading Threat Intel: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, [authToken]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleAddIOC = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!authToken || !iocValue.trim()) return;
    try {
      await createThreatIOC(authToken, {
        ioc_type: iocType,
        value: iocValue.trim(),
        threat_actor: threatActor.trim() || "External Adversary",
        severity,
        source: "SOC-Analyst-Feed",
        confidence: 90,
      });
      setIocValue("");
      setThreatActor("");
      setStatusMsg("IOC added to live correlation feed.");
      await loadData();
    } catch (err: any) {
      setStatusMsg(`Error adding IOC: ${err.message}`);
    }
  };

  const handleDeleteIOC = async (id: string) => {
    if (!authToken) return;
    try {
      await deleteThreatIOC(authToken, id);
      await loadData();
    } catch (err: any) {
      setStatusMsg(`Error removing IOC: ${err.message}`);
    }
  };

  const handleTriggerTrap = async (trapId: string, name: string) => {
    if (!authToken) return;
    try {
      await triggerDeceptionTrap(authToken, trapId);
      setStatusMsg(`Canary trap '${name}' triggered! Critical SIEM alert generated.`);
      await loadData();
    } catch (err: any) {
      setStatusMsg(`Error triggering trap: ${err.message}`);
    }
  };

  const handleIngestSyslog = async () => {
    if (!authToken || !syslogInput.trim()) return;
    try {
      const lines = syslogInput.split("\n").map((l) => l.trim()).filter(Boolean);
      const res = await ingestSyslogLines(authToken, "opnsense-gw", lines);
      setStatusMsg(`Ingested ${res.length} syslog event(s) into SIEM + Threat Intel correlation.`);
      await loadData();
    } catch (err: any) {
      setStatusMsg(`Syslog ingestion failed: ${err.message}`);
    }
  };

  const handleSimulateSuricataNDR = async () => {
    if (!authToken) return;
    try {
      const res = await ingestNDREvents(authToken, "suricata", [
        {
          event_type: "alert",
          host: "opnsense-suricata-em0",
          src_ip: "198.51.100.50",
          dest_ip: "10.0.0.15",
          dest_port: 445,
          alert: { signature: "ET EXPLOIT SMBv1 EternalBlue Probe", severity: 1 },
        },
      ]);
      setStatusMsg(`Suricata NDR event ingested (${res.length} event) and correlated in SIEM.`);
      await loadData();
    } catch (err: any) {
      setStatusMsg(`NDR ingestion failed: ${err.message}`);
    }
  };

  if (!authToken) {
    return (
      <div className="p-8 max-w-4xl mx-auto">
        <div className="rounded-xl border border-amber-500/30 bg-amber-950/20 p-6 text-center">
          <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto mb-2" />
          <h2 className="text-sm font-semibold text-amber-200">Authentication Required</h2>
          <p className="text-xs text-amber-400/80 mt-1">
            Sign in on the SOC Dashboard to manage Threat Intelligence IOCs, Honeypot Traps, and NDR Log Ingestion.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto w-full">
      {/* Header */}
      <div className="rounded-xl border border-slate-800 bg-gradient-to-r from-slate-950 via-slate-900 to-rose-950/25 p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Radar className="w-5 h-5 text-rose-400" />
            <h1 className="text-xl font-bold text-white tracking-tight">
              Threat Intelligence (TIP), Deception &amp; NDR Ingestion
            </h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
              TIP + NDR ACTIVE
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Manage IOC feeds (MISP/OTX style IPs, domains, hashes), deploy decoy deception traps, and ingest OPNsense syslog / Suricata EVE NDR streams into SIEM correlation.
          </p>
        </div>
        <button
          onClick={loadData}
          disabled={loading}
          className="px-3.5 py-2 rounded-lg border border-slate-700 bg-slate-900 hover:bg-slate-800 text-xs text-slate-200 flex items-center space-x-1.5"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-cyan-400" : ""}`} />
          <span>Refresh</span>
        </button>
      </div>

      {statusMsg && (
        <div className="p-3 rounded-lg border border-cyan-500/30 bg-cyan-950/30 text-cyan-300 text-xs flex items-center justify-between font-mono">
          <span>{statusMsg}</span>
          <button onClick={() => setStatusMsg(null)} className="text-slate-400 hover:text-white">✕</button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Threat IOCs Panel */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200 flex items-center space-x-2">
              <ShieldAlert className="w-4 h-4 text-rose-400" />
              <span>Active Threat Intelligence IOCs ({iocs.length})</span>
            </h2>
          </div>

          <form onSubmit={handleAddIOC} className="grid grid-cols-12 gap-2 text-xs">
            <select
              value={iocType}
              onChange={(e) => setIocType(e.target.value as any)}
              className="col-span-3 bg-slate-950 border border-slate-800 rounded-lg px-2 py-1.5 text-slate-200"
            >
              <option value="IP">IP</option>
              <option value="DOMAIN">DOMAIN</option>
              <option value="SHA256">SHA256</option>
            </select>
            <input
              type="text"
              required
              placeholder="e.g. 198.51.100.99"
              value={iocValue}
              onChange={(e) => setIocValue(e.target.value)}
              className="col-span-5 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-200"
            />
            <input
              type="text"
              placeholder="Actor / Campaign"
              value={threatActor}
              onChange={(e) => setThreatActor(e.target.value)}
              className="col-span-4 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-200"
            />
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value as any)}
              className="col-span-4 bg-slate-950 border border-slate-800 rounded-lg px-2 py-1.5 text-slate-200"
            >
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
            </select>
            <button
              type="submit"
              className="col-span-8 flex items-center justify-center space-x-1.5 bg-rose-600 hover:bg-rose-500 text-white font-semibold rounded-lg py-1.5 transition"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Threat Indicator</span>
            </button>
          </form>

          <div className="space-y-2 max-h-80 overflow-y-auto">
            {iocs.map((ioc) => (
              <div key={ioc.id} className="p-3 rounded-lg bg-slate-950/70 border border-slate-800 flex items-center justify-between text-xs font-mono">
                <div className="min-w-0">
                  <div className="flex items-center space-x-2">
                    <span className="px-1.5 py-0.5 rounded bg-slate-800 text-cyan-300 text-[10px]">{ioc.ioc_type}</span>
                    <span className="text-white font-semibold truncate">{ioc.value}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded border ${
                      ioc.severity === "CRITICAL" ? "bg-rose-500/10 text-rose-400 border-rose-500/30" : "bg-amber-500/10 text-amber-400 border-amber-500/30"
                    }`}>{ioc.severity}</span>
                  </div>
                  <div className="text-[10px] text-slate-400 mt-1">
                    {ioc.threat_actor} • {ioc.source} • Hits: <span className="text-rose-400 font-bold">{ioc.hit_count}</span>
                  </div>
                </div>
                <button
                  onClick={() => handleDeleteIOC(ioc.id)}
                  className="text-slate-500 hover:text-rose-400 p-1 ml-2"
                  title="Remove IOC"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Deception / Honeypot Traps & NDR Ingestion */}
        <div className="space-y-6">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
            <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200 flex items-center space-x-2 border-b border-slate-800 pb-3">
              <Crosshair className="w-4 h-4 text-amber-400" />
              <span>Deception &amp; Canary Traps ({traps.length})</span>
            </h2>
            <div className="space-y-2.5">
              {traps.map((trap) => (
                <div key={trap.id} className="p-3 rounded-lg bg-slate-950/70 border border-slate-800 flex items-center justify-between text-xs">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-slate-100">{trap.name}</span>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                        {trap.trap_type}
                      </span>
                    </div>
                    <div className="text-[11px] font-mono text-cyan-400 mt-0.5">{trap.target_indicator}</div>
                    <div className="text-[10px] text-slate-400 mt-0.5">
                      Triggers: <span className="font-mono text-amber-300">{trap.triggered_count}</span>
                    </div>
                  </div>
                  <button
                    onClick={() => handleTriggerTrap(trap.id, trap.name)}
                    className="px-2.5 py-1.5 rounded-lg bg-amber-600/20 hover:bg-amber-600/30 border border-amber-500/30 text-amber-300 text-[11px] font-mono flex items-center space-x-1 shrink-0"
                  >
                    <Zap className="w-3 h-3" />
                    <span>Test Canary</span>
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
            <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200 flex items-center space-x-2 border-b border-slate-800 pb-3">
              <FileCode2 className="w-4 h-4 text-cyan-400" />
              <span>Syslog &amp; Suricata / Zeek NDR Pipeline</span>
            </h2>
            <p className="text-[11px] text-slate-400">
              Send raw OPNsense <code className="text-slate-300">filterlog</code>, <code className="text-slate-300">sshd</code>, or Suricata EVE alerts directly into SIEM &amp; Threat Intel matching (UDP Syslog listener port <code className="text-cyan-400">5514</code> when enabled).
            </p>
            <textarea
              rows={3}
              value={syslogInput}
              onChange={(e) => setSyslogInput(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 font-mono text-[11px] text-slate-200 focus:outline-none focus:border-cyan-500"
            />
            <div className="flex items-center space-x-2">
              <button
                onClick={handleIngestSyslog}
                className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold flex items-center space-x-1.5"
              >
                <Radio className="w-3.5 h-3.5" />
                <span>Ingest Syslog Line</span>
              </button>
              <button
                onClick={handleSimulateSuricataNDR}
                className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center space-x-1.5"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Ingest Suricata EVE Alert</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
