"""Rotation Plate Device - angular control and monitoring."""

from typing import Any, Dict

from devices.base_device import BaseDevice
from devices.oms_channel import oms_channel


class RotationPlateDevice(BaseDevice):
    """Rotation plate with absolute-angle control."""

    def __init__(self):
        super().__init__("Rotation Plate")
        self.current_angle = 0.0
        self.target_angle = 0.0

    @staticmethod
    def _normalize_angle(angle: float) -> float:
        """Normalize an angle into [0, 360) degrees."""
        value = float(angle) % 360.0
        if value < 0:
            value += 360.0
        return value

    def get_rotation(self) -> float:
        """Read current rotation from hardware API or fallback to cached value."""
        try:
            value = oms_channel.call_interface("get_rotation", require_connected=True)
            if value is not None:
                normalized = self._normalize_angle(float(value))
                with self.lock:
                    self.current_angle = normalized
                return normalized
        except Exception:
            pass

        with self.lock:
            return self.current_angle

    def set_rotation(self, angle: float) -> None:
        """Set desired rotation angle in degrees."""
        normalized = self._normalize_angle(angle)

        try:
            reply = oms_channel.call_interface("set_rotation", float(normalized), require_connected=True)
            if reply is not None:
                self.status_message = f"Rotation set via shared channel: {normalized:.2f} deg"
        except Exception as exc:
            self.status_message = f"Rotation command failed: {exc}"

        with self.lock:
            self.target_angle = normalized
            self.current_angle = normalized
            if "failed" not in self.status_message.lower():
                self.status_message = f"Rotation set to {normalized:.2f} deg"

    def nudge(self, delta: float) -> float:
        """Apply a relative rotation delta in degrees and return target angle."""
        current = self.get_rotation()
        target = self._normalize_angle(current + float(delta))
        self.set_rotation(target)
        return target

    def get_device_type(self) -> str:
        return "rotation"

    def get_device_status(self) -> Dict[str, Any]:
        angle = self.get_rotation()
        with self.lock:
            return {
                "device_type": self.get_device_type(),
                "name": self.name,
                "is_on": True,
                "status": self.status_message,
                "connected": oms_channel.is_connected(),
                "current_angle": angle,
                "target_angle": self.target_angle,
            }
