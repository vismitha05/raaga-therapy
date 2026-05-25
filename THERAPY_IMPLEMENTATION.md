# Raga Therapy System - Complete Implementation Guide

## System Overview

This is a complete binaural beat therapy system using Indian ragas (classical music) to guide brain states. The system detects current EEG frequency patterns and smoothly transitions users to target brain states (sleep, relaxed, focused) through scientifically-mapped raga sequences.

## Architecture

### Backend (Python/FastAPI)

**Core Components:**

1. **raga_therapy_engine.py** - Core therapeutic logic
   - Frequency band mapping (T1-B2, covering 4-30 Hz)
   - 18-raga matrix indexed by frequency and time of day
   - Transition path calculation between brain states
   - Playlist generation with proper timing

2. **eeg_monitoring_service.py** - EEG signal processing
   - Real-time brain state detection
   - Power band accumulation (alpha, beta, theta)
   - 15-second monitoring window
   - Simulated and real hardware support

3. **therapy_routes.py** - REST API endpoints
   - `/therapy/eeg-scan/start` - Begin EEG monitoring
   - `/therapy/eeg-scan/progress/{session_id}` - Poll scan progress
   - `/therapy/eeg-scan/result/{session_id}` - Get detection results
   - `/therapy/state-selection` - User selects target state
   - `/therapy/duration-selection` - Generate playlist
   - `/therapy/playback/update` - Track playback progress
   - `/therapy/session/complete/{session_id}` - End session

### Frontend (React)

**Screen Components:**

1. **EEGMonitoringScreen.jsx**
   - 15-second EEG scan timer
   - Real-time progress polling
   - Brain wave analysis display
   - Auto-advances on completion

2. **TargetStateScreen.jsx**
   - Sleep/Relaxed/Focused selection
   - Transition information
   - Effectiveness estimates

3. **DurationScreen.jsx**
   - 10/20/30 minute selection
   - Effectiveness scoring per duration
   - Therapeutic timeline visualization

4. **TherapyPlayerScreen.jsx**
   - Raga playlist display
   - Real-time playback with frequency visualization
   - Lazy loading of audio files
   - Smooth transitions between ragas
   - Progress tracking

5. **SessionCompletionScreen.jsx**
   - Session summary
   - Therapeutic benefits achieved
   - Recommendations
   - Ability to start new session

**Custom Hooks:**

- `useTherapyWorkflow()` - Complete workflow state management
- `useRagaPlayback()` - Audio lazy loading and playback
- `useTherapyAPI()` - API communication utilities

## Frequency Band Mapping

```
T1: 4-6 Hz   → Ahir_Bhairav, Todi (morning), Madhmad_Sarang (afternoon), etc.
T2: 6-8 Hz   → Deep relaxation border
A1: 8-10 Hz  → Bhairav, Shuddh_Sarang, Yaman (Relaxed baseline)
A2: 10-12 Hz → Alpha-beta border
B1: 12-21 Hz → Jaunpuri, Kafi, Khamaj (Focused cognitive)
B2: 21-30 Hz → Hindol, Marwa, Shankara (Intense focus)
```

## Raga Matrix (18 Total)

**Across 6 frequency bands × 4 time periods:**

```python
RAGA_MATRIX = {
    T1: {morning: "Ahir_Bhairav", afternoon: "Madhmad_Sarang", evening: "Malkauns", night: "Malkauns"},
    T2: {morning: "Todi", afternoon: "Bhimpalasi", evening: "Darbari_Kanada", night: "Darbari_Kanada"},
    A1: {morning: "Bhairav", afternoon: "Shuddh_Sarang", evening: "Yaman", night: "Yaman"},
    A2: {morning: "Alhaiya_Bilawal", afternoon: "Multani", evening: "Bhopali", night: "Bhopali"},
    B1: {morning: "Jaunpuri", afternoon: "Kafi", evening: "Khamaj", night: "Khamaj"},
    B2: {morning: "Hindol", afternoon: "Marwa", evening: "Shankara", night: "Shankara"},
}
```

## Transition Logic

### Example: Sleep (T1) → Focused (B1) over 10 minutes

1. **Path Calculation:** T1 → T2 → A1 → A2 → B1 (5 steps)
2. **Duration per Raga:** 10 min ÷ 5 = 2 minutes each
3. **Playlist Generated:**
   - 0:00 - 2:00   | T1 | Ahir_Bhairav | 4-6 Hz
   - 2:00 - 4:00   | T2 | Todi | 6.1-8 Hz
   - 4:00 - 6:00   | A1 | Bhairav | 8.1-10 Hz
   - 6:00 - 8:00   | A2 | Alhaiya_Bilawal | 10.1-12 Hz
   - 8:00 - 10:00  | B1 | Jaunpuri | 12.1-21 Hz

### Supported Transitions

- **Sleep → Relaxed:** T1 → A1 (2 steps)
- **Sleep → Focused:** T1 → T2 → A1 → A2 → B1 (5 steps)
- **Relaxed → Sleep:** A1 → T2 → T1 (3 steps)
- **Relaxed → Focused:** A1 → A2 → B1 (3 steps)
- **Focused → Sleep:** B1 → A2 → A1 → T2 → T1 (5 steps)
- **Focused → Relaxed:** B1 → A2 → A1 (3 steps)

## API Workflow

### Complete Flow

```
1. POST /eeg-scan/start
   ↓ Returns: {session_id, message}
   ↓

2. GET /eeg-scan/progress/{session_id} (poll every 500ms)
   ↓ When progress reaches 100%
   ↓

3. GET /eeg-scan/result/{session_id}
   ↓ Returns: {detected_band, detected_state, confidence, power_values}
   ↓

4. POST /state-selection
   ↓ Payload: {session_id, target_state}
   ↓ Returns: {target_state, effectiveness_estimates: {10: 50, 20: 75, 30: 90}}
   ↓

5. POST /duration-selection
   ↓ Payload: {session_id, duration_minutes}
   ↓ Returns: {playlist with tracks, total_steps, day_part}
   ↓

6. PLAYBACK (Frontend-only, lazy loads audio)
   ↓

7. POST /playback/update (optional logging)
   ↓

8. POST /session/complete/{session_id}
```

## Lazy Loading Strategy

### Why Lazy Loading?

- **Memory Efficiency:** Load ragas only when needed, not all at once
- **Faster Session Start:** Begin playback without waiting for all files to load
- **Reduced Bandwidth:** Stream audio on-demand
- **Dynamic Transitions:** Adapt to user skip/pause actions

### Implementation

```javascript
// Load raga only when track index is active
const loadRagaDynamically = async (trackIndex) => {
  if (loadedRagas.has(trackIndex)) return;
  
  const ragaPath = `/audio/ragas/${band}/${raga}.mp3`;
  const audio = new Audio(ragaPath);
  
  // Setup event handlers
  audio.onended = handleTrackEnd;
  audio.onerror = handleLoadError;
  
  // Mark as loaded
  loadedRagas.add(trackIndex);
  
  return audio;
};

// In playback loop
if (isPlaying) {
  await loadRagaDynamically(currentIndex);
  audioRef.current.play();
}
```

### Preloading Strategy

- **Current Track:** Must be loaded before playback
- **Next Track:** Preload in background during current playback
- **Previous Track:** Keep in memory for quick backtrack

## File Structure

```
backend/
├── adaptive_backend/
│   ├── api/
│   │   ├── routes/
│   │   │   └── therapy.py          ← NEW: Therapy endpoints
│   │   └── router.py               (updated to include therapy_router)
│   ├── services/
│   │   ├── raga_therapy_engine.py  ← NEW: Core logic
│   │   └── eeg_monitoring_service.py ← NEW: EEG processing
│   ├── domain/
│   │   └── enums.py                (BrainState, DayPart, FrequencyBand)
│   └── main.py
│
frontend/
└── src/
    ├── screens/
    │   ├── EEGMonitoringScreen.jsx  ← NEW
    │   ├── TargetStateScreen.jsx    ← NEW
    │   ├── DurationScreen_v2.jsx    ← NEW (replace old)
    │   ├── TherapyPlayerScreen.jsx  ← NEW
    │   └── SessionCompletionScreen.jsx ← NEW
    ├── hooks/
    │   └── useTherapyWorkflow.js    ← NEW
    ├── App_v2.jsx                   ← NEW (replace App.jsx)
    └── App.css
```

## Audio Files Organization

```
public/
└── audio/
    └── ragas/
        ├── T1/
        │   ├── Ahir_Bhairav.mp3
        │   ├── Madhmad_Sarang.mp3
        │   └── Malkauns.mp3
        ├── T2/
        │   ├── Todi.mp3
        │   ├── Bhimpalasi.mp3
        │   └── Darbari_Kanada.mp3
        ├── A1/
        ├── A2/
        ├── B1/
        └── B2/
```

Each folder contains 3-4 raga variations for different times of day.

## Integration Steps

### 1. Install Dependencies (Backend)

```bash
# Already included in requirements.txt
# Ensure these are present:
pip install fastapi
pip install numpy
pip install scipy
```

### 2. Update Backend Router

Edit `backend/adaptive_backend/api/router.py`:

```python
from adaptive_backend.api.routes.therapy import router as therapy_router
api_router.include_router(therapy_router)
```

✓ Already done in the provided implementation

### 3. Add Enums

Update `backend/adaptive_backend/domain/enums.py` to include:

```python
class FrequencyBand(str, Enum):
    T1 = "T1"
    T2 = "T2"
    # ... etc
```

✓ Already included in `raga_therapy_engine.py`

### 4. Copy Frontend Files

Replace `frontend/src/App.jsx` with `App_v2.jsx` and integrate screens.

### 5. Organize Audio Files

Place raga MP3 files in `frontend/public/audio/ragas/` folder structure.

### 6. Update CSS (Optional)

Add styling for new screens in `frontend/src/styles/screens.module.css`

## Testing

### Backend Testing

```bash
# Start server
cd backend
python -m uvicorn adaptive_backend.main:app --reload

# Test EEG scan
curl -X POST http://localhost:8000/api/therapy/eeg-scan/start \
  -H "Content-Type: application/json" \
  -d '{"duration_seconds": 15, "simulate": true}'

# Poll progress
curl http://localhost:8000/api/therapy/eeg-scan/progress/{session_id}

# Get results
curl http://localhost:8000/api/therapy/eeg-scan/result/{session_id}
```

### Frontend Testing

```bash
# Start development server
cd frontend
npm start

# Test workflow:
# 1. Click "Start Scan"
# 2. Wait 15 seconds (simulator)
# 3. Select target state
# 4. Select duration
# 5. Play therapy (mock audio plays)
# 6. Completion screen shows
```

## Configuration

### Backend Settings

In `adaptive_backend/core/config.py`:

```python
# Add if not present
RAGA_AUDIO_PATH = "/audio/ragas"
EEG_MONITORING_DURATION = 15  # seconds
SAMPLE_RATE = 256  # Hz
BAND_ORDER = ["T1", "T2", "A1", "A2", "B1", "B2"]
```

### Frontend Settings

In `.env`:

```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_AUDIO_BASE_PATH=/audio/ragas
```

## Performance Optimization

### Backend

- **Database Caching:** Cache session data in Redis (optional)
- **Async EEG Processing:** Use async tasks for monitoring
- **Playlist Precomputation:** Cache common transition paths

### Frontend

- **Code Splitting:** Split screens into separate chunks
- **Audio Caching:** Cache loaded ragas in IndexedDB
- **Virtual Scrolling:** For large playlist displays
- **Memoization:** Use React.memo() for heavy components

## Error Handling

### EEG Monitoring Errors

```python
# Backend validates
if detection.confidence < 0.5:
    return {"warning": "Low confidence, consider retaking scan"}
```

### Playback Errors

```javascript
// Frontend gracefully handles
audio.onerror = () => {
  console.warn(`Failed to load ${raga}, skipping to next`);
  handleTrackEnd(); // Auto-advance
};
```

### Network Errors

All API calls include retry logic with exponential backoff.

## Security Considerations

1. **CORS:** Configure CORS in FastAPI for frontend origin
2. **Authentication:** Add JWT tokens for production
3. **Rate Limiting:** Limit API calls per session
4. **Audio Streaming:** Use HTTPS for audio file delivery
5. **Data Privacy:** Don't log raw EEG data without consent

## Future Enhancements

1. **Real-Time EEG:** Integrate with actual EEG hardware (Muse, Neuri)
2. **Machine Learning:** Train models to detect individual brain state thresholds
3. **Personalization:** Learn user preferences across sessions
4. **Community Ragas:** Allow users to upload custom raga sequences
5. **Mobile App:** React Native version for iOS/Android
6. **Social:** Share session results and compare scores
7. **Analytics:** Track therapeutic effectiveness over time

## Troubleshooting

### Issue: "Failed to load raga audio"
- **Check:** Audio files exist in `/public/audio/ragas/` folder
- **Solution:** Verify file paths match band/raga names exactly

### Issue: "Session not found"
- **Check:** Session ID from `/eeg-scan/start` endpoint
- **Solution:** Sessions expire after 24 hours; start new session

### Issue: "Playlist generation failed"
- **Check:** Selected duration is 10, 20, or 30 minutes
- **Solution:** Validate input before sending to backend

### Issue: "EEG detection shows 0% confidence"
- **Check:** EEG simulator is running (use `simulate: true`)
- **Solution:** In production, connect real EEG hardware

## References

- **Brainwave Frequencies:** https://en.wikipedia.org/wiki/Binaural_beats
- **Indian Ragas:** https://en.wikipedia.org/wiki/Raga
- **EEG Analysis:** https://en.wikipedia.org/wiki/Electroencephalography

---

**Version:** 1.0
**Last Updated:** 2026-05-25
**Maintainers:** Raaga Therapy Team
