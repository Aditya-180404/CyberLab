"""
Digital Twin Schemas (Phase 8)
Pydantic v2 data models for topological graph, attack-path discovery,
blast-radius analysis, and choke-point defense.
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class DigitalTwinNodeType:
    ASSET = "ASSET"
    DEVICE = "DEVICE"
    SEGMENT = "SEGMENT"
    ADVERSARY = "ADVERSARY"


class DigitalTwinNode(BaseModel):
    id: str
    label: str
    node_type: str = Field(..., description="ASSET, DEVICE, SEGMENT, or ADVERSARY")
    asset_type: Optional[str] = None
    device_type: Optional[str] = None
    ip_addresses: List[str] = Field(default_factory=list)
    zone: str = Field(default="INTERNAL", description="EXTERNAL, DMZ, INTERNAL, SECURE_VAULT, or MANAGEMENT")
    criticality: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH, or CRITICAL")
    risk_score: int = Field(default=0, ge=0, le=100)
    is_compromised: bool = False
    status: str = Field(default="ACTIVE")
    services: List[Dict[str, Any]] = Field(default_factory=list)
    security_tags: List[str] = Field(default_factory=list)
    position: Optional[Dict[str, float]] = None


class DigitalTwinEdge(BaseModel):
    id: str
    source: str
    target: str
    protocol: str = Field(default="TCP")
    ports: List[int] = Field(default_factory=list)
    status: str = Field(default="OPEN", description="OPEN, RESTRICTED, or BLOCKED")
    weight: float = Field(default=1.0, ge=0.1)
    label: Optional[str] = None


class DigitalTwinGraphSummary(BaseModel):
    total_nodes: int
    total_edges: int
    compromised_nodes: int
    critical_nodes: int
    average_risk_score: float
    choke_points_count: int
    generated_at: str


class DigitalTwinGraphResponse(BaseModel):
    nodes: List[DigitalTwinNode]
    edges: List[DigitalTwinEdge]
    summary: DigitalTwinGraphSummary


class AttackPathStep(BaseModel):
    hop_number: int
    source_node_id: str
    source_label: str
    target_node_id: str
    target_label: str
    technique_id: str
    technique_name: str
    tactic: str
    protocol: str
    port: Optional[int] = None
    risk_weight: float
    description: str


class AttackPathItem(BaseModel):
    path_id: str
    node_sequence: List[str]
    node_labels: List[str]
    hops: int
    cumulative_risk: int = Field(ge=0, le=100)
    viability: str = Field(default="HIGH", description="HIGH, MEDIUM, or LOW")
    steps: List[AttackPathStep]
    choke_point_node_ids: List[str] = Field(default_factory=list)
    mitigation_summary: str


class AttackPathRequest(BaseModel):
    source_node_id: str
    target_node_id: str
    max_hops: Optional[int] = Field(default=6, ge=1, le=12)


class AttackPathResponse(BaseModel):
    source_node_id: str
    target_node_id: str
    total_paths_found: int
    shortest_path_hops: int
    recommended_choke_point: Optional[str] = None
    paths: List[AttackPathItem]


class ReachableAssetDetail(BaseModel):
    node_id: str
    label: str
    node_type: str
    zone: str
    criticality: str
    risk_score: int
    hops_away: int
    impact_summary: str


class BlastRadiusResponse(BaseModel):
    node_id: str
    node_label: str
    blast_score: int = Field(ge=0, le=100)
    total_reachable_nodes: int
    reachable_by_criticality: Dict[str, int]
    reachable_by_zone: Dict[str, int]
    reachable_assets: List[ReachableAssetDetail]
    containment_recommendation: str
    playbook_to_execute: Optional[str] = None


class ChokePointItem(BaseModel):
    node_id: str
    label: str
    node_type: str
    zone: str
    betweenness_centrality: float
    paths_intercepted_pct: float
    critical_assets_shielded: int
    risk_level: str
    recommendation: str
    suggested_action: str


class ChokePointResponse(BaseModel):
    choke_points: List[ChokePointItem]
    top_recommended_node_id: Optional[str] = None
    summary: str


class SimulateCompromiseRequest(BaseModel):
    node_id: str
    compromised: bool = True
