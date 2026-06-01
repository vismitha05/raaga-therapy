import React from "react";

const QUALITY_COLORS = {
  GOOD: "good",
  WARNING: "warning",
  BAD: "bad",
};

export function TherapyStatus({
  currentState,
  currentStateLabel,
  targetState,
  targetStateLabel,
  currentRaaga,
  upcomingRaaga,
  sessionProgress,
  headsetReady,
  headsetMessage,
  channelQuality,
  pendingState,
  pendingSeconds,
}) {
  return (
    <div className="therapy-status-panel">
      <div className="therapy-status-grid">
        <div className="therapy-stat-card">
          <span className="therapy-stat-label">Current EEG State</span>
          <strong>{currentState || "—"}</strong>
          <p>{currentStateLabel || "Waiting for stable state"}</p>
        </div>
        <div className="therapy-stat-card">
          <span className="therapy-stat-label">Target EEG State</span>
          <strong>{targetState || "—"}</strong>
          <p>{targetStateLabel || "Select a target to begin"}</p>
        </div>
        <div className="therapy-stat-card">
          <span className="therapy-stat-label">Current Raaga</span>
          <strong>{currentRaaga || "—"}</strong>
          <p>Now guiding the active segment.</p>
        </div>
        <div className="therapy-stat-card">
          <span className="therapy-stat-label">Upcoming Raaga</span>
          <strong>{upcomingRaaga || "—"}</strong>
          <p>Prepared for the next crossfade.</p>
        </div>
      </div>

      <div className="therapy-session-progress">
        <div className="signal-row">
          <span>Session Progress</span>
          <span>{Math.round(sessionProgress || 0)}%</span>
        </div>
        <div className="signal-track">
          <div style={{ width: `${Math.round(sessionProgress || 0)}%` }} />
        </div>
      </div>

      <div className="therapy-status-grid">
        <div className="therapy-stat-card">
          <span className="therapy-stat-label">Headset Ready</span>
          <strong>{headsetReady ? "True" : "False"}</strong>
          <p>{headsetReady ? "Channel quality is acceptable." : headsetMessage || "Adjust Headband Position"}</p>
        </div>
        <div className="therapy-stat-card">
          <span className="therapy-stat-label">Stability Filter</span>
          <strong>{pendingState || "Stable"}</strong>
          <p>
            {pendingState
              ? `${pendingState} held for ${pendingSeconds || 0}s of 30s required`
              : "No pending fluctuation right now."}
          </p>
        </div>
      </div>

      <div className="channel-quality-grid">
        {["O1", "T3", "T4", "O2"].map((channel) => {
          const quality = channelQuality?.[channel] || "BAD";
          return (
            <div key={channel} className={`channel-quality-card ${QUALITY_COLORS[quality] || "bad"}`}>
              <span>{channel}</span>
              <strong>{quality}</strong>
            </div>
          );
        })}
      </div>
    </div>
  );
}
