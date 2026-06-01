#!/usr/bin/env python3
"""
Channel Quality Verification Script
====================================
Tests the resistance quality pipeline and headset ready flag.

Verifies:
1. Resistance callbacks received
2. Channel quality classification
3. Headset ready flag computation
4. WebSocket payload generation
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from adaptive_backend.eeg.capsule_adapter import CapsuleAdapter
from adaptive_backend.services.realtime.monitoring_service import _capsule_ws_payload
from adaptive_backend.eeg.runtime_metrics_store import runtime_metrics_store


def main():
    print("=" * 70)
    print("CHANNEL QUALITY VERIFICATION")
    print("=" * 70)
    print()

    # Use extended scan window
    adapter = CapsuleAdapter(scan_seconds=20)
    
    print("[Verify] Initializing SDK...")
    adapter.initialize_sdk()
    print()
    
    print("[Verify] Scanning for headset...")
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
    
    print("[Verify] Connecting with aggressive retries...")
    try:
        info = adapter.connect(serial="821108", bipolar_channels=True, retry_count=10)
        print(f"✅ Connected successfully!")
        print()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    print("[Verify] Starting stream...")
    try:
        adapter.start_stream()
    except Exception as e:
        print(f"❌ Stream start failed: {e}")
        adapter.shutdown()
        return
    
    print("=" * 70)
    print("CAPTURING CHANNEL QUALITY DATA - 20 seconds")
    print("=" * 70)
    print()
    
    try:
        start_time = time.time()
        duration = 20
        last_quality_print = 0
        
        while time.time() - start_time < duration:
            adapter.locator.update()
            
            # Check for quality updates every 2 seconds
            elapsed = time.time() - start_time
            if elapsed - last_quality_print >= 2:
                last_quality_print = elapsed
                
                # Get current snapshot
                snapshot = runtime_metrics_store.snapshot()
                
                if snapshot.get("channel_quality"):
                    print(f"\n[{elapsed:5.1f}s] Quality Update:")
                    print("-" * 70)
                    
                    # Show resistance and quality
                    channel_quality = snapshot.get("channel_quality", {})
                    channel_resistance = snapshot.get("channel_resistance", {})
                    headset_ready = snapshot.get("headset_ready", False)
                    
                    for channel in sorted(channel_quality.keys()):
                        quality = channel_quality[channel]
                        resistance = channel_resistance.get(channel, "?")
                        
                        # Colorize output
                        if quality == "GOOD":
                            status_str = "✅ GOOD"
                        elif quality == "WARNING":
                            status_str = "⚠️  WARNING"
                        else:
                            status_str = "❌ BAD"
                        
                        if isinstance(resistance, (int, float)):
                            print(f"  {channel:6s} {status_str:15s} {resistance:>10.0f} Ω")
                        else:
                            print(f"  {channel:6s} {status_str:15s} {resistance:>10s}")
                    
                    # Show summary
                    stats = {"GOOD": 0, "WARNING": 0, "BAD": 0}
                    for q in channel_quality.values():
                        stats[q] += 1
                    
                    print()
                    print(f"  Summary: GOOD={stats['GOOD']} WARNING={stats['WARNING']} BAD={stats['BAD']}")
                    print(f"  Headset Ready: {'✅ YES' if headset_ready else '❌ NO'}")
                    
                    # Show WebSocket payload sample
                    payload = _capsule_ws_payload()
                    print()
                    print("  WebSocket Payload (sample):")
                    print(f"    channel_quality: {payload.get('channel_quality')}")
                    print(f"    headset_ready: {payload.get('headset_ready')}")
                    print("-" * 70)
            
            time.sleep(0.01)
        
        print()
        print("=" * 70)
        print("✅ VERIFICATION COMPLETE")
        print("=" * 70)
        
        # Final summary
        final_snapshot = runtime_metrics_store.snapshot()
        print()
        print("Final State:")
        print(f"  Device Connected: {final_snapshot.get('device_connected')}")
        print(f"  EEG Packets Received: {final_snapshot.get('eeg_packets_received')}")
        print(f"  Battery: {final_snapshot.get('battery_percent')}%")
        print(f"  Total Channels: {len(final_snapshot.get('channel_quality', {}))}")
        print(f"  Headset Ready: {final_snapshot.get('headset_ready')}")
        
        print()
        print("Next Steps:")
        print("1. Frontend should subscribe to /ws/live")
        print("2. Render channel_quality indicators with color coding")
        print("3. Show headset_ready state prominently")
        print("4. Disable therapy start until headset_ready = True")
        
    except KeyboardInterrupt:
        print()
        print("[Verify] Interrupted by user")
    finally:
        print()
        print("[Verify] Shutting down...")
        adapter.shutdown()
        print("✅ Cleanup complete")


if __name__ == "__main__":
    main()
