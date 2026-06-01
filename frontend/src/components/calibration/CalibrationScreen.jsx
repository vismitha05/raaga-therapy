import React, { useEffect, useMemo, useState } from "react";

import { createLiveSocket } from "../../services/websocketService";
import { CalibrationProgress } from "./CalibrationProgress";
import { ChannelStatus } from "./ChannelStatus";
import { DeviceConnectionStatus } from "./DeviceConnectionStatus";
import { API_BASE, API_PREFIX, WS_URL } from "../../config/runtimeConfig";

const CALIBRATION_STATUS_URL = `${API_BASE}${API_PREFIX}/calibration/status`;

const DEFAULT_CALIBRATION = {
  status: "idle",
  calibrator_progress: 0,
  productivity_progress: 0,
  physiological_progress: 0,
  calibration_failed: false,
};

export function CalibrationScreen() {
  const [connectionState, setConnectionState] = useState({ state: "disconnected", last_error: null });
  const [capsuleEegStatus, setCapsuleEegStatus] = useState("waiting");
  const [battery, setBattery] = useState(null);
  const [channels, setChannels] = useState({});
  const [physiologicalStates, setPhysiologicalStates] = useState({});
  const [calibration, setCalibration] = useState(DEFAULT_CALIBRATION);

  useEffect(() => {
    let alive = true;

    async function pollCalibrationStatus() {
      try {
        const res = await fetch(CALIBRATION_STATUS_URL);
        if (!res.ok || !alive) return;
        const payload = await res.json();
        if (alive && payload && typeof payload === "object") {
          setCalibration((prev) => ({ ...prev, ...payload }));
        }
      } catch (_e) {
        // keep previous status
      }
    }

    pollCalibrationStatus();
    const pollId = setInterval(pollCalibrationStatus, 1500);

    const ws = createLiveSocket(WS_URL, (payload) => {
      if (!alive || !payload) return;

      if (payload.capsule_eeg_status) setCapsuleEegStatus(payload.capsule_eeg_status);
      if (typeof payload.battery === "number") setBattery(payload.battery);

      if (payload.resistance && typeof payload.resistance === "object") {
        const mapped = {};
        Object.entries(payload.resistance).forEach(([channel, value]) => {
          const resistance = Number(value);
          let quality = "RED";
          if (!Number.isNaN(resistance)) {
            if (resistance <= 10000) quality = "GREEN";
            else if (resistance <= 30000) quality = "YELLOW";
          }
          mapped[channel] = { resistance, quality };
        });
        setChannels(mapped);
      }

      if (payload.physiological_states && typeof payload.physiological_states === "object") {
        setPhysiologicalStates(payload.physiological_states);
      }
    });

    ws.onopen = () => {
      if (!alive) return;
      setConnectionState((prev) => ({ ...prev, state: "connecting" }));
    };

    ws.onclose = () => {
      if (!alive) return;
      setConnectionState({ state: "disconnected", last_error: null });
    };

    ws.onerror = () => {
      if (!alive) return;
      setConnectionState({ state: "error", last_error: "WebSocket connection error" });
      try {
        ws.close();
      } catch (_e) {
        // noop
      }
    };

    return () => {
      alive = false;
      clearInterval(pollId);
      ws.close();
    };
  }, []);

  const overallReady = useMemo(() => {
    const values = Object.values(channels);
    if (values.length === 0) return false;
    return values.every((v) => v.quality !== "RED");
  }, [channels]);

  useEffect(() => {
    setConnectionState((prev) => ({ ...prev, state: capsuleEegStatus === "live" ? "streaming" : prev.state }));
  }, [capsuleEegStatus]);

  return (
    <div className="layout two" style={{ alignItems: "start" }}>
      <div style={{ display: "grid", gap: 16 }}>
        <DeviceConnectionStatus
          connectionState={connectionState}
          capsuleEegStatus={capsuleEegStatus}
          battery={battery}
        />
        <ChannelStatus channels={channels} overallReady={overallReady} />
      </div>

      <div style={{ display: "grid", gap: 16 }}>
        <CalibrationProgress calibration={calibration} />
        <div className="glass-card">
          <p className="section-kicker">Readiness</p>
          <h3 className="screen-title" style={{ marginBottom: 10 }}>Headset Readiness</h3>
          <div className="muted">
            {overallReady ? "Headset is ready for calibration and session start." : "Adjust electrode contact to remove RED channels."}
          </div>
          <div style={{ marginTop: 10, color: overallReady ? "#34d399" : "#fbbf24", fontWeight: 600 }}>
            {overallReady ? "READY" : "NOT READY"}
          </div>
          {Object.keys(physiologicalStates).length > 0 ? (
            <pre style={{ marginTop: 12, fontSize: 12, color: "#9fb5e8", whiteSpace: "pre-wrap" }}>
              {JSON.stringify(physiologicalStates, null, 2)}
            </pre>
          ) : null}
        </div>
      </div>
    </div>
  );
}
