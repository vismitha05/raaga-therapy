/**
 * useTherapyWorkflow.js
 * -------------------
 * Complete therapy session state management and workflow orchestration.
 * Manages: EEG scan → State selection → Duration → Playback → Completion.
 */

import { useState, useCallback, useRef } from 'react';

export const WORKFLOW_SCREENS = {
  INITIAL: 'initial',
  EEG_MONITORING: 'eeg_monitoring',
  STATE_SELECTION: 'state_selection',
  DURATION_SELECTION: 'duration_selection',
  THERAPY_PLAYBACK: 'therapy_playback',
  COMPLETION: 'completion',
};

export function useTherapyWorkflow() {
  // Navigation
  const [currentScreen, setCurrentScreen] = useState(WORKFLOW_SCREENS.INITIAL);

  // Session data
  const [sessionId, setSessionId] = useState(null);

  // Step 1: EEG Detection
  const [eegDetection, setEegDetection] = useState(null);

  // Step 2: State Selection
  const [targetState, setTargetState] = useState(null);
  const [effectivenessEstimates, setEffectivenessEstimates] = useState(null);

  // Step 3: Duration Selection
  const [selectedDuration, setSelectedDuration] = useState(20); // default

  // Step 4: Playlist
  const [playlist, setPlaylist] = useState(null);

  // Step 5: Session completion
  const [sessionComplete, setSessionComplete] = useState(null);

  // ─────────────────────────────────────────────────────────────────────────

  /**
   * Start the workflow: EEG monitoring → State Selection
   */
  const startWorkflow = useCallback(() => {
    setCurrentScreen(WORKFLOW_SCREENS.EEG_MONITORING);
  }, []);

  /**
   * After EEG scan completes, store detection and move to state selection
   */
  const handleEEGScanComplete = useCallback((detection) => {
    setEegDetection(detection);
    setCurrentScreen(WORKFLOW_SCREENS.STATE_SELECTION);
  }, []);

  /**
   * After state selection, store target state and move to duration selection
   */
  const handleStateSelected = useCallback((stateData) => {
    setTargetState(stateData.target_state);
    setEffectivenessEstimates(stateData.effectiveness_estimates);
    setCurrentScreen(WORKFLOW_SCREENS.DURATION_SELECTION);
  }, []);

  /**
   * After duration selection, store selection and move to playback
   */
  const handleDurationSelected = useCallback((durationData) => {
    setSelectedDuration(durationData.duration_minutes);
    setPlaylist(durationData.playlist);
    setCurrentScreen(WORKFLOW_SCREENS.THERAPY_PLAYBACK);
  }, []);

  /**
   * After playback completes, show completion screen
   */
  const handleSessionComplete = useCallback((completionData) => {
    setSessionComplete(completionData);
    setCurrentScreen(WORKFLOW_SCREENS.COMPLETION);
  }, []);

  /**
   * Start a new session (reset and go back to initial)
   */
  const startNewSession = useCallback(() => {
    setSessionId(null);
    setEegDetection(null);
    setTargetState(null);
    setEffectivenessEstimates(null);
    setSelectedDuration(20);
    setPlaylist(null);
    setSessionComplete(null);
    setCurrentScreen(WORKFLOW_SCREENS.INITIAL);
  }, []);

  /**
   * Go back to previous screen
   */
  const goBack = useCallback(() => {
    switch (currentScreen) {
      case WORKFLOW_SCREENS.STATE_SELECTION:
        setCurrentScreen(WORKFLOW_SCREENS.EEG_MONITORING);
        break;
      case WORKFLOW_SCREENS.DURATION_SELECTION:
        setCurrentScreen(WORKFLOW_SCREENS.STATE_SELECTION);
        break;
      case WORKFLOW_SCREENS.THERAPY_PLAYBACK:
        setCurrentScreen(WORKFLOW_SCREENS.DURATION_SELECTION);
        break;
      default:
        break;
    }
  }, [currentScreen]);

  // ─────────────────────────────────────────────────────────────────────────

  return {
    // Current state
    currentScreen,
    sessionId,
    eegDetection,
    targetState,
    selectedDuration,
    playlist,
    sessionComplete,
    effectivenessEstimates,

    // Setters
    setSessionId,
    setEegDetection,
    setTargetState,
    setSelectedDuration,
    setPlaylist,

    // Navigation callbacks
    startWorkflow,
    handleEEGScanComplete,
    handleStateSelected,
    handleDurationSelected,
    handleSessionComplete,
    startNewSession,
    goBack,
  };
}

/**
 * Custom hook for raga audio lazy loading and playback
 */
export function useRagaPlayback(playlist) {
  const [currentTrackIndex, setCurrentTrackIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [loadedRagas, setLoadedRagas] = useState(new Set());
  const [error, setError] = useState(null);

  const audioRef = useRef(null);
  const playbackIntervalRef = useRef(null);

  const tracks = playlist?.tracks || [];
  const currentTrack = tracks[currentTrackIndex];

  /**
   * Lazy load raga audio dynamically
   */
  const loadRagaDynamically = useCallback(
    async (trackIndex) => {
      if (!tracks[trackIndex]) return;

      const track = tracks[trackIndex];
      const ragaKey = `${track.band}-${track.raga}`;

      // Skip if already loaded
      if (loadedRagas.has(ragaKey)) {
        return;
      }

      try {
        // Construct raga file path
        const ragaPath = `/audio/ragas/${track.band}/${track.raga}.mp3`;

        // Create audio element with proper event handlers
        const audio = new Audio(ragaPath);

        audio.onended = () => {
          // Auto-advance to next track
          if (trackIndex < tracks.length - 1) {
            setCurrentTrackIndex(trackIndex + 1);
            setElapsedTime(0);
            // Load and play next
            setTimeout(() => {
              loadRagaDynamically(trackIndex + 1);
              audio.play();
            }, 500); // 500ms gap between ragas
          } else {
            // Session complete
            setIsPlaying(false);
          }
        };

        audio.onerror = (e) => {
          console.error(`Failed to load: ${ragaPath}`, e);
          setError(`Failed to load ${track.raga}`);
          // Auto-skip to next on error
          if (trackIndex < tracks.length - 1) {
            setCurrentTrackIndex(trackIndex + 1);
            setElapsedTime(0);
          }
        };

        audioRef.current = audio;

        // Mark as loaded
        setLoadedRagas((prev) => new Set([...prev, ragaKey]));

        console.log(`[Lazy Load] ${track.raga} (${track.band})`);

        return audio;
      } catch (err) {
        setError(err.message);
        console.error('Lazy load failed:', err);
      }
    },
    [tracks, loadedRagas]
  );

  /**
   * Play/Pause toggle
   */
  const togglePlayPause = useCallback(async () => {
    if (isPlaying) {
      audioRef.current?.pause();
      setIsPlaying(false);
      clearInterval(playbackIntervalRef.current);
    } else {
      // Load current track if not already loaded
      await loadRagaDynamically(currentTrackIndex);

      if (audioRef.current) {
        audioRef.current.play();
        setIsPlaying(true);

        // Start time tracking
        playbackIntervalRef.current = setInterval(() => {
          setElapsedTime((prev) => {
            const trackDuration = currentTrack?.duration_seconds || 0;
            if (prev >= trackDuration) {
              clearInterval(playbackIntervalRef.current);
              return trackDuration;
            }
            return prev + 1;
          });
        }, 1000);
      }
    }
  }, [isPlaying, currentTrackIndex, currentTrack, loadRagaDynamically]);

  /**
   * Skip to next track
   */
  const skipToNext = useCallback(async () => {
    if (currentTrackIndex < tracks.length - 1) {
      audioRef.current?.pause();
      setCurrentTrackIndex(currentTrackIndex + 1);
      setElapsedTime(0);

      // Preload next track
      await loadRagaDynamically(currentTrackIndex + 1);

      // Optionally auto-play
      if (isPlaying) {
        setTimeout(() => {
          audioRef.current?.play();
        }, 300);
      }
    }
  }, [currentTrackIndex, tracks.length, isPlaying, loadRagaDynamically]);

  /**
   * Skip to previous track
   */
  const skipToPrev = useCallback(() => {
    if (currentTrackIndex > 0) {
      audioRef.current?.pause();
      setCurrentTrackIndex(currentTrackIndex - 1);
      setElapsedTime(0);

      if (isPlaying) {
        audioRef.current?.play();
      }
    }
  }, [currentTrackIndex, isPlaying]);

  /**
   * Cleanup on unmount
   */
  React.useEffect(() => {
    return () => {
      audioRef.current?.pause();
      clearInterval(playbackIntervalRef.current);
    };
  }, []);

  return {
    currentTrackIndex,
    currentTrack,
    isPlaying,
    elapsedTime,
    loadedRagas,
    error,
    togglePlayPause,
    skipToNext,
    skipToPrev,
    setCurrentTrackIndex,
    setElapsedTime,
  };
}

/**
 * Utility hook for API calls with error handling
 */
export function useTherapyAPI() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const request = useCallback(
    async (endpoint, method = 'GET', body = null) => {
      setIsLoading(true);
      setError(null);

      try {
        const options = {
          method,
          headers: { 'Content-Type': 'application/json' },
        };

        if (body) {
          options.body = JSON.stringify(body);
        }

        const response = await fetch(endpoint, options);

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();
        return data;
      } catch (err) {
        setError(err.message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  return { isLoading, error, request };
}
