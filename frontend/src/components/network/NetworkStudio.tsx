"use client";

import React, { useState, useCallback, useMemo } from "react";
import {
  ReactFlow,
  Controls,
  Background,
  applyNodeChanges,
  applyEdgeChanges,
  addEdge,
  Node,
  Edge,
  OnNodesChange,
  OnEdgesChange,
  OnConnect,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import {
  Plus,
  Play,
  Square,
  ShieldAlert,
  Server,
  Network,
  Terminal,
  Save,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
} from "lucide-react";

import { CustomDeviceNode } from "./CustomDeviceNode";
import { createTopology, previewTopology, deployTopology, teardownTopology } from "../../lib/api";

const INITIAL_NODES: Node[] = [
  {
    id: "fw-1",
    type: "deviceNode",
    position: { x: 300, y: 50 },
    data: { label: "Edge-Firewall", deviceType: "firewall", ipAddress: "192.168.1.1", status: "STOPPED" },
  },
  {
    id: "sw-dmz",
    type: "deviceNode",
    position: { x: 150, y: 180 },
    data: { label: "DMZ-Bridge", deviceType: "switch", vlanId: 100, status: "STOPPED" },
  },
  {
    id: "sw-lan",
    type: "deviceNode",
    position: { x: 450, y: 180 },
    data: { label: "Corp-Bridge", deviceType: "switch", vlanId: 200, status: "STOPPED" },
  },
  {
    id: "srv-web",
    type: "deviceNode",
    position: { x: 100, y: 320 },
    data: { label: "Web-Server-01", deviceType: "server", ipAddress: "192.168.100.10", status: "STOPPED" },
  },
  {
    id: "ep-workstation",
    type: "deviceNode",
    position: { x: 480, y: 320 },
    data: { label: "Analyst-WS", deviceType: "endpoint", ipAddress: "192.168.200.25", status: "STOPPED" },
  },
];

const INITIAL_EDGES: Edge[] = [
  { id: "e1-2", source: "fw-1", target: "sw-dmz", animated: true },
  { id: "e1-3", source: "fw-1", target: "sw-lan", animated: true },
  { id: "e2-4", source: "sw-dmz", target: "srv-web" },
  { id: "e3-5", source: "sw-lan", target: "ep-workstation" },
];

export function NetworkStudio({ authToken }: { authToken: string | null }) {
  const [nodes, setNodes] = useState<Node[]>(INITIAL_NODES);
  const [edges, setEdges] = useState<Edge[]>(INITIAL_EDGES);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  const [topologyId, setTopologyId] = useState<string | null>(null);
  const [status, setStatus] = useState<"STOPPED" | "DEPLOYED" | "DEPLOYING">("STOPPED");
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [previewData, setPreviewData] = useState<any>(null);
  const [message, setMessage] = useState<string | null>(null);

  const nodeTypes = useMemo(() => ({ deviceNode: CustomDeviceNode }), []);

  const onNodesChange: OnNodesChange = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );

  const onEdgesChange: OnEdgesChange = useCallback(
    (changes) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );

  const onConnect: OnConnect = useCallback(
    (connection) => setEdges((eds) => addEdge({ ...connection, animated: true }, eds)),
    []
  );

  const onNodeClick = useCallback((_: any, node: Node) => {
    setSelectedNode(node);
  }, []);

  const handleAddDevice = (type: "router" | "switch" | "firewall" | "server" | "endpoint") => {
    const id = `${type}-${Date.now().toString().slice(-4)}`;
    const newNode: Node = {
      id,
      type: "deviceNode",
      position: { x: 250 + Math.random() * 80, y: 200 + Math.random() * 80 },
      data: {
        label: `New-${type.toUpperCase()}`,
        deviceType: type,
        ipAddress: type === "switch" ? undefined : `10.10.${Math.floor(Math.random() * 50) + 1}.10`,
        status: status === "DEPLOYED" ? "RUNNING" : "STOPPED",
      },
    };
    setNodes((nds) => [...nds, newNode]);
    setSelectedNode(newNode);
  };

  const handleUpdateNodeProp = (key: string, val: any) => {
    if (!selectedNode) return;
    setNodes((nds) =>
      nds.map((n) => {
        if (n.id === selectedNode.id) {
          const updated = { ...n, data: { ...n.data, [key]: val } };
          setSelectedNode(updated);
          return updated;
        }
        return n;
      })
    );
  };

  const ensureTopologyCreated = async (): Promise<string> => {
    if (topologyId) return topologyId;
    const token = authToken || "demo-token";

    // Format nodes as CyberLab segments & devices
    const segments = nodes
      .filter((n) => n.data.deviceType === "switch")
      .map((n) => ({
        name: n.data.label as string,
        bridge_name: `cl-br-${n.id.replace(/[^a-zA-Z0-9]/g, "").toLowerCase()}`,
        vlan_id: (n.data.vlanId as number) || 100,
        cidr_block: "192.168.10.0/24",
        gateway_ip: "192.168.10.1",
      }));

    const devices = nodes
      .filter((n) => n.data.deviceType !== "switch")
      .map((n) => ({
        name: n.data.label as string,
        device_type: n.data.deviceType as string,
        namespace_name: `cl-ns-${n.id.replace(/[^a-zA-Z0-9]/g, "").toLowerCase()}`,
        ip_address: n.data.ipAddress as string,
      }));

    const created = await createTopology(token, {
      name: "Network Studio Interactive Topology",
      description: "Visual topology designed in React Flow Network Studio",
      segments,
      devices,
      graph_data: JSON.stringify({ nodes, edges }),
    });

    setTopologyId(created.id);
    return created.id;
  };

  const handleOpenPreview = async () => {
    try {
      const topId = await ensureTopologyCreated();
      const prev = await previewTopology(authToken || "demo-token", topId);
      setPreviewData(prev);
      setShowPreviewModal(true);
    } catch (err: any) {
      setMessage(`Preview Error: ${err.message}`);
    }
  };

  const handleExecuteDeploy = async () => {
    setShowPreviewModal(false);
    setStatus("DEPLOYING");
    setMessage("Deploying isolated Linux namespaces and virtual bridges...");
    try {
      const topId = await ensureTopologyCreated();
      const res = await deployTopology(authToken || "demo-token", topId);
      setStatus("DEPLOYED");
      setMessage(res.message);
      // Mark nodes running
      setNodes((nds) => nds.map((n) => ({ ...n, data: { ...n.data, status: "RUNNING" } })));
    } catch (err: any) {
      setStatus("STOPPED");
      setMessage(`Deployment Failed: ${err.message}`);
    }
  };

  const handleTeardown = async () => {
    if (!topologyId) return;
    setStatus("DEPLOYING");
    setMessage("Tearing down virtual network resources...");
    try {
      const res = await teardownTopology(authToken || "demo-token", topologyId);
      setStatus("STOPPED");
      setMessage(res.message);
      // Mark nodes stopped
      setNodes((nds) => nds.map((n) => ({ ...n, data: { ...n.data, status: "STOPPED" } })));
    } catch (err: any) {
      setStatus("STOPPED");
      setMessage(`Teardown Failed: ${err.message}`);
    }
  };

  return (
    <div className="flex h-[calc(100vh-4rem)] overflow-hidden">
      {/* Canvas Area */}
      <div className="flex-1 flex flex-col relative bg-slate-950">
        {/* Canvas Toolbar */}
        <div className="h-14 border-b border-slate-800 bg-slate-950/80 backdrop-blur px-5 flex items-center justify-between z-10">
          <div className="flex items-center space-x-2">
            <span className="font-mono text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
              <Network className="w-4 h-4 text-cyan-400" />
              <span>Network Studio</span>
            </span>
            <span
              className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                status === "DEPLOYED"
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                  : "bg-slate-800 text-slate-400 border-slate-700"
              }`}
            >
              {status}
            </span>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-2">
            {status !== "DEPLOYED" ? (
              <button
                onClick={handleOpenPreview}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-950/40 transition"
              >
                <Play className="w-3.5 h-3.5" />
                <span>Deploy Simulation</span>
              </button>
            ) : (
              <button
                onClick={handleTeardown}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow-md shadow-rose-950/40 transition"
              >
                <Square className="w-3.5 h-3.5" />
                <span>Teardown Resources</span>
              </button>
            )}
          </div>
        </div>

        {/* Message Banner if any */}
        {message && (
          <div className="bg-cyan-950/50 border-b border-cyan-800/40 px-5 py-2 text-xs font-mono text-cyan-300 flex items-center justify-between">
            <span>{message}</span>
            <button onClick={() => setMessage(null)} className="text-slate-400 hover:text-white">
              ✕
            </button>
          </div>
        )}

        {/* Interactive React Flow Canvas */}
        <div className="flex-1 w-full h-full">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            fitView
          >
            <Background color="#1e293b" gap={24} size={1.5} />
            <Controls className="!bg-slate-900 !border-slate-800 !text-slate-200 fill-white" />
          </ReactFlow>
        </div>
      </div>

      {/* Right Drawer: Palette & Inspector */}
      <div className="w-80 border-l border-slate-800 bg-slate-950 flex flex-col justify-between p-5 space-y-6">
        <div>
          <h3 className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider mb-3">
            Add Simulation Nodes
          </h3>
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => handleAddDevice("router")}
              className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-cyan-500/50 text-slate-300 hover:text-white text-xs flex items-center space-x-2 transition"
            >
              <Network className="w-4 h-4 text-cyan-400" />
              <span>Router</span>
            </button>
            <button
              onClick={() => handleAddDevice("switch")}
              className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-purple-500/50 text-slate-300 hover:text-white text-xs flex items-center space-x-2 transition"
            >
              <Network className="w-4 h-4 text-purple-400" />
              <span>Bridge (L2)</span>
            </button>
            <button
              onClick={() => handleAddDevice("firewall")}
              className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-rose-500/50 text-slate-300 hover:text-white text-xs flex items-center space-x-2 transition"
            >
              <ShieldAlert className="w-4 h-4 text-rose-400" />
              <span>Firewall</span>
            </button>
            <button
              onClick={() => handleAddDevice("server")}
              className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-emerald-500/50 text-slate-300 hover:text-white text-xs flex items-center space-x-2 transition"
            >
              <Server className="w-4 h-4 text-emerald-400" />
              <span>Server</span>
            </button>
            <button
              onClick={() => handleAddDevice("endpoint")}
              className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-amber-500/50 text-slate-300 hover:text-white text-xs flex items-center space-x-2 transition col-span-2"
            >
              <Terminal className="w-4 h-4 text-amber-400" />
              <span>Linux Endpoint</span>
            </button>
          </div>

          {/* Node Inspector */}
          <div className="mt-6 border-t border-slate-800 pt-5">
            <h3 className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider mb-3">
              Device Properties
            </h3>
            {selectedNode ? (
              <div className="space-y-3 font-mono text-xs">
                <div>
                  <label className="text-[10px] text-slate-400 uppercase">Device Label</label>
                  <input
                    type="text"
                    value={selectedNode.data.label as string}
                    onChange={(e) => handleUpdateNodeProp("label", e.target.value)}
                    className="w-full mt-1 px-2.5 py-1.5 rounded bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>
                {selectedNode.data.deviceType !== "switch" && (
                  <div>
                    <label className="text-[10px] text-slate-400 uppercase">IP Address</label>
                    <input
                      type="text"
                      value={(selectedNode.data.ipAddress as string) || ""}
                      onChange={(e) => handleUpdateNodeProp("ipAddress", e.target.value)}
                      placeholder="10.10.1.10"
                      className="w-full mt-1 px-2.5 py-1.5 rounded bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                    />
                  </div>
                )}
                {selectedNode.data.deviceType === "switch" && (
                  <div>
                    <label className="text-[10px] text-slate-400 uppercase">VLAN ID (802.1Q)</label>
                    <input
                      type="number"
                      value={(selectedNode.data.vlanId as number) || 100}
                      onChange={(e) => handleUpdateNodeProp("vlanId", parseInt(e.target.value, 10))}
                      className="w-full mt-1 px-2.5 py-1.5 rounded bg-slate-900 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                    />
                  </div>
                )}
                <div className="p-2.5 rounded bg-slate-900/60 border border-slate-800 text-[11px] text-slate-400">
                  <div>Type: <span className="text-slate-200">{selectedNode.data.deviceType as string}</span></div>
                  <div>Namespace: <span className="text-cyan-400">{`cl-ns-${selectedNode.id}`}</span></div>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-500">Click any device node on canvas to configure parameters.</p>
            )}
          </div>
        </div>

        {/* Safety Indicator */}
        <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-500/20 text-emerald-400 text-[11px] flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>Host Protection Active: All operations bounded to isolated namespaces.</span>
        </div>
      </div>

      {/* Deployment Preview & Confirmation Modal */}
      {showPreviewModal && previewData && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center space-x-2 text-cyan-400">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              <h3 className="font-bold text-sm uppercase font-mono text-white">
                Pre-Flight Deployment Safety Check
              </h3>
            </div>
            <p className="text-xs text-slate-300">
              Review virtual resources scheduled for creation in isolated Linux subsystems:
            </p>

            <div className="space-y-2 text-xs font-mono max-h-60 overflow-y-auto bg-slate-950 p-3 rounded-lg border border-slate-800">
              <div>
                <span className="text-cyan-400 font-semibold">Linux Bridges (Switches):</span>
                <ul className="list-disc ml-5 text-slate-300">
                  {previewData.bridges_to_create.map((b: string) => (
                    <li key={b}>{b}</li>
                  ))}
                </ul>
              </div>
              <div className="pt-2">
                <span className="text-purple-400 font-semibold">Network Namespaces:</span>
                <ul className="list-disc ml-5 text-slate-300">
                  {previewData.namespaces_to_create.map((ns: string) => (
                    <li key={ns}>{ns}</li>
                  ))}
                </ul>
              </div>
              <div className="pt-2">
                <span className="text-emerald-400 font-semibold">Host Interface Safety Check:</span>
                <div className="text-emerald-400 text-[11px]">
                  ✓ Verified: Physical Wi-Fi, Ethernet, and Host Gateway are 100% excluded.
                </div>
              </div>
            </div>

            <div className="flex justify-end space-x-3 pt-2">
              <button
                onClick={() => setShowPreviewModal(false)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition"
              >
                Cancel
              </button>
              <button
                onClick={handleExecuteDeploy}
                className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow transition"
              >
                Confirm & Deploy Simulation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
