import React, { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";

const EEGRealtimeContext = createContext(null);

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";
const API_PREFIX = process.env.REACT_APP_API_PREFIX || "/api/v1";
const WS_URL =
  process.env.REACT_APP_WS_URL ||
  `${API_BASE.replace(/^http/, "ws")}${API_PREFIX}/ws/live`;
const POLL_URL = `${API_BASE}${API_PREFIX}/eeg/live`;

function mapPayloadState(payload) {
  const raw = payload.detected_state || payload.detectedState || payload.classifier_state;
  if (!raw) return null;
  if (raw === "Fatigued" || raw === "sleepy" || raw === "sleep") return "Sleep";
  if (raw === "focused") return "Focused";
  if (raw === "relaxed") return "Relaxed";
  return raw;
}

function applySample(setters, payload) {
  const state = mapPayloadState(payload);
  if (state && state !== "Connecting") {
    setters.setDetectedState(state);
  }
  if (typeof payload.confidence === "number") {
    const pct = payload.confidence <= 1 ? Math.round(payload.confidence * 100) : Math.round(payload.confidence);
    setters.setConfidence(pct);
  }
  if (payload.active_raaga || payload.activeRaaga) {
    setters.setSuggestedRaaga(payload.active_raaga || payload.activeRaaga);
  }
  if (typeof payload.transition_stage === "number") {
    setters.setTransitionStage(payload.transition_stage);
  }
  const live = payload.eeg_status === "live";
  setters.setConnected(live);
  setters.setMode(live ? "live" : "waiting");

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
    const peak = Math.max(alpha, beta, theta) / scale;
    setters.setQuality(Math.round(72 + peak * 26));
  }
}

export function EEGRealtimeProvider({ children }) {
  const [connected, setConnected] = useState(false);
  const [quality, setQuality] = useState(0);
  const [confidence, setConfidence] = useState(0);
  const [detectedState, setDetectedState] = useState("Connecting");
  const [suggestedRaaga, setSuggestedRaaga] = useState("—");
  const [transitionStage, setTransitionStage] = useState(0);
  const [eegSeries, setEegSeries] = useState([]);
  const [mode, setMode] = useState("waiting");
  const wsRef = useRef(null);

  const setters = useMemo(
    () => ({
      setConnected,
      setConfidence,
      setDetectedState,
      setSuggestedRaaga,
      setTransitionStage,
      setMode,
      setQuality,
      appendSeries: (point) => setEegSeries((prev) => [...prev.slice(-23), point]),
    }),
    []
  );

  useEffect(() => {
    let alive = true;

    async function poll() {
      try {
        const res = await fetch(POLL_URL);
        if (!res.ok || !alive) return;
        const payload = await res.json();
        applySample(setters, payload);
      } catch (_e) {
        if (alive) {
          setConnected(false);
          setMode("waiting");
          setDetectedState("Connecting");
        }
      }
    }

    poll();
    const pollId = setInterval(poll, 1000);

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
          const payload = JSON.parse(event.data);
          applySample(setters, payload);
        } catch (_e) {
          /* ignore malformed frames */
        }
      };

      ws.onclose = () => {
        if (!alive) return;
        setMode("waiting");
      };

      ws.onerror = () => {
        if (!alive) return;
        try {
          ws.close();
        } catch (_e) {
          /* noop */
        }
      };
    } catch (_e) {
      setMode("waiting");
    }

    return () => {
      alive = false;
      clearInterval(pollId);
      if (wsRef.current) wsRef.current.close();
    };
  }, [setters]);

  const value = useMemo(
    () => ({
      connected,
      quality: Math.round(quality),
      confidence: Math.round(confidence),
      detectedState,
      suggestedRaaga,
      transitionStage,
      eegSeries,
      mode,
    }),
    [connected, quality, confidence, detectedState, suggestedRaaga, transitionStage, eegSeries, mode]
  );

  return <EEGRealtimeContext.Provider value={value}>{children}</EEGRealtimeContext.Provider>;
}

export function useEEGRealtime() {
  const ctx = useContext(EEGRealtimeContext);
  if (!ctx) throw new Error("useEEGRealtime must be used within EEGRealtimeProvider");
  return ctx;
}
