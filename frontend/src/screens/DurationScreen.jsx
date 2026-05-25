import React from "react";
import { useTherapy } from "../context/TherapyContext";
import { CTAButton, GlassCard } from "../components/ui/Primitives";

const DURATION_OPTIONS = [
  { min: 10, impact: "Light adjustment" },
  { min: 20, impact: "Moderate regulation" },
  { min: 30, impact: "Deep neural relaxation" },
];

export function DurationScreen() {
  const { duration, setDuration, setScreen, startSession, audio, targetState } = useTherapy();

  return (
    <div className="layout one">
      <GlassCard title="Therapy Duration">
        <h2 className="screen-title">Select Session Length</h2>
        <div className="option-grid three">
          {DURATION_OPTIONS.map((d) => (
            <button key={d.min} className={`option-card ${duration === d.min ? "active" : ""}`} onClick={() => setDuration(d.min)}>
              <h3>{d.min} Minutes</h3>
              <p>{d.impact}</p>
            </button>
          ))}
        </div>
        <div className="actions-row">
          <CTAButton kind="ghost" onClick={() => setScreen("state")}>Back</CTAButton>
          <CTAButton onClick={async () => {
            const queue = audio.setQueueForState(targetState);
            startSession();
            setScreen("player");
            if (queue[0]) await audio.playTrack(queue[0]);
          }}>Start Therapy</CTAButton>
        </div>
      </GlassCard>
    </div>
  );
}
