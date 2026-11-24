# CyberLab Real Virtual Machine Integration Engine

## 1. Architectural Purpose & Overview

The **Virtual Machine Integration Engine** bridges real hypervisors into CyberLab's unified cybersecurity platform:
1. **Hypervisor Driver Layer**: Interacts with hypervisor management interfaces (VMware Workstation CLI `vmrun`, and QEMU/KVM `virsh` in future).
2. **Automated Discovery Engine**: Scans designated host volumes and hypervisor directories, parses `.vmx` configuration files, and syncs virtual hardware specifications.
3. **Adapter Inspection & Isolation Safety**:
   - Inspects virtual NIC bindings (`ethernet0` through `ethernet9`).
   - Distinguishes `custom` (`vmnet1`), `hostonly`, `nat`, and `bridged` modes.
   - Enforces a critical safety policy: vulnerable targets (e.g. Metasploitable 2) are checked for accidental exposure to bridged physical Wi-Fi/LAN.
4. **Power State Lifecycle**: Manages start, graceful shutdown, hard reset, and suspension directly from the SOC control plane.
5. **Network Segment Bridging**: Maps virtual machine adapters directly to CyberLab's virtual bridges (`cl-br-*`) created in Network Studio.

---

## 2. Supported Hypervisors

| Hypervisor | Integration Protocol | Capabilities |
|---|---|---|
| **VMware Workstation Pro / Player** | CLI `vmrun -T ws` + `.vmx` parser | Discovery, power states, adapter inspection, memory/vCPU telemetry |
| **QEMU / KVM (Planned Phase 12)** | `libvirt` / `virsh` | Domain XML inspection, snapshotting, macvtap bridging |
| **VirtualBox (Optional Adapter)** | `VBoxManage` | VM list, power control, adapter mode inspection |

---

## 3. Discovered Host Machines (Live Verified)

| Virtual Machine | Guest OS | vCPU | RAM | Network Binding | Security Classification |
|---|---|---|---|---|---|
| **Metasploitable 2** | Linux / Ubuntu | 1 | 512 MB | `custom (vmnet1)` | **Vulnerable Target** (Host-Only Isolated) |
| **Parrot OS** | Debian / Parrot | 3 | 4096 MB | `custom (vmnet1)` | **Attacker / Workstation** |
| **OPNsense** | FreeBSD | 2 | 4096 MB | 5x `custom (vmnet1)` | **Firewall / Perimeter Gateway** |
| **Stapler** | Linux / Ubuntu | 2 | 2048 MB | `custom (vmnet1)` | **Vulnerable Target** (VulnHub Lab) |
| **Windows Server 2019** | Windows Server | 2 | 2048 MB | `custom (vmnet1)` | **Active Directory / Server Asset** |
| **Windows 11** | Windows 11 | 2 | 5120 MB | `nat (vmnet1)` | **Client Workstation** |

---

## 4. Security Boundaries & Protection Rules

1. **Safety Exclusion**: Vulnerable target VMs (Metasploitable, Stapler, Kioptrix) configured in `bridged` mode trigger an immediate critical alert on the SOC dashboard.
2. **Non-Root Execution**: The web server interacts with `vmrun` as the local workstation user (`ghost`) without requiring root access.
3. **Immutable Audit Records**: Every power operation (`VM_POWER_START`, `VM_POWER_STOP`, `VM_POWER_RESET`) generates an auditable, timestamped record in `audit_logs`.
