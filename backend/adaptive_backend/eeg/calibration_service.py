from __future__ import annotations

import threading
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .device_manager import device_manager


@dataclass
class CalibrationState:
    status: str = "idle"  # idle | running | completed | failed
    mode: Optional[str] = None  # full | quick | baseline

    calibrator_progress: float = 0.0
    productivity_progress: float = 0.0
    physiological_progress: float = 0.0

    calibrator_complete: bool = False
    baseline_complete: bool = False
    calibration_failed: bool = False

    failure_reason: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


class CalibrationService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state = CalibrationState()

    def start_calibration(self) -> Dict[str, Any]:
        """
        Start full calibration flow:
        1) Individual NFB calibration via Calibrator.calibrate()
        2) Baseline calibration for Productivity and PhysiologicalStates
        """
        self._begin(mode="full")
        try:
            adapter = self._require_adapter()
            self._register_callbacks(adapter)

            calibrator = self._require_calibrator(adapter)
            calibrator.calibrate(0)

            # Start baseline collection in parallel after calibrator kickoff.
            adapter.productivity.calibrate_baselines()
            adapter.physiological_states.calibrate_baselines()

            with self._lock:
                self._state.status = "running"
                self._state.details["started"] = "full"
            return self.calibration_status()
        except Exception as exc:
            self._fail(str(exc))
            return self.calibration_status()

    def quick_calibration(self) -> Dict[str, Any]:
        """
        Start quick calibration via Calibrator.calibrate_quick().
        """
        self._begin(mode="quick")
        try:
            adapter = self._require_adapter()
            self._register_callbacks(adapter)

            calibrator = self._require_calibrator(adapter)
            calibrator.calibrate_quick()

            with self._lock:
                self._state.status = "running"
                self._state.details["started"] = "quick"
            return self.calibration_status()
        except Exception as exc:
            self._fail(str(exc))
            return self.calibration_status()

    def baseline_calibration(self) -> Dict[str, Any]:
        """
        Start baseline calibration for Productivity + PhysiologicalStates.
        """
        self._begin(mode="baseline")
        try:
            adapter = self._require_adapter()
            self._register_callbacks(adapter)

            adapter.productivity.calibrate_baselines()
            adapter.physiological_states.calibrate_baselines()

            with self._lock:
                self._state.status = "running"
                self._state.details["started"] = "baseline"
            return self.calibration_status()
        except Exception as exc:
            self._fail(str(exc))
            return self.calibration_status()

    def calibration_status(self) -> Dict[str, Any]:
        with self._lock:
            return deepcopy(self._state.__dict__)

    def readiness_check(self) -> Dict[str, Any]:
        """
        Returns readiness for downstream EEG-driven logic.
        Readiness is true when calibration is complete and no failure is present.
        """
        state = self.calibration_status()
        ready = bool(
            state["status"] == "completed"
            and state["calibrator_complete"]
            and not state["calibration_failed"]
        )
        return {
            "ready": ready,
            "status": state["status"],
            "calibration_complete": state["calibrator_complete"],
            "baseline_complete": state["baseline_complete"],
            "calibration_failed": state["calibration_failed"],
            "failure_reason": state["failure_reason"],
            "progress": {
                "calibrator": state["calibrator_progress"],
                "productivity": state["productivity_progress"],
                "physiological": state["physiological_progress"],
            },
        }

    def _require_adapter(self):
        adapter = device_manager.adapter
        if adapter is None:
            raise RuntimeError("Capsule adapter is not initialized")
        if adapter.device is None:
            raise RuntimeError("Capsule device is not connected")
        if adapter.productivity is None or adapter.physiological_states is None:
            raise RuntimeError("Capsule classifiers are not initialized")
        return adapter

    def _require_calibrator(self, adapter):
        if adapter.calibrator is None:
            raise RuntimeError("Capsule calibrator is not initialized")
        return adapter.calibrator

    def _register_callbacks(self, adapter) -> None:
        calibrator = self._require_calibrator(adapter)

        calibrator.set_on_calibration_finished(self._on_calibrator_finished)
        calibrator.set_on_calibration_stage_finished(self._on_calibrator_stage_finished)

        adapter.productivity.set_on_calibration_progress(self._on_productivity_progress)
        adapter.productivity.set_on_baseline_update(self._on_productivity_baseline)

        adapter.physiological_states.set_on_calibration_progress(self._on_physiological_progress)
        adapter.physiological_states.set_on_calibrated(self._on_physiological_baseline)

    def _begin(self, mode: str) -> None:
        with self._lock:
            self._state = CalibrationState(mode=mode, status="running")

    def _fail(self, reason: str) -> None:
        with self._lock:
            self._state.status = "failed"
            self._state.calibration_failed = True
            self._state.failure_reason = reason

    def _update_completion(self) -> None:
        with self._lock:
            if self._state.calibration_failed:
                self._state.status = "failed"
                return

            if self._state.mode == "quick":
                if self._state.calibrator_complete:
                    self._state.status = "completed"
                return

            if self._state.mode == "baseline":
                if self._state.baseline_complete:
                    self._state.status = "completed"
                return

            # full mode
            if self._state.calibrator_complete and self._state.baseline_complete:
                self._state.status = "completed"

    # Capsule callbacks
    def _on_calibrator_stage_finished(self, _calibrator: Any) -> None:
        with self._lock:
            self._state.calibrator_progress = min(1.0, self._state.calibrator_progress + 0.25)

    def _on_calibrator_finished(self, calibrator: Any, data: Any) -> None:
        try:
            failed = bool(calibrator.has_calibration_failed())
        except Exception:
            failed = False

        with self._lock:
            self._state.calibrator_progress = 1.0
            self._state.calibrator_complete = not failed
            if failed:
                self._state.calibration_failed = True
                self._state.failure_reason = f"calibrator_fail_reason={int(getattr(data, 'failReason', -1))}"
            self._state.details["individual_nfb"] = {
                "timestamp_milli": int(getattr(data, "timestampMilli", -1)),
                "individual_frequency": float(getattr(data, "individualFrequency", -1.0)),
                "lower_frequency": float(getattr(data, "lowerFrequency", -1.0)),
                "upper_frequency": float(getattr(data, "upperFrequency", -1.0)),
            }

        self._update_completion()

    def _on_productivity_progress(self, _prod: Any, progress: float) -> None:
        with self._lock:
            self._state.productivity_progress = float(max(0.0, min(1.0, progress)))
        self._update_baseline_completion()

    def _on_productivity_baseline(self, _prod: Any, baselines: Any) -> None:
        with self._lock:
            self._state.details["productivity_baseline"] = {
                "timestamp_milli": int(getattr(baselines, "timestampMilli", -1)),
                "gravity": float(getattr(baselines, "gravity", -1.0)),
                "productivity": float(getattr(baselines, "productivity", -1.0)),
                "fatigue": float(getattr(baselines, "fatigue", -1.0)),
                "relaxation": float(getattr(baselines, "relaxation", -1.0)),
                "concentration": float(getattr(baselines, "concentration", -1.0)),
            }

    def _on_physiological_progress(self, _phy: Any, progress: float) -> None:
        with self._lock:
            self._state.physiological_progress = float(max(0.0, min(1.0, progress)))
        self._update_baseline_completion()

    def _on_physiological_baseline(self, _phy: Any, baselines: Any) -> None:
        with self._lock:
            self._state.physiological_progress = 1.0
            self._state.details["physiological_baseline"] = {
                "timestamp_milli": int(getattr(baselines, "timestampMilli", -1)),
                "alpha": float(getattr(baselines, "alpha", -1.0)),
                "beta": float(getattr(baselines, "beta", -1.0)),
                "concentration": float(getattr(baselines, "concentration", -1.0)),
            }
        self._update_baseline_completion(force=True)

    def _update_baseline_completion(self, force: bool = False) -> None:
        with self._lock:
            p = self._state.productivity_progress
            ps = self._state.physiological_progress
            if force or (p >= 1.0 and ps >= 1.0):
                self._state.baseline_complete = True
        self._update_completion()


calibration_service = CalibrationService()
