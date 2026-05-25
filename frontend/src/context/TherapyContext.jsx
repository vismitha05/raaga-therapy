/**
 * TherapyContext.jsx
 * ──────────────────
 * Root context that wires EEG, session, and audio together.
 *
 * BUGS FIXED
 * ----------
 * BUG-1  TherapyBridge had TWO separate useEffects both reacting to
 *        session.isSessionActive. The first called setQueueForState() and
 *        set a status message. The second called audio.pause(). On session
 *        start both fired in the same render cycle, racing each other.
 *        Fix: merged into one unified effect with clear start/stop branches.
 *
 * BUG-2  audio.isPlaying was listed as a dep in the "stop on disconnect"
 *        useEffect. Every time isPlaying flipped, the effect re-ran and
 *        could pause music that had just been started.
 *        Fix: read isPlaying via a ref inside the effect so it doesn't
 *        need to be a dependency.
 *
 * BUG-3  STATE_META had placeholder "?" icons — replaced with real values.
 *
 * BUG-4  setQueueForState called with session.targetState as first arg but
 *        buildTrialQueue takes preferredName, not targetState. The state was
 *        silently dropped and the queue was always built with undefined.
 *        Fix: pass targetState as preferredName explicitly.
 *
 * BUG-5  On EEG reconnect the audio queue was never refreshed, so the
 *        wrong track could keep playing.
 *        Fix: refresh queue when EEG reconnects (connected flips true).
 */

import React, {
  createContext,
  useContext,
  useEffect,
  useRef,
  useMemo,
} from "react";
import { AudioPlayerProvider, useAudioPlayer } from "./AudioPlayerContext";
import { EEGRealtimeProvider, useEEGRealtime } from "./EEGRealtimeContext";
import { TherapySessionProvider, useTherapySession } from "./TherapySessionContext";

const TherapyContext = createContext(null);

// ── Baseline metrics shown before a session accumulates history ────────────

const DEFAULT_METRICS = {
  focus:          42,
  relaxation:     30,
  stability:      51,
  stressReduction: 24,
  sleepReadiness: 40,
};

// ── Per-state metadata ─────────────────────────────────────────────────────

const STATE_META = {
  Focused: { desc: "Enhance concentration and productivity",    icon: "⚡" },
  Relaxed: { desc: "Reduce stress and calm the mind",           icon: "🌿" },
  Sleep:   { desc: "Prepare the brain for deeper sleep",        icon: "🌙" },
};

// ── Bridge component ───────────────────────────────────────────────────────

function TherapyBridge({ children }) {
  const eeg     = useEEGRealtime();
  const session = useTherapySession();
  const audio   = useAudioPlayer();

  // Keep a ref to audio.isPlaying so effects don't need it as a dep
  const isPlayingRef = useRef(audio.isPlaying);
  useEffect(() => { isPlayingRef.current = audio.isPlaying; }, [audio.isPlaying]);

  // ── FIX BUG-1: unified session start/stop effect ─────────────────────────
  useEffect(() => {
    if (session.isSessionActive) {
      // Session started: build queue for the target state
      // FIX BUG-4: pass targetState as preferredName so the queue is relevant
      const ordered = audio.setQueueForState(session.targetState, session.targetState);
      if (ordered[0]) {
        // Keep first play user-initiated to respect browser autoplay policy
        audio.setPlaybackStatus("Ready — click Play to begin");
      }
    } else {
      // Session ended: stop playback
      if (isPlayingRef.current) {
        audio.pause();
      }
    }
  }, [session.isSessionActive]);

  // ── FIX BUG-2: pause on disconnect — don't depend on isPlaying ──────────
  useEffect(() => {
    if (!eeg.connected && isPlayingRef.current) {
      audio.pause();
    }
  }, [eeg.connected]);   // audio.pause is stable (defined outside state)

  // ── FIX BUG-5: refresh queue when EEG reconnects ────────────────────────
  const prevConnected = useRef(eeg.connected);
  useEffect(() => {
    const wasDisconnected = !prevConnected.current;
    const nowConnected    =  eeg.connected;
    prevConnected.current = eeg.connected;

    if (wasDisconnected && nowConnected && session.isSessionActive) {
      // EEG came back — refresh the audio queue so the right track plays
      audio.refreshQueue(session.targetState);
    }
  }, [eeg.connected, session.isSessionActive, session.targetState]);

  // ── Live metrics (grow as session progresses) ────────────────────────────

  const liveMetrics = useMemo(() => {
    const drift = session.sessionProgress / 100;
    return {
      focus:          Math.min(98, Math.round(DEFAULT_METRICS.focus          + drift * 45 + (session.targetState === "Focused" ? 5 : 0))),
      relaxation:     Math.min(98, Math.round(DEFAULT_METRICS.relaxation     + drift * 48 + (session.targetState === "Relaxed" ? 5 : 0))),
      stability:      Math.min(98, Math.round(DEFAULT_METRICS.stability      + drift * 35)),
      stressReduction:Math.min(98, Math.round(DEFAULT_METRICS.stressReduction+ drift * 60)),
      sleepReadiness: Math.min(98, Math.round(DEFAULT_METRICS.sleepReadiness + drift * 44 + (session.targetState === "Sleep"   ? 6 : 0))),
    };
  }, [session.sessionProgress, session.targetState]);

  // ── Before/after comparison for session summary ──────────────────────────

  const sessionResult = useMemo(() => ({
    before: { focus: 42, stress: 76, relaxation: 30, stability: 51, sleep: 40 },
    after: {
      focus:      liveMetrics.focus,
      stress:     Math.max(18, 76 - liveMetrics.stressReduction),
      relaxation: liveMetrics.relaxation,
      stability:  liveMetrics.stability,
      sleep:      liveMetrics.sleepReadiness,
    },
  }), [liveMetrics]);

  // ── Context value ─────────────────────────────────────────────────────────

  const value = {
    // Navigation
    screen:    session.screen,
    setScreen: session.setScreen,

    // Session config
    targetState:    session.targetState,
    setTargetState: session.setTargetState,
    duration:       session.duration,
    setDuration:    session.setDuration,

    // Playback controls (delegated to audio)
    isPlaying:    audio.isPlaying,
    setIsPlaying: (next) => (next ? audio.resume() : audio.pause()),

    // Session timing
    sessionProgress:    session.sessionProgress,
    setSessionProgress: () => {},
    timerSec:           session.elapsedSec,
    setTimerSec:        () => {},

    // Live EEG + audio stream status
    stream: {
      connected:       eeg.connected,
      quality:         eeg.quality,
      confidence:      eeg.confidence,
      detectedState:   eeg.detectedState,
      currentRaaga:    audio.currentTrack?.name || eeg.suggestedRaaga,
      eegSeries:       eeg.eegSeries,
      transitionStage: eeg.transitionStage,
      playbackStatus:  audio.playbackStatus,
      playbackProgress:audio.playbackProgress,
      trackDuration:   audio.trackDuration,
      currentTime:     audio.currentTime,
      transitionState: audio.transitionState,
      error:           audio.error,
      mode:            eeg.mode,
    },

    stateMeta:     STATE_META,
    liveMetrics,
    sessionResult,

    // Session lifecycle
    startSession:  session.startSession,
    endSession:    session.endSession,
    resetSession:  session.resetSession,
    remainingSec:  session.remainingSec,

    // Raw audio context for advanced consumers
    audio,
  };

  return <TherapyContext.Provider value={value}>{children}</TherapyContext.Provider>;
}

// ── Provider tree ──────────────────────────────────────────────────────────

export function TherapyProvider({ children }) {
  return (
    <EEGRealtimeProvider>
      <TherapySessionProvider>
        <AudioPlayerProvider>
          <TherapyBridge>{children}</TherapyBridge>
        </AudioPlayerProvider>
      </TherapySessionProvider>
    </EEGRealtimeProvider>
  );
}

export function useTherapy() {
  const ctx = useContext(TherapyContext);
  if (!ctx) throw new Error("useTherapy must be used inside TherapyProvider");
  return ctx;
}
