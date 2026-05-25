import React from "react";
import { useTherapy } from "../context/TherapyContext";
import { ImprovementBars, SessionRadar } from "../components/charts/AnalyticsCharts";
import { CTAButton, GlassCard } from "../components/ui/Primitives";

export function CompletionScreen() {
  const { sessionResult, setScreen, resetSession } = useTherapy();
  const { before, after } = sessionResult;

  return (
    <div className="layout one">
      <GlassCard title="Session Completion Insights">
        <h2 className="screen-title">Neural Session Outcome</h2>
        <div className="table-shell">
          <table>
            <thead>
              <tr><th>Metric</th><th>Before</th><th>After</th><th>Improvement</th></tr>
            </thead>
            <tbody>
              <tr><td>Focus Level</td><td>{before.focus}%</td><td>{after.focus}%</td><td>+{after.focus - before.focus}%</td></tr>
              <tr><td>Stress Level</td><td>{before.stress}%</td><td>{after.stress}%</td><td>Reduced</td></tr>
              <tr><td>Relaxation</td><td>{before.relaxation}%</td><td>{after.relaxation}%</td><td>Improved</td></tr>
            </tbody>
          </table>
        </div>

        <div className="chart-grid">
          <SessionRadar before={before} after={after} />
          <ImprovementBars before={before} after={after} />
        </div>

        <div className="insights">
          <p>Your brain achieved <strong>{after.focus}% focus stability</strong>.</p>
          <p>Stress levels significantly reduced after Raaga therapy.</p>
          <p>Neural relaxation improved consistently during the session.</p>
        </div>

        <CTAButton onClick={() => { resetSession(); setScreen("landing"); }}>Start New Session</CTAButton>
      </GlassCard>
    </div>
  );
}
