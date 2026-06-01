import React from "react";

const dotStyle = {
  width: 10,
  height: 10,
  borderRadius: "50%",
  display: "inline-block",
  marginRight: 8,
};

function statusColor(state) {
  if (state === "streaming" || state === "connected" || state === "ready") return "#34d399";
  if (state === "connecting" || state === "waiting") return "#fbbf24";
  return "#f87171";
}

export function DeviceConnectionStatus({ connectionState, capsuleEegStatus, battery }) {
  const state = connectionState?.state || "disconnected";
  const color = statusColor(state);

  return (
    <div className="glass-card">
      <p className="section-kicker">Headset</p>
      <h3 className="screen-title" style={{ marginBottom: 10 }}>Device Connection</h3>

      <div style={{ display: "grid", gap: 8 }}>
        <div>
          <span style={{ ...dotStyle, background: color }} />
          <strong>{state}</strong>
        </div>
        <div className="muted">EEG Stream: {capsuleEegStatus || "waiting"}</div>
        <div className="muted">Battery: {typeof battery === "number" ? `${battery}%` : "--"}</div>
        {connectionState?.last_error ? (
          <div className="error-state" style={{ margin: 0 }}>
            {connectionState.last_error}
          </div>
        ) : null}
      </div>
    </div>
  );
}
