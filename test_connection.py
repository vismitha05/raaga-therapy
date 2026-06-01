#!/usr/bin/env python3
"""
Connection & Streaming Verification Script
===========================================
Tests stable connection to headset 821108 and logs all callbacks.

Logs:
1. Connection state transitions
2. Battery updates
3. Resistance/impedance updates
4. EEG data packets
5. Productivity metrics
6. Physiological states
"""

import sys
import time
from pathlib import Path
from datetime import datetime
from threading import Lock

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from adaptive_backend.eeg.capsule_adapter import CapsuleAdapter


class ConnectionLogger:
    """Logs all connection and streaming events with timestamps."""
    
    def __init__(self):
        self.lock = Lock()
        self.events = []
        self.start_time = time.time()
    
    def log(self, level: str, message: str):
        """Log a timestamped event."""
        elapsed = time.time() - self.start_time
        with self.lock:
            entry = f"[{elapsed:6.2f}s] {level:10s} {message}"
            self.events.append(entry)
            print(entry)
    
    def info(self, message: str):
        self.log("INFO", message)
    
    def success(self, message: str):
        self.log("✅ SUCCESS", message)
    
    def error(self, message: str):
        self.log("❌ ERROR", message)
    
    def warning(self, message: str):
        self.log("⚠️  WARNING", message)
    
    def callback(self, callback_name: str, data: str):
        self.log(f"📡 {callback_name}", data)


class CallbackLogger:
    """Enhanced callback handler with logging."""
    
    def __init__(self, logger: ConnectionLogger):
        self.logger = logger
    
    def on_connection_status(self, status: int):
        """Intercept connection status changes."""
        connected = status == 1
        status_str = "CONNECTED" if connected else "DISCONNECTED"
        self.logger.callback("CONNECTION", f"Status={status} → {status_str}")
    
    def on_battery(self, charge: int):
        """Intercept battery updates."""
        self.logger.callback("BATTERY", f"{charge}%")
    
    def on_resistance(self, channel_count: int, channels_data: str):
        """Intercept resistance updates."""
        self.logger.callback("RESISTANCE", f"{channel_count} channels: {channels_data}")
    
    def on_eeg(self, samples: int, channels: int, timestamp: int):
        """Intercept EEG packets."""
        self.logger.callback("EEG", f"samples={samples} channels={channels} ts={timestamp}")
    
    def on_productivity(self, focus: float, relax: float, fatigue: float):
        """Intercept productivity metrics."""
        self.logger.callback("PRODUCTIVITY", 
                           f"focus={focus:.3f} relax={relax:.3f} fatigue={fatigue:.3f}")
    
    def on_physiological(self, relax: float, fatigue: float, stress: float):
        """Intercept physiological states."""
        self.logger.callback("PHYSIOLOGICAL", 
                           f"relax={relax:.3f} fatigue={fatigue:.3f} stress={stress:.3f}")


# Global logger instance
logger = ConnectionLogger()
callback_logger = CallbackLogger(logger)


def wrap_callbacks(adapter):
    """Wrap the callbacks to log all events."""
    
    if not adapter.device or not adapter.productivity or not adapter.physiological_states:
        return
    
    # Store original callback methods
    original_on_connection = adapter.callback_handler.on_connection_status
    original_on_battery = adapter.callback_handler.on_battery
    original_on_resistance = adapter.callback_handler.on_resistance
    original_on_eeg = adapter.callback_handler.on_eeg
    original_on_productivity = adapter.callback_handler.on_productivity
    original_on_physiological = adapter.callback_handler.on_physiological
    
    # Wrap callbacks with logging
    def logged_on_connection(_device, status):
        callback_logger.on_connection_status(int(status))
        return original_on_connection(_device, status)
    
    def logged_on_battery(_device, charge):
        callback_logger.on_battery(int(charge))
        return original_on_battery(_device, charge)
    
    def logged_on_resistance(_device, resistance_data):
        try:
            values = {}
            for idx in range(len(resistance_data)):
                name = resistance_data.get_channel_name(idx)
                value = float(resistance_data.get_value(idx))
                values[name] = value
            callback_logger.on_resistance(len(values), str(values))
        except Exception as e:
            logger.warning(f"Failed to parse resistance: {e}")
        return original_on_resistance(_device, resistance_data)
    
    def logged_on_eeg(_device, eeg_data):
        try:
            samples = eeg_data.get_samples_count()
            channels = eeg_data.get_channels_count()
            if samples > 0:
                timestamp = int(eeg_data.get_timestamp(samples - 1))
                callback_logger.on_eeg(samples, channels, timestamp)
        except Exception as e:
            logger.warning(f"Failed to parse EEG: {e}")
        return original_on_eeg(_device, eeg_data)
    
    def logged_on_productivity(_prod, metrics):
        try:
            focus = float(metrics.concentrationScore)
            relax = float(metrics.relaxationScore)
            fatigue = float(metrics.fatigueScore)
            callback_logger.on_productivity(focus, relax, fatigue)
        except Exception as e:
            logger.warning(f"Failed to parse productivity: {e}")
        return original_on_productivity(_prod, metrics)
    
    def logged_on_physiological(_phy, states):
        try:
            relax = float(states.relaxation)
            fatigue = float(states.fatigue)
            stress = float(states.stress)
            callback_logger.on_physiological(relax, fatigue, stress)
        except Exception as e:
            logger.warning(f"Failed to parse physiological: {e}")
        return original_on_physiological(_phy, states)
    
    # Replace callbacks with logged versions
    adapter.callback_handler.on_connection_status = logged_on_connection
    adapter.callback_handler.on_battery = logged_on_battery
    adapter.callback_handler.on_resistance = logged_on_resistance
    adapter.callback_handler.on_eeg = logged_on_eeg
    adapter.callback_handler.on_productivity = logged_on_productivity
    adapter.callback_handler.on_physiological = logged_on_physiological


def main():
    print("=" * 70)
    print("CONNECTION & STREAMING VERIFICATION - Serial 821108")
    print("=" * 70)
    print()
    
    logger.info("Initializing SDK...")
    adapter = CapsuleAdapter(scan_seconds=20)
    
    try:
        adapter.initialize_sdk()
        logger.success("SDK initialized")
    except Exception as e:
        logger.error(f"SDK initialization failed: {e}")
        return
    
    print()
    logger.info("Discovering headset...")
    try:
        devices = adapter.discover_devices(timeout_seconds=20)
        logger.callback("DISCOVERY", f"Found {len(devices)} device(s)")
        
        if not devices:
            logger.error("No devices discovered")
            return
        
        target = next((d for d in devices if d["serial"] == "821108"), None)
        if not target:
            logger.error(f"Serial 821108 not found. Found: {[d['serial'] for d in devices]}")
            return
        
        logger.success(f"Found target: {target['name']} ({target['serial']})")
    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        return
    
    print()
    logger.info("Connecting to serial 821108...")
    try:
        info = adapter.connect(serial="821108", bipolar_channels=True, retry_count=10)
        logger.success(f"Connected: {info['name']} (SR={info['eeg_sample_rate']}Hz)")
        
        # Wrap callbacks to log all events
        wrap_callbacks(adapter)
        
    except RuntimeError as e:
        logger.error(f"Connection failed: {e}")
        logger.info(f"Current state: device={adapter.device}, connected={adapter.device.is_connected() if adapter.device else 'N/A'}")
        return
    except Exception as e:
        logger.error(f"Unexpected error during connection: {e}")
        return
    
    print()
    logger.info("Starting EEG stream...")
    try:
        adapter.start_stream()
        logger.success("Stream started")
    except Exception as e:
        logger.error(f"Stream start failed: {e}")
        adapter.shutdown()
        return
    
    print()
    print("=" * 70)
    print("STREAMING - Capturing all callbacks for 60 seconds")
    print("=" * 70)
    print()
    
    try:
        start_time = time.time()
        duration = 60  # seconds
        
        while time.time() - start_time < duration:
            adapter.locator.update()
            time.sleep(0.01)
        
        elapsed = time.time() - start_time
        
        print()
        print("=" * 70)
        logger.success(f"STREAMING COMPLETED - Ran for {elapsed:.1f} seconds")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print()
        logger.warning("Interrupted by user")
    finally:
        print()
        logger.info("Shutting down...")
        try:
            adapter.shutdown()
            logger.success("Shutdown complete")
        except Exception as e:
            logger.error(f"Shutdown error: {e}")
    
    # Print summary
    print()
    print("=" * 70)
    print("EVENT SUMMARY")
    print("=" * 70)
    
    with logger.lock:
        connection_events = [e for e in logger.events if "CONNECTION" in e]
        battery_events = [e for e in logger.events if "BATTERY" in e]
        resistance_events = [e for e in logger.events if "RESISTANCE" in e]
        eeg_events = [e for e in logger.events if "EEG" in e]
        productivity_events = [e for e in logger.events if "PRODUCTIVITY" in e]
        physiological_events = [e for e in logger.events if "PHYSIOLOGICAL" in e]
        
        print(f"Total events: {len(logger.events)}")
        print(f"  Connection: {len(connection_events)}")
        print(f"  Battery: {len(battery_events)}")
        print(f"  Resistance: {len(resistance_events)}")
        print(f"  EEG: {len(eeg_events)}")
        print(f"  Productivity: {len(productivity_events)}")
        print(f"  Physiological: {len(physiological_events)}")
        
        if connection_events:
            print(f"\nFirst connection event: {connection_events[0]}")
            print(f"Last connection event: {connection_events[-1]}")
        
        if battery_events:
            print(f"\nBattery events: {len(battery_events)}")
            print(f"  First: {battery_events[0]}")
            print(f"  Last: {battery_events[-1]}")
        
        if resistance_events:
            print(f"\nResistance events: {len(resistance_events)}")
            print(f"  First: {resistance_events[0]}")
            print(f"  Last: {resistance_events[-1]}")
        
        if eeg_events:
            print(f"\nEEG events: {len(eeg_events)}")
            print(f"  Rate: {len(eeg_events) / max(1, elapsed):.1f} packets/sec")
            print(f"  First: {eeg_events[0]}")
            print(f"  Last: {eeg_events[-1]}")
        
        if productivity_events:
            print(f"\nProductivity events: {len(productivity_events)}")
            print(f"  First: {productivity_events[0]}")
            print(f"  Last: {productivity_events[-1]}")
        
        if physiological_events:
            print(f"\nPhysiological events: {len(physiological_events)}")
            print(f"  First: {physiological_events[0]}")
            print(f"  Last: {physiological_events[-1]}")
    
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
