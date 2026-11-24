# CyberLab v1.0.0 — Network Engine & Host Isolation Safety Audit

**Component Audited**: `backend/app/network/` (`safety.py`, `linux_driver.py`, `simulation_driver.py`, `manager.py`)  
**Standard**: Host Protection Guarantee, Kernel Boundary Enforcement, RFC 1918 Private Addressing  
**Auditor Roles**: Linux Infrastructure Engineer, Principal Security Auditor  

---

## 1. Host Protection & Safety Architecture

The primary design requirement for CyberLab's Linux Network Simulation Engine is **strict containment**: under no circumstances may simulation operations modify, disrupt, or compromise the host machine's physical networking, default gateway, or firewall tables.

### Safety Guarantee Matrix

```
                      INCOMING NETWORK OPERATION
                                  │
                                  ▼
                 ┌─────────────────────────────────┐
                 │     HostProtectionValidator     │
                 └────────────────┬────────────────┘
                                  │
         ┌────────────────────────┴────────────────────────┐
         ▼                                                 ▼
[Protected Host Pattern?]                         [Prefix Compliance?]
Matches:                                          Must start with:
 • lo                                              • cl-
 • wlan*, wlp* (Wi-Fi)                             • cl_
 • eth*, enp*, ens* (Host LAN)                     • cl-ns- (namespaces)
 • docker*, virbr* (Host Virtual)                          │
         │                                                 │
      [YES]                                              [NO]
         │                                                 │
         ▼                                                 ▼
 🛑 CRITICAL SAFETY VIOLATION                      🛑 REJECTED: NON-CONFORMANT
  Operation Aborted Immediately                     Operation Aborted Immediately
```

---

## 2. Validator Implementation Analysis (`safety.py`)

### Interface Name Validation
```python
PROTECTED_PATTERNS: List[str] = [
    r"^lo$",
    r"^wlan\d*",
    r"^wlp\w+",
    r"^eth\d*",
    r"^enp\w+",
    r"^ens\w+",
    r"^docker\d*",
    r"^virbr\d*",
]
```
- **Test Evidence**:
  - `HostProtectionValidator.validate_interface_name("wlan0")` $\to$ Raises `HostProtectionError` ("CRITICAL SAFETY VIOLATION: Operation on protected host interface 'wlan0' is blocked").
  - `HostProtectionValidator.validate_interface_name("eth0")` $\to$ Raises `HostProtectionError`.
  - `HostProtectionValidator.validate_interface_name("br0")` $\to$ Raises `HostProtectionError` (Missing allowed `cl-` / `cl_` prefix).
  - `HostProtectionValidator.validate_interface_name("cl-br0")` $\to$ Validated successfully.

### Namespace Isolation Validation
- Namespaces must strictly begin with `cl-ns-` or `cl-`.
- Calling `validate_namespace_name("default")` or `validate_namespace_name("root")` immediately raises a `HostProtectionError`.

### Default Route Hijacking Prevention
- `validate_route(dest_cidr, gateway_ip)`:
  - If `dest_cidr` is `"0.0.0.0/0"` or `"default"`, the gateway IP is strictly required to be an RFC 1918 private address (`10.x`, `172.x`, or `192.168.x`).
  - Public IPs cannot be configured as gateways, preventing unintended external routing leakage.

---

## 3. Kernel Driver vs. Simulation Driver Findings

### 1. `LinuxKernelDriver` Subprocess Safety
- Subprocess invocations pass arguments as **lists of strings** (`subprocess.run(full_cmd, capture_output=True, text=True, check=True)`).
- Shell execution (`shell=True`) is strictly avoided, preventing shell metacharacter injection (`|`, `;`, `&&`, `$()`).
- All `nftables` commands target namespace-isolated tables (`ip netns exec <namespace> nft add table inet <table_name>`).

### 2. Driver Decoupling in API Server (Key Finding)
- In `backend/app/network/manager.py`:
  ```python
  class NetworkEngineManager:
      def __init__(self, driver: NetworkDriver = None):
          self.driver = driver or SimulationDriver()

  network_manager = NetworkEngineManager()
  ```
- **Operational Reality**: The API server imports and uses `network_manager` initialized without arguments. Consequently, all API calls to `/api/v1/topologies/{id}/deploy` and `/teardown` execute within `SimulationDriver`'s in-memory dictionaries.
- **Limitation**: Even if the host has `CAP_NET_ADMIN` or passwordless `sudo`, CyberLab currently provides **no environment variable or configuration toggle** (e.g. `NETWORK_ENGINE_DRIVER=kernel`) to switch the running application to `LinuxKernelDriver`.

---

## 4. Teardown & Resource Cleanup

- `SimulationDriver.delete_namespace` and `delete_bridge` safely pop virtual resources from memory tables without leaving orphan references.
- In `LinuxKernelDriver`, `delete_namespace` executes `ip netns delete <name>`, which automatically collapses and cleans up all veth endpoints inside the deleted namespace.
- Before a topology is deleted from the database via `DELETE /api/v1/topologies/{id}`, `network_manager.teardown_topology` is invoked if `topology.status == "DEPLOYED"`, guaranteeing that kernel interfaces are not orphaned.
