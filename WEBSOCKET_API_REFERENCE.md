# WebSocket API Reference - Channel Quality & Headset Ready

## Endpoint

```
URL: ws://localhost:8000/ws/live
Method: WebSocket
Protocol: JSON
```

## Message Format

Every tick (default: 100ms), the server broadcasts a JSON object with the following structure:

```json
{
  "eeg_status": "live|waiting",
  "detected_state": "Focused|Relaxed|Sleepy|Connecting",
  "confidence": 0.75,
  "timestamp": "2026-05-30T10:35:42.123456",
  
  "capsule_eeg_status": "live|waiting",
  "battery": 85,
  
  "resistance": {
    "AF3": 35000.0,
    "F3": 45000.0,
    "FC5": 75000.0,
    "T7": 250000.0,
    "FP1": 32000.0,
    "FP2": 38000.0,
    "AF4": 42000.0,
    "F4": 48000.0,
    "FC6": 65000.0,
    "T8": 220000.0,
    "P7": 55000.0,
    "P8": 58000.0,
    "O1": 120000.0,
    "O2": 130000.0
  },
  
  "channel_quality": {
    "AF3": "GOOD",
    "F3": "GOOD",
    "FC5": "WARNING",
    "T7": "BAD",
    "FP1": "GOOD",
    "FP2": "GOOD",
    "AF4": "GOOD",
    "F4": "GOOD",
    "FC6": "WARNING",
    "T8": "BAD",
    "P7": "WARNING",
    "P8": "WARNING",
    "O1": "BAD",
    "O2": "BAD"
  },
  
  "headset_ready": false,
  
  "focus": 0.65,
  "relaxation": 0.42,
  "fatigue": 0.15,
  "stress": 0.22,
  
  "physiological_states": {
    "timestamp_milli": 1234567890,
    "relaxation": 0.42,
    "fatigue": 0.15,
    "stress": 0.22,
    "concentration": 0.65,
    "involvement": 0.58,
    "none": 0.01,
    "nfb_artifacts": false,
    "cardio_artifacts": false
  }
}
```

## Channel Quality Fields

### 1. `channel_quality`
**Type**: `Object<string, "GOOD" | "WARNING" | "BAD">`

Maps each EEG channel to its quality level based on electrode impedance.

**Possible values per channel**:
- `"GOOD"`: Impedance < 50 kΩ (excellent contact)
- `"WARNING"`: Impedance 50-100 kΩ (acceptable but marginal)
- `"BAD"`: Impedance > 100 kΩ (poor contact, high noise)

**Example**:
```json
{
  "channel_quality": {
    "AF3": "GOOD",
    "F3": "GOOD",
    "FC5": "WARNING",
    "T7": "BAD"
  }
}
```

**Frontend usage**:
```typescript
// Subscribe to WebSocket messages
websocket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  const channelQualities = data.channel_quality;
  
  // Display quality for each channel
  Object.entries(channelQualities).forEach(([channel, quality]) => {
    const color = {
      "GOOD": "#22c55e",     // Green
      "WARNING": "#eab308",  // Amber/Yellow
      "BAD": "#ef4444"       // Red
    }[quality];
    
    updateChannelIndicator(channel, quality, color);
  });
};
```

### 2. `headset_ready`
**Type**: `boolean`

Indicates whether the headset is ready for therapy session.

**True when**:
- All EEG channels have quality `"GOOD"` or `"WARNING"`
- NO channels have quality `"BAD"`

**False when**:
- At least ONE channel has quality `"BAD"`

**Example**:
```json
{
  "headset_ready": true
}
```

**Frontend usage**:
```typescript
websocket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  const isReady = data.headset_ready;
  
  if (isReady) {
    // Enable therapy start
    document.getElementById("start-button").disabled = false;
    document.getElementById("status").innerText = "✅ Headset Ready";
    document.getElementById("status").className = "status-ready";
  } else {
    // Disable therapy start
    document.getElementById("start-button").disabled = true;
    document.getElementById("status").innerText = "⚠️ Adjust headset fit";
    document.getElementById("status").className = "status-warning";
  }
};
```

## Related Fields (Context)

### `resistance`
**Type**: `Object<string, number>`

Raw impedance values in Ohms (Ω) for each channel. Use `channel_quality` for UI display; this is for advanced diagnostics.

### `battery`
**Type**: `number` (0-100)

Battery percentage of the headset.

### `capsule_eeg_status`
**Type**: `"live" | "waiting"`

Whether EEG data is actively streaming from the headset.

## Connection Example

```typescript
// React Hook
import { useEffect, useState } from 'react';

export function HeadsetQualityDisplay() {
  const [channelQuality, setChannelQuality] = useState({});
  const [headsetReady, setHeadsetReady] = useState(false);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/live');
    
    ws.onopen = () => {
      setConnected(true);
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setChannelQuality(data.channel_quality || {});
      setHeadsetReady(data.headset_ready || false);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnected(false);
    };
    
    return () => ws.close();
  }, []);

  if (!connected) {
    return <div>Connecting to headset...</div>;
  }

  return (
    <div className="headset-quality">
      <div className="status-indicator" style={{
        backgroundColor: headsetReady ? '#22c55e' : '#ef4444'
      }}>
        {headsetReady ? '✅ Ready' : '❌ Not Ready'}
      </div>
      
      <div className="channels">
        {Object.entries(channelQuality).map(([channel, quality]) => {
          const colorMap = {
            'GOOD': '#22c55e',
            'WARNING': '#eab308',
            'BAD': '#ef4444'
          };
          return (
            <div key={channel} className="channel" style={{
              backgroundColor: colorMap[quality]
            }}>
              <span className="channel-name">{channel}</span>
              <span className="channel-quality">{quality}</span>
            </div>
          );
        })}
      </div>
      
      <button 
        disabled={!headsetReady}
        onClick={handleStartTherapy}
      >
        Start Therapy
      </button>
    </div>
  );
}
```

## Message Frequency

Messages are broadcast every tick at the configured poll interval (default: 100ms).

The `channel_quality` and `headset_ready` fields update whenever:
1. Resistance data arrives from the headset (typically every 1-2 seconds)
2. Or at every tick if resistance hasn't changed

## Error Handling

The server always includes these fields, but they may be:
- `null` if headset is disconnected
- `{}` (empty object) if no channels have been measured yet

Always check for null/undefined before accessing:

```typescript
const quality = data.channel_quality || {};
const ready = data.headset_ready ?? false;
```

## Testing

### Manual WebSocket Test
```bash
# In browser console
const ws = new WebSocket('ws://localhost:8000/ws/live');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

### Python Test
```python
import asyncio
import json
import websockets

async def test():
    uri = "ws://localhost:8000/ws/live"
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Channel Quality: {data.get('channel_quality')}")
            print(f"Headset Ready: {data.get('headset_ready')}")
```

## Notes

- `channel_quality` contains an entry for each EEG electrode on the headset (typically 10-14 channels for a standard EEG band)
- `headset_ready` is computed as: `not any(q == "BAD" for q in channel_quality.values())`
- Quality thresholds are defined in backend (currently: GOOD<50kΩ, WARNING<100kΩ, BAD>100kΩ)
- To adjust thresholds, modify `backend/adaptive_backend/eeg/resistance_analyzer.py` and restart backend
