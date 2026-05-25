# Playback Error Troubleshooting Guide

## Error: "Playback failed: Unknown error. Try again after clicking Play."

This error occurs when the audio files can't be found or loaded. Here's how to fix it:

---

## Quick Fix (5 minutes)

### Option 1: Use Demo Mode (Testing Without Audio)

The system now includes automatic fallback to **Demo Mode** when audio files aren't available.

1. **Verify demo mode is active:**
   - Click the Play button
   - If you see "🎵 Demo Mode - Audio files not found" message, it's working
   - Session will auto-play with simulated timing (no actual sound)

2. **This allows you to:**
   - Test the complete therapy workflow
   - Verify UI/UX without audio
   - Confirm transitions work correctly

### Option 2: Create Dummy Audio Files (10 minutes)

Run this to create minimal test audio files:

```bash
# Windows
python create_demo_audio.py

# Or manually:
mkdir frontend/public/audio/ragas
mkdir frontend/public/audio/ragas/{T1,T2,A1,A2,B1,B2}
```

This creates 18 minimal MP3 files (silent, for testing only).

---

## Complete Solution (Adding Real Ragas)

### Step 1: Create Folder Structure

```bash
frontend/
└── public/
    └── audio/
        └── ragas/
            ├── T1/
            ├── T2/
            ├── A1/
            ├── A2/
            ├── B1/
            └── B2/
```

**Command:**
```bash
# Windows
mkdir frontend\public\audio\ragas\{T1,T2,A1,A2,B1,B2}

# Mac/Linux
mkdir -p frontend/public/audio/ragas/{T1,T2,A1,A2,B1,B2}
```

### Step 2: Add MP3 Files

Place 18 raga MP3 files in the structure:

```
frontend/public/audio/ragas/
├── T1/
│   ├── Ahir_Bhairav.mp3
│   ├── Madhmad_Sarang.mp3
│   └── Malkauns.mp3
├── T2/
│   ├── Todi.mp3
│   ├── Bhimpalasi.mp3
│   └── Darbari_Kanada.mp3
├── A1/
│   ├── Bhairav.mp3
│   ├── Shuddh_Sarang.mp3
│   └── Yaman.mp3
├── A2/
│   ├── Alhaiya_Bilawal.mp3
│   ├── Multani.mp3
│   └── Bhopali.mp3
├── B1/
│   ├── Jaunpuri.mp3
│   ├── Kafi.mp3
│   └── Khamaj.mp3
└── B2/
    ├── Hindol.mp3
    ├── Marwa.mp3
    └── Shankara.mp3
```

### Step 3: Verify File Naming

- ✅ CORRECT: `Ahir_Bhairav.mp3` (PascalCase with underscore)
- ❌ WRONG: `ahir_bhairav.mp3` (lowercase)
- ❌ WRONG: `Ahir Bhairav.mp3` (space instead of underscore)

### Step 4: Restart Frontend

```bash
npm start
```

---

## Debugging

### Check Browser Console

1. Open **Developer Tools** (F12)
2. Go to **Console** tab
3. Try playing a session and look for messages like:

```
[Lazy Load] Bhairav (A1) - ready
[Playback] Starting track 0: Bhairav
[Audio] Ready to play: Bhairav
[Playback] Audio ready, playing...
```

### If You See Errors:

**❌ "Failed to load raga"**
- Audio file doesn't exist at expected path
- Fix: Create all 18 files in correct folders

**❌ "Audio loading error"**
- MP3 file is corrupted
- Fix: Re-download or convert to MP3 format

**❌ "Play error: NotAllowedError"**
- Browser security issue (autoplay not allowed)
- Fix: This is normal, click Play button manually

**✅ "Demo Mode - Audio files not found"**
- Working correctly! Using fallback mode
- Fix: Optional - add real audio files to replace demo

---

## File Format Requirements

### MP3 Specifications

- **Format:** MPEG-1/2 Layer 3
- **Sample Rate:** 44.1 kHz or 48 kHz
- **Bitrate:** 128-320 kbps
- **Duration:** 2-10 minutes (depending on session)
- **File Size:** 1-50 MB each

### Check Audio File Quality

Use ffprobe (if installed):
```bash
ffprobe -v error -show_entries format=duration,codec_type frontend/public/audio/ragas/A1/Bhairav.mp3
```

---

## Demo Mode Details

When audio files aren't found, the system automatically:

1. ✓ Switches to Demo Mode
2. ✓ Shows "Demo Mode" indicator
3. ✓ Simulates playback timing
4. ✓ Auto-advances through ragas
5. ✓ Completes session normally

**Demo Mode is for testing only** - real audio won't play, but workflow will work.

---

## Finding Raga Audio

### Recommended Sources

1. **YouTube** - Search "Raga Bhairav 30 minutes" etc.
   - Download using tools like yt-dlp
   - Convert to MP3 using ffmpeg

2. **Spotify/Apple Music** - Classical Indian ragas
   - Artists: Pandit Ravi Shankar, Hari Prasad Chaurasia, etc.
   - Use screen recording with audio capture (if licensed)

3. **Subscription Services**
   - Raga.com
   - Classical Indian music libraries
   - SoundCloud raga collections

4. **Open Source**
   - FreesoundProject.org
   - Zapsplat.com
   - Free Raga downloads

### Example: Convert YouTube to MP3

```bash
# Download from YouTube
yt-dlp -f "bestaudio" -o "%(title)s.mp3" https://youtube.com/watch?v=xxxx

# Or use ffmpeg to convert WAV/flac to MP3
ffmpeg -i Bhairav.wav -codec:a libmp3lame -q:a 2 Bhairav.mp3
```

---

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Files created but still error | Path incorrect | Check exact spelling: `Ahir_Bhairav.mp3` |
| Works for some ragas, not others | Missing file | Verify all 18 files exist |
| Audio plays but cuts off | File too short | Use ragas ≥2 minutes each |
| "NotAllowedError" | Browser autoplay policy | Click Play button manually |
| Demo mode showing | Files in wrong location | Move to `frontend/public/audio/ragas/` |
| CORS error in console | Server config issue | Add CORS headers to backend |

---

## Verification Checklist

- [ ] Created `frontend/public/audio/ragas/` folder
- [ ] Created T1, T2, A1, A2, B1, B2 subfolders
- [ ] Added all 18 raga MP3 files
- [ ] Files named correctly (e.g., `Bhairav.mp3`)
- [ ] Restarted `npm start`
- [ ] Browser console shows no 404 errors
- [ ] Session plays without "Demo Mode" message
- [ ] All ragas are audible

---

## Still Having Issues?

### Step-by-Step Debug

1. **Check file exists:**
```bash
ls -la frontend/public/audio/ragas/A1/Bhairav.mp3
```

2. **Test direct URL in browser:**
   - Navigate to `http://localhost:3000/audio/ragas/A1/Bhairav.mp3`
   - Should start playing or download

3. **Check backend CORS:**
   - Open Frontend DevTools → Network tab
   - Look for XHR requests to audio files
   - Check response headers include `Access-Control-Allow-Origin: *`

4. **View console logs:**
   - Clear console (Ctrl+Shift+K)
   - Start session and click Play
   - Look for `[Lazy Load]` and `[Playback]` messages
   - Share these logs if requesting help

---

## Backend Configuration (If Needed)

If you're serving audio from a different backend, add CORS:

```python
# backend/adaptive_backend/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Conclusion

- ✅ **Demo Mode:** Works immediately (no audio files needed)
- ✅ **Real Audio:** Add MP3 files to `frontend/public/audio/ragas/`
- ✅ **Testing:** Use `create_demo_audio.py` to create dummy files
- ✅ **Debugging:** Check browser console for error messages

**Your therapy session will work either way!**

---

Last Updated: May 25, 2026
