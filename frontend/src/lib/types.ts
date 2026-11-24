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
