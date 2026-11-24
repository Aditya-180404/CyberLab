# CyberLab Linux Network Infrastructure Engine

## 1. Architectural Purpose & Scope

The **Linux Network Infrastructure Engine** orchestrates virtualized, isolated Layer 2 and Layer 3 networks entirely within Linux kernel subsystems:
1. **Network Namespaces (`netns`)**: Provide completely independent network stacks (separate interface lists, routing tables, ARP tables, and socket spaces).
2. **Virtual Ethernet Pairs (`veth`)**: Emulate physical Ethernet patch cables. Packets transmitted into one peer instantly emerge from the opposite peer.
3. **Linux Bridges**: Function as Layer 2 switches, forwarding frames between attached virtual interfaces and virtual machines.
4. **VLAN-Aware Filtering**: Implements IEEE 802.1Q tagging and trunking across virtual bridges.
5. **nftables Packet Filtering**: Provides programmable, stateful firewall policies per virtual router and network segment.
6. **Strict Host Isolation & Protection**: Hardcoded boundaries ensure zero modification of host physical interfaces, Wi-Fi adapters, or default routing tables.

---

## 2. Resource Hierarchy & Naming Conventions

All kernel resources created by CyberLab enforce an unambiguous naming schema to prevent collision with host networking:

```
+----------------------------------------------------------------------------------------+
|                                    CYBERLAB TOPOLOGY                                   |
|                                                                                        |
|  +------------------------+                        +--------------------------------+  |
|  | Linux Namespace        |                        | Linux Namespace                |  |
|  | Name: cl-ns-<id>       |                        | Name: cl-ns-<id>               |  |
|  | IP: 10.10.1.10/24      |                        | IP: 10.10.2.10/24              |  |
|  | Dev: cl-veth-<id>      |                        | Dev: cl-veth-<id>              |  |
|  +-----------+------------+                        +---------------+----------------+  |
|              │                                                     │                   |
|              │ veth peer                                           │ veth peer         |
|              │                                                     │                   |
|  +-----------▼-----------------------------------------------------▼----------------+  |
|  | Linux Virtual Bridge (Switch) : cl-br-<id>                                      |  |
|  | VLAN 100 & VLAN 200 Segments                                                    |  |
|  +-----------------------------------+----------------------------------------------+  |
|                                      │                                                 |
|                        +-------------▼--------------+                                  |
|                        | Virtual Router Namespace   |                                  |
|                        | Name: cl-ns-rtr-<id>       |                                  |
|                        | nftables Filter Table      |                                  |
|                        +----------------------------+                                  |
+----------------------------------------------------------------------------------------+
```

| Resource Type | Pattern | Example | Purpose |
|---|---|---|---|
| **Network Namespace** | `cl-ns-<suffix>` | `cl-ns-srv01` | Isolated network execution domain |
| **Virtual Bridge** | `cl-br-<suffix>` | `cl-br-lan1` | Virtual Layer 2 Ethernet switch |
| **Veth Interface (Endpoint)** | `cl-ep-<suffix>` | `cl-ep-srv01` | Interface moved inside target namespace |
| **Veth Interface (Bridge Peer)**| `cl-brp-<suffix>` | `cl-brp-srv01`| Peer interface plugged into Linux bridge |
| **VLAN Sub-Interface** | `<iface>.<vlan>` | `cl-ep-rtr.100` | 802.1Q tagged interface |
| **nftables Table** | `cl_table_<suffix>`| `cl_table_fw1` | Isolated stateful firewall table |

---

## 3. Host Protection Boundaries & Safety Rules

To guarantee that CyberLab NEVER disrupts host connectivity, the engine enforces immutable validation guards:

```python
PROTECTED_INTERFACES = [
    "lo", "wlan0", "eth0", "wlan", "wlp", "enp", "ens", "docker0"
]
```

1. **Interface Name Check**: Any operation targeting an interface matching host patterns is immediately aborted with a `HostProtectionViolation`.
2. **Default Route Guard**: Modifying or removing the host's primary gateway (`0.0.0.0/0`) is strictly prohibited.
3. **Dedicated nftables Tables**: CyberLab creates its own isolated tables (e.g., `table inet cl_filter`). It never flushes or overwrites existing host tables.
4. **Ownership Tracking & Reversible Lifecycle**: Every resource is registered in the database with its creator, topology, and creation timestamp. Tearing down a topology performs a deterministic, reverse-order cleanup:
   1. Flush `nftables` rules.
   2. Remove `veth` interfaces.
   3. Bring down and delete `cl-br-*` bridges.
   4. Delete `cl-ns-*` namespaces.

---

## 4. Execution Architecture: Driver Model

Because production deployments may run on dedicated Linux hosts with `CAP_NET_ADMIN` while CI/CD and sandboxed environments run under restricted privileges, CyberLab utilizes a driver abstraction:

1. **`LinuxKernelDriver`**: Executes real system commands (`ip netns`, `ip link`, `nft`) using a secure, allowlisted privileged runner.
2. **`SimulationDriver`**: Validates topologies, calculates IP address conflicts, ensures subnet CIDR correctness, tracks interface states, and simulates packet forwarding metrics in memory when operating in restricted sandboxes.

Both drivers implement the identical interface:
- `create_namespace(name)`
- `delete_namespace(name)`
- `create_bridge(name)`
- `delete_bridge(name)`
- `create_veth_pair(endpoint_iface, peer_iface, namespace, bridge_name, ip_cidr)`
- `configure_route(namespace, destination_cidr, gateway_ip)`
- `apply_nftables_rules(namespace, rules)`
- `teardown_topology(topology_id)`
