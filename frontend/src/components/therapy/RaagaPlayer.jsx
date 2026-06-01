import React from "react";

export function RaagaPlayer({
  currentTrack,
  upcomingTrack,
  isPlaying,
  playbackStatus,
  currentTime,
  trackDuration,
  crossfadeSeconds,
}) {
  return (
    <div className="raaga-player-panel">
      <div className="therapy-stat-card">
        <span className="therapy-stat-label">Playback Status</span>
        <strong>{playbackStatus || (isPlaying ? "Playing" : "Paused")}</strong>
        <p>{isPlaying ? "Dual-deck crossfade player is active." : "Playback is paused."}</p>
      </div>
      <div className="therapy-status-grid">
        <div className="therapy-stat-card">
          <span className="therapy-stat-label">Current Track Window</span>
          <strong>{currentTrack?.raaga || "—"}</strong>
          <p>{currentTrack ? `${currentTrack.start_time}s → ${currentTrack.end_time}s` : "Waiting for playlist."}</p>
        </div>
        <div className="therapy-stat-card">
          <span className="therapy-stat-label">Upcoming Crossfade</span>
          <strong>{upcomingTrack?.raaga || "Final Track"}</strong>
          <p>{crossfadeSeconds ? `Crossfade length: ${crossfadeSeconds}s` : "No crossfade scheduled."}</p>
        </div>
      </div>
      <div className="signal-row">
        <span>Track Playback</span>
        <span>{Math.floor(currentTime || 0)}s / {Math.floor(trackDuration || 0)}s</span>
      </div>
    </div>
  );
}
