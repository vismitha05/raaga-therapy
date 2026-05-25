# Adaptive Backend (FastAPI)

This module extends the existing EEG pipeline without changing C++ bridge logic.

## Run

```bash
cd backend
uvicorn adaptive_backend.main:app --host 0.0.0.0 --port 8000 --reload
```

## Core flows

1. Existing `EEGListener` streams EEG continuously.
2. `RealTimeMonitoringService` builds rolling 30s windows.
3. `feature_extraction` computes alpha/beta/theta features.
4. `brain_state_analyzer` detects focused/relaxed/sleep state.
5. `state_transition_engine` applies safe gradual tempo steps.
6. `playback_decision_engine` picks raaga by target state + time-of-day + tempo.
7. Results are persisted and broadcast over `/api/v1/ws/live`.

## API

- `POST /api/v1/sessions/start`
- `POST /api/v1/sessions/{session_id}/stop`
- `POST /api/v1/sessions/{session_id}/target`
- `GET /api/v1/state/current`
- `GET /api/v1/state/raaga`
- `GET /api/v1/state/transitions/{session_id}`
- `WS /api/v1/ws/live`

## Tempo safety

Tempo never jumps directly from low to high. Controller always does one-step progression:
- sleepy -> focused: `very_low -> low -> medium -> high`
- focused -> relaxed: `high -> medium -> low`
- relaxed -> sleep: `medium -> low -> very_low`

## Database tables

- `eeg_sessions`
- `brain_state_history`
- `raaga_metadata`
- `transition_history`
- `user_preferences`
- `playback_history`
- `eeg_analytics`
