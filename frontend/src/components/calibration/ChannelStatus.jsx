import React from "react";

function qualityColor(quality) {
  if (quality === "GREEN") return "#34d399";
  if (quality === "YELLOW") return "#fbbf24";
  return "#f87171";
}

export function ChannelStatus({ channels = {}, overallReady = false }) {
  const entries = Object.entries(channels);

  return (
    <div className="glass-card">
      <p className="section-kicker">Signal Quality</p>
      <h3 className="screen-title" style={{ marginBottom: 10 }}>Channel Status</h3>

      <div className="muted" style={{ marginBottom: 12 }}>
        Readiness: <strong style={{ color: overallReady ? "#34d399" : "#fbbf24" }}>{overallReady ? "READY" : "NOT READY"}</strong>
      </div>

      {entries.length === 0 ? (
        <div className="muted">Waiting for resistance/impedance data...</div>
      ) : (
        <div style={{ display: "grid", gap: 8 }}>
          {entries.map(([channel, data]) => {
            const color = qualityColor(data?.quality);
            return (
              <div
                key={channel}
                style={{
                  border: "1px solid rgba(153, 181, 241, .2)",
                  borderRadius: 12,
                  padding: "10px 12px",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <div>
                  <strong>{channel}</strong>
                  <div className="muted" style={{ fontSize: 12 }}>
                    {typeof data?.resistance === "number" ? data.resistance.toFixed(1) : "--"}
                  </div>
                </div>
                <span
                  style={{
                    color,
                    border: `1px solid ${color}`,
                    borderRadius: 999,
                    padding: "3px 10px",
                    fontSize: 12,
                    fontWeight: 600,
                  }}
                >
                  {data?.quality || "RED"}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
