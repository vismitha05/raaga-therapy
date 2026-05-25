# Raaga Therapy API Reference

## Base URL
```
http://localhost:8000/api/therapy
```

## Endpoints

### 1. Start EEG Scan
```
POST /eeg-scan/start

Request Body:
{
  "duration_seconds": 15,
  "simulate": true
}

Response (202 Accepted):
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "EEG scan started, monitoring for 15 seconds",
  "total_duration_seconds": 15
}
```

### 2. Get Scan Progress
```
GET /eeg-scan/progress/{session_id}

Response (200 OK):
{
  "progress_percent": 45.5,
  "time_remaining_seconds": 8.2,
  "is_monitoring": true
}

Polling Strategy:
- Poll every 500ms until progress_percent reaches 100
- When 100% is reached, call /eeg-scan/result
```

### 3. Get Scan Results
```
GET /eeg-scan/result/{session_id}

Response (200 OK):
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "detected_band": "A1",
  "detected_state": "relaxed",
  "confidence": 0.87,
  "alpha_power": 0.62,
  "beta_power": 0.22,
  "theta_power": 0.16,
  "monitoring_duration_seconds": 15
}

Frequency Bands:
- T1: 4-6 Hz (sleep/theta)
- T2: 6-8 Hz (theta-alpha border)
- A1: 8-10 Hz (alpha/relaxed)
- A2: 10-12 Hz (alpha-beta border)
- B1: 12-21 Hz (beta/focused)
- B2: 21-30 Hz (high beta/intense focus)
```

### 4. Select Target State
```
POST /state-selection

Request Body:
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "target_state": "focused"
}

Valid States: "sleep", "relaxed", "focused"

Response (200 OK):
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "target_state": "focused",
  "current_state": "relaxed",
  "current_band": "A1",
  "effectiveness_estimates": {
    "10": 65,
    "20": 82,
    "30": 94
  },
  "message": "Target state selected. Choose session duration."
}

effectiveness_estimates: Percentage (0-100) for each duration
- Higher % = More effective transition
- 10 min: Quick therapy
- 20 min: Recommended (sweet spot)
- 30 min: Most thorough
```

### 5. Generate Playlist (Select Duration)
```
POST /duration-selection

Request Body:
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "duration_minutes": 20
}

Valid Durations: 10, 20, or 30 minutes

Response (200 OK):
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "start_band": "A1",
  "target_state": "focused",
  "total_duration_minutes": 20,
  "total_steps": 3,
  "day_part": "afternoon",
  "tracks": [
    {
      "order": 0,
      "band": "A1",
      "raga": "Shuddh_Sarang",
      "duration_seconds": 400.0,
      "frequency_range": [8.1, 10.0],
      "estimated_start_time_seconds": 0.0
    },
    {
      "order": 1,
      "band": "A2",
      "raga": "Multani",
      "duration_seconds": 400.0,
      "frequency_range": [10.1, 12.0],
      "estimated_start_time_seconds": 400.0
    },
    {
      "order": 2,
      "band": "B1",
      "raga": "Kafi",
      "duration_seconds": 400.0,
      "frequency_range": [12.1, 21.0],
      "estimated_start_time_seconds": 800.0
    }
  ]
}

Key Fields:
- duration_seconds: How long to play this raga
- frequency_range: Target frequency band in Hz
- estimated_start_time_seconds: When raga starts in session timeline
```

### 6. Get Playlist
```
GET /playlist/{session_id}

Response (200 OK):
Same format as duration-selection response above

Use Cases:
- Retrieve playlist after generation
- Update UI with latest track info
- Validate before playback starts
```

### 7. Update Playback Progress
```
POST /playback/update

Request Body:
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "track_index": 1,
  "raga_name": "Multani",
  "frequency_range": [10.1, 12.0],
  "duration_seconds": 400.0,
  "elapsed_seconds": 123.5,
  "is_playing": true
}

Response (200 OK):
{
  "status": "progress_recorded",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}

Usage:
- Call every 10-30 seconds during playback
- Helps backend track session progress
- Optional (for analytics/logging)
```

### 8. Complete Session
```
POST /session/complete/{session_id}

Response (200 OK):
{
  "status": "session_completed",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "duration": 1204.3
}

Call When:
- All ragas have played
- User manually stops session
- Session has finished playback
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid target state: xxx"
}
```
Causes:
- Invalid duration (not 10, 20, or 30)
- Invalid state (not sleep/relaxed/focused)
- Missing required fields

### 404 Not Found
```json
{
  "detail": "Session not found"
}
```
Causes:
- Invalid session_id
- Session expired (>24 hours)
- Session was never created

### 202 Accepted
```json
{
  "detail": "Still monitoring..."
}
```
Status: Results not yet available, keep polling

---

## Frontend Implementation Example

### JavaScript Fetch Pattern

```javascript
// 1. Start scan
const scanResponse = await fetch('/api/therapy/eeg-scan/start', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    duration_seconds: 15,
    simulate: true,
  }),
});

const { session_id } = await scanResponse.json();

// 2. Poll progress
const pollProgress = setInterval(async () => {
  const progressResponse = await fetch(`/api/therapy/eeg-scan/progress/${session_id}`);
  const progress = await progressResponse.json();
  
  console.log(`Progress: ${progress.progress_percent}%`);
  
  if (progress.progress_percent >= 100) {
    clearInterval(pollProgress);
    
    // 3. Get results
    const resultsResponse = await fetch(`/api/therapy/eeg-scan/result/${session_id}`);
    const detection = await resultsResponse.json();
    console.log(`Detected: ${detection.detected_state} (${detection.detected_band})`);
  }
}, 500);

// 4. Select state
const stateResponse = await fetch('/api/therapy/state-selection', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: session_id,
    target_state: 'focused',
  }),
});

const { effectiveness_estimates } = await stateResponse.json();
console.log(`Effectiveness: 10m=${effectiveness_estimates[10]}%`);

// 5. Select duration
const playlistResponse = await fetch('/api/therapy/duration-selection', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: session_id,
    duration_minutes: 20,
  }),
});

const playlist = await playlistResponse.json();
console.log(`Playlist: ${playlist.tracks.length} ragas`);

// 6. Start playback with lazy loading
for (let i = 0; i < playlist.tracks.length; i++) {
  const track = playlist.tracks[i];
  
  // Lazy load audio
  const audioPath = `/audio/ragas/${track.band}/${track.raga}.mp3`;
  const audio = new Audio(audioPath);
  
  // Play
  audio.play();
  
  // Wait for completion
  await new Promise(resolve => {
    audio.onended = resolve;
  });
  
  // Update progress
  await fetch('/api/therapy/playback/update', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: session_id,
      track_index: i,
      raga_name: track.raga,
      frequency_range: track.frequency_range,
      duration_seconds: track.duration_seconds,
      elapsed_seconds: track.duration_seconds,
      is_playing: false,
    }),
  });
}

// 7. Complete session
await fetch(`/api/therapy/session/complete/${session_id}`, {
  method: 'POST',
});
```

---

## Raga File Naming Convention

Audio files should follow this structure:

```
/audio/ragas/{BAND}/{RAGA_NAME}.mp3

Examples:
/audio/ragas/T1/Ahir_Bhairav.mp3
/audio/ragas/A1/Shuddh_Sarang.mp3
/audio/ragas/B1/Jaunpuri.mp3
```

Band abbreviations:
- T1, T2: Theta/Low frequency
- A1, A2: Alpha
- B1, B2: Beta/High frequency

Raga naming: PascalCase with underscores for multi-word names

---

## Rate Limiting

No explicit rate limiting in current implementation.
For production, recommend:
- Max 10 sessions per user per day
- Max 1 EEG scan start per minute
- Max 100 playlist generations per hour

---

## Session Timeout

- Sessions auto-expire after **24 hours**
- No manual cleanup required
- In-memory storage (use database in production)

---

## Testing the API

```bash
# Using curl

# 1. Start scan
curl -X POST http://localhost:8000/api/therapy/eeg-scan/start \
  -H "Content-Type: application/json" \
  -d '{"duration_seconds": 15, "simulate": true}'

# 2. Check progress (substitute SESSION_ID)
curl http://localhost:8000/api/therapy/eeg-scan/progress/SESSION_ID

# 3. Get results
curl http://localhost:8000/api/therapy/eeg-scan/result/SESSION_ID

# 4. Select state
curl -X POST http://localhost:8000/api/therapy/state-selection \
  -H "Content-Type: application/json" \
  -d '{"session_id": "SESSION_ID", "target_state": "focused"}'

# 5. Generate playlist
curl -X POST http://localhost:8000/api/therapy/duration-selection \
  -H "Content-Type: application/json" \
  -d '{"session_id": "SESSION_ID", "duration_minutes": 20}'
```

---

**Last Updated:** 2026-05-25
**API Version:** 1.0
