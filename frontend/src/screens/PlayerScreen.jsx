import React from "react";
import { useTherapy } from "../context/TherapyContext";
import { EEGLineChart } from "../components/charts/AnalyticsCharts";
import { CTAButton, GlassCard, ProgressBar } from "../components/ui/Primitives";

export function PlayerScreen() {
  const {
    stream,
    targetState,
    liveMetrics,
    sessionProgress,
    timerSec,
    remainingSec,
    setScreen,
    audio,
    endSession,
  } = useTherapy();

  const mins = String(Math.floor(timerSec / 60)).padStart(2, "0");
  const secs = String(timerSec % 60).padStart(2, "0");
  const rMins = String(Math.floor(remainingSec / 60)).padStart(2, "0");
  const rSecs = String(remainingSec % 60).padStart(2, "0");

  return (
    <div className="layout two">
      <GlassCard title="Adaptive Raaga Therapy Player">
        <div className="player-top">
          <div>
            <h2>{stream.currentRaaga}</h2>
            <p>AI selected Raaga: {stream.currentRaaga} for enhanced {targetState.toLowerCase()}</p>
            <p className="muted">Current state: {stream.detectedState} | Target state: {targetState}</p>
            <p className="muted">Status: {stream.playbackStatus} | Transition: {stream.transitionState}</p>
          </div>
          <div className={`breath-orb ${audio.isPlaying ? "play" : ""}`} />
        </div>

        <div className="music-controls">
          <button className="play-btn" onClick={audio.togglePlayPause}>{audio.isPlaying ? "Pause" : "Play"}</button>
          <div className="progress-wrap">
            <div className="signal-track"><div style={{ width: `${Math.round(sessionProgress)}%` }} /></div>
            <div className="signal-row"><span>Therapy Progress</span><span>{Math.round(sessionProgress)}%</span></div>
          </div>
          <span className="timer-pill">{mins}:{secs}</span>
        </div>
        <div className="music-controls">
          <div className="signal-row"><span>Remaining</span><span>{rMins}:{rSecs}</span></div>
          <div className="progress-wrap">
            <div className="signal-track"><div style={{ width: `${Math.round(stream.playbackProgress)}%` }} /></div>
            <div className="signal-row"><span>Track Progress</span><span>{Math.round(stream.playbackProgress)}%</span></div>
          </div>
          <span className="timer-pill">{Math.floor(stream.currentTime)}s / {Math.floor(stream.trackDuration || 0)}s</span>
        </div>
        <div className="music-controls">
          <span className="muted">Volume</span>
          <input type="range" min="0" max="1" step="0.01" value={audio.volume} onChange={(e) => audio.setVolume(Number(e.target.value))} />
          <span className="timer-pill">{Math.round(audio.volume * 100)}%</span>
        </div>
        {stream.error ? <div className="error-state">{stream.error}</div> : null}

        <EEGLineChart data={stream.eegSeries} />
      </GlassCard>

      <GlassCard title="Live Progress Analytics">
        <ProgressBar label="Focus Level" value={liveMetrics.focus} color="cyan" />
        <ProgressBar label="Relaxation Level" value={liveMetrics.relaxation} color="blue" />
        <ProgressBar label="Cognitive Stability" value={liveMetrics.stability} color="purple" />
        <ProgressBar label="Stress Reduction" value={liveMetrics.stressReduction} color="green" />
        <ProgressBar label="Sleep Readiness" value={liveMetrics.sleepReadiness} color="blue" />
        <CTAButton kind="ghost" onClick={() => { endSession(); setScreen("completion"); }}>End Session</CTAButton>
      </GlassCard>
    </div>
  );
}
