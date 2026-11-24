import { HealthResponse, LoginResponse, AuditLogItem, UserProfile } from "./types";

const BACKEND_BASE = "http://127.0.0.1:8000/api/v1";

export async function fetchSystemHealth(): Promise<HealthResponse> {
  try {
    const res = await fetch(`${BACKEND_BASE}/health`, {
      cache: "no-store",
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  } catch (err: any) {
    // Fallback to client proxy if direct port 8000 fails
    const proxyRes = await fetch("/api/backend/health", { cache: "no-store" });
    if (!proxyRes.ok) throw err;
    return await proxyRes.json();
  }
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
  if (!res.ok) {
    throw new Error("Failed to verify user session");
  }
  return await res.json();
}

export async function fetchAuditLogs(token: string, limit = 10): Promise<AuditLogItem[]> {
  const res = await fetch(`${BACKEND_BASE}/audit?limit=${limit}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new Error("Failed to fetch audit records");
  }
  return await res.json();
}
