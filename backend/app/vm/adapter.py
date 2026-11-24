"""
Hypervisor Adapter Interface
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class HypervisorAdapter(ABC):
    @abstractmethod
    def list_running_vms(self) -> List[str]:
        pass

    @abstractmethod
    def start_vm(self, config_path: str) -> bool:
        pass

    @abstractmethod
    def stop_vm(self, config_path: str, soft: bool = True) -> bool:
        pass

    @abstractmethod
    def reset_vm(self, config_path: str, soft: bool = True) -> bool:
        pass

    @abstractmethod
    def suspend_vm(self, config_path: str) -> bool:
        pass
