import React, { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
import { useAudioPlayer } from "./AudioPlayerContext";
import { useEEGRealtime } from "./EEGRealtimeContext";
import { API_BASE, API_PREFIX } from "../config/runtimeConfig";

const TherapyContext = createContext(undefined);

const STATE_META = {
  T1: { icon: "T1", title: "Deep Meditation", desc: "Sleep-border calm and grounding." },
  T2: { icon: "T2", title: "Creative Drift", desc: "Hypnagogic ease with gentle movement." },
  A1: { icon: "A1", title: "Deep Relaxation", desc: "Warm, steady calm." },
  A2: { icon: "A2", title: "Mindful Alertness", desc: "Balanced flow and presence." },
  B1: { icon: "B1", title: "Cognitive Focus", desc: "Structured focus for work mode." },
  B2: { icon: "B2", title: "High Alertness", desc: "Stress-peak activation that needs careful release." },
};

function average(values = []) {
  if (!values.length) return 0;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function computeLiveMetrics(eegSeries = []) {
  const alpha = average(eegSeries.map((entry) => entry.alpha || 0));
  const beta = average(eegSeries.map((entry) => entry.beta || 0));
  const theta = average(eegSeries.map((entry) => entry.theta || 0));

  return {
    focus: Math.max(0, Math.min(100, Math.round((beta * 0.9) - (theta * 0.25) + 35))),
    relaxation: Math.max(0, Math.min(100, Math.round((alpha * 0.8) - (beta * 0.18) + 28))),
    stability: Math.max(0, Math.min(100, Math.round(((alpha + theta) / 2) * 0.85))),
    stressReduction: Math.max(0, Math.min(100, Math.round(100 - ((beta * 0.55) - (alpha * 0.35))))),
    sleepReadiness: Math.max(0, Math.min(100, Math.round((theta * 0.95) - (beta * 0.2) + 30))),
  };
}

async function requestJson(path, options = {}) {
  const response = await fetch(`${API_BASE}${API_PREFIX}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || `Request failed: ${response.status}`);
  }
  return data;
}

export function TherapyProvider({ children }) {
  const audio = useAudioPlayer();
  const eeg = useEEGRealtime();

  const [screen, setScreen] = useState("headset");
  const [duration, setDuration] = useState(20);
  const [targetState, setTargetState] = useState("A1");
  const [sessionId, setSessionId] = useState(null);
  const [sessionResult, setSessionResult] = useState({
    before: { focus: 0, stress: 0, relaxation: 0 },
    after: { focus: 0, stress: 0, relaxation: 0 },
  });
  const [baselineMetrics, setBaselineMetrics] = useState(null);
  const [error, setError] = useState("");
  const lastPlaylistVersionRef = useRef(0);

  const liveMetrics = useMemo(() => computeLiveMetrics(eeg.eegSeries), [eeg.eegSeries]);
  const totalSec = duration * 60;
  const elapsedSec = Math.round(((eeg.sessionProgress || 0) / 100) * totalSec);
  const remainingSec = Math.max(0, totalSec - elapsedSec);

  useEffect(() => {
    if (!eeg.therapyActive || !eeg.currentTrack) return;
    const nextTrack = {
      id: `${eeg.currentTrack.index}-${eeg.currentTrack.state}`,
      name: eeg.currentTrack.raaga,
      title: eeg.currentTrack.raaga,
      url: eeg.currentTrack.file_path,
      state: eeg.currentTrack.state,
      duration_seconds: eeg.currentTrack.duration_seconds,
    };
    const currentUrl = audio.currentTrack?.url || null;
    if (currentUrl === nextTrack.url) return;

    if (audio.currentTrack && lastPlaylistVersionRef.current === eeg.playlistVersion) {
      audio.switchTrack(nextTrack, "raaga-transition");
    } else {
      audio.playTrack(nextTrack);
    }
    lastPlaylistVersionRef.current = eeg.playlistVersion;
  }, [audio, eeg.currentTrack, eeg.playlistVersion, eeg.therapyActive]);

  async function startSession() {
    if (!eeg.headsetReady) {
      setError(eeg.headsetMessage || "Adjust Headband Position");
      return false;
    }

    try {
      setError("");
      const response = await requestJson("/therapy/session/start", {
        method: "POST",
        body: JSON.stringify({
          target_state: targetState,
          duration_minutes: duration,
        }),
      });
      setSessionId(response.session_id);
      setBaselineMetrics(liveMetrics);
      setScreen("player");
      return true;
    } catch (requestError) {
      setError(requestError.message);
      return false;
    }
  }

  async function endSession() {
    if (sessionId) {
      try {
        await requestJson(`/therapy/session/stop/${sessionId}`, { method: "POST" });
      } catch (_error) {
        // Keep completion flow responsive even if stop reporting fails.
      }
    }

    audio.pause();
    const before = baselineMetrics || { focus: 0, relaxation: 0 };
    setSessionResult({
      before: {
        focus: before.focus || 0,
        stress: Math.max(0, 100 - (before.relaxation || 0)),
        relaxation: before.relaxation || 0,
      },
      after: {
        focus: liveMetrics.focus,
        stress: Math.max(0, 100 - liveMetrics.relaxation),
        relaxation: liveMetrics.relaxation,
      },
    });
    setScreen("completion");
  }

  function resetSession() {
    setSessionId(null);
    setBaselineMetrics(null);
    setError("");
    lastPlaylistVersionRef.current = 0;
    setScreen("headset");
  }

  const stream = useMemo(
    () => ({
      connected: eeg.connected,
      quality: eeg.quality,
      confidence: eeg.confidence,
      detectedState: eeg.detectedState,
      detectedStateLabel: eeg.detectedStateLabel,
      targetState: eeg.targetState,
      targetStateLabel: eeg.targetStateLabel,
      currentRaaga: eeg.suggestedRaaga,
      upcomingRaaga: eeg.upcomingRaaga,
      playbackStatus: audio.playbackStatus,
      transitionState: eeg.playlistVersion,
      playbackProgress: audio.playbackProgress,
      currentTime: audio.currentTime,
      trackDuration: audio.trackDuration,
      error: error || audio.error || "",
      eegSeries: eeg.eegSeries,
      headsetReady: eeg.headsetReady,
      headsetMessage: eeg.headsetMessage,
      channelQuality: eeg.channelQuality,
      resistance: eeg.resistance,
      sessionProgress: eeg.sessionProgress,
      currentTrack: eeg.currentTrack,
      upcomingTrack: eeg.upcomingTrack,
      playlist: eeg.playlist,
      pendingState: eeg.pendingState,
      pendingSeconds: eeg.pendingSeconds,
      therapyActive: eeg.therapyActive,
      crossfadeSeconds: eeg.crossfadeSeconds,
    }),
    [audio, eeg, error]
  );

  const value = {
    screen,
    setScreen,
    duration,
    setDuration,
    targetState,
    setTargetState,
    stateMeta: STATE_META,
    stream,
    audio,
    totalSec,
    elapsedSec,
    remainingSec,
    sessionProgress: eeg.sessionProgress,
    liveMetrics,
    sessionResult,
    sessionId,
    startSession,
    endSession,
    resetSession,
    error,
  };

  return <TherapyContext.Provider value={value}>{children}</TherapyContext.Provider>;
}

export function useTherapy() {
  const context = useContext(TherapyContext);
  if (!context) throw new Error("useTherapy must be used within TherapyProvider");
  return context;
}
