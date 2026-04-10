/**
 * RagaPlayerStatus.jsx
 * --------------------
 * Shows which raga track is currently playing and provides
 * volume control + mode toggle.
 *
 * Props:
 *   audio  – { track, state, mode, playing, volume }
 *   onModeChange   – fn(newMode: string)
 *   onVolumeChange – fn(newVolume: float)
 */

import React, { useState } from "react";

const TRACK_META = {
  "focus.mp3":  { name: "Raga Bhairav",   mood: "Clarity & Precision", emoji: "🎵" },
  "calm.mp3":   { name: "Raga Yaman",      mood: "Serenity & Peace",    emoji: "🎶" },
  "energy.mp3": { name: "Raga Bhairavi",   mood: "Vitality & Revival",  emoji: "🎸" },
};

const RagaPlayerStatus = ({ audio, onModeChange, onVolumeChange }) => {
  const [localVolume, setLocalVolume] = useState(audio?.volume ?? 0.75);

  const meta = TRACK_META[audio?.track] || { name: "—", mood: "Initialising…", emoji: "⏳" };
  const isStudy = audio?.mode === "Study";

  const handleVolumeChange = (e) => {
    const v = parseFloat(e.target.value);
    setLocalVolume(v);
    onVolumeChange(v);
  };

  const handleModeToggle = () => {
    onModeChange(isStudy ? "Relax" : "Study");
  };

  return (
    <div className="raga-player">
      <h2 className="section-title">Adaptive Audio</h2>

      {/* Now playing */}
      <div className="now-playing">
        <div className={`equaliser ${audio?.playing ? "playing" : ""}`}>
          {[1, 2, 3, 4].map((i) => (
            <span key={i} className="eq-bar" style={{ animationDelay: `${i * 0.15}s` }} />
          ))}
        </div>
        <div className="track-info">
          <span className="track-name">{meta.emoji} {meta.name}</span>
          <span className="track-mood">{meta.mood}</span>
        </div>
        <div className={`playing-dot ${audio?.playing ? "active" : ""}`} />
      </div>

      {/* Volume slider */}
      <div className="volume-control">
        <span className="control-label">🔈</span>
        <input
          type="range"
          min="0"
          max="1"
          step="0.01"
          value={localVolume}
          onChange={handleVolumeChange}
          className="volume-slider"
        />
        <span className="control-label">🔊</span>
        <span className="volume-value">{Math.round(localVolume * 100)}%</span>
      </div>

      {/* Mode toggle */}
      <div className="mode-toggle" onClick={handleModeToggle}>
        <div className={`toggle-track ${isStudy ? "study" : "relax"}`}>
          <div className="toggle-thumb" />
        </div>
        <span className="mode-label">
          {isStudy ? "📚 Study Mode" : "🌙 Relax Mode"}
        </span>
        <span className="mode-hint">
          {isStudy
            ? "Focus tracks enabled"
            : "Calm tracks prioritised"}
        </span>
      </div>
    </div>
  );
};

export default RagaPlayerStatus;