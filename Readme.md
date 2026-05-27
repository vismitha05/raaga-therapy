# Raaga Therapy

Hindustani raga therapy guided by EEG brain-state frequency bands.

## Structure

- `backend/` — FastAPI therapy API and raga playlist engine
- `frontend/` — React UI

## Run

- Backend: `python app.py` or `python -m uvicorn adaptive_backend.main:app --reload`
- Frontend: `npm start` (from `frontend/`)
- EEG hardware (optional): Capsule example under `capsule-public-v1.7.0/Example/Win/build/Release`

## Raga selection flow

### Style & production (all sessions)

- **Genre:** Traditional Indian Classical, Hindustani Raga, solo instrument
- **Instruments:** Sitar, Santoor, Bansuri, Tanpura drone
- **Production:** High fidelity, clean acoustic, no vocals

### Time-of-day matrices

Pick **one** matrix from the current clock:

| Window | Day part |
|--------|----------|
| 6:00 AM – 12:00 PM | Morning |
| 6:00 PM – 6:00 AM | Evening / night |
| 12:00 PM – 6:00 PM | Morning matrix (daytime fallback) |

**Morning (6:00–12:00)**

| Band (Hz) | Raga | BPM | Lay |
|-----------|------|-----|-----|
| 4.0–6.0 (T1) | Ahir Bhairav | 60 | Vilambit |
| 6.1–8.0 (T2) | Todi | 70 | Vilambit |
| 8.1–10.0 (A1) | Bhairav | 85 | Madhyam |
| 10.1–12.0 (A2) | Alhaiya Bilawal | 100 | Madhyam |
| 12.1–21.0 (B1) | Jaunpuri | 120 | Drut |
| 21.1–30.0 (B2) | Hindol | 140 | Drut |

**Evening / night (18:00–6:00)**

| Band (Hz) | Raga | BPM | Lay |
|-----------|------|-----|-----|
| 4.0–6.0 (T1) | Malkauns | 55 | Vilambit |
| 6.1–8.0 (T2) | Darbari Kanada | 65 | Vilambit |
| 8.1–10.0 (A1) | Yaman | 80 | Madhyam |
| 10.1–12.0 (A2) | Bhopali | 95 | Madhyam |
| 12.1–21.0 (B1) | Khamaj | 115 | Drut |
| 21.1–30.0 (B2) | Shankara | 135 | Drut |

### Playback logic

1. **Detect** current band from EEG (T1–B2) or dominant Hz.
2. **Target** user goal: sleep → T1, relaxed → A1, focused → B1.
3. **Path** — step through intermediate bands between current and target:
   - **Up** (e.g. sleep → focus): T2 → A1 → A2 → B1
   - **Down** (e.g. B2 + sleep): B1 → A2 → A1 → T2 → T1 (decreasing Hz; does not replay B2)
4. **Duration per raga** = `selected_minutes × 60 / number_of_ragas_in_path`

Example: detected **B2** (21.1–30 Hz), target **sleep**, session **20 min** → 5 ragas → **4 min** each (Khamaj → Bhopali → Yaman → Darbari Kanada → Malkauns in evening window).

Implementation: `backend/adaptive_backend/services/raga_therapy_engine.py`
