import React, { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";

const EEGRealtimeContext = createContext(null);

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";
const WS_URL = process.env.REACT_APP_WS_URL || API_BASE.replace(/^http/, "ws") + "/api/v1/ws/live";

const STATES = ["Focused", "Relaxed", "Sleep"];

export function EEGRealtimeProvider({ children }) {
  const [connected, setConnected] = useState(false);
  const [quality, setQuality] = useState(90);
  const [confidence, setConfidence] = useState(82);
  const [detectedState, setDetectedState] = useState("Focused");
  const [suggestedRaaga, setSuggestedRaaga] = useState("Hamsadhwani");
  const [transitionStage, setTransitionStage] = useState(0);
  const [eegSeries, setEegSeries] = useState([]);
  const [mode, setMode] = useState("mock");
  const wsRef = useRef(null);

  useEffect(() => {
    let alive = true;
    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!alive) return;
        setConnected(true);
        setMode("ws");
      };

      ws.onmessage = (event) => {
        if (!alive) return;
        const payload = JSON.parse(event.data);
        const state = payload.detected_state || payload.detectedState;
        const raaga = payload.active_raaga || payload.activeRaaga;
        if (state) setDetectedState(state);
        if (raaga) setSuggestedRaaga(raaga);
        if (typeof payload.confidence === "number") setConfidence(Math.round(payload.confidence * 100));
        if (typeof payload.transition_stage === "number") setTransitionStage(payload.transition_stage);
        // respect backend-reported EEG status (live vs offline)
        if (payload.eeg_status && payload.eeg_status !== "live") {
          setConnected(false);
        } else {
          setConnected(true);
        }
      };

      ws.onclose = () => {
        if (!alive) return;
        setConnected(false);
        setMode("mock");
      };

      ws.onerror = () => {
        if (!alive) return;
        setConnected(false);
        setMode("mock");
        try { ws.close(); } catch (_e) {}
      };
    } catch (_e) {
      setMode("mock");
    }

    return () => {
      alive = false;
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  useEffect(() => {
    const start = Date.now();
    const id = setInterval(() => {
      const t = (Date.now() - start) / 1000;
      const alpha = Math.round(48 + Math.sin(t * 0.7) * 18 + Math.random() * 8);
      const beta = Math.round(44 + Math.cos(t * 1.1) * 16 + Math.random() * 9);
      const theta = Math.round(38 + Math.sin(t * 0.5 + 0.8) * 14 + Math.random() * 10);
      setEegSeries((prev) => [...prev.slice(-23), { tick: new Date().toLocaleTimeString(), alpha, beta, theta }]);

      if (mode === "mock") {
        setQuality((q) => Math.max(72, Math.min(99, q + (Math.random() * 6 - 3))));
        setConfidence((c) => Math.max(70, Math.min(98, c + (Math.random() * 5 - 2.5))));
        if (Math.random() > 0.86) setDetectedState(STATES[Math.floor(Math.random() * STATES.length)]);
      }
    }, 1200);

    return () => clearInterval(id);
  }, [mode]);

  const value = useMemo(
    () => ({ connected, quality: Math.round(quality), confidence: Math.round(confidence), detectedState, suggestedRaaga, transitionStage, eegSeries, mode }),
    [connected, quality, confidence, detectedState, suggestedRaaga, transitionStage, eegSeries, mode]
  );

  return <EEGRealtimeContext.Provider value={value}>{children}</EEGRealtimeContext.Provider>;
}

export function useEEGRealtime() {
  const ctx = useContext(EEGRealtimeContext);
  if (!ctx) throw new Error("useEEGRealtime must be used within EEGRealtimeProvider");
  return ctx;
}
