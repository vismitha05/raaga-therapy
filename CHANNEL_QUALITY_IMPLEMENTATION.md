# Resistance & Channel Quality System - Implementation Summary

## Overview

The resistance quality system replicates the channel-quality indicators shown in the official Neiry software. It continuously monitors EEG electrode impedance and exposes real-time quality indicators through the WebSocket API.

## What Was Implemented

### 1. **Resistance Quality Analyzer** ✅
**File**: [backend/adaptive_backend/eeg/resistance_analyzer.py](backend/adaptive_backend/eeg/resistance_analyzer.py)

Maps impedance/resistance values to quality indicators:
- **GOOD** (< 50 kΩ): Excellent signal quality
- **WARNING** (50-100 kΩ): Acceptable but marginal
- **BAD** (> 100 kΩ): Poor contact, high noise

Key methods:
```python
ResistanceQualityAnalyzer.analyze_channel(resistance_ohms)  # Single channel
ResistanceQualityAnalyzer.analyze_all(channel_resistance)   # All channels
ResistanceQualityAnalyzer.is_headset_ready(channel_quality) # Ready flag
```

### 2. **Enhanced Runtime Metrics Store** ✅
**File**: [backend/adaptive_backend/eeg/runtime_metrics_store.py](backend/adaptive_backend/eeg/runtime_metrics_store.py)

New fields in `RuntimeMetricsSnapshot`:
```python
channel_resistance: Dict[str, float]                    # Raw Ω values
channel_quality: Dict[str, "GOOD|WARNING|BAD"]          # Quality per channel  
headset_ready: bool                                      # Ready flag
```

New method:
```python
def update_channel_quality(channel_quality, headset_ready)
```

### 3. **Enhanced EEG Callbacks** ✅
**File**: [backend/adaptive_backend/eeg/eeg_callbacks.py](backend/adaptive_backend/eeg/eeg_callbacks.py)

The `on_resistance()` callback now:
1. Receives raw resistance values
2. Analyzes each channel → quality classification
3. Computes headset_ready flag
4. Prints detailed quality info to console
5. Stores in runtime metrics

Example console output:
```
[Capsule] resistance: {'AF3': 35000.0, 'F3': 45000.0, ...}
[Capsule] channel quality: {'AF3': 'GOOD', 'F3': 'GOOD', ...}
[Capsule] quality summary: GOOD=6 WARNING=2 BAD=1
[Capsule] headset ready: False
```

### 4. **WebSocket Payload Updates** ✅
**File**: [backend/adaptive_backend/services/realtime/monitoring_service.py](backend/adaptive_backend/services/realtime/monitoring_service.py)

The `_capsule_ws_payload()` function now exposes:

```json
{
  "channel_quality": {
    "AF3": "GOOD",
    "F3": "GOOD", 
    "FC5": "WARNING",
    "T7": "BAD",
    ...
  },
  "headset_ready": false,
  "resistance": {
    "AF3": 35000,
    "F3": 45000,
    ...
  },
  ...
}
```

## WebSocket Fields for Frontend

### Channel Quality Indicator
**Field**: `channel_quality`
**Type**: `Dict[str, "GOOD" | "WARNING" | "BAD"]`
**Source**: `channel_quality` in websocket message
**Purpose**: Display per-channel electrode quality

**Rendering guidance**:
```typescript
const colorMap = {
  "GOOD": "#22c55e",    // Green
  "WARNING": "#eab308", // Yellow
  "BAD": "#ef4444"      // Red
};

message.channel_quality.forEach((channel, quality) => {
  const color = colorMap[quality];
  renderChannelIndicator(channel, quality, color);
});
```

### Headset Ready State
**Field**: `headset_ready`
**Type**: `boolean`
**Source**: `headset_ready` in websocket message
**Purpose**: Signal if headset is ready for therapy session

**Logic**:
```typescript
if (message.headset_ready) {
  // ✅ All channels are GOOD or WARNING
  // → Enable "Start Therapy" button
  // → Show: "Headset Ready"
} else {
  // ❌ At least one channel is BAD
  // → Disable "Start Therapy" button
  // → Show: "Please adjust headset fit"
}
```

## How the Pipeline Works

```
┌─────────────────────────────────────────────────────────────┐
│ 1. HARDWARE: Capsule Headset                                │
│    - Continuously measures electrode impedance              │
│    - Calls: on_resistance() with raw Ω values               │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 2. ANALYSIS: ResistanceQualityAnalyzer                      │
│    - Maps each Ω value → GOOD | WARNING | BAD               │
│    - Computes headset_ready flag                            │
│    - Thresholds: GOOD<50kΩ, WARNING<100kΩ, BAD>100kΩ       │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 3. STORAGE: RuntimeMetricsStore                             │
│    - channel_resistance (raw values)                        │
│    - channel_quality (GOOD/WARNING/BAD)                     │
│    - headset_ready (boolean)                                │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 4. BROADCAST: WebSocket via /ws/live                        │
│    - Every tick: Send _capsule_ws_payload()                 │
│    - Includes: channel_quality + headset_ready              │
│    - To: All connected frontend clients                     │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 5. FRONTEND: Real-time Quality Display                      │
│    - Render channel quality indicators                      │
│    - Show headset ready state                               │
│    - Control therapy start button                           │
└─────────────────────────────────────────────────────────────┘
```

## Files Modified

| File | Changes | Purpose |
|------|---------|---------|
| [eeg_callbacks.py](backend/adaptive_backend/eeg/eeg_callbacks.py) | Enhanced `on_resistance()` | Analyze and classify channel quality |
| [runtime_metrics_store.py](backend/adaptive_backend/eeg/runtime_metrics_store.py) | Added quality fields + method | Store and expose quality metrics |
| [monitoring_service.py](backend/adaptive_backend/services/realtime/monitoring_service.py) | Updated websocket payload | Broadcast quality to frontend |

## Files Added

| File | Purpose |
|------|---------|
| [resistance_analyzer.py](backend/adaptive_backend/eeg/resistance_analyzer.py) | Quality classification logic |
| [CHANNEL_QUALITY_SYSTEM.md](backend/CHANNEL_QUALITY_SYSTEM.md) | Detailed system documentation |
| [verify_channel_quality.py](verify_channel_quality.py) | Verification script |

## Verification

Run the verification script:
```bash
python verify_channel_quality.py
```

Expected output:
```
[5.0s] Quality Update:
------
  AF3    ✅ GOOD          35000 Ω
  F3     ✅ GOOD          45000 Ω
  FC5    ⚠️  WARNING        75000 Ω
  T7     ❌ BAD           250000 Ω
  
  Summary: GOOD=6 WARNING=2 BAD=1
  Headset Ready: ❌ NO
  
  WebSocket Payload (sample):
    channel_quality: {'AF3': 'GOOD', 'F3': 'GOOD', 'FC5': 'WARNING', 'T7': 'BAD', ...}
    headset_ready: False
```

## Frontend Integration Checklist

- [ ] Connect to WebSocket endpoint `/ws/live`
- [ ] Extract `channel_quality` from each message
- [ ] Extract `headset_ready` from each message
- [ ] Render channel quality indicators with color coding (GOOD=green, WARNING=yellow, BAD=red)
- [ ] Display headset ready status prominently
- [ ] Disable "Start Therapy" button if `headset_ready == false`
- [ ] Show helpful message: "Please adjust headset fit" when `headset_ready == false`

## Configuration

Threshold values are in [resistance_analyzer.py](backend/adaptive_backend/eeg/resistance_analyzer.py):

```python
QUALITY_THRESHOLDS = {
    "GOOD": 50_000,      # < 50 kΩ
    "WARNING": 100_000,  # 50-100 kΩ
}
# > 100 kΩ = BAD
```

To adjust, edit and restart backend.

## What's NOT Modified

✅ Therapy logic (unchanged)  
✅ Calibration logic (unchanged)  
✅ Frontend code (ready for integration)  
✅ EEG streaming (continues normally)

## Next Steps

1. **Frontend**: Integrate channel quality display
2. **Frontend**: Show headset ready indicator
3. **Frontend**: Control therapy button based on `headset_ready`
4. **Testing**: Run full integration test
5. **Documentation**: Update frontend dev docs
