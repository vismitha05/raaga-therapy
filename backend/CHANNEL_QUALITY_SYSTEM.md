# Headset Channel Quality System

## Overview

The channel quality system monitors EEG electrode impedance/resistance and provides real-time quality indicators, similar to the official Neiry software interface.

## Quality Classification

Each EEG channel is classified into one of three quality levels based on its impedance:

| Quality | Resistance Range | Description |
|---------|------------------|-------------|
| **GOOD** | < 50 kΩ | Excellent signal quality, ideal electrode contact |
| **WARNING** | 50-100 kΩ | Acceptable but marginal, may have increased noise |
| **BAD** | > 100 kΩ | Poor electrode contact, high noise, unreliable data |

## Channel Quality Pipeline

### 1. **Hardware Level**: Resistance Measurement
- The Capsule headset continuously measures electrode impedance
- Callback: `on_resistance()` is triggered with raw resistance values per channel
- Values reported in Ohms (Ω)

### 2. **Analysis Level**: Quality Mapping
```python
# Location: backend/adaptive_backend/eeg/eeg_callbacks.py
on_resistance() {
  → channel_resistance = {"AF3": 35000, "F3": 45000, "FC5": 75000, ...}
  → analyze_all(channel_resistance)  # Maps each to GOOD/WARNING/BAD
  → channel_quality = {"AF3": "GOOD", "F3": "GOOD", "FC5": "WARNING", ...}
}
```

### 3. **Storage Level**: Runtime Metrics
```python
# Location: backend/adaptive_backend/eeg/runtime_metrics_store.py
RuntimeMetricsSnapshot {
  channel_resistance: Dict[str, float]           # Raw Ω values
  channel_quality: Dict[str, "GOOD|WARNING|BAD"]  # Quality per channel
  headset_ready: bool                              # Ready flag
}
```

### 4. **Readiness Check**: Headset Ready Flag
```python
headset_ready = True  # Only if NO channels are "BAD"
```

The `headset_ready` flag is:
- ✅ **True**: All channels are GOOD or WARNING (safe to start therapy)
- ❌ **False**: At least one channel is BAD (user should adjust fit)

## WebSocket API

### Broadcast Message Structure

Every tick (default: 100ms), the monitoring service broadcasts:

```json
{
  "capsule_eeg_status": "live|waiting",
  "battery": 85,
  "resistance": {
    "AF3": 35000,
    "F3": 45000,
    "FC5": 75000,
    "T7": 250000,
    ...
  },
  "channel_quality": {
    "AF3": "GOOD",
    "F3": "GOOD",
    "FC5": "WARNING",
    "T7": "BAD",
    ...
  },
  "headset_ready": false,
  "focus": 0.45,
  "relaxation": 0.62,
  "fatigue": 0.15,
  "stress": 0.20,
  "physiological_states": { ... }
}
```

### WebSocket Endpoint

```
POST /ws/live
Content-Type: application/json
```

## Frontend Integration Points

### 1. **Channel Quality Indicator Display**
```typescript
// From: channel_quality field in websocket message
const channelQualities = message.channel_quality;
// Example: { "AF3": "GOOD", "F3": "WARNING", ... }

// Render each channel with color coding:
const colorMap = {
  "GOOD": "#22c55e",      // Green
  "WARNING": "#eab308",   // Yellow  
  "BAD": "#ef4444"        // Red
};
```

### 2. **Headset Ready State**
```typescript
// From: headset_ready field in websocket message
const isReady = message.headset_ready;

// Show UI indicator:
if (isReady) {
  // Display: "✅ Headset Ready"
  // Enable: Start Therapy button
} else {
  // Display: "⚠️ Adjust Fit" or "❌ Poor Signal"
  // Disable: Start Therapy button
}
```

### 3. **Resistance Raw Values (Advanced)**
```typescript
// From: resistance field in websocket message
const resistanceValues = message.resistance;
// Example: { "AF3": 35000, "F3": 45000, ... }

// Optional: Show impedance graph or heatmap
```

## Backend Files

### New/Modified Files

1. **[resistance_analyzer.py](resistance_analyzer.py)** (NEW)
   - `ResistanceQualityAnalyzer` class
   - Threshold mapping: GOOD/WARNING/BAD
   - `is_headset_ready()` logic

2. **[eeg_callbacks.py](eeg_callbacks.py)** (MODIFIED)
   - `on_resistance()` now calls analyzer
   - Prints quality per channel
   - Stores channel_quality in runtime metrics

3. **[runtime_metrics_store.py](runtime_metrics_store.py)** (MODIFIED)
   - Added `channel_quality` field to snapshot
   - Added `headset_ready` flag
   - New `update_channel_quality()` method

4. **[monitoring_service.py](monitoring_service.py)** (MODIFIED)
   - `_capsule_ws_payload()` now includes:
     - `channel_quality`
     - `headset_ready`

## Console Output Example

When resistance data arrives:

```
[Capsule] resistance: {'AF3': 35000.0, 'F3': 45000.0, 'FC5': 75000.0, 'T7': 250000.0, ...}
[Capsule] channel quality: {'AF3': 'GOOD', 'F3': 'GOOD', 'FC5': 'WARNING', 'T7': 'BAD', ...}
[Capsule] quality summary: GOOD=6 WARNING=2 BAD=1
[Capsule] headset ready: False
```

## Configuration

Threshold values (in Ohms) are defined in [resistance_analyzer.py](resistance_analyzer.py):

```python
QUALITY_THRESHOLDS = {
    "GOOD": 50_000,      # < 50 kΩ
    "WARNING": 100_000,  # 50-100 kΩ
}
# > 100 kΩ = BAD
```

To adjust thresholds, edit the `QUALITY_THRESHOLDS` dict and restart the backend.

## Future Enhancements

1. **Adaptive Thresholds**: Adjust based on electrode type and placement
2. **Historical Trend**: Track quality degradation over time
3. **User Feedback**: Suggest which electrode to adjust
4. **Calibration Integration**: Use quality metrics during impedance calibration
5. **Per-Frequency Analysis**: Separate quality by frequency band (alpha, beta, theta)

## Verification Checklist

- [x] Resistance callbacks received after connection
- [x] Raw resistance values printed per channel
- [x] Channel quality mapped (GOOD/WARNING/BAD)
- [x] Headset ready flag computed correctly
- [x] WebSocket payload includes channel_quality
- [x] WebSocket payload includes headset_ready
- [x] Frontend-ready JSON format
- [x] No modifications to therapy logic
- [x] No modifications to calibration logic (yet)
