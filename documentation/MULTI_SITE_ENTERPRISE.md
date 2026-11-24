# CyberLab Multi-Site Enterprise Fleet Management & Governance

**Platform Module**: Phase 12 (v1.0 Production Release)  
**Package**: `backend/app/enterprise/`, `backend/app/api/v1/sites.py`, `backend/app/api/v1/reports.py`  
**Frontend**: `frontend/src/components/enterprise/EnterpriseSitesView.tsx`

---

## 1. Architectural Overview

As security operations mature from localized lab environments into distributed hybrid enterprise infrastructures, security platforms must deliver multi-site awareness without duplicating administrative overhead.

CyberLab **Phase 12** introduces a multi-site enterprise control plane that supports:
1. **Multi-Site Isolation & Fleet Segmentation**: Segregating network topologies, virtual machines, cloud instances, and physical workstations into logical sites (e.g., `Primary CyberLab HQ / Kali Node`, `Frankfurt AWS VPC`, `Branch Office Lab A`).
2. **Dynamic Cross-Site Telemetry Aggregation**: Real-time aggregation of managed assets, active EDR agent heartbeats, open SOAR incidents, and unmitigated CVEs grouped per site or rolled up enterprise-wide.
3. **Executive Security Posture Reporting**: Automated generation of board-level risk scorecards (0–100 posture score, risk level tiers, strategic vulnerabilities, and prioritized remediation roadmaps).
4. **NIST CSF 2.0 & CIS Controls Continuous Compliance Auditing**: Direct mapping of live platform telemetry, endpoint controls, and vulnerability state to standard cybersecurity framework controls with automated evidence collection and readiness scoring.

```
                              ┌──────────────────────────────────────┐
                              │     CyberLab Executive Console       │
                              │  (Next.js 14 Web UI / REST APIs)     │
                              └──────────────────┬───────────────────┘
                                                 │
                      ┌──────────────────────────┴──────────────────────────┐
                      ▼                                                     ▼
        ┌───────────────────────────┐                         ┌───────────────────────────┐
        │    SiteService            │                         │   EnterpriseReportGen     │
        │  • Multi-Site Partition   │                         │  • Executive Scorecard    │
        │  • Site Stats Aggregation │                         │  • NIST CSF 2.0 Audit     │
        │  • Fleet Health Rollup    │                         │  • CIS Controls v8 Audit  │
        └─────────────┬─────────────┘                         └─────────────┬─────────────┘
                      │                                                     │
         ┌────────────┴───────────────────────────┬─────────────────────────┴────────────┐
         ▼                                        ▼                                      ▼
┌──────────────────┐                    ┌──────────────────┐                   ┌──────────────────┐
│   Site Alpha     │                    │    Site Beta     │                   │   Site Gamma     │
│   (HQ / Primary) │                    │  (Cloud VPC Lab) │                   │  (Branch Office) │
│ • 13 Real VMs    │                    │ • AWS EC2 Nodes  │                   │ • Edge Micro-Lab │
│ • Netns Topos    │                    │ • Cloud Agents   │                   │ • Linux Endpoints│
│ • EDR Agents     │                    │ • VPC Mirrors    │                   │ • Local Sensors  │
└──────────────────┘                    └──────────────────┘                   └──────────────────┘
```

---

## 2. Multi-Site Data Architecture

### Relational Schema (`backend/app/models/site.py`)

The `Site` model establishes a logical boundary for asset grouping, agent assignment, and risk isolation:

```python
class Site(Base):
    __tablename__ = "sites"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(128), nullable=True)          # e.g., "Frankfurt DC", "On-Premises Kali Lab"
    status = Column(String(32), default="ACTIVE")          # "ACTIVE", "INACTIVE", "MAINTENANCE"
    ip_range = Column(String(64), nullable=True)           # e.g., "10.100.0.0/16"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    organization = relationship("Organization", back_populates="sites")
    assets = relationship("Asset", back_populates="site")
```

Assets link to sites via an optional foreign key `site_id`:
- In single-site or localized installations, assets without an explicit `site_id` belong to the default primary site (`Primary CyberLab HQ / Kali Node`).
- In distributed installations, telemetry, agents, and scans are partitioned by `site_id`.

---

## 3. Real-Time Fleet Statistics Aggregation

The `SiteService.get_site_stats(db, org_id)` method runs an aggregation across the relational database to calculate:

$$\text{Site Risk} = \text{Average}(\text{Asset Risk Scores in Site})$$

For each site, the service counts:
- **`total_assets`**: Physical, virtual, and simulated assets assigned to the site.
- **`active_agents`**: Distributed agents reporting `AgentStatus.ONLINE` within the heartbeat threshold.
- **`open_incidents`**: Security incidents in `OPEN` or `INVESTIGATING` status.
- **`critical_vulnerabilities`**: Vulnerabilities on site assets with CVSS $\ge 9.0$ in `OPEN` status.
- **`average_risk_score`**: Mean composite risk score (0–100) across all site assets.

---

## 4. Executive Security Posture Reporting

The `EnterpriseReportGenerator` synthesizes operational telemetry into executive summaries designed for CISOs, CIOs, and Board of Directors presentations.

### Composite Posture Formula

$$\text{Posture Score} = 100 - \left( \text{AvgAssetRisk} \times 0.40 + \min(\text{OpenIncidents} \times 10, 30) + \min(\text{CriticalVulns} \times 5, 30) \right)$$

Bounded between $0$ (catastrophic exposure) and $100$ (hardened baseline).

### Posture Levels
- **`EXCELLENT`** ($85 \le \text{Score} \le 100$): Robust defense-in-depth, zero unmitigated critical CVEs, low incident backlog.
- **`ACCEPTABLE`** ($70 \le \text{Score} < 85$): Operational defense with manageable residual risk; minor patch cycle items pending.
- **`AT_RISK`** ($50 \le \text{Score} < 70$): Elevated threat profile; critical vulnerabilities or active incident investigations present.
- **`CRITICAL`** ($\text{Score} < 50$): Severe risk exposure; immediate leadership escalation and containment required.

### Report Output Formats
1. **Structured JSON**: Complete KPI dictionaries, ranked top risks, and remediation action checklists for programmatic SIEM/ITSM ingestion.
2. **Executive Markdown**: Pre-formatted, publication-ready markdown with ASCII tables, executive summaries, and action checklists for instant export and PDF compilation.

---

## 5. Regulatory Compliance Engine (NIST CSF 2.0 & CIS Controls)

CyberLab evaluates live system telemetry against canonical cybersecurity control benchmarks to produce audit-ready compliance scorecards.

### Supported Frameworks

#### 1. NIST Cybersecurity Framework 2.0 (NIST CSF 2.0)
Evaluates controls across the six core functions:
- **`GOVERN` (GV.OC)**: Organizational context, asset criticality, risk appetite definitions.
- **`IDENTIFY` (ID.AM)**: Physical, virtual, and container asset discovery and software inventory.
- **`PROTECT` (PR.AC / PR.DS)**: Endpoint isolation, FIM integrity baselines, and host validation.
- **`DETECT` (DE.AE / DE.CM)**: State-based SIEM detection correlation and atomic simulation validation.
- **`RESPOND` (RS.MA / RS.MI)**: SOAR playbook automation, human-in-the-loop containment approvals.
- **`RECOVER` (RC.RP)**: Automated quarantine rollback and state restoration verification.

#### 2. CIS Critical Security Controls v8
Evaluates foundational controls:
- **`CIS 01`**: Inventory and Control of Enterprise Assets.
- **`CIS 02`**: Inventory and Control of Software Assets.
- **`CIS 07`**: Continuous Vulnerability Management.
- **`CIS 08`**: Audit Log Management.
- **`CIS 10`**: Malware Defenses and Endpoint Detection.
- **`CIS 17`**: Incident Response Management.

### Compliance Score & Audit Status
$$\text{Compliance Readiness (\%)} = \frac{\sum \text{Control Coverage Scores}}{\text{Total Evaluated Controls}}$$

- **`AUDIT_READY`** ($\text{Score} \ge 85\%$): Sufficient automated evidence collected for external third-party audit.
- **`CONDITIONALLY_COMPLIANT`** ($65\% \le \text{Score} < 85\%$): Core telemetry in place; minor gaps in continuous purple-team validation or asset coverage.
- **`NON_COMPLIANT`** ($\text{Score} < 65\%$): Fundamental gaps in asset monitoring or incident response controls.

---

## 6. REST API Reference

### Sites API (`/api/v1/sites`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/v1/sites` | List all registered enterprise sites | Bearer JWT |
| `GET` | `/api/v1/sites/stats` | Retrieve aggregated telemetry & risk KPIs per site | Bearer JWT |
| `POST` | `/api/v1/sites` | Register a new enterprise site/branch | Bearer JWT (Admin) |
| `GET` | `/api/v1/sites/{site_id}` | Get detailed configuration of a site | Bearer JWT |
| `PUT` | `/api/v1/sites/{site_id}` | Update site metadata, location, or CIDR | Bearer JWT (Admin) |
| `DELETE` | `/api/v1/sites/{site_id}` | Remove a site (assets preserved) | Bearer JWT (Admin) |

### Enterprise Reports API (`/api/v1/reports`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/v1/reports/executive` | Generate real-time Executive Posture Scorecard (JSON & Markdown) | Bearer JWT |
| `GET` | `/api/v1/reports/compliance?standard=NIST+CSF+2.0` | Generate NIST CSF 2.0 Compliance Audit Report | Bearer JWT |
| `GET` | `/api/v1/reports/compliance?standard=CIS+Controls+v8` | Generate CIS Controls v8 Compliance Audit Report | Bearer JWT |
