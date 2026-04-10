/**
 * StateHistoryChart.jsx
 * ---------------------
 * Compact timeline showing brain state transitions over the session.
 * Each coloured segment represents a period in one state.
 *
 * Props:
 *   history – array of { state, timestamp } objects
 */

import React, { useMemo } from "react";

const STATE_COLOR = {
  Focused:  "#69f0ae",
  Relaxed:  "#4fc3f7",
  Fatigued: "#ff6b35",
};

const StateHistoryChart = ({ history }) => {
  // Compress consecutive identical states into run-length encoded segments
  const segments = useMemo(() => {
    if (!history.length) return [];
    const result = [];
    let current = { state: history[0].state, count: 1, ts: history[0].timestamp };

    for (let i = 1; i < history.length; i++) {
      if (history[i].state === current.state) {
        current.count++;
      } else {
        result.push({ ...current });
        current = { state: history[i].state, count: 1, ts: history[i].timestamp };
      }
    }
    result.push({ ...current });
    return result;
  }, [history]);

  const total = segments.reduce((acc, s) => acc + s.count, 0) || 1;

  // State duration summary
  const stateSummary = useMemo(() => {
    const counts = { Focused: 0, Relaxed: 0, Fatigued: 0 };
    history.forEach((h) => { if (counts[h.state] !== undefined) counts[h.state]++; });
    const total = history.length || 1;
    return Object.entries(counts).map(([s, c]) => ({
      state: s,
      pct: Math.round((c / total) * 100),
      color: STATE_COLOR[s],
    }));
  }, [history]);

  return (
    <div className="history-chart">
      <h2 className="section-title">State Timeline</h2>

      {/* Segmented bar */}
      <div className="timeline-bar">
        {segments.map((seg, i) => (
          <div
            key={i}
            className="timeline-seg"
            style={{
              width: `${(seg.count / total) * 100}%`,
              background: STATE_COLOR[seg.state] || "#555",
              opacity: 0.85,
            }}
            title={`${seg.state} (${seg.count} samples)`}
          />
        ))}
      </div>
      <div className="timeline-labels">
        <span>Session start</span>
        <span>Now</span>
      </div>

      {/* Percentage breakdown */}
      <div className="state-summary">
        {stateSummary.map(({ state, pct, color }) => (
          <div key={state} className="summary-item">
            <span className="summary-dot" style={{ background: color }} />
            <span className="summary-state">{state}</span>
            <span className="summary-pct" style={{ color }}>{pct}%</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default StateHistoryChart;