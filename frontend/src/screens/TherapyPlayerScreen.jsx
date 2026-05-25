/**
 * TherapyPlayerScreen.jsx
 * ---------------------
 * Fourth screen: Plays generated raga playlist with smooth transitions.
 * Implements lazy loading (load ragas dynamically as needed).
 * Shows real-time playback progress and frequency band visualization.
 */

import React, { useState, useEffect, useRef } from 'react';
import { GlassCard, CTAButton } from '../components/ui/Primitives';
import styles from '../styles/screens.module.css';

export function TherapyPlayerScreen({
  sessionId,
  playlist,
  detection,
  targetState,
  onSessionComplete,
}) {
  // Playback state
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTrackIndex, setCurrentTrackIndex] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [totalTime, setTotalTime] = useState(0);
  const [demoMode, setDemoMode] = useState(false); // Fallback mode when audio files unavailable

  // Audio management
  const [loadedRagas, setLoadedRagas] = useState(new Set()); // Track loaded audio files
  const [currentAudio, setCurrentAudio] = useState(null);
  const audioRef = useRef(null);

  // Error handling
  const [error, setError] = useState(null);

  const tracks = playlist?.tracks || [];
  const currentTrack = tracks[currentTrackIndex];

  // Calculate total session duration
  useEffect(() => {
    const total = tracks.reduce((sum, track) => sum + track.duration_seconds, 0);
    setTotalTime(total);
  }, [tracks]);

  // Start playback
  const handlePlayPause = async () => {
    if (isPlaying) {
      audioRef.current?.pause();
      setIsPlaying(false);
      return;
    }

    try {
      setError(null);
      console.log(`[Playback] Starting track ${currentTrackIndex}: ${currentTrack?.raga}`);

      // Lazy load current raga
      const audio = await loadRagaDynamically(currentTrackIndex);
      
      if (!audio) {
        console.warn('[Playback] Audio file not available, using demo mode');
        setDemoMode(true);
        setIsPlaying(true);
        return;
      }

      // Make sure audio element is ready
      if (audio.src && audio.readyState >= 2) {
        // Audio is already loaded
        audio.play().catch(err => {
          console.error('Play error:', err);
          console.warn('Falling back to demo mode');
          setDemoMode(true);
          setIsPlaying(true);
        });
        setDemoMode(false);
        setIsPlaying(true);
      } else {
        // Wait for audio to be loadable
        const playWhenReady = () => {
          console.log(`[Playback] Audio ready, playing...`);
          audio.play().catch(err => {
            console.error('Play error after loading:', err);
            console.warn('Falling back to demo mode');
            setDemoMode(true);
          });
          audio.removeEventListener('canplay', playWhenReady);
        };
        
        audio.addEventListener('canplay', playWhenReady, { once: true });
        
        // Timeout if doesn't load - fallback to demo mode
        const timeoutId = setTimeout(() => {
          console.warn('[Playback] Timeout waiting for audio, switching to demo mode');
          audio.removeEventListener('canplay', playWhenReady);
          setDemoMode(true);
        }, 3000);

        setIsPlaying(true);

        // Clean up timeout if audio loads
        audio.addEventListener('canplay', () => clearTimeout(timeoutId), { once: true });
      }
    } catch (err) {
      console.error('[Playback Error]', err);
      console.warn('Using demo mode instead');
      setDemoMode(true);
      setIsPlaying(true);
    }
  };

  // Lazy load raga audio file
  const loadRagaDynamically = async (trackIndex) => {
    if (!tracks[trackIndex]) return;

    const track = tracks[trackIndex];
    const ragaKey = `${track.band}-${track.raga}`;

    // Skip if already loaded
    if (loadedRagas.has(ragaKey)) {
      if (audioRef.current) return audioRef.current;
    }

    try {
      console.log(`[Loading] ${track.raga} (${track.band}) - Track ${trackIndex}`);

      // Construct raga file path
      const ragaPath = `/audio/ragas/${track.band}/${track.raga}.mp3`;

      // Try to load audio
      const audio = new Audio();
      
      // Add event listeners BEFORE setting source
      audio.onloadstart = () => {
        console.log(`[Audio] Loading started: ${track.raga}`);
      };

      audio.oncanplay = () => {
        console.log(`[Audio] Ready to play: ${track.raga}`);
      };

      audio.onended = () => {
        console.log(`[Audio] Track ended: ${track.raga}`);
        handleTrackEnd();
      };

      audio.onerror = (e) => {
        console.error(`[Audio Error] Failed to load ${track.raga}:`, audio.error);
        console.log(`Attempted path: ${ragaPath}`);
        // Auto-advance on error after short delay
        setTimeout(() => {
          handleTrackEnd();
        }, 1000);
      };

      audio.onplay = () => {
        console.log(`[Audio] Playing: ${track.raga}`);
      };

      audio.onpause = () => {
        console.log(`[Audio] Paused: ${track.raga}`);
      };

      // Set source
      audio.src = ragaPath;
      audio.crossOrigin = "anonymous";

      // Store reference
      audioRef.current = audio;

      // Mark as loaded
      setLoadedRagas((prev) => new Set([...prev, ragaKey]));

      console.log(`[Lazy Load] ✓ ${track.raga} (${track.band}) ready`);

      return audio;
    } catch (err) {
      console.error(`[Load Error] ${track.raga}:`, err);
      setError(`Failed to load ${track.raga}: ${err.message}`);
      return null;
    }
  };

  // Handle track end - auto-advance to next track
  const handleTrackEnd = async () => {
    console.log(`[Track End] ${currentTrack?.raga} completed`);

    if (currentTrackIndex < tracks.length - 1) {
      // Move to next track
      const nextIndex = currentTrackIndex + 1;
      setCurrentTrackIndex(nextIndex);
      setElapsedTime(0);

      // Record progress
      await recordPlaybackProgress(nextIndex);

      console.log(`[Auto Advance] Moving to track ${nextIndex}`);

      // Lazy load next track
      if (!demoMode) {
        await loadRagaDynamically(nextIndex);
      }

      // Auto-play next track after transition gap
      if (isPlaying) {
        setTimeout(() => {
          if (demoMode) {
            console.log(`[Playback] Starting next track in demo mode`);
          } else if (audioRef.current) {
            console.log(`[Playback] Playing next track`);
            audioRef.current.play().catch(err => {
              console.warn(`Failed to play next track, staying in demo mode`, err);
              setDemoMode(true);
            });
          }
        }, 500); // 500ms transition gap
      }
    } else {
      // Session complete
      console.log(`[Session Complete] All tracks finished`);
      completeSession();
    }
  };

  // Skip to next track
  const handleNextTrack = async () => {
    if (currentTrackIndex < tracks.length - 1) {
      setCurrentTrackIndex(currentTrackIndex + 1);
      setElapsedTime(0);

      await recordPlaybackProgress(currentTrackIndex + 1);
      await loadRagaDynamically(currentTrackIndex + 1);
    }
  };

  // Skip to previous track
  const handlePrevTrack = () => {
    if (currentTrackIndex > 0) {
      setCurrentTrackIndex(currentTrackIndex - 1);
      setElapsedTime(0);
    }
  };

  // Track elapsed time
  useEffect(() => {
    if (!isPlaying) return;

    const interval = setInterval(() => {
      setElapsedTime((prev) => {
        const duration = currentTrack?.duration_seconds || 0;
        
        // In demo mode, just simulate the passage of time
        if (demoMode) {
          if (prev >= duration) {
            clearInterval(interval);
            handleTrackEnd();
            return duration;
          }
          return prev + 1;
        }

        // For real audio, check actual playback time
        if (audioRef.current) {
          const currentTime = audioRef.current.currentTime || prev;
          if (currentTime >= duration) {
            clearInterval(interval);
            return duration;
          }
          return currentTime;
        }

        return prev;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isPlaying, currentTrack, currentTrackIndex, demoMode]);

  // Complete session
  const completeSession = async () => {
    try {
      await fetch(`/api/therapy/session/complete/${sessionId}`, {
        method: 'POST',
      });

      setIsPlaying(false);
      onSessionComplete({
        status: 'completed',
        total_duration_seconds: totalTime,
      });
    } catch (err) {
      setError('Failed to complete session: ' + err.message);
    }
  };

  // Record playback progress
  const recordPlaybackProgress = async (trackIndex) => {
    if (!tracks[trackIndex]) return;

    try {
      await fetch('/api/therapy/playback/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          track_index: trackIndex,
          raga_name: tracks[trackIndex].raga,
          frequency_range: tracks[trackIndex].frequency_range,
          duration_seconds: tracks[trackIndex].duration_seconds,
          elapsed_seconds: 0,
          is_playing: true,
        }),
      });
    } catch (err) {
      console.error('Failed to record progress:', err);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const progressPercent = (currentTrackIndex + elapsedTime / (currentTrack?.duration_seconds || 1)) / tracks.length * 100;

  return (
    <div className={styles.screenContainer}>
      <GlassCard title="Raaga Therapy Session">
        {/* Session Info */}
        <div className={styles.sessionInfo}>
          <h2 className={styles.screenTitle}>
            Transition: {detection?.detected_state} → {targetState?.target_state}
          </h2>

          <div className={styles.sessionMeta}>
            <span>Duration: {formatTime(totalTime)} total</span>
            <span>Step {currentTrackIndex + 1} of {tracks.length}</span>
          </div>
        </div>

        {/* Current Raga Display */}
        {currentTrack && (
          <div className={styles.currentRagaContainer}>
            <div className={styles.ragaCard}>
              <div className={styles.ragaFrequencyBand}>{currentTrack.band}</div>

              <h3 className={styles.ragaName}>{currentTrack.raga}</h3>

              <div className={styles.frequencyRange}>
                <span>{currentTrack.frequency_range[0]}</span>
                <span>-</span>
                <span>{currentTrack.frequency_range[1]} Hz</span>
              </div>

              <p className={styles.ragaDescription}>
                Frequency band for {targetState?.target_state} therapy
              </p>

              {/* Frequency Visualization */}
              <div className={styles.frequencyVisualization}>
                <div className={styles.frequencyBars}>
                  {[...Array(12)].map((_, i) => (
                    <div
                      key={i}
                      className={styles.frequencyBar}
                      style={{
                        height: `${20 + Math.random() * 60}%`,
                        animation: `pulse ${0.5 + i * 0.05}s infinite`,
                      }}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Playback Controls */}
        <div className={styles.playbackControls}>
          <div className={styles.timeDisplay}>
            <span className={styles.currentTime}>{formatTime(elapsedTime)}</span>
            <span className={styles.totalTime}>{formatTime(currentTrack?.duration_seconds || 0)}</span>
          </div>

          {demoMode && (
            <div style={{
              padding: '8px 12px',
              backgroundColor: '#f59e0b',
              borderRadius: '4px',
              fontSize: '12px',
              marginBottom: '8px',
              textAlign: 'center',
            }}>
              🎵 Demo Mode - Audio files not found. Session timing simulated.
            </div>
          )}

          <div className={styles.progressBar}>
            <div
              className={styles.progressFill}
              style={{
                width: `${(elapsedTime / (currentTrack?.duration_seconds || 1)) * 100}%`,
              }}
            />
          </div>

          <div className={styles.controls}>
            <CTAButton
              onClick={handlePrevTrack}
              kind="secondary"
              disabled={currentTrackIndex === 0}
            >
              ← Prev
            </CTAButton>

            <CTAButton
              onClick={handlePlayPause}
              size="large"
              className={styles.playButton}
            >
              {isPlaying ? '⏸ Pause' : '▶ Play'}
            </CTAButton>

            <CTAButton
              onClick={handleNextTrack}
              kind="secondary"
              disabled={currentTrackIndex === tracks.length - 1}
            >
              Next →
            </CTAButton>
          </div>
        </div>

        {/* Playlist Overview */}
        <div className={styles.playlistOverview}>
          <h4>Session Playlist ({tracks.length} ragas)</h4>
          <div className={styles.trackList}>
            {tracks.map((track, idx) => (
              <div
                key={idx}
                className={`${styles.trackItem} ${idx === currentTrackIndex ? styles.active : ''}`}
              >
                <span className={styles.trackNumber}>{idx + 1}</span>
                <span className={styles.trackBand}>{track.band}</span>
                <span className={styles.trackRaga}>{track.raga}</span>
                <span className={styles.trackDuration}>
                  {formatTime(track.duration_seconds)}
                </span>
                {loadedRagas.has(`${track.band}-${track.raga}`) && (
                  <span className={styles.loadedIndicator}>✓</span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Overall Progress */}
        <div className={styles.overallProgress}>
          <label>Session Progress</label>
          <div className={styles.overallProgressBar}>
            <div
              className={styles.overallProgressFill}
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          <span>{Math.round(progressPercent)}% complete</span>
        </div>

        {error && (
          <div className={styles.errorMessage}>
            <p>Error: {error}</p>
          </div>
        )}

        {/* Footer */}
        <div className={styles.playerFooter}>
          <p className={styles.instruction}>
            🎵 Session will auto-advance through ragas. Sit back and relax for therapeutic benefits.
          </p>
          
          {demoMode && (
            <div style={{
              marginTop: '12px',
              padding: '10px',
              backgroundColor: 'rgba(245, 158, 11, 0.1)',
              borderLeft: '3px solid #f59e0b',
              borderRadius: '4px',
              fontSize: '12px',
            }}>
              <strong>ℹ️ Demo Mode Active</strong><br/>
              Audio files not found. To use real ragas:<br/>
              1. Create folder: <code>frontend/public/audio/ragas/{`{BAND}/{RAGA}.mp3`}</code><br/>
              2. Add MP3 files (e.g., <code>A1/Bhairav.mp3</code>)<br/>
              3. Reload this page<br/>
              See IMPLEMENTATION_SUMMARY.md for details.
            </div>
          )}
        </div>
      </GlassCard>

      <style jsx>{`
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.6;
          }
        }
      `}</style>
    </div>
  );
}
