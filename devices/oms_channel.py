"""Shared OpenMicroStage hardware channel for all device modules."""

import os
from threading import Lock
from typing import Optional

try:
    from open_micro_stage_api import OpenMicroStageInterface
    from open_micro_stage_api.api import SerialInterface
except Exception:  # pragma: no cover - optional hardware dependency
    OpenMicroStageInterface = None
    SerialInterface = None


class OpenMicroStageChannel:
    """Singleton-like shared serial channel for stage, thermal, and vacuum controls."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._interface: Optional[object] = None
        self._last_error = "Not connected"
        self._port: Optional[str] = None
        self._baud_rate: Optional[int] = None
        self.default_port = (os.getenv("OMS_PORT", "") or "").strip() or None
        self.default_baud_rate = self._env_int("OMS_BAUD_RATE", 921600)
        self.default_show_communication = self._env_bool("OMS_SHOW_COMMUNICATION", True)
        self.default_show_log_messages = self._env_bool("OMS_SHOW_LOG_MESSAGES", True)
        self.exception_on_no_device = self._env_bool("OMS_EXCEPTION_ON_NO_DEVICE", False)
        self.auto_connect = self._env_bool("OMS_AUTO_CONNECT", False)
        self.serial_broadcast = (os.getenv("OMS_SERIAL_BROADCAST", "") or "").strip() or None
        self._ensure_interface()
        if self.auto_connect and self.default_port:
            self.connect(self.default_port, self.default_baud_rate)

    @staticmethod
    def _env_bool(name: str, default: bool) -> bool:
        raw = os.getenv(name)
        if raw is None:
            return default
        return raw.strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _env_int(name: str, default: int) -> int:
        raw = os.getenv(name)
        if raw is None:
            return default
        try:
            return int(raw)
        except ValueError:
            return default

    def _apply_optional_runtime_attrs(self, interface: object) -> None:
        """Apply optional library runtime attributes when available."""
        if self.serial_broadcast is None:
            return
        for attr in ("serial_broadcast", "serial_broadcast_id", "broadcast", "boardcast"):
            if hasattr(interface, attr):
                try:
                    setattr(interface, attr, self.serial_broadcast)
                except Exception:
                    pass

    def _ensure_interface(self) -> Optional[object]:
        """Ensure an interface instance exists in virtual-capable mode."""
        if OpenMicroStageInterface is None:
            self._last_error = "OpenMicroStage API is unavailable"
            return None

        if self._interface is not None:
            return self._interface

        try:
            self._interface = OpenMicroStageInterface(
                show_communication=self.default_show_communication,
                show_log_messages=self.default_show_log_messages,
                exception_on_no_device=self.exception_on_no_device,
            )
        except TypeError:
            # Fallback for older installed builds that do not yet expose exception_on_no_device.
            self._interface = OpenMicroStageInterface(
                show_communication=self.default_show_communication,
                show_log_messages=self.default_show_log_messages,
            )
        self._apply_optional_runtime_attrs(self._interface)
        return self._interface

    def connect(
        self,
        port: str | None = None,
        baud_rate: int | None = None,
        show_communication: bool | None = None,
        show_log_messages: bool | None = None,
    ) -> bool:
        """Create a shared OpenMicroStageInterface and connect to hardware."""
        if OpenMicroStageInterface is None:
            self._last_error = "OpenMicroStage API is unavailable"
            return False

        resolved_port = port or self.default_port
        resolved_baud = baud_rate if baud_rate is not None else self.default_baud_rate
        resolved_show_comm = self.default_show_communication if show_communication is None else show_communication
        resolved_show_log = self.default_show_log_messages if show_log_messages is None else show_log_messages

        if not resolved_port:
            self._last_error = "OMS_PORT is not configured"
            return False

        with self._lock:
            interface = self._ensure_interface()
            if interface is None:
                return False

            # Keep runtime verbosity aligned with connect request.
            setattr(interface, "show_communication", resolved_show_comm)
            setattr(interface, "show_log_messages", resolved_show_log)

            try:
                interface.connect(resolved_port, resolved_baud)
            except Exception as exc:
                self._last_error = str(exc)
                self._port = None
                self._baud_rate = None
                return False

            if getattr(interface, "serial", None) is None:
                self._last_error = f"Failed to connect on {resolved_port}"
                self._port = None
                self._baud_rate = None
                return False

            self._interface = interface
            self._last_error = ""
            self._port = resolved_port
            self._baud_rate = resolved_baud
            return True

    def disconnect(self) -> None:
        """Disconnect the shared interface while keeping no-device mode available."""
        with self._lock:
            if self._interface is not None:
                try:
                    self._interface.disconnect()
                except Exception:
                    pass
            self._last_error = "Disconnected"
            self._port = None
            self._baud_rate = None

    def get_interface(self) -> Optional[object]:
        """Return the active shared interface instance."""
        with self._lock:
            return self._ensure_interface()

    def is_connected(self) -> bool:
        """Return whether the shared channel is connected."""
        with self._lock:
            return self._interface is not None and getattr(self._interface, "serial", None) is not None

    def status(self) -> dict:
        """Return current channel metadata for API responses."""
        with self._lock:
            return {
                "connected": self._interface is not None and getattr(self._interface, "serial", None) is not None,
                "port": self._port,
                "baud_rate": self._baud_rate,
                "error": self._last_error,
                "api_available": OpenMicroStageInterface is not None,
                "virtual_mode_enabled": True,
                "defaults": {
                    "port": self.default_port,
                    "baud_rate": self.default_baud_rate,
                    "show_communication": self.default_show_communication,
                    "show_log_messages": self.default_show_log_messages,
                    "exception_on_no_device": self.exception_on_no_device,
                    "auto_connect": self.auto_connect,
                    "serial_broadcast": self.serial_broadcast,
                },
            }

    def call_interface(self, method_name: str, *args, require_connected: bool = True, **kwargs):
        """Call an OpenMicroStageInterface method under a shared channel lock."""
        with self._lock:
            interface = self._ensure_interface()
            if interface is None:
                return None
            if require_connected and getattr(interface, "serial", None) is None:
                return None

            method = getattr(interface, method_name, None)
            if method is None:
                raise AttributeError(f"Interface has no method '{method_name}'")
            return method(*args, **kwargs)


oms_channel = OpenMicroStageChannel()
