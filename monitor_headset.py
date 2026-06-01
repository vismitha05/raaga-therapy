#!/usr/bin/env python3
"""
Headset Discovery Monitor
============================
Continuously monitors for headset availability.
Useful when headset needs to be power-cycled.
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
    print("HEADSET DISCOVERY MONITOR")
    print("=" * 70)
    print()
    print("Monitoring for headset with serial 821108")
    print("Press Ctrl+C to stop")
    print()

    adapter = CapsuleAdapter()
    adapter.initialize_sdk()
    
    attempt = 0
    discovered_time = None
    
    try:
        while True:
            attempt += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            devices = adapter.discover_devices(timeout_seconds=10)
            
            if devices:
                for dev in devices:
                    if dev["serial"] == "821108":
                        if not discovered_time:
                            print()
                            print("🟢 " + "=" * 66)
                            print(f"✅ HEADSET DISCOVERED at {timestamp}")
                            print("=" * 70)
                            print(f"  Name:   {dev['name']}")
                            print(f"  Serial: {dev['serial']}")
                            print(f"  Type:   {dev['type']}")
                            print("=" * 70)
                            print()
                            discovered_time = timestamp
                        else:
                            print(f"[{timestamp}] ✅ Still visible (attempt #{attempt})")
                    else:
                        print(f"[{timestamp}] Found different device: {dev['name']} ({dev['serial']})")
            else:
                status = "❌ Not discoverable" if not discovered_time else "⚠️  Lost connection"
                print(f"[{timestamp}] {status} (attempt #{attempt})")
            
            time.sleep(2)
    
    except KeyboardInterrupt:
        print()
        print("Monitor stopped by user")


if __name__ == "__main__":
    main()
