"""
audio_engine.py
---------------
Adaptive audio engine that maps EEG brain states to raga audio files.

State → File mapping:
  Focused  → focus.mp3   (enhances concentration)
  Relaxed  → calm.mp3    (deepens rest)
  Fatigued → energy.mp3  (provides gentle stimulation)

Features:
  - Smooth fade-out / fade-in transitions
  - Debounce logic: state must be stable for STABILITY_THRESHOLD seconds
    before a track switch is triggered (prevents rapid toggling)
  - Mode-aware: "Study" mode biases toward focus.mp3 during ambiguous states
  - Thread-safe: can be called from the Flask polling loop

Audio playback uses pygame.mixer when available; falls back to a no-op stub
so the rest of the system works even without audio hardware.
"""

import threading
import time
from pathlib import Path
from typing import Optional

# ── pygame import with graceful fallback ──────────────────────────────────────
try:
    import pygame
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
    AUDIO_AVAILABLE = True
    print("[AudioEngine] pygame.mixer initialised.")
except Exception as exc:
    AUDIO_AVAILABLE = False
    print(f"[AudioEngine] pygame not available ({exc}). Audio disabled.")


# ─────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────

AUDIO_DIR = Path(__file__).parent / "audio"   # put .mp3 files here

STATE_TRACK_MAP = {
    "Focused":  "Desh.mp3",
    "Relaxed":  "Ahir bhairav.mp3",
    "Fatigued": "Raag Darbari.mp3",
}

# How long (seconds) a new state must persist before we switch tracks
STABILITY_THRESHOLD = 4.0

# Fade duration in milliseconds (pygame uses ms)
FADE_OUT_MS = 1500
FADE_IN_MS  = 1500

# Volume range [0.0 – 1.0]
DEFAULT_VOLUME = 0.75


# ─────────────────────────────────────────────
#  Stub for environments without pygame
# ─────────────────────────────────────────────

class _AudioStub:
    """No-op audio player used when pygame is unavailable."""
    def load(self, path): pass
    def play(self, loops=-1, fade_ms=0): pass
    def fadeout(self, ms): pass
    def set_volume(self, v): pass
    def get_busy(self): return False


# ─────────────────────────────────────────────
#  AudioEngine
# ─────────────────────────────────────────────

class AudioEngine:
    """
    Manages adaptive background audio playback driven by brain state.

    Thread-safety: all public methods acquire self._lock before mutating state.
    """

    def __init__(self, mode: str = "Study"):
        self._lock = threading.Lock()

        # Current playback state
        self._current_state: Optional[str] = None   # e.g. "Focused"
        self._current_track: Optional[str] = None   # e.g. "focus.mp3"
        self._is_playing: bool = False

        # Debounce / stability tracking
        self._candidate_state: Optional[str] = None
        self._candidate_since: float = 0.0

        # Operating mode: "Study" | "Relax"
        self._mode: str = mode

        # Volume (0–1)
        self._volume: float = DEFAULT_VOLUME

        # pygame channel (or stub)
        if AUDIO_AVAILABLE:
            self._channel = pygame.mixer.Channel(0)
        else:
            self._channel = _AudioStub()

    # ── Public API ────────────────────────────────────────────────────────────

    def update(self, state: str):
        """
        Call this each time a new EEG state arrives.
        Internal debounce decides whether to actually switch tracks.
        """
        with self._lock:
            self._debounce(state)

    def set_mode(self, mode: str):
        """Switch between 'Study' and 'Relax' operating modes."""
        with self._lock:
            self._mode = mode
            print(f"[AudioEngine] Mode switched to: {mode}")
            # Re-evaluate current state immediately
            if self._current_state:
                self._switch_track(self._resolve_track(self._current_state))

    def set_volume(self, volume: float):
        """Set playback volume [0.0 – 1.0]."""
        with self._lock:
            self._volume = max(0.0, min(1.0, volume))
            if AUDIO_AVAILABLE and self._channel.get_busy():
                self._channel.set_volume(self._volume)

    def stop(self):
        """Fade out and stop playback."""
        with self._lock:
            if AUDIO_AVAILABLE and self._channel.get_busy():
                self._channel.fadeout(FADE_OUT_MS)
            self._is_playing = False
            self._current_state = None
            self._current_track = None

    @property
    def status(self) -> dict:
        """Return a snapshot of engine status for the API response."""
        with self._lock:
            return {
                "track":   self._current_track,
                "state":   self._current_state,
                "mode":    self._mode,
                "playing": self._is_playing,
                "volume":  self._volume,
            }

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _debounce(self, incoming_state: str):
        """
        Only switch when `incoming_state` has been stable for
        STABILITY_THRESHOLD seconds.  Prevents rapid track-switching
        on transient EEG fluctuations.
        """
        now = time.time()

        if incoming_state != self._candidate_state:
            # New candidate — reset the stability timer
            self._candidate_state = incoming_state
            self._candidate_since = now
            return

        elapsed = now - self._candidate_since
        if elapsed >= STABILITY_THRESHOLD and incoming_state != self._current_state:
            # State has been stable long enough → switch
            track = self._resolve_track(incoming_state)
            self._switch_track(track)
            self._current_state = incoming_state

    def _resolve_track(self, state: str) -> str:
        """
        Map brain state → track filename, taking operating mode into account.

        In "Relax" mode we never play the high-energy focus track;
        instead we fall back to calm even when the user is focused.
        """
        if self._mode == "Relax" and state == "Focused":
            return STATE_TRACK_MAP["Relaxed"]
        return STATE_TRACK_MAP.get(state, "calm.mp3")

    def _switch_track(self, track_name: str):
        """Fade out current, load new file, fade in."""
        if track_name == self._current_track:
            return  # already playing the right track

        track_path = AUDIO_DIR / track_name

        if AUDIO_AVAILABLE:
            # Fade out current track
            if self._channel.get_busy():
                self._channel.fadeout(FADE_OUT_MS)
                time.sleep(FADE_OUT_MS / 1000 + 0.1)   # brief pause between tracks

            if not track_path.exists():
                print(f"[AudioEngine] ⚠  Track not found: {track_path}. Skipping.")
                return

            try:
                sound = pygame.mixer.Sound(str(track_path))
                sound.set_volume(self._volume)
                self._channel.play(sound, loops=-1, fade_ms=FADE_IN_MS)
                self._is_playing = True
                print(f"[AudioEngine] ▶  Now playing: {track_name}")
            except Exception as exc:
                print(f"[AudioEngine] Playback error: {exc}")
                return
        else:
            print(f"[AudioEngine] (stub) Would play: {track_name}")
            self._is_playing = True

        self._current_track = track_name