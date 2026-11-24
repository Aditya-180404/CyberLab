import { HealthResponse, LoginResponse, AuditLogItem, UserProfile, VirtualMachineItem, VMDiscoveryResult } from "./types";

const BACKEND_BASE = "http://127.0.0.1:8000/api/v1";

export async function fetchSystemHealth(): Promise<HealthResponse> {
  const res = await fetch(`${BACKEND_BASE}/health`, { cache: "no-store" });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  return await res.json();
}

export async function loginUser(username: string, password: string): Promise<LoginResponse> {
  const res = await fetch(`${BACKEND_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Authentication failed (HTTP ${res.status})`);
  }
  return await res.json();
}

export async function fetchCurrentUser(token: string): Promise<UserProfile> {
  const res = await fetch(`${BACKEND_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to verify user session");
  return await res.json();
}

export async function fetchAuditLogs(token: string, limit = 10): Promise<AuditLogItem[]> {
  const res = await fetch(`${BACKEND_BASE}/audit?limit=${limit}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch audit records");
  return await res.json();
}

// Topology & Network API (Phase 2)
export async function fetchTopologies(token: string) {
  const res = await fetch(`${BACKEND_BASE}/topologies`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch topologies");
  return await res.json();
}

export async function createTopology(token: string, payload: any) {
  const res = await fetch(`${BACKEND_BASE}/topologies`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to create topology");
  }
  return await res.json();
}

export async function previewTopology(token: string, topologyId: string) {
  const res = await fetch(`${BACKEND_BASE}/topologies/${topologyId}/preview`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to generate deployment preview");
  }
  return await res.json();
}

export async function deployTopology(token: string, topologyId: string) {
  const res = await fetch(`${BACKEND_BASE}/topologies/${topologyId}/deploy`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Deployment failed");
  }
  return await res.json();
}

export async function teardownTopology(token: string, topologyId: string) {
  const res = await fetch(`${BACKEND_BASE}/topologies/${topologyId}/teardown`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Teardown failed");
  }
  return await res.json();
}

// Virtual Machine API (Phase 3)
export async function fetchVMs(token: string): Promise<VirtualMachineItem[]> {
  const res = await fetch(`${BACKEND_BASE}/vms`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch virtual machines");
  return await res.json();
}

export async function discoverVMs(token: string): Promise<VMDiscoveryResult> {
  const res = await fetch(`${BACKEND_BASE}/vms/discover`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to discover virtual machines");
  }
  return await res.json();
}

export async function powerVM(
  token: string,
  vmId: string,
  action: "start" | "stop" | "reset" | "suspend",
  mode: "soft" | "hard" = "soft"
): Promise<VirtualMachineItem> {
  const res = await fetch(`${BACKEND_BASE}/vms/${vmId}/power`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ action, mode }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Power action '${action}' failed`);
  }
  return await res.json();
}
