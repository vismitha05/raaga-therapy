#!/usr/bin/env python3
"""
Immediate Connection Streaming
================================
Attempts connection immediately after first successful discovery,
without waiting for stable advertisement pattern.
Useful for devices with aggressive intermittent BLE patterns.
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from adaptive_backend.eeg.capsule_adapter import CapsuleAdapter


def main():
    print("=" * 70)
    print("IMMEDIATE CONNECTION STREAMING")
    print("=" * 70)
    print()
    print("Strategy: Scan, discover, and connect immediately")
    print("(Bypasses stability check for intermittent BLE devices)")
    print()

    # Use extended scan window
    adapter = CapsuleAdapter(scan_seconds=20)
    
    print("[Connection] Initializing SDK...")
    adapter.initialize_sdk()
    print()
    
    print("[Connection] Scanning for headset (20-second window)...")
    devices = adapter.discover_devices(timeout_seconds=20)
    
    if not devices:
        print("❌ Failed to discover headset in initial scan")
        return
    
    target = next((d for d in devices if d["serial"] == "821108"), None)
    if not target:
        print(f"❌ Target serial 821108 not found. Found: {[d['serial'] for d in devices]}")
        return
    
    print(f"✅ Headset discovered: {target['name']} ({target['serial']})")
    print()
    
    print("[Connection] Attempting immediate connection with aggressive retries...")
    print()
    try:
        # Use very aggressive retry (up to 10 attempts)
        info = adapter.connect(serial="821108", bipolar_channels=True, retry_count=10)
        print(f"✅ Connected successfully!")
        print(f"   Name:            {info['name']}")
        print(f"   Serial:          {info['serial']}")
        print(f"   Type:            {info['type']}")
        print(f"   EEG Sample Rate: {info['eeg_sample_rate']} Hz")
        print()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("[Connection] Starting realtime EEG stream...")
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
    print("  • Connection status changes")
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
        print("[Connection] Interrupted by user")
    finally:
        print()
        print("[Connection] Shutting down...")
        adapter.shutdown()
        print("✅ Cleanup complete")


if __name__ == "__main__":
    main()
