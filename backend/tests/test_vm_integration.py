"""
Tests for Virtual Machine Integration Engine (Phase 3)
"""
import pytest
import os
from app.vm.vmx_parser import VMXParser
from app.vm.adapter import HypervisorAdapter
from app.vm.manager import vm_manager


class MockHypervisorAdapter(HypervisorAdapter):
    def __init__(self):
        self.running_vms = set()

    def list_running_vms(self):
        return list(self.running_vms)

    def start_vm(self, config_path: str):
        self.running_vms.add(config_path)
        return True

    def stop_vm(self, config_path: str, soft: bool = True):
        self.running_vms.discard(config_path)
        return True

    def reset_vm(self, config_path: str, soft: bool = True):
        self.running_vms.add(config_path)
        return True

    def suspend_vm(self, config_path: str):
        self.running_vms.discard(config_path)
        return True


@pytest.fixture(autouse=True)
def use_mock_vm_adapter():
    mock_adapter = MockHypervisorAdapter()
    original_adapter = vm_manager.adapter
    vm_manager.set_adapter(mock_adapter)
    yield mock_adapter
    vm_manager.set_adapter(original_adapter)


def test_vmx_parser_sample_data(tmp_path):
    """Verifies VMX parser accurately extracts specs and network adapter details."""
    sample_vmx = tmp_path / "test_target.vmx"
    sample_vmx.write_text(
        """
        displayName = "Metasploitable2-Target"
        memsize = "512"
        numvcpus = "1"
        guestos = "ubuntu"
        ethernet0.present = "TRUE"
        ethernet0.connectionType = "custom"
        ethernet0.vnet = "vmnet1"
        ethernet0.virtualDev = "e1000"
        ethernet0.generatedAddress = "00:0C:29:4D:91:81"
        """
    )

    parsed = VMXParser.parse_vmx(str(sample_vmx))
    assert parsed["name"] == "Metasploitable2-Target"
    assert parsed["memory_mb"] == 512
    assert parsed["vcpus"] == 1
    assert len(parsed["network_adapters"]) == 1
    assert parsed["network_adapters"][0]["connection_type"] == "custom"
    assert parsed["network_adapters"][0]["vnet"] == "vmnet1"
    assert parsed["network_adapters"][0]["mac_address"] == "00:0C:29:4D:91:81"
    assert parsed["is_vulnerable_target"] is True
    assert parsed["safety_warning"] is None  # Safe because it is custom vmnet1


def test_vmx_parser_bridged_vulnerable_safety_warning(tmp_path):
    """Ensures vulnerable target VMs on bridged mode trigger a critical safety warning."""
    unsafe_vmx = tmp_path / "unsafe_metasploitable.vmx"
    unsafe_vmx.write_text(
        """
        displayName = "Metasploitable2-Exposed"
        memsize = "512"
        ethernet0.present = "TRUE"
        ethernet0.connectionType = "bridged"
        """
    )

    parsed = VMXParser.parse_vmx(str(unsafe_vmx))
    assert parsed["is_vulnerable_target"] is True
    assert parsed["safety_warning"] is not None
    assert "CRITICAL SECURITY RISK" in parsed["safety_warning"]


def test_vm_api_registration_and_power_control(client, admin_token, tmp_path):
    """Tests manual VM registration, power-on, power-off, and segment association via REST API."""
    vmx_file = tmp_path / "Parrot-OS.vmx"
    vmx_file.write_text(
        """
        displayName = "Parrot-Security-Lab"
        memsize = "4096"
        numvcpus = "2"
        ethernet0.present = "TRUE"
        ethernet0.connectionType = "custom"
        ethernet0.vnet = "vmnet1"
        """
    )

    # 1. Register VM
    reg_res = client.post(
        "/api/v1/vms/register",
        json={"config_path": str(vmx_file), "name": "Parrot-Security-Lab"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert reg_res.status_code == 201
    vm_data = reg_res.json()
    vm_id = vm_data["id"]
    assert vm_data["power_state"] == "STOPPED"
    assert vm_data["memory_mb"] == 4096

    # 2. Power On VM
    power_on_res = client.post(
        f"/api/v1/vms/{vm_id}/power",
        json={"action": "start", "mode": "soft"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert power_on_res.status_code == 200
    assert power_on_res.json()["power_state"] == "RUNNING"

    # 3. Power Off VM
    power_off_res = client.post(
        f"/api/v1/vms/{vm_id}/power",
        json={"action": "stop", "mode": "soft"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert power_off_res.status_code == 200
    assert power_off_res.json()["power_state"] == "STOPPED"


def test_analyst_cannot_power_vm(client, analyst_token, tmp_path):
    """SOC Analyst lacks permission to execute VM power operations."""
    vmx_file = tmp_path / "restricted.vmx"
    vmx_file.write_text("displayName = 'Restricted'")

    # Attempt registration as analyst -> must fail with 403
    reg_res = client.post(
        "/api/v1/vms/register",
        json={"config_path": str(vmx_file)},
        headers={"Authorization": f"Bearer {analyst_token}"}
    )
    assert reg_res.status_code == 403


def test_vm_list_auto_syncs_live_hypervisor_state(client, admin_token, use_mock_vm_adapter, tmp_path):
    """Verifies GET /vms automatically synchronizes live RUNNING/STOPPED state from hypervisor."""
    vmx_file = tmp_path / "Metasploitable-Live.vmx"
    vmx_file.write_text('displayName = "Metasploitable-Live"\nmemsize = "512"\n')

    reg_res = client.post(
        "/api/v1/vms/register",
        json={"config_path": str(vmx_file)},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert reg_res.status_code == 201
    vm_id = reg_res.json()["id"]
    assert reg_res.json()["power_state"] == "STOPPED"

    # Simulate external VM start in VMware Workstation
    use_mock_vm_adapter.running_vms.add(os.path.realpath(str(vmx_file)))

    list_res = client.get("/api/v1/vms", headers={"Authorization": f"Bearer {admin_token}"})
    assert list_res.status_code == 200
    matched = [v for v in list_res.json() if v["id"] == vm_id][0]
    assert matched["power_state"] == "RUNNING"

    # Simulate external VM stop in VMware Workstation
    use_mock_vm_adapter.running_vms.clear()

    list_res_2 = client.get("/api/v1/vms", headers={"Authorization": f"Bearer {admin_token}"})
    assert list_res_2.status_code == 200
    matched_2 = [v for v in list_res_2.json() if v["id"] == vm_id][0]
    assert matched_2["power_state"] == "STOPPED"
