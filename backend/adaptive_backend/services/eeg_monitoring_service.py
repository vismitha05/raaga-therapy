"""
eeg_monitoring_service.py
------------------------
Monitors EEG signals in real-time and detects brain state.
Listens for configurable duration and accumulates power band data.
"""

import threading
import time
import numpy as np
from collections import deque
from datetime import datetime, timedelta
from typing import Optional, Callable

from adaptive_backend.services.raga_therapy_engine import (
    EEGStateAnalyzer, EEGDetection, FrequencyBand
)


class EEGMonitoringService:
    """
    Real-time EEG monitoring service with state detection.
    - Accumulates EEG samples over a monitoring window
    - Computes power band statistics (alpha, beta, theta)
    - Detects brain state and confidence
    """

    def __init__(self, window_seconds: int = 15, sample_rate: int = 256):
        """
        Initialize EEG monitoring service.

        Args:
            window_seconds: Duration to monitor EEG (default 15s)
            sample_rate: EEG sampling rate in Hz (default 256 Hz)
        """
        self.window_seconds = window_seconds
        self.sample_rate = sample_rate
        self.window_samples = window_seconds * sample_rate

        # Data buffers
        self._eeg_buffer: deque = deque(maxlen=self.window_samples)
        self._power_bands: deque = deque()  # Stores (alpha, beta, theta) tuples

        # State tracking
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._latest_detection: Optional[EEGDetection] = None

        # Callbacks
        self._on_sample_callback: Optional[Callable] = None
        self._on_detection_callback: Optional[Callable] = None

    def start_monitoring(self):
        """Start background monitoring thread"""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="EEGMonitoringThread"
        )
        self._monitor_thread.start()

    def stop_monitoring(self):
        """Stop monitoring and return final detection"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        return self._latest_detection

    def add_eeg_sample(self, raw_value: float):
        """
        Add a raw EEG sample to the buffer.
        Typically called by EEG hardware interface.

        Args:
            raw_value: Raw EEG measurement
        """
        with self._lock:
            self._eeg_buffer.append(raw_value)

            # Call sample callback if registered
            if self._on_sample_callback:
                self._on_sample_callback(raw_value)

    def set_sample_callback(self, callback: Callable[[float], None]):
        """Register callback for each EEG sample"""
        self._on_sample_callback = callback

    def set_detection_callback(self, callback: Callable[[EEGDetection], None]):
        """Register callback for brain state detection"""
        self._on_detection_callback = callback

    def add_power_bands(self, alpha: float, beta: float, theta: float):
        """
        Add pre-computed power band values (alternative to raw samples).
        Useful when EEG hardware provides frequency domain data directly.

        Args:
            alpha: Alpha band power (8-12 Hz)
            beta: Beta band power (12-30 Hz)
            theta: Theta band power (4-8 Hz)
        """
        with self._lock:
            self._power_bands.append((alpha, beta, theta))

    def get_latest_detection(self) -> Optional[EEGDetection]:
        """Get most recent brain state detection"""
        with self._lock:
            return self._latest_detection

    def get_monitoring_progress(self) -> float:
        """Get monitoring progress as percentage (0.0 - 1.0)"""
        with self._lock:
            if len(self._power_bands) > 0:
                return min(1.0, len(self._power_bands) / max(1, self.window_seconds))
            if self.window_samples == 0:
                return 0.0
            return min(1.0, len(self._eeg_buffer) / self.window_samples)

    def get_monitoring_time_remaining(self) -> float:
        """Get remaining monitoring time in seconds"""
        progress = self.get_monitoring_progress()
        elapsed = progress * self.window_seconds
        return max(0.0, self.window_seconds - elapsed)

    def _monitor_loop(self):
        """Background monitoring loop"""
        start_time = time.time()
        last_detection_time = start_time

        while self._monitoring:
            elapsed = time.time() - start_time
            if elapsed > self.window_seconds:
                # Monitoring window complete
                break

            # Check if we have enough power band data to make a detection
            with self._lock:
                if len(self._power_bands) > 0:
                    # Use latest power bands
                    alpha, beta, theta = self._power_bands[-1]

                    # Perform detection every 1 second or more frequently if configured
                    if time.time() - last_detection_time >= 1.0:
                        detection = EEGStateAnalyzer.create_detection(alpha, beta, theta)
                        self._latest_detection = detection

                        if self._on_detection_callback:
                            self._on_detection_callback(detection)

                        last_detection_time = time.time()

            time.sleep(0.1)  # Check 10 times per second

        # Final detection after window completes
        self._perform_final_detection()

    def _perform_final_detection(self):
        """Compute final brain state detection from accumulated data"""
        with self._lock:
            if len(self._power_bands) == 0:
                # No data available - use simulated default
                alpha, beta, theta = 0.5, 0.3, 0.2
            else:
                # Average power bands over the monitoring window
                alphas = [pb[0] for pb in self._power_bands]
                betas = [pb[1] for pb in self._power_bands]
                thetas = [pb[2] for pb in self._power_bands]

                alpha = np.mean(alphas) if alphas else 0.5
                beta = np.mean(betas) if betas else 0.3
                theta = np.mean(thetas) if thetas else 0.2

            detection = EEGStateAnalyzer.create_detection(alpha, beta, theta)
            self._latest_detection = detection

            if self._on_detection_callback:
                self._on_detection_callback(detection)

        return detection

    def simulate_15_second_scan(self) -> EEGDetection:
        """
        Simulate a realistic 15-second EEG scan for testing/demo.
        Generates realistic power band variations over time.

        Returns:
            Final brain state detection after simulation
        """
        import random

        # Start from a baseline state and drift over 15 seconds
        base_alpha = random.uniform(0.4, 0.8)
        base_beta = random.uniform(0.2, 0.5)
        base_theta = random.uniform(0.1, 0.4)

        self.start_monitoring()

        for i in range(self.window_seconds):
            # Add realistic noise and drift
            alpha = max(0.0, base_alpha + random.gauss(0, 0.1))
            beta = max(0.0, base_beta + random.gauss(0, 0.08))
            theta = max(0.0, base_theta + random.gauss(0, 0.08))

            self.add_power_bands(alpha, beta, theta)
            time.sleep(1.0)

        return self.stop_monitoring()


class EEGSimulator:
    """Simulates realistic EEG data for development and testing"""

    @staticmethod
    def generate_relaxed_pattern(duration_seconds: int = 15) -> deque:
        """Generate relaxed brain state pattern (high alpha)"""
        patterns = deque()
        for i in range(duration_seconds):
            # High alpha, low beta
            alpha = np.random.normal(0.6, 0.1)
            beta = np.random.normal(0.2, 0.05)
            theta = np.random.normal(0.15, 0.05)
            patterns.append((alpha, beta, theta))
        return patterns

    @staticmethod
    def generate_focused_pattern(duration_seconds: int = 15) -> deque:
        """Generate focused brain state pattern (high beta)"""
        patterns = deque()
        for i in range(duration_seconds):
            # High beta, moderate alpha
            alpha = np.random.normal(0.35, 0.08)
            beta = np.random.normal(0.55, 0.1)
            theta = np.random.normal(0.1, 0.05)
            patterns.append((alpha, beta, theta))
        return patterns

    @staticmethod
    def generate_sleepy_pattern(duration_seconds: int = 15) -> deque:
        """Generate sleepy brain state pattern (high theta)"""
        patterns = deque()
        for i in range(duration_seconds):
            # High theta, low others
            alpha = np.random.normal(0.2, 0.06)
            beta = np.random.normal(0.15, 0.05)
            theta = np.random.normal(0.65, 0.1)
            patterns.append((alpha, beta, theta))
        return patterns
