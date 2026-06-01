import React, { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
import { WS_URL } from "../config/runtimeConfig";

const EEGRealtimeContext = createContext(null);

function qualityToPercent(channelQuality = {}) {
  const weights = { GOOD: 100, WARNING: 60, BAD: 20 };
  const values = Object.values(channelQuality);
  if (!values.length) return 0;
  const total = values.reduce((sum, quality) => sum + (weights[quality] ?? 0), 0);
  return Math.round(total / values.length);
}

function normalizeConfidence(value) {
  if (typeof value !== "number") return 0;
  return value <= 1 ? Math.round(value * 100) : Math.round(value);
}

function applySample(setters, payload) {
  setters.setConnected(payload.eeg_status === "live");
  setters.setConfidence(normalizeConfidence(payload.confidence));
  setters.setDetectedState(payload.current_eeg_state || payload.instant_cognitive_state || payload.detected_state || "Connecting");
  setters.setDetectedStateLabel(
    payload.current_eeg_state_label ||
      payload.instant_cognitive_state_label ||
      payload.detected_state ||
      "Connecting"
  );
  setters.setSuggestedRaaga(payload.current_raaga || payload.active_raaga || "—");
  setters.setUpcomingRaaga(payload.upcoming_raaga || "—");
  setters.setTargetState(payload.target_eeg_state || null);
  setters.setTargetStateLabel(payload.target_eeg_state_label || "");
  setters.setTransitionStage(payload.playlist_version || payload.transition_stage || 0);
  setters.setSessionProgress(Math.round(payload.session_progress_percent || 0));
  setters.setCurrentTrack(payload.current_track || null);
  setters.setUpcomingTrack(payload.upcoming_track || null);
  setters.setPlaylist(payload.playlist || []);
  setters.setPlaylistVersion(payload.playlist_version || 0);
  setters.setHeadsetReady(Boolean(payload.headset_ready));
  setters.setHeadsetMessage(payload.headset_message || "");
  setters.setChannelQuality(payload.channel_quality || {});
  setters.setResistance(payload.resistance || {});
  setters.setPendingState(payload.pending_eeg_state || null);
  setters.setPendingSeconds(payload.pending_state_stable_for_seconds || 0);
  setters.setTherapyActive(Boolean(payload.therapy_active));
  setters.setCrossfadeSeconds(payload.crossfade_seconds || 0);
  setters.setMode(payload.eeg_status === "live" ? "live" : "waiting");
  setters.setQuality(qualityToPercent(payload.channel_quality || {}));

  const alpha = payload.alpha;
  const beta = payload.beta;
  const theta = payload.theta;
  if (typeof alpha === "number" && typeof beta === "number" && typeof theta === "number") {
    const scale = Math.max(alpha, beta, theta, 1e-9);
    setters.appendSeries({
      tick: new Date().toLocaleTimeString(),
      alpha: Math.round((alpha / scale) * 100),
      beta: Math.round((beta / scale) * 100),
      theta: Math.round((theta / scale) * 100),
    });
  }
}

export function EEGRealtimeProvider({ children }) {
  const [connected, setConnected] = useState(false);
  const [quality, setQuality] = useState(0);
  const [confidence, setConfidence] = useState(0);
  const [detectedState, setDetectedState] = useState("Connecting");
  const [detectedStateLabel, setDetectedStateLabel] = useState("Connecting");
  const [suggestedRaaga, setSuggestedRaaga] = useState("—");
  const [upcomingRaaga, setUpcomingRaaga] = useState("—");
  const [targetState, setTargetState] = useState(null);
  const [targetStateLabel, setTargetStateLabel] = useState("");
  const [transitionStage, setTransitionStage] = useState(0);
  const [sessionProgress, setSessionProgress] = useState(0);
  const [eegSeries, setEegSeries] = useState([]);
  const [mode, setMode] = useState("waiting");
  const [headsetReady, setHeadsetReady] = useState(false);
  const [headsetMessage, setHeadsetMessage] = useState("");
  const [channelQuality, setChannelQuality] = useState({});
  const [resistance, setResistance] = useState({});
  const [currentTrack, setCurrentTrack] = useState(null);
  const [upcomingTrack, setUpcomingTrack] = useState(null);
  const [playlist, setPlaylist] = useState([]);
  const [playlistVersion, setPlaylistVersion] = useState(0);
  const [pendingState, setPendingState] = useState(null);
  const [pendingSeconds, setPendingSeconds] = useState(0);
  const [therapyActive, setTherapyActive] = useState(false);
  const [crossfadeSeconds, setCrossfadeSeconds] = useState(0);
  const wsRef = useRef(null);

  const setters = useMemo(
    () => ({
      setConnected,
      setConfidence,
      setDetectedState,
      setDetectedStateLabel,
      setSuggestedRaaga,
      setUpcomingRaaga,
      setTargetState,
      setTargetStateLabel,
      setTransitionStage,
      setSessionProgress,
      setMode,
      setQuality,
      setHeadsetReady,
      setHeadsetMessage,
      setChannelQuality,
      setResistance,
      setCurrentTrack,
      setUpcomingTrack,
      setPlaylist,
      setPlaylistVersion,
      setPendingState,
      setPendingSeconds,
      setTherapyActive,
      setCrossfadeSeconds,
      appendSeries: (point) => setEegSeries((prev) => [...prev.slice(-23), point]),
    }),
    []
  );

  useEffect(() => {
    let alive = true;

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!alive) return;
        setMode("live");
      };

      ws.onmessage = (event) => {
        if (!alive) return;
        try {
          applySample(setters, JSON.parse(event.data));
        } catch (_error) {
          // Ignore malformed frames.
        }
      };

      ws.onclose = () => {
        if (alive) setMode("waiting");
      };

      ws.onerror = () => {
        if (!alive) return;
        try {
          ws.close();
        } catch (_error) {
          // noop
        }
      };
    } catch (_error) {
      setMode("waiting");
    }

    return () => {
      alive = false;
      if (wsRef.current) wsRef.current.close();
    };
  }, [setters]);

  const value = useMemo(
    () => ({
      connected,
      quality,
      confidence,
      detectedState,
      detectedStateLabel,
      suggestedRaaga,
      upcomingRaaga,
      targetState,
      targetStateLabel,
      transitionStage,
      sessionProgress,
      eegSeries,
      mode,
      headsetReady,
      headsetMessage,
      channelQuality,
      resistance,
      currentTrack,
      upcomingTrack,
      playlist,
      playlistVersion,
      pendingState,
      pendingSeconds,
      therapyActive,
      crossfadeSeconds,
    }),
    [
      connected,
      quality,
      confidence,
      detectedState,
      detectedStateLabel,
      suggestedRaaga,
      upcomingRaaga,
      targetState,
      targetStateLabel,
      transitionStage,
      sessionProgress,
      eegSeries,
      mode,
      headsetReady,
      headsetMessage,
      channelQuality,
      resistance,
      currentTrack,
      upcomingTrack,
      playlist,
      playlistVersion,
      pendingState,
      pendingSeconds,
      therapyActive,
      crossfadeSeconds,
    ]
  );

  return <EEGRealtimeContext.Provider value={value}>{children}</EEGRealtimeContext.Provider>;
}

export function useEEGRealtime() {
  const ctx = useContext(EEGRealtimeContext);
  if (!ctx) throw new Error("useEEGRealtime must be used within EEGRealtimeProvider");
  return ctx;
}
