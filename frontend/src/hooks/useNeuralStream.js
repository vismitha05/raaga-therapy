import { useEffect, useMemo, useState } from "react";

const STATES = ["Focused", "Relaxed", "Sleep"];
const RAAGAS = {
  Focused: "Hamsadhwani",
  Relaxed: "Yaman",
  Sleep: "Bageshri",
};

export function useNeuralStream() {
  const [connected, setConnected] = useState(true);
  const [quality, setQuality] = useState(92);
  const [confidence, setConfidence] = useState(86);
  const [detectedState, setDetectedState] = useState("Focused");
  const [eegSeries, setEegSeries] = useState([]);

  useEffect(() => {
    const start = Date.now();
    const id = setInterval(() => {
      const t = (Date.now() - start) / 1000;
      const alpha = 48 + Math.sin(t * 0.7) * 18 + Math.random() * 8;
      const beta = 44 + Math.cos(t * 1.1) * 16 + Math.random() * 9;
      const theta = 38 + Math.sin(t * 0.5 + 0.8) * 14 + Math.random() * 10;

      setEegSeries((prev) => {
        const next = [...prev, { tick: new Date().toLocaleTimeString(), alpha: Math.round(alpha), beta: Math.round(beta), theta: Math.round(theta) }];
        return next.slice(-24);
      });

      setQuality((q) => Math.max(74, Math.min(99, q + (Math.random() * 6 - 3))));
      setConfidence((c) => Math.max(70, Math.min(99, c + (Math.random() * 4 - 2))));

      if (Math.random() > 0.82) {
        const state = STATES[Math.floor(Math.random() * STATES.length)];
        setDetectedState(state);
      }
      if (Math.random() > 0.97) setConnected(false);
      if (Math.random() > 0.85) setConnected(true);
    }, 1200);

    return () => clearInterval(id);
  }, []);

  const currentRaaga = useMemo(() => RAAGAS[detectedState] || "Hamsadhwani", [detectedState]);

  return {
    connected,
    quality: Math.round(quality),
    confidence: Math.round(confidence),
    detectedState,
    eegSeries,
    currentRaaga,
  };
}
