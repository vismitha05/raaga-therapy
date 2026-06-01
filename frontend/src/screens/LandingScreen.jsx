import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useTherapy } from "../context/TherapyContext";
import { EEGLineChart } from "../components/charts/AnalyticsCharts";
import { CircularMeter, CTAButton, GlassCard, Skeleton } from "../components/ui/Primitives";

export function LandingScreen() {
  const { stream, setScreen } = useTherapy();
  const [analysisPhase, setAnalysisPhase] = useState("idle");
  const [countdownSec, setCountdownSec] = useState(10);
  const [finalState, setFinalState] = useState("");
  const [finalConfidence, setFinalConfidence] = useState(0);

  useEffect(() => {
    if (analysisPhase !== "analyzing") return;
    if (countdownSec <= 0) {
      setFinalState(stream.detectedState);
      setFinalConfidence(stream.confidence);
      setAnalysisPhase("complete");
      return;
    }
    const id = setInterval(() => {
      setCountdownSec((s) => Math.max(0, s - 1));
    }, 1000);
    return () => clearInterval(id);
  }, [analysisPhase, countdownSec, stream.detectedState, stream.confidence]);

  function startAnalysis() {
    if (!stream.connected) return;
    setCountdownSec(10);
    setFinalState("");
    setFinalConfidence(0);
    setAnalysisPhase("analyzing");
  }

  return (
    <div className="layout one">
      <GlassCard title="Neiry EEG Live Monitoring" className="hero-card">
        <div className="hero-head">
          <h1>Adaptive Raaga Neural Detection</h1>
          <p>AI is continuously evaluating your brainwave patterns for real-time therapeutic calibration.</p>
        </div>

        {!stream.connected ? (
          <div className="error-state">Device disconnected. Reposition headband to resume neural sync.</div>
        ) : null}
        {!stream.headsetReady ? (
          <div className="error-state">{stream.headsetMessage || "Adjust Headband Position"}</div>
        ) : null}

        <div className="hero-grid">
          <div className="state-card">
            <p className="muted">Detected Mental State</p>
            <h2>{analysisPhase === "complete" ? finalState : stream.detectedState}</h2>
            <p>{stream.detectedStateLabel}</p>
            <p>Confidence {analysisPhase === "complete" ? finalConfidence : stream.confidence}%</p>
            <div className="signal-row">
              <span>Signal Quality</span>
              <span>{stream.quality}%</span>
            </div>
            <div className="signal-track"><div style={{ width: `${stream.quality}%` }} /></div>
            {analysisPhase === "idle" ? (
              <div className="muted">Click Start to begin 10-second brain-state analysis.</div>
            ) : null}
            {analysisPhase === "analyzing" ? (
              <motion.div className="analyzing" animate={{ opacity: [0.4, 1, 0.4] }} transition={{ repeat: Infinity, duration: 1.8 }}>
                Analyzing Brainwaves... {countdownSec}s
              </motion.div>
            ) : null}
            {analysisPhase === "complete" ? (
              <div className="analyzing">Analysis complete. Current brain state: {finalState}</div>
            ) : null}
          </div>

          <CircularMeter value={stream.confidence} label="Neural Confidence" />
        </div>

        <div className="wave-shell">
          {stream.eegSeries.length ? <EEGLineChart data={stream.eegSeries} /> : <Skeleton className="chart-skeleton" />}
        </div>

        {analysisPhase !== "complete" ? (
        <CTAButton onClick={startAnalysis} disabled={!stream.connected || analysisPhase === "analyzing"}>
            {analysisPhase === "analyzing" ? `Analyzing... ${countdownSec}s` : "Start Analysis"}
          </CTAButton>
        ) : null}
        <div className="actions-row">
          <CTAButton kind="ghost" onClick={() => setScreen("headset")}>
            Headset Setup
          </CTAButton>
          <CTAButton
            onClick={() => setScreen("state")}
            disabled={!stream.connected || !stream.headsetReady || analysisPhase !== "complete"}
          >
          Continue Therapy
          </CTAButton>
        </div>
      </GlassCard>
    </div>
  );
}
