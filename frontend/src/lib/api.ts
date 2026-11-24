import {
  HealthResponse,
  LoginResponse,
  AuditLogItem,
  UserProfile,
  VirtualMachineItem,
  VMDiscoveryResult,
  AgentItem,
  AgentDetailItem,
  AssetItem,
  AssetDetailItem,
  AssetSyncResult,
  AssetKPIs,
  SecurityEventItem,
  SecurityAlertItem,
  SecurityIncidentItem,
  MitreMatrixSummaryItem,
  SIEMKPIsItem,
  SOARPlaybookItem,
  SOARActionItem,
  SOARKPIsItem,
  DigitalTwinGraphResponse,
  AttackPathRequest,
  AttackPathResponse,
  BlastRadiusResponse,
  ChokePointResponse,
  SimulationScenarioItem,
  SimulationExecutionItem,
  RunCampaignResponse,
  MitreCoverageResponse,
  PurpleTeamKPIsItem,
  VulnerabilityItem,
  AssetVulnerabilityItem,
  AssetVulnerabilitySummary,
  ScanResultResponse,
  VulnerabilityKPIsItem,
} from "./types";

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

// Distributed Linux Agent API (Phase 4)
export async function fetchAgents(token: string): Promise<AgentItem[]> {
  const res = await fetch(`${BACKEND_BASE}/agents`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch agent fleet");
  return await res.json();
}

export async function fetchAgentDetail(token: string, agentId: string): Promise<AgentDetailItem> {
  const res = await fetch(`${BACKEND_BASE}/agents/${agentId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch agent details");
  return await res.json();
}

export async function isolateAgent(token: string, agentId: string): Promise<AgentItem> {
  const res = await fetch(`${BACKEND_BASE}/agents/${agentId}/isolate`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to isolate agent");
  }
  return await res.json();
}

export async function restoreAgent(token: string, agentId: string): Promise<AgentItem> {
  const res = await fetch(`${BACKEND_BASE}/agents/${agentId}/restore`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to restore agent");
  }
  return await res.json();
}

export async function revokeAgent(token: string, agentId: string): Promise<AgentItem> {
  const res = await fetch(`${BACKEND_BASE}/agents/${agentId}/revoke`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to revoke agent");
  }
  return await res.json();
}

// Unified Asset Inventory API (Phase 5)
export async function fetchAssets(
  token: string,
  params?: { asset_type?: string; criticality?: string; min_risk?: number; search?: string }
): Promise<AssetItem[]> {
  const query = new URLSearchParams();
  if (params?.asset_type && params.asset_type !== "ALL") query.set("asset_type", params.asset_type);
  if (params?.criticality && params.criticality !== "ALL") query.set("criticality", params.criticality);
  if (params?.min_risk) query.set("min_risk", params.min_risk.toString());
  if (params?.search) query.set("search", params.search);

  const res = await fetch(`${BACKEND_BASE}/assets?${query.toString()}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch assets");
  return await res.json();
}

export async function fetchAssetKPIs(token: string): Promise<AssetKPIs> {
  const res = await fetch(`${BACKEND_BASE}/assets/kpis`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch asset KPIs");
  return await res.json();
}

export async function syncAssets(token: string): Promise<AssetSyncResult> {
  const res = await fetch(`${BACKEND_BASE}/assets/sync`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to synchronize assets");
  }
  return await res.json();
}

export async function fetchAssetDetail(token: string, assetId: string): Promise<AssetDetailItem> {
  const res = await fetch(`${BACKEND_BASE}/assets/${assetId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch asset details");
  return await res.json();
}

export async function updateAssetCriticality(
  token: string,
  assetId: string,
  criticality: string,
  exposure?: string
): Promise<AssetItem> {
  const res = await fetch(`${BACKEND_BASE}/assets/${assetId}/criticality`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ criticality, exposure }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to update asset criticality");
  }
  return await res.json();
}

// SIEM & MITRE ATT&CK API (Phase 6)
export async function fetchSecurityEvents(
  token: string,
  params?: { category?: string; severity?: string; hostname?: string; search?: string; limit?: number }
): Promise<SecurityEventItem[]> {
  const query = new URLSearchParams();
  if (params?.category && params.category !== "ALL") query.set("category", params.category);
  if (params?.severity && params.severity !== "ALL") query.set("severity", params.severity);
  if (params?.hostname) query.set("hostname", params.hostname);
  if (params?.search) query.set("search", params.search);
  if (params?.limit) query.set("limit", params.limit.toString());

  const res = await fetch(`${BACKEND_BASE}/siem/events?${query.toString()}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch security events");
  return await res.json();
}

export async function fetchSecurityAlerts(token: string): Promise<SecurityAlertItem[]> {
  const res = await fetch(`${BACKEND_BASE}/siem/alerts`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch security alerts");
  return await res.json();
}

export async function fetchSecurityIncidents(token: string): Promise<SecurityIncidentItem[]> {
  const res = await fetch(`${BACKEND_BASE}/siem/incidents`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch security incidents");
  return await res.json();
}

export async function fetchMitreMatrix(token: string): Promise<MitreMatrixSummaryItem> {
  const res = await fetch(`${BACKEND_BASE}/siem/mitre`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch MITRE matrix");
  return await res.json();
}

export async function fetchSIEMKPIs(token: string): Promise<SIEMKPIsItem> {
  const res = await fetch(`${BACKEND_BASE}/siem/kpis`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch SIEM KPIs");
  return await res.json();
}

export async function simulateAttackScenario(
  token: string,
  scenario: string,
  target_hostname = "metasploitable2",
  target_ip = "192.168.1.120"
): Promise<SecurityEventItem[]> {
  const res = await fetch(`${BACKEND_BASE}/siem/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ scenario, target_hostname, target_ip }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Attack simulation failed");
  }
  return await res.json();
}

// SOAR & Incident Response API (Phase 7)
export async function fetchSOARPlaybooks(token: string): Promise<SOARPlaybookItem[]> {
  const res = await fetch(`${BACKEND_BASE}/soar/playbooks`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch SOAR playbooks");
  return await res.json();
}

export async function executeSOARPlaybook(
  token: string,
  playbookId: string,
  payload: { target_id: string; target_name?: string; target_type?: string; action_type: string; incident_id?: string }
): Promise<SOARActionItem> {
  const res = await fetch(`${BACKEND_BASE}/soar/playbooks/${playbookId}/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Playbook execution failed");
  }
  return await res.json();
}

export async function fetchSOARActions(
  token: string,
  params?: { status?: string; action_type?: string }
): Promise<SOARActionItem[]> {
  const query = new URLSearchParams();
  if (params?.status && params.status !== "ALL") query.set("status", params.status);
  if (params?.action_type) query.set("action_type", params.action_type);

  const res = await fetch(`${BACKEND_BASE}/soar/actions?${query.toString()}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch SOAR actions");
  return await res.json();
}

export async function approveSOARAction(token: string, actionId: string): Promise<SOARActionItem> {
  const res = await fetch(`${BACKEND_BASE}/soar/actions/${actionId}/approve`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Action approval failed");
  }
  return await res.json();
}

export async function rejectSOARAction(token: string, actionId: string, reason?: string): Promise<SOARActionItem> {
  const res = await fetch(`${BACKEND_BASE}/soar/actions/${actionId}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ reason }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Action rejection failed");
  }
  return await res.json();
}

export async function rollbackSOARAction(token: string, actionId: string): Promise<SOARActionItem> {
  const res = await fetch(`${BACKEND_BASE}/soar/actions/${actionId}/rollback`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Rollback failed");
  }
  return await res.json();
}

export async function fetchSOARKPIs(token: string): Promise<SOARKPIsItem> {
  const res = await fetch(`${BACKEND_BASE}/soar/kpis`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch SOAR KPIs");
  return await res.json();
}

// Digital Twin & Attack Path API (Phase 8)
export async function fetchDigitalTwinGraph(token: string): Promise<DigitalTwinGraphResponse> {
  const res = await fetch(`${BACKEND_BASE}/digital-twin/graph`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch Digital Twin graph");
  return await res.json();
}

export async function discoverAttackPaths(token: string, payload: AttackPathRequest): Promise<AttackPathResponse> {
  const res = await fetch(`${BACKEND_BASE}/digital-twin/attack-paths`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Attack path discovery failed");
  }
  return await res.json();
}

export async function fetchAssetBlastRadius(token: string, assetId: string): Promise<BlastRadiusResponse> {
  const res = await fetch(`${BACKEND_BASE}/digital-twin/blast-radius/${assetId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to calculate blast radius");
  }
  return await res.json();
}

export async function fetchDefensiveChokePoints(token: string): Promise<ChokePointResponse> {
  const res = await fetch(`${BACKEND_BASE}/digital-twin/choke-points`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch defensive choke points");
  return await res.json();
}

export async function simulateNodeCompromise(token: string, nodeId: string, compromised: boolean) {
  const res = await fetch(`${BACKEND_BASE}/digital-twin/simulate-compromise`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ node_id: nodeId, compromised }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Compromise simulation failed");
  }
  return await res.json();
}

export async function resetDigitalTwinSimulation(token: string) {
  const res = await fetch(`${BACKEND_BASE}/digital-twin/reset-simulation`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Simulation reset failed");
  return await res.json();
}

// Purple-Team & Attack Simulation API (Phase 9)
export async function fetchSimulationScenarios(token: string, tactic?: string): Promise<SimulationScenarioItem[]> {
  const url = tactic
    ? `${BACKEND_BASE}/purple-team/scenarios?tactic=${encodeURIComponent(tactic)}`
    : `${BACKEND_BASE}/purple-team/scenarios`;
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch simulation scenarios");
  return await res.json();
}

export async function executeSimulationScenario(
  token: string,
  scenarioId: string,
  targetAssetId?: string
): Promise<SimulationExecutionItem> {
  const res = await fetch(`${BACKEND_BASE}/purple-team/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ scenario_id: scenarioId, target_asset_id: targetAssetId }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Scenario execution failed");
  }
  return await res.json();
}

export async function runPurpleTeamCampaign(
  token: string,
  targetAssetId?: string,
  tacticFilter?: string
): Promise<RunCampaignResponse> {
  const res = await fetch(`${BACKEND_BASE}/purple-team/run-campaign`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ target_asset_id: targetAssetId, tactic_filter: tacticFilter }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Campaign execution failed");
  }
  return await res.json();
}

export async function fetchSimulationExecutions(token: string, limit = 25): Promise<SimulationExecutionItem[]> {
  const res = await fetch(`${BACKEND_BASE}/purple-team/executions?limit=${limit}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch simulation executions");
  return await res.json();
}

export async function fetchMitreCoverage(token: string): Promise<MitreCoverageResponse> {
  const res = await fetch(`${BACKEND_BASE}/purple-team/coverage`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch MITRE coverage");
  return await res.json();
}

export async function fetchPurpleTeamKPIs(token: string): Promise<PurpleTeamKPIsItem> {
  const res = await fetch(`${BACKEND_BASE}/purple-team/kpis`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch Purple-Team KPIs");
  return await res.json();
}

// Vulnerability Management & CVE API (Phase 11)
export async function fetchVulnerabilityCatalog(
  token: string,
  search?: string,
  severity?: string
): Promise<VulnerabilityItem[]> {
  const query = new URLSearchParams();
  if (search) query.set("search", search);
  if (severity && severity !== "ALL") query.set("severity", severity);

  const res = await fetch(`${BACKEND_BASE}/vulnerabilities?${query.toString()}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch vulnerability catalog");
  return await res.json();
}

export async function fetchFleetVulnerabilitySummary(token: string): Promise<AssetVulnerabilitySummary[]> {
  const res = await fetch(`${BACKEND_BASE}/vulnerabilities/summary`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch fleet vulnerability summary");
  return await res.json();
}

export async function runVulnerabilityScan(token: string, assetId?: string): Promise<ScanResultResponse> {
  const res = await fetch(`${BACKEND_BASE}/vulnerabilities/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ asset_id: assetId }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Vulnerability scan failed");
  }
  return await res.json();
}

export async function fetchAssetVulnerabilities(token: string, assetId: string): Promise<AssetVulnerabilityItem[]> {
  const res = await fetch(`${BACKEND_BASE}/vulnerabilities/assets/${assetId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch asset vulnerabilities");
  return await res.json();
}

export async function remediateVulnerability(
  token: string,
  assetVulnId: string,
  status: string,
  notes?: string
): Promise<AssetVulnerabilityItem> {
  const res = await fetch(`${BACKEND_BASE}/vulnerabilities/remediate`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ asset_vulnerability_id: assetVulnId, status, notes }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Remediation update failed");
  }
  return await res.json();
}

export async function fetchVulnerabilityKPIs(token: string): Promise<VulnerabilityKPIsItem> {
  const res = await fetch(`${BACKEND_BASE}/vulnerabilities/kpis`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch vulnerability KPIs");
  return await res.json();
}



