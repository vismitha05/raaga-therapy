import React from "react";
import { useTherapy } from "../context/TherapyContext";
import { CTAButton, GlassCard } from "../components/ui/Primitives";

const OPTIONS = ["T1", "T2", "A1", "A2", "B1", "B2"];

export function StateSelectionScreen() {
  const { targetState, setTargetState, stateMeta, setScreen } = useTherapy();

  return (
    <div className="layout one">
      <GlassCard title="Target State Selection">
        <h2 className="screen-title">Choose Your Preferred Mental State</h2>
        <div className="option-grid three">
          {OPTIONS.map((name) => (
            <button key={name} className={`option-card ${targetState === name ? "active" : ""}`} onClick={() => setTargetState(name)}>
              <span className="option-icon">{stateMeta[name].icon}</span>
              <h3>{name} · {stateMeta[name].title}</h3>
              <p>{stateMeta[name].desc}</p>
            </button>
          ))}
        </div>
        <div className="actions-row">
          <CTAButton kind="ghost" onClick={() => setScreen("landing")}>Back</CTAButton>
          <CTAButton onClick={() => setScreen("duration")}>Next</CTAButton>
        </div>
      </GlassCard>
    </div>
  );
}
