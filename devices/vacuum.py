"""Vacuum Pump Device - simple on/off control."""

from typing import Any, Dict

from devices.base_device import BaseDevice
from devices.oms_channel import oms_channel


class VacuumDevice(BaseDevice):
    """Vacuum pump with simple on/off control."""
    
    def __init__(self):
        """Initialize vacuum device."""
        super().__init__("Vacuum Pump")
    
    def get_device_type(self) -> str:
        """Return device type identifier."""
        return "vacuum"

    def set_vacuum(self, vacuum_on: bool) -> None:
        """Compatibility wrapper for OpenMicroStageInterface-style vacuum control."""
        self.set_power(vacuum_on)
        reply = oms_channel.call_interface("set_vacuum", bool(vacuum_on), require_connected=True)
        if reply is not None:
            self.status_message = f"Vacuum set via shared channel: {'ON' if vacuum_on else 'OFF'}"

    def get_vacuum(self) -> bool:
        """Read vacuum state from hardware API or fallback to cached value."""
        try:
            value = oms_channel.call_interface("get_vacuum", require_connected=True)
            if value is not None:
                parsed = bool(value)
                self.is_on = parsed
                return parsed
        except Exception:
            return self.is_on
        return self.is_on
    
    def get_device_status(self) -> Dict[str, Any]:
        """Get complete vacuum pump status."""
        is_on = self.get_vacuum()
        with self.lock:
            return {
                "device_type": self.get_device_type(),
                "name": self.name,
                "is_on": is_on,
                "status": self.status_message,
                "connected": oms_channel.is_connected(),
            }
