#!/usr/bin/env python3
"""
Resilient Diagnostic Streaming Script
======================================
Waits for stable headset discovery, then immediately connects and streams.
Handles intermittent BLE advertisement patterns.
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from adaptive_backend.eeg.capsule_adapter import CapsuleAdapter


def wait_for_stable_discovery(adapter, target_serial="821108", stable_count=2, check_interval=3):
    """
    Wait for the headset to appear consistently.
    Uses extended 20-second scan windows to handle intermittent BLE advertisements.
    Requires N consecutive successful discoveries before proceeding.
    """
    print("[Streaming] Waiting for stable headset discovery...")
    print(f"[Streaming] Using 20-second scan windows (handles intermittent BLE)")
    print(f"[Streaming] Target: {stable_count} consecutive discoveries, {check_interval}s apart")
    print()
    
    consecutive_found = 0
    attempt = 0
    
    # Create a new adapter instance with extended scan window
    discovery_adapter = adapter if hasattr(adapter, 'scan_seconds') else type(adapter)(scan_seconds=20)
    if discovery_adapter is adapter and not hasattr(adapter, 'scan_seconds'):
        discovery_adapter = type(adapter)(scan_seconds=20)
        discovery_adapter.initialize_sdk()
    
    while consecutive_found < stable_count:
        attempt += 1
        devices = discovery_adapter.discover_devices(timeout_seconds=20)
        
        found = any(d["serial"] == target_serial for d in devices)
        
        if found:
            consecutive_found += 1
            status = f"✅ Found ({consecutive_found}/{stable_count})"
        else:
            consecutive_found = 0
            status = "❌ Not visible (reset counter)"
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] Scan attempt {attempt:2d}: {status}")
        
        if consecutive_found < stable_count:
            time.sleep(check_interval)
    
    print()
    print("🟢 Headset is stable - proceeding with connection")
    print()
    return True


def main():
    print("=" * 70)
    print("DIAGNOSTIC STREAMING - Resilient Connection")
    print("=" * 70)
    print()

    # Use extended scan window to handle intermittent BLE advertisements
    adapter = CapsuleAdapter(scan_seconds=20)
    
    print("[Streaming] Initializing SDK...")
    adapter.initialize_sdk()
    print()
    
    # Wait for stable discovery
    try:
        if not wait_for_stable_discovery(adapter):
            print("❌ Failed to achieve stable discovery")
            return
    except KeyboardInterrupt:
        print()
        print("[Streaming] Interrupted during discovery wait")
        return
    
    target_serial = "821108"
    
    print("[Streaming] Connecting to serial 821108...")
    try:
        # Use retry logic to handle intermittent BLE advertisements during connection
        info = adapter.connect(serial=target_serial, bipolar_channels=True, retry_count=5)
        print(f"✅ Connected successfully!")
        print(f"   Name:            {info['name']}")
        print(f"   Serial:          {info['serial']}")
        print(f"   Type:            {info['type']}")
        print(f"   EEG Sample Rate: {info['eeg_sample_rate']} Hz")
        print()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    print("[Streaming] Starting realtime EEG stream...")
    print()
    try:
        adapter.start_stream()
    except Exception as e:
        print(f"❌ Stream start failed: {e}")
        adapter.shutdown()
        return
    
    print("=" * 70)
    print("STREAMING ACTIVE - Capturing callbacks for 30 seconds")
    print("=" * 70)
    print()
    print("Expected callbacks:")
    print("  • Battery updates")
    print("  • Resistance measurements")
    print("  • EEG packets")
    print("  • Productivity metrics")
    print("  • Physiological states")
    print()
    print("-" * 70)
    print()
    
    try:
        start_time = time.time()
        duration = 30  # seconds
        
        while time.time() - start_time < duration:
            adapter.locator.update()
            time.sleep(0.01)
        
        elapsed = time.time() - start_time
        print()
        print("-" * 70)
        print()
        print("=" * 70)
        print(f"✅ STREAMING COMPLETED - Ran for {elapsed:.1f} seconds")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print()
        print("[Streaming] Interrupted by user")
    finally:
        print()
        print("[Streaming] Shutting down...")
        adapter.shutdown()
        print("✅ Cleanup complete")


if __name__ == "__main__":
    main()
