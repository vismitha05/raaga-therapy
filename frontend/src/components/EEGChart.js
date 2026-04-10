/**
 * StateDisplay.jsx
 * ----------------
 * Shows the current detected brain state with a pulsing animated indicator.
 * Colour-coded:
 *   Focused  → green  (#69f0ae)
 *   Relaxed  → blue   (#4fc3f7)
 *   Fatigued → orange (#ff6b35)
 *
 * Also displays the three raw band power values as gauges.
 *
 * Props:
 *   state  – string: "Focused" | "Relaxed" | "Fatigued"
 *   alpha  – float 0–1
 *   beta   – float 0–1
 *   theta  – float 0–1
 */

import React, { useEffect, useRef } from "react";

const STATE_CONFIG = {
  Focused:  { color: "#69f0ae", icon: "◈", label: "FOCUSED",  desc: "High concentration detected" },
  Relaxed:  { color: "#4fc3f7", icon: "◉", label: "RELAXED",  desc: "Calm alpha waves dominant" },
  Fatigued: { color: "#ff6b35", icon: "◎", label: "FATIGUED", desc: "Theta waves elevated" },
};

// ── Band power gauge ──────────────────────────────────────────────────────────
const BandGauge = ({ label, value, color }) => (
  <div className="band-gauge">
    <div className="band-label">
      <span>{label}</span>
      <span style={{ color }}>{(value * 100).toFixed(1)}%</span>
    </div>
    <div className="gauge-track">
      <div
        className="gauge-fill"
        style={{
          width: `${Math.min(100, value * 100)}%`,
          background: `linear-gradient(90deg, ${color}88, ${color})`,
          boxShadow: `0 0 8px ${color}66`,
        }}
      />
    </div>
  </div>
);

// ── Main component ────────────────────────────────────────────────────────────
const StateDisplay = ({ state, alpha, beta, theta }) => {
  const prevStateRef = useRef(state);
  const cardRef = useRef(null);

  const config = STATE_CONFIG[state] || STATE_CONFIG.Relaxed;

  // Flash animation whenever state changes
  useEffect(() => {
    if (state !== prevStateRef.current && cardRef.current) {
      cardRef.current.classList.remove("state-flash");
      // Force reflow to restart animation
      void cardRef.current.offsetWidth;
      cardRef.current.classList.add("state-flash");
      prevStateRef.current = state;
    }
  }, [state]);

  return (
    <div className="state-display" ref={cardRef}>
      {/* Main state indicator */}
      <div className="state-badge" style={{ borderColor: config.color }}>
        <div className="state-pulse" style={{ background: config.color }} />
        <span className="state-icon" style={{ color: config.color }}>{config.icon}</span>
        <div className="state-text">
          <span className="state-label" style={{ color: config.color }}>
            {config.label}
          </span>
          <span className="state-desc">{config.desc}</span>
        </div>
      </div>

      {/* Band power gauges */}
      <div className="band-gauges">
        <BandGauge label="Alpha" value={alpha} color="#4fc3f7" />
        <BandGauge label="Beta"  value={beta}  color="#69f0ae" />
        <BandGauge label="Theta" value={theta} color="#ff8a65" />
      </div>
    </div>
  );
};

export default StateDisplay;