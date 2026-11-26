"""
VMware Workstation CLI Adapter
Interacts with /usr/bin/vmrun to control VM power states and query running inventory.
"""
import subprocess
import os
import logging
from typing import List, Optional
from app.vm.adapter import HypervisorAdapter

logger = logging.getLogger("cyberlab.vm.vmware")


class VMwareWorkstationAdapter(HypervisorAdapter):
    def __init__(self, vmrun_path: str = "/usr/bin/vmrun"):
        self.vmrun_path = vmrun_path

    def _execute(self, args: List[str]) -> subprocess.CompletedProcess:
        cmd = [self.vmrun_path, "-T", "ws"] + args
        logger.info(f"Executing vmrun: {' '.join(cmd)}")
        return subprocess.run(cmd, capture_output=True, text=True, check=True)

    def try_list_running_vms(self) -> Optional[List[str]]:
        """Returns normalized paths of currently running VMs, or None if vmrun is unavailable/failed."""
        if not os.path.isfile(self.vmrun_path):
            logger.warning(f"vmrun binary not found at {self.vmrun_path}")
            return None

        try:
            res = self._execute(["list"])
            lines = res.stdout.strip().split("\n")
            running = []
            for line in lines[1:]:  # First line is 'Total running VMs: N'
                line = line.strip()
                if line:
                    running.append(os.path.realpath(line) if os.path.exists(line) else line)
            return running
        except Exception as e:
            logger.warning(f"vmrun list failed (may lack X11 or direct socket): {e}")
            return None

    def list_running_vms(self) -> List[str]:
        """Returns normalized absolute paths of all currently running VMs."""
        return self.try_list_running_vms() or []

    def start_vm(self, config_path: str) -> bool:
        try:
            self._execute(["start", config_path, "nogui"])
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start VM {config_path}: {e.stderr}")
            raise RuntimeError(f"VMware start failed: {e.stderr.strip() or e.stdout.strip()}")

    def stop_vm(self, config_path: str, soft: bool = True) -> bool:
        mode = "soft" if soft else "hard"
        try:
            self._execute(["stop", config_path, mode])
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stop VM {config_path}: {e.stderr}")
            raise RuntimeError(f"VMware stop failed: {e.stderr.strip() or e.stdout.strip()}")

    def reset_vm(self, config_path: str, soft: bool = True) -> bool:
        mode = "soft" if soft else "hard"
        try:
            self._execute(["reset", config_path, mode])
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to reset VM {config_path}: {e.stderr}")
            raise RuntimeError(f"VMware reset failed: {e.stderr.strip() or e.stdout.strip()}")

    def suspend_vm(self, config_path: str) -> bool:
        try:
            self._execute(["suspend", config_path, "soft"])
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to suspend VM {config_path}: {e.stderr}")
            raise RuntimeError(f"VMware suspend failed: {e.stderr.strip() or e.stdout.strip()}")
