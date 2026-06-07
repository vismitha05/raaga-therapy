import time
import json
from collections import Counter

LOG = "backend/classification_trace.log"
WAIT = 30
print(f"Waiting {WAIT}s to collect logs in {LOG}...")
# Wait for logging to accumulate
time.sleep(WAIT)

counts = Counter()
runtime_counts = Counter()
lines = 0
try:
    with open(LOG, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            lines += 1
            try:
                obj = json.loads(line)
            except Exception:
                continue
            ev = obj.get("event") or obj.get("event")
            if ev == "classification_instant":
                src = obj.get("data_source", "UNKNOWN")
                counts[src] += 1
            elif ev == "derived_state":
                src = obj.get("data_source", "UNKNOWN")
                counts[f"derived_{src}"] += 1
            elif ev == "runtime_update":
                runtime_counts[obj.get("source", "UNKNOWN")] += 1
except FileNotFoundError:
    print("Log file not found:", LOG)
    raise

print("\nClassification log summary:")
print(f"Total log lines: {lines}")
print(f"Instant classifications: {sum(counts.values())}")
for k, v in counts.items():
    print(f"  {k}: {v}")
print("\nDerived-state events:")
for k, v in counts.items():
    if k.startswith("derived_"):
        print(f"  {k}: {v}")
print("\nRuntime updates (which source drove runtime_store updates):")
for k, v in runtime_counts.items():
    print(f"  {k}: {v}")

print("\nDone.")
