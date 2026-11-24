export interface PlatformMetrics {
  os: string;
  kernel: string;
  python: string;
  cpu_usage_pct: number;
  memory_total_gb: number;
  memory_used_gb: number;
  memory_usage_pct: number;
  disk_total_gb: number;
  disk_free_gb: number;
  disk_usage_pct: number;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  project_name: string;
  tagline: string;
  database: string;
  platform: PlatformMetrics;
  checks: Record<string, boolean>;
}

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  role: string;
  organization_id?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in_minutes: number;
  user: UserProfile;
}

export interface AuditLogItem {
  id: string;
  user_id?: string;
  username: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  status: string;
  ip_address?: string;
  details?: string;
  created_at: string;
}

// VM Integration Types (Phase 3)
export interface VMNetworkAdapter {
  name: string;
  connection_type: string;
  vnet?: string;
  mac_address?: string;
  virtual_dev?: string;
  is_bridged: boolean;
}

export interface VirtualMachineItem {
  id: string;
  organization_id: string;
  name: string;
  hypervisor_type: string;
  config_path: string;
  power_state: "RUNNING" | "STOPPED" | "SUSPENDED" | "UNKNOWN";
  os_type: string;
  vcpus: number;
  memory_mb: number;
  network_adapters: VMNetworkAdapter[];
  attached_segment_id?: string;
  is_vulnerable_target: boolean;
  safety_warning?: string;
  created_at: string;
  updated_at: string;
}

export interface VMDiscoveryResult {
  discovered_count: number;
  registered_vms: VirtualMachineItem[];
  scanned_paths: string[];
}

// Distributed Linux Agent Types (Phase 4)
export interface AgentHardwareSpecs {
  cpu_cores?: number;
  memory_mb?: number;
  disk_total_gb?: number;
}

export interface AgentItem {
  id: string;
  organization_id: string;
  hostname: string;
  ip_address: string;
  os_type: string;
  os_release: string;
  kernel_version: string;
  agent_version: string;
  status: "ONLINE" | "OFFLINE" | "ISOLATED" | "REVOKED";
  last_heartbeat: string;
  heartbeat_interval_sec: number;
  hardware_specs?: AgentHardwareSpecs;
  created_at: string;
  updated_at: string;
}

export interface AgentLatestTelemetry {
  timestamp: string;
  cpu_pct: number;
  memory_pct: number;
  disk_pct: number;
  network_connections: Array<{
    protocol: string;
    local_port: number;
    remote_ip?: string;
    remote_port?: number;
    state?: string;
  }>;
  processes_count: number;
  fim_alerts: Array<{
    path: string;
    action: string;
    severity: string;
    message: string;
  }>;
}

export interface AgentDetailItem extends AgentItem {
  pending_commands: string[];
  latest_telemetry?: AgentLatestTelemetry;
}

// Unified Asset Inventory Types (Phase 5)
export interface AssetServiceItem {
  port: number;
  protocol: string;
  service?: string;
  state: string;
}

export interface AssetItem {
  id: string;
  organization_id: string;
  site_id?: string;
  name: string;
  asset_type: "VIRTUAL_MACHINE" | "AGENT_HOST" | "SIMULATED_DEVICE" | "PHYSICAL_HOST";
  ip_addresses: string[];
  mac_addresses: string[];
  os_family: string;
  os_version: string;
  kernel_version?: string;
  criticality: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  risk_score: number;
  exposure: "INTERNAL" | "ISOLATED" | "DMZ" | "PUBLIC";
  status: "ACTIVE" | "INACTIVE" | "QUARANTINED" | "DECOMMISSIONED";
  virtual_machine_id?: string;
  agent_id?: string;
  network_device_id?: string;
  hardware_specs?: Record<string, any>;
  services?: AssetServiceItem[];
  software_inventory?: Array<Record<string, any>>;
  security_tags: string[];
  last_seen: string;
  created_at: string;
  updated_at: string;
}

export interface AssetDetailItem extends AssetItem {
  vm_details?: Record<string, any>;
  agent_details?: Record<string, any>;
  device_details?: Record<string, any>;
}

export interface AssetSyncResult {
  total_synced: number;
  vm_assets_synced: number;
  agent_assets_synced: number;
  simulated_assets_synced: number;
  message: string;
}

export interface AssetKPIs {
  total_assets: number;
  average_risk_score: number;
  high_risk_count: number;
  critical_assets_count: number;
  by_type: Record<string, number>;
  by_criticality: Record<string, number>;
}

// SIEM & MITRE ATT&CK Types (Phase 6)
export interface SecurityEventItem {
  id: string;
  organization_id: string;
  timestamp: string;
  category: string;
  severity: string;
  action: string;
  message: string;
  asset_id?: string;
  hostname?: string;
  source_ip?: string;
  destination_ip?: string;
  mitre_tactic?: string;
  mitre_technique_id?: string;
  mitre_technique_name?: string;
  raw_data?: Record<string, any>;
}

export interface SecurityAlertItem {
  id: string;
  organization_id: string;
  rule_id: string;
  title: string;
  description: string;
  severity: string;
  status: string;
  asset_id?: string;
  hostname?: string;
  source_ip?: string;
  mitre_tactic?: string;
  mitre_technique_id?: string;
  mitre_technique_name?: string;
  evidence_count: number;
  first_seen: string;
  last_seen: string;
  incident_id?: string;
  details?: Record<string, any>;
}

export interface SecurityIncidentItem {
  id: string;
  organization_id: string;
  title: string;
  severity: string;
  status: string;
  primary_hostname?: string;
  alert_count: number;
  mitre_tactics: string[];
  mitre_techniques: string[];
  summary?: string;
  created_at: string;
  updated_at: string;
}

export interface MitreTechniqueCountItem {
  technique_id: string;
  technique_name: string;
  tactic: string;
  event_count: number;
  alert_count: number;
  last_seen?: string;
}

export interface MitreMatrixSummaryItem {
  total_techniques_mapped: number;
  active_techniques_triggered: number;
  tactics: Record<string, MitreTechniqueCountItem[]>;
}

export interface SIEMKPIsItem {
  total_events: number;
  total_alerts: number;
  open_alerts: number;
  active_incidents: number;
  by_severity: Record<string, number>;
  by_category: Record<string, number>;
}

// SOAR & Incident Response Types (Phase 7)
export interface SOARPlaybookItem {
  id: string;
  organization_id: string;
  name: string;
  description: string;
  trigger_event: string;
  requires_approval: boolean;
  action_type: string;
  is_enabled: boolean;
  created_at: string;
}

export interface SOARActionItem {
  id: string;
  organization_id: string;
  playbook_id?: string;
  action_type: string;
  status: "PENDING_APPROVAL" | "APPROVED" | "REJECTED" | "EXECUTING" | "COMPLETED" | "FAILED" | "ROLLED_BACK";
  target_type: string;
  target_id: string;
  target_name?: string;
  incident_id?: string;
  requested_by: string;
  approved_by?: string;
  rejection_reason?: string;
  executed_at?: string;
  verified: boolean;
  verification_details?: string;
  rollback_supported: boolean;
  is_rolled_back: boolean;
  rollback_details?: string;
  parameters?: Record<string, any>;
  output_log?: string;
  created_at: string;
  updated_at: string;
}

export interface SOARKPIsItem {
  total_actions: number;
  pending_approval: number;
  completed_actions: number;
  failed_actions: number;
  rolled_back: number;
  by_type: Record<string, number>;
}
