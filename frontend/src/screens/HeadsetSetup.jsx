import React from "react";
import { useTherapy } from "../context/TherapyContext";
import { CTAButton, GlassCard } from "../components/ui/Primitives";

const CHANNELS = ["O1", "T3", "T4", "O2"];

function getQualityFromResistance(value, fallbackQuality = "BAD") {
  if (typeof value !== "number") return fallbackQuality;
  if (value <= 500) return "GOOD";
  if (value <= 1000) return "WARNING";
  return "BAD";
}

function formatResistance(value) {
  if (typeof value !== "number") return "—";
  return Math.round(value);
}

function qualityIcon(quality) {
  if (quality === "GOOD") return "🟢";
  if (quality === "WARNING") return "🟡";
  return "🔴";
}

export function HeadsetSetup() {
  const { stream, setScreen } = useTherapy();
  const headsetStatus = stream.headsetReady ? "READY" : "ADJUST HEADBAND";

  return (
    <div className="layout one">
      <GlassCard title="Headset Setup" className="hero-card">
        <div className="hero-head">
          <h1>Headset Setup</h1>
          <p>Adjust the headset while watching each EEG channel update live through the existing websocket stream.</p>
        </div>

        <div className="setup-grid">
          {CHANNELS.map((channel) => {
            const resistanceValue = stream.resistance?.[channel];
            const quality = getQualityFromResistance(resistanceValue, stream.channelQuality?.[channel] || "BAD");
            return (
              <div key={channel} className={`setup-channel-card ${quality.toLowerCase()}`}>
                <div className="setup-channel-head">
                  <strong>{channel}</strong>
                  <span>{qualityIcon(quality)} {quality}</span>
                </div>
                <div className="setup-resistance">
                  <span>Resistance</span>
                  <strong>{formatResistance(resistanceValue)}</strong>
                </div>
              </div>
            );
          })}
        </div>

        <div className="setup-panels">
          <div className="setup-panel">
            <h3>Resistance Values</h3>
            {CHANNELS.map((channel) => (
              <div key={channel} className="setup-row">
                <span>{channel}</span>
                <strong>{formatResistance(stream.resistance?.[channel])}</strong>
              </div>
            ))}
          </div>

          <div className="setup-panel">
            <h3>Headset Status</h3>
            <div className={`setup-status ${stream.headsetReady ? "ready" : "warning"}`}>
              <strong>{stream.headsetReady ? "✅ READY" : "⚠️ ADJUST HEADBAND"}</strong>
              <p>
                {stream.headsetReady
                  ? "All channels are acceptable. Therapy controls are now enabled."
                  : "Adjust Headband Position Until All Channels Are Green"}
              </p>
            </div>
            <div className="setup-row">
              <span>Live Link</span>
              <strong>{stream.connected ? "WebSocket Live" : "Waiting for Live Stream"}</strong>
            </div>
            <div className="setup-row">
              <span>Status</span>
              <strong>{headsetStatus}</strong>
            </div>
          </div>
        </div>

        {!stream.headsetReady ? (
          <div className="error-state">Adjust Headband Position Until All Channels Are Green</div>
        ) : null}

        <div className="actions-row">
          <CTAButton kind="ghost" onClick={() => setScreen("landing")} disabled={!stream.headsetReady}>
            Continue
          </CTAButton>
        </div>
      </GlassCard>
    </div>
  );
}
