/**
 * App.jsx
 * -------
 * Root component for the Neiry Neurofeedback Dashboard.
 *
 * Responsibilities:
 *  - Polls /data every 750 ms for live EEG + audio status
 *  - Polls /history every 3 s for the timeline graph data
 *  - Orchestrates child components: StateDisplay, EEGChart,
 *    RagaPlayerStatus, StateHistoryChart
 *  - Sends mode / volume changes to backend
 */

import React, { useState, useEffect, useCallback, useRef } from "react";
import axios from "axios";

import StateDisplay      from "./components/StateDisplay";
import EEGChart          from "./components/EEGChart";
import RagaPlayerStatus  from "./components/RagaPlayerStatus";
import StateHistoryChart from "./components/StateHistoryChart";

import "./App.css";

// ── Config ────────────────────────────────────────────────────────────────────
const API_BASE      = process.env.REACT_APP_API_URL || "http://localhost:5000";
const POLL_LIVE_MS  = 750;    // live data polling interval
const POLL_HIST_MS  = 3000;   // history polling interval

// ── Default state ─────────────────────────────────────────────────────────────
const DEFAULT_EEG = { alpha: 0, beta: 0, theta: 0, state: "Relaxed" };
const DEFAULT_AUDIO = { track: null, state: null, mode: "Study", playing: false, volume: 0.75 };

// ─────────────────────────────────────────────
const App = () => {
  const [eeg,     setEEG    ] = useState(DEFAULT_EEG);
  const [audio,   setAudio  ] = useState(DEFAULT_AUDIO);
  const [history, setHistory] = useState([]);
  const [status,  setStatus ] = useState("Connecting…");
  const [lastUpdate, setLastUpdate] = useState(null);

  // Keep latest audio state in a ref so callbacks don't close over stale state
  const audioRef = useRef(audio);
  audioRef.current = audio;

  // ── Live data polling ───────────────────────────────────────────────────────
  const fetchLive = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API_BASE}/data`, { timeout: 2000 });
      setEEG({ alpha: data.alpha, beta: data.beta, theta: data.theta, state: data.state });
      if (data.audio) setAudio(data.audio);
      setStatus("Live");
      setLastUpdate(new Date().toLocaleTimeString());
    } catch {
      setStatus("Reconnecting…");
    }
  }, []);

  // ── History polling ─────────────────────────────────────────────────────────
  const fetchHistory = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API_BASE}/history`, { timeout: 3000 });
      if (Array.isArray(data)) setHistory(data);
    } catch {
      // silent — history is non-critical
    }
  }, []);

  // ── Set up polling intervals on mount ──────────────────────────────────────
  useEffect(() => {
    fetchLive();
    fetchHistory();

    const liveTimer = setInterval(fetchLive,    POLL_LIVE_MS);
    const histTimer = setInterval(fetchHistory, POLL_HIST_MS);

    return () => {
      clearInterval(liveTimer);
      clearInterval(histTimer);
    };
  }, [fetchLive, fetchHistory]);

  // ── Mode change ─────────────────────────────────────────────────────────────
  const handleModeChange = useCallback(async (newMode) => {
    try {
      await axios.post(`${API_BASE}/mode`, { mode: newMode });
      setAudio((prev) => ({ ...prev, mode: newMode }));
    } catch (err) {
      console.error("Mode change failed:", err);
    }
  }, []);

  // ── Volume change ───────────────────────────────────────────────────────────
  const handleVolumeChange = useCallback(async (vol) => {
    try {
      await axios.post(`${API_BASE}/volume`, { volume: vol });
    } catch (err) {
      console.error("Volume change failed:", err);
    }
  }, []);

  // ─────────────────────────────────────────────────────────────────────────────
  return (
    <div className="app">
      {/* ── Header ─────────────────────────────────────────────── */}
      <header className="header">
        <div className="header-left">
          <div className="logo">
            <span className="logo-icon">⬡</span>
            <span className="logo-text">NeuroSync</span>
          </div>
          <span className="logo-sub">Neiry EEG · Real-time Neurofeedback</span>
        </div>
        <div className="header-right">
          <div className={`status-pill ${status === "Live" ? "live" : "reconnect"}`}>
            <span className="status-dot" />
            {status}
          </div>
          {lastUpdate && (
            <span className="last-update">Updated {lastUpdate}</span>
          )}
        </div>
      </header>

      {/* ── Main grid ──────────────────────────────────────────── */}
      <main className="grid">

        {/* Row 1: State display (left) + Raga player (right) */}
        <section className="card state-col">
          <StateDisplay
            state={eeg.state}
            alpha={eeg.alpha}
            beta={eeg.beta}
            theta={eeg.theta}
          />
        </section>

        <section className="card raga-col">
          <RagaPlayerStatus
            audio={audio}
            onModeChange={handleModeChange}
            onVolumeChange={handleVolumeChange}
          />
        </section>

        {/* Row 2: EEG line chart (full width) */}
        <section className="card chart-col">
          <EEGChart history={history} />
        </section>

        {/* Row 3: State history timeline */}
        <section className="card history-col">
          <StateHistoryChart history={history} />
        </section>

      </main>

      {/* ── Footer ─────────────────────────────────────────────── */}
      <footer className="footer">
        <span>Neiry EEG · LSL Stream · Adaptive Raga Audio</span>
        <span>Polling every {POLL_LIVE_MS}ms</span>
      </footer>
    </div>
  );
};

export default App;