import React, { createContext, useContext, useMemo, useState } from "react";

const CalibrationContext = createContext(null);

export function CalibrationProvider({ children }) {
  const [status, setStatus] = useState("not_started");
  const value = useMemo(() => ({ status, setStatus }), [status]);
  return <CalibrationContext.Provider value={value}>{children}</CalibrationContext.Provider>;
}

export function useCalibration() {
  const ctx = useContext(CalibrationContext);
  if (!ctx) throw new Error("useCalibration must be used within CalibrationProvider");
  return ctx;
}

