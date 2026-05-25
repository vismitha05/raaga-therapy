import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

const TherapySessionContext = createContext(null);

export function TherapySessionProvider({ children }) {
  const [screen, setScreen] = useState("landing");
  const [targetState, setTargetState] = useState("Focused");
  const [duration, setDuration] = useState(20);
  const [isSessionActive, setIsSessionActive] = useState(false);
  const [elapsedSec, setElapsedSec] = useState(0);

  useEffect(() => {
    if (!isSessionActive) return;
    const id = setInterval(() => setElapsedSec((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, [isSessionActive]);

  const totalSec = duration * 60;
  const remainingSec = Math.max(0, totalSec - elapsedSec);
  const sessionProgress = Math.min(100, (elapsedSec / totalSec) * 100);

  useEffect(() => {
    if (isSessionActive && elapsedSec >= totalSec) {
      setIsSessionActive(false);
      setScreen("completion");
    }
  }, [isSessionActive, elapsedSec, totalSec]);

  function startSession() {
    setElapsedSec(0);
    setIsSessionActive(true);
  }

  function endSession() {
    setIsSessionActive(false);
    setScreen("completion");
  }

  function resetSession() {
    setIsSessionActive(false);
    setElapsedSec(0);
  }

  const value = useMemo(
    () => ({ screen, setScreen, targetState, setTargetState, duration, setDuration, isSessionActive, startSession, endSession, resetSession, elapsedSec, remainingSec, sessionProgress, totalSec }),
    [screen, targetState, duration, isSessionActive, elapsedSec, remainingSec, sessionProgress, totalSec]
  );

  return <TherapySessionContext.Provider value={value}>{children}</TherapySessionContext.Provider>;
}

export function useTherapySession() {
  const ctx = useContext(TherapySessionContext);
  if (!ctx) throw new Error("useTherapySession must be used within TherapySessionProvider");
  return ctx;
}
