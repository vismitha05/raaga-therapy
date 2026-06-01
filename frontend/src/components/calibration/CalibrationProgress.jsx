import React from "react";

function toPercent(value) {
  const n = typeof value === "number" ? value : 0;
  if (n <= 1) return Math.round(n * 100);
  return Math.max(0, Math.min(100, Math.round(n)));
}

export function CalibrationProgress({ calibration }) {
  const status = calibration?.status || "idle";
  const calibrator = toPercent(calibration?.calibrator_progress);
  const productivity = toPercent(calibration?.productivity_progress);
  const physiological = toPercent(calibration?.physiological_progress);

  const progress = Math.round((calibrator + productivity + physiological) / 3);
  const failed = Boolean(calibration?.calibration_failed);
  const complete = status === "completed";

  return (
    <div className="glass-card">
      <p className="section-kicker">Calibration</p>
      <h3 className="screen-title" style={{ marginBottom: 10 }}>Calibration Progress</h3>

      <div className="metric-line">
        <div className="metric-head">
          <span>Overall</span>
          <span>{progress}%</span>
        </div>
        <div className="metric-track">
          <div className="metric-fill cyan" style={{ width: `${progress}%` }} />
        </div>
      </div>

      <div className="metric-line">
        <div className="metric-head"><span>NFB Calibration</span><span>{calibrator}%</span></div>
        <div className="metric-track"><div className="metric-fill blue" style={{ width: `${calibrator}%` }} /></div>
      </div>

      <div className="metric-line">
        <div className="metric-head"><span>Productivity Baseline</span><span>{productivity}%</span></div>
        <div className="metric-track"><div className="metric-fill purple" style={{ width: `${productivity}%` }} /></div>
      </div>

      <div className="metric-line">
        <div className="metric-head"><span>Physiological Baseline</span><span>{physiological}%</span></div>
        <div className="metric-track"><div className="metric-fill green" style={{ width: `${physiological}%` }} /></div>
      </div>

      <div className="muted" style={{ marginTop: 10 }}>
        Status: <strong>{status}</strong>
      </div>

      {complete ? <div style={{ color: "#34d399", marginTop: 6 }}>Calibration complete</div> : null}
      {failed ? <div style={{ color: "#f87171", marginTop: 6 }}>Calibration failed</div> : null}
    </div>
  );
}
