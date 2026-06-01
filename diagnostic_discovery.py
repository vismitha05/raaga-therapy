#!/usr/bin/env python3
"""
Diagnostic Discovery Script
============================
Scans for Capsule devices using DeviceType.Any to determine visibility across all device types.

Requirements met:
1. No connection - scan only
2. No streaming - scan only
3. DeviceType.Any search
4. Prints device details: name, serial, type
5. Prints total count
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from adaptive_backend.eeg.capsule_adapter import CapsuleAdapter


def main():
    print("=" * 70)
    print("DIAGNOSTIC DISCOVERY - DeviceType.Any")
    print("=" * 70)
    print()

    adapter = CapsuleAdapter()
    
    print("[Diagnostic] Initializing SDK...")
    adapter.initialize_sdk()
    
    print("[Diagnostic] Running discovery with DeviceType.Any (no connect, no stream)...")
    print()
    
    devices = adapter.discover_devices_diagnostic(timeout_seconds=15)
    
    print()
    print("=" * 70)
    print("DISCOVERY RESULTS")
    print("=" * 70)
    print()
    
    if not devices:
        print("⚠️  No devices discovered")
    else:
        print(f"📊 Total Devices Found: {len(devices)}")
        print()
        for idx, device in enumerate(devices, 1):
            print(f"Device #{idx}:")
            print(f"  Name:   {device['name']}")
            print(f"  Serial: {device['serial']}")
            print(f"  Type:   {device['type']}")
            print()
    
    print("=" * 70)
    print(f"TOTAL COUNT: {len(devices)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
