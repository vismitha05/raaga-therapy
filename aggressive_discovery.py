#!/usr/bin/env python3
"""
Aggressive Headset Discovery
=============================
Uses extended scan windows (15-20s) to catch intermittent BLE advertisements.
Attempts multiple rapid rescans to improve capture likelihood.
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from adaptive_backend.eeg.capsule_adapter import CapsuleAdapter


def aggressive_discovery(timeout_seconds=20, max_attempts=5):
    """
    Try multiple extended-window scans to catch intermittent BLE advertisements.
    """
    print("[Aggressive] Using extended scan windows (20 seconds each)")
    print(f"[Aggressive] Will attempt up to {max_attempts} rescans")
    print()
    
    adapter = CapsuleAdapter(scan_seconds=20)  # Extended from default 8 to 20 seconds
    adapter.initialize_sdk()
    
    target_serial = "821108"
    for attempt in range(1, max_attempts + 1):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] Scan attempt {attempt}/{max_attempts} (20s window)...")
        
        devices = adapter.discover_devices(timeout_seconds=timeout_seconds)
        
        if devices:
            for dev in devices:
                if dev["serial"] == target_serial:
                    print(f"  ✅ FOUND: {dev['name']} ({dev['serial']})")
                    return devices
                else:
                    print(f"  📡 Found: {dev['name']} ({dev['serial']})")
        else:
            print(f"  ❌ No devices found")
        
        if attempt < max_attempts:
            print(f"  ⏳ Waiting 3 seconds before next scan...")
            time.sleep(3)
        print()
    
    return None


def main():
    print("=" * 70)
    print("AGGRESSIVE HEADSET DISCOVERY")
    print("=" * 70)
    print()
    print("Using extended 20-second scan windows to catch")
    print("intermittent BLE advertisements from the headset.")
    print()
    
    try:
        devices = aggressive_discovery(timeout_seconds=20, max_attempts=5)
        
        if devices:
            target = next((d for d in devices if d["serial"] == "821108"), None)
            if target:
                print("=" * 70)
                print("🟢 SUCCESS - Headset is discoverable")
                print("=" * 70)
                print(f"Name:   {target['name']}")
                print(f"Serial: {target['serial']}")
                print(f"Type:   {target['type']}")
                print()
                print("You can now run: python diagnostic_streaming.py")
            else:
                print("⚠️  Different devices found, but not 821108")
        else:
            print("=" * 70)
            print("❌ FAILED - Headset not found in any scan")
            print("=" * 70)
            print()
            print("Troubleshooting:")
            print("1. Ensure headset is powered ON")
            print("2. Move headset closer to PC (< 1 meter)")
            print("3. Check for radio interference")
            print("4. Try power-cycling the headset")
            print("5. Check Windows Bluetooth settings")
    
    except KeyboardInterrupt:
        print()
        print("[Aggressive] Interrupted by user")


if __name__ == "__main__":
    main()
