from __future__ import annotations

import ctypes
import importlib
import os
import platform
import sys
import time
from pathlib import Path
from threading import Event
from typing import Any, Dict, List, Optional

from .eeg_callbacks import EEGCallbacks, callbacks
from .runtime_metrics_store import RuntimeMetricsStore, runtime_metrics_store


class CapsuleAdapter:
    def __init__(
        self,
        sdk_root: Optional[Path] = None,
        logs_dir: str = "Logs",
        scan_seconds: int = 8,
        store: RuntimeMetricsStore = runtime_metrics_store,
        callback_handler: EEGCallbacks = callbacks,
    ) -> None:
        self.sdk_root = Path(sdk_root) if sdk_root else Path(__file__).resolve().parents[1] / "capsule_sdk" / "python_sdk"
        self.logs_dir = logs_dir
        self.scan_seconds = scan_seconds

        self.store = store
        self.callback_handler = callback_handler

        self.lib: Optional[Any] = None
        self.locator: Optional[Any] = None
        self.device: Optional[Any] = None
        self.calibrator: Optional[Any] = None
        self.productivity: Optional[Any] = None
        self.physiological_states: Optional[Any] = None

        self._device_infos: List[Dict[str, Any]] = []
        self._device_list_event = Event()

    def initialize_sdk(self) -> None:
        if str(self.sdk_root) not in sys.path:
            sys.path.insert(0, str(self.sdk_root))

        self._DeviceLocator = importlib.import_module("DeviceLocator").DeviceLocator
        self._Device = importlib.import_module("Device").Device
        self._DeviceType = importlib.import_module("DeviceType").DeviceType
        self._Calibrator = importlib.import_module("Calibrator").Calibrator
        self._Productivity = importlib.import_module("Productivity").Productivity
        self._PhysiologicalStates = importlib.import_module("PhysiologicalStates").PhysiologicalStates

        self.lib = self._load_dll()
        self.locator = self._DeviceLocator(self.logs_dir, self.lib)

    def _load_dll(self) -> Any:
        project_capsule_root = self.sdk_root.parent
        candidates = [
            project_capsule_root / "libs" / "CapsuleClient.dll",
            project_capsule_root / "python_sdk" / "CapsuleClient.dll",
        ]

        dll_path = next((p for p in candidates if p.exists()), None)
        if dll_path is None:
            raise FileNotFoundError(
                "CapsuleClient.dll not found. Expected one of: "
                + ", ".join(str(p) for p in candidates)
            )

        if platform.system().lower().startswith("win"):
            os.add_dll_directory(str(dll_path.parent))

        return ctypes.CDLL(str(dll_path))

    def discover_devices(self, timeout_seconds: int = 15, device_type: Optional[Any] = None) -> List[Dict[str, Any]]:
        if self.locator is None:
            self.initialize_sdk()

        self._device_infos = []
        self._device_list_event.clear()
        self.locator.set_on_devices_list(self._on_device_list)

        # Default to real headband hardware (Neiry/Capsule) instead of the synthetic Noise device.
        # Keep Noise available only when explicitly requested via the `device_type` argument.
        selected_type = device_type if device_type is not None else self._DeviceType.Band
        self.locator.request_devices(selected_type, self.scan_seconds)

        deadline = time.time() + timeout_seconds
        while time.time() < deadline and not self._device_list_event.is_set():
            self.locator.update()
            time.sleep(0.02)

        return list(self._device_infos)

    def discover_until_found(
        self,
        timeout_seconds: int = 10,
        retry_delay_seconds: float = 2.0,
        max_attempts: int = 30,
        device_type: Optional[Any] = None,
    ) -> List[Dict[str, Any]]:
        """
        Repeat BLE scans until at least one device appears.

        Matches monitor_headset.py: request_devices(Band, scan_seconds) with a
        timeout_seconds poll loop, then sleep(retry_delay_seconds) and rescan.
        """
        for attempt in range(1, max_attempts + 1):
            devices = self.discover_devices(timeout_seconds=timeout_seconds, device_type=device_type)
            if devices:
                return devices
            if attempt < max_attempts:
                print(
                    f"[Capsule] discovery attempt {attempt}/{max_attempts} found 0 devices; "
                    f"retrying in {retry_delay_seconds}s..."
                )
                time.sleep(retry_delay_seconds)
        return []

    def discover_devices_diagnostic(self, timeout_seconds: int = 15) -> List[Dict[str, Any]]:
        """
        Diagnostic discovery: search using DeviceType.Any to enumerate all devices exposed by the SDK.
        This method is intended for temporary debugging only and does NOT change the default discovery behavior.
        """
        if self.locator is None:
            self.initialize_sdk()

        print("[Capsule][Diagnostic] starting discovery using DeviceType.Any (diagnostic only)")
        return self.discover_devices(timeout_seconds=timeout_seconds, device_type=self._DeviceType.Any)

    def connect(
        self,
        serial: Optional[str] = None,
        bipolar_channels: bool = True,
        *,
        discover_timeout_seconds: int = 10,
        discover_retry_delay_seconds: float = 2.0,
        discover_max_attempts: int = 30,
        device_type: Optional[Any] = None,
        # Legacy alias kept for scripts that still pass retry_count.
        retry_count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Connect to a Capsule device.

        Discovery uses the same retry loop as monitor_headset.py by default.
        """
        max_attempts = discover_max_attempts if retry_count is None else retry_count + 1
        devices = self.discover_until_found(
            timeout_seconds=discover_timeout_seconds,
            retry_delay_seconds=discover_retry_delay_seconds,
            max_attempts=max_attempts,
            device_type=device_type,
        )

        if not devices:
            raise RuntimeError("No Capsule devices found")

        selected = next((d for d in devices if serial and d["serial"] == serial), devices[0])

        self.device = self._Device(self.locator, selected["serial"], self.lib)
        self.calibrator = self._Calibrator(self.device, self.lib)
        self.productivity = self._Productivity(self.device, self.lib)
        self.physiological_states = self._PhysiologicalStates(self.device, self.lib)

        self.callback_handler.register(self.device, self.productivity, self.physiological_states)

        self.device.connect(bipolar_channels)
        self._wait_until_connected(timeout_seconds=40)

        info_obj = self.device.get_info()
        info = {
            "serial": info_obj.get_serial(),
            "name": info_obj.get_name(),
            "type": int(info_obj.get_type()),
            "eeg_sample_rate": float(self.device.get_eeg_sample_rate()),
        }
        self.store.set_device_connected(True, info)
        print(f"[Capsule] connected: {info}")
        return info

    def start_stream(self) -> None:
        if self.device is None:
            raise RuntimeError("Device is not connected")
        self.device.start()
        print("[Capsule] realtime EEG stream started")

    def stop_stream(self) -> None:
        if self.device is None:
            return
        self.device.stop()
        print("[Capsule] stream stopped")

    def disconnect(self) -> None:
        if self.device is None:
            return
        try:
            if self.device.is_connected():
                self.device.disconnect()
        finally:
            self.store.set_device_connected(False)
            print("[Capsule] device disconnected")

    def shutdown(self) -> None:
        try:
            self.stop_stream()
        finally:
            self.disconnect()

    def _wait_until_connected(self, timeout_seconds: int) -> None:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            self.locator.update()
            if self.device and self.device.is_connected():
                return
            time.sleep(0.02)
        raise TimeoutError("Timed out waiting for Capsule connection")

    def _on_device_list(self, _locator: Any, info_list: Any, fail_reason: Any) -> None:
        self._device_infos = []
        for i in range(len(info_list)):
            info = info_list[i]
            self._device_infos.append(
                {
                    "serial": info.get_serial(),
                    "name": info.get_name(),
                    "type": int(info.get_type()),
                }
            )

        # Resolve fail_reason code and name for clearer logging.
        try:
            fail_code = int(fail_reason)
        except Exception:
            try:
                fail_code = int(getattr(fail_reason, 'value'))
            except Exception:
                fail_code = None

        fail_name = None
        try:
            # Map known fail reasons from DeviceLocator.FailReason
            if fail_code == 0:
                fail_name = 'OK'
            elif fail_code == 1:
                fail_name = 'BluetoothDisabled'
            elif fail_code == 2:
                fail_name = 'Unknown'
        except Exception:
            fail_name = None

        print(f"[Capsule] discovered={len(self._device_infos)} fail_reason={fail_code} ({fail_name})")
        for dev in self._device_infos:
            print(f"[Capsule] device name='{dev['name']}' serial='{dev['serial']}' type={dev['type']}")
        self._device_list_event.set()
