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

// Digital Twin & Attack-Path Analysis Types (Phase 8)
export interface DigitalTwinNode {
  id: string;
  label: string;
  node_type: "ASSET" | "DEVICE" | "SEGMENT" | "ADVERSARY";
  asset_type?: string;
  device_type?: string;
  ip_addresses: string[];
  zone: "EXTERNAL" | "DMZ" | "INTERNAL" | "SECURE_VAULT" | "TRANSIT_ROUTER";
  criticality: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  risk_score: number;
  is_compromised: boolean;
  status: string;
  services?: Array<{ port: number; service: string }>;
  security_tags?: string[];
  position?: { x: number; y: number };
}

export interface DigitalTwinEdge {
  id: string;
  source: string;
  target: string;
  protocol: string;
  ports: number[];
  status: "OPEN" | "RESTRICTED" | "BLOCKED";
  weight: number;
  label?: string;
}

export interface DigitalTwinGraphSummary {
  total_nodes: number;
  total_edges: number;
  compromised_nodes: number;
  critical_nodes: number;
  average_risk_score: number;
  choke_points_count: number;
  generated_at: string;
}

export interface DigitalTwinGraphResponse {
  nodes: DigitalTwinNode[];
  edges: DigitalTwinEdge[];
  summary: DigitalTwinGraphSummary;
}

export interface AttackPathStep {
  hop_number: number;
  source_node_id: string;
  source_label: string;
  target_node_id: string;
  target_label: string;
  technique_id: string;
  technique_name: string;
  tactic: string;
  protocol: string;
  port?: number;
  risk_weight: number;
  description: string;
}

export interface AttackPathItem {
  path_id: string;
  node_sequence: string[];
  node_labels: string[];
  hops: number;
  cumulative_risk: number;
  viability: "HIGH" | "MEDIUM" | "LOW";
  steps: AttackPathStep[];
  choke_point_node_ids: string[];
  mitigation_summary: string;
}

export interface AttackPathRequest {
  source_node_id: string;
  target_node_id: string;
  max_hops?: number;
}

export interface AttackPathResponse {
  source_node_id: string;
  target_node_id: string;
  total_paths_found: number;
  shortest_path_hops: number;
  recommended_choke_point?: string;
  paths: AttackPathItem[];
}

export interface ReachableAssetDetail {
  node_id: string;
  label: string;
  node_type: string;
  zone: string;
  criticality: string;
  risk_score: number;
  hops_away: number;
  impact_summary: string;
}

export interface BlastRadiusResponse {
  node_id: string;
  node_label: string;
  blast_score: number;
  total_reachable_nodes: number;
  reachable_by_criticality: Record<string, number>;
  reachable_by_zone: Record<string, number>;
  reachable_assets: ReachableAssetDetail[];
  containment_recommendation: string;
  playbook_to_execute?: string;
}

export interface ChokePointItem {
  node_id: string;
  label: string;
  node_type: string;
  zone: string;
  betweenness_centrality: number;
  paths_intercepted_pct: number;
  critical_assets_shielded: number;
  risk_level: string;
  recommendation: string;
  suggested_action: string;
}

export interface ChokePointResponse {
  choke_points: ChokePointItem[];
  top_recommended_node_id?: string;
  summary: string;
}

// Purple-Team Validation & Attack Simulation Types (Phase 9)
export interface SimulationScenarioItem {
  id: string;
  name: string;
  mitre_tactic: string;
  mitre_technique_id: string;
  mitre_technique_name: string;
  description: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  safe_payload_type: string;
  command_template?: string;
  expected_detection_rule?: string;
  is_atomic: boolean;
  created_at: string;
}

export interface ValidationResultItem {
  id: string;
  execution_id: string;
  detection_status: "DETECTED" | "MISSED" | "BLOCKED" | "PENDING_VERIFICATION";
  matched_alert_id?: string;
  matched_rule_id?: string;
  detection_latency_seconds: number;
  verification_details?: string;
  created_at: string;
}

export interface SimulationExecutionItem {
  id: string;
  organization_id: string;
  scenario_id: string;
  scenario_name?: string;
  mitre_technique_id?: string;
  mitre_tactic?: string;
  target_asset_id?: string;
  target_name?: string;
  executed_by: string;
  status: "SCHEDULED" | "RUNNING" | "COMPLETED" | "FAILED";
  executed_at: string;
  completed_at: string;
  execution_log?: string;
  validation_result?: ValidationResultItem;
}

export interface RunCampaignResponse {
  campaign_id: string;
  total_scenarios_executed: number;
  detected_count: number;
  missed_count: number;
  efficacy_rate_pct: number;
  executions: SimulationExecutionItem[];
}

export interface MitreCoverageItem {
  tactic: string;
  technique_id: string;
  technique_name: string;
  total_simulated: number;
  detected_count: number;
  coverage_status: "COVERED" | "PARTIAL" | "GAP";
  detection_efficacy_pct: number;
  rule_name?: string;
}

export interface MitreCoverageResponse {
  total_techniques_tested: number;
  covered_techniques: number;
  gap_techniques: number;
  overall_coverage_pct: number;
  coverage_items: MitreCoverageItem[];
}

export interface PurpleTeamKPIsItem {
  total_simulations: number;
  total_detected: number;
  total_missed: number;
  overall_efficacy_rate: number;
  mean_time_to_detect_seconds: number;
  by_tactic_efficacy: Record<string, number>;
}

// Vulnerability Management & Risk Engine Types (Phase 11)
export interface VulnerabilityItem {
  id: string;
  cve_id: string;
  title: string;
  description: string;
  cvss_score: number;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  affected_product: string;
  affected_versions?: string;
  port_hint?: number;
  cwe_id?: string;
  remediation_advisory?: string;
  created_at: string;
}

export interface AssetVulnerabilityItem {
  id: string;
  asset_id: string;
  asset_name?: string;
  vulnerability_id: string;
  cve_id: string;
  title: string;
  cvss_score: number;
  severity: string;
  status: "OPEN" | "IN_REMEDIATION" | "MITIGATED" | "ACCEPTED_RISK";
  detected_service?: string;
  discovered_at: string;
  remediated_at?: string;
  remediation_notes?: string;
  remediated_by?: string;
}

export interface AssetVulnerabilitySummary {
  asset_id: string;
  asset_name: string;
  asset_type: string;
  criticality: string;
  risk_score: number;
  total_vulns: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  open_count: number;
  mitigated_count: number;
}

export interface ScanResultResponse {
  scan_id: string;
  scanned_assets_count: number;
  discovered_vulnerabilities_count: number;
  new_findings_count: number;
  scan_timestamp: string;
  summary: string;
}

export interface VulnerabilityKPIsItem {
  total_vulnerabilities_tracked: number;
  total_asset_findings: number;
  open_findings: number;
  mitigated_findings: number;
  critical_severity_count: number;
  high_severity_count: number;
  remediation_progress_pct: number;
  average_cvss_score: number;
}

// Multi-Site & Enterprise Reporting Types (Phase 12)
export interface SiteItem {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  location?: string;
  status: string;
  ip_range?: string;
  created_at: string;
}

export interface SiteStatsItem {
  site_id: string;
  name: string;
  location?: string;
  status: string;
  total_assets: number;
  active_agents: number;
  open_incidents: number;
  critical_vulnerabilities: number;
  average_risk_score: number;
}

export interface TopRiskItem {
  category: string;
  item_name: string;
  severity: string;
  impact: string;
  recommended_action: string;
}

export interface ExecutiveReportItem {
  report_id: string;
  title: string;
  organization_name: string;
  generated_at: string;
  overall_posture_score: number;
  posture_level: "EXCELLENT" | "ACCEPTABLE" | "AT_RISK" | "CRITICAL";
  executive_summary: string;
  kpi_summary: Record<string, any>;
  top_risks: TopRiskItem[];
  remediation_recommendations: string[];
  report_markdown: string;
}

export interface ComplianceControlItem {
  control_id: string;
  family: string;
  title: string;
  status: "COMPLIANT" | "PARTIAL" | "NON_COMPLIANT";
  coverage_score_pct: number;
  evidence: string;
}

export interface ComplianceReportItem {
  report_id: string;
  title: string;
  organization_name: string;
  standard: string;
  generated_at: string;
  compliance_score_pct: number;
  certification_status: "AUDIT_READY" | "CONDITIONALLY_COMPLIANT" | "NON_COMPLIANT";
  summary: string;
  controls: ComplianceControlItem[];
  evidence_count: number;
  report_markdown: string;
}

// Threat Intelligence & Deception Types
export interface ThreatIOCItem {
  id: string;
  organization_id: string;
  ioc_type: "IP" | "DOMAIN" | "SHA256";
  value: string;
  threat_actor: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  source: string;
  confidence: number;
  is_active: boolean;
  hit_count: number;
  last_seen?: string;
  created_at: string;
}

export interface DeceptionTrapItem {
  id: string;
  organization_id: string;
  name: string;
  trap_type: "CANARY_FILE" | "DECOY_PORT" | "DECOY_CREDENTIAL";
  target_indicator: string;
  description?: string;
  is_active: boolean;
  triggered_count: number;
  last_triggered?: string;
  created_at: string;
}




