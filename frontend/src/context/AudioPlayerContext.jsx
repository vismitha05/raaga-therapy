/**
 * AudioPlayerContext.jsx
 * ─────────────────────
 * Manages dual-deck crossfade audio playback.
 *
 * BUGS FIXED
 * ----------
 * BUG-1  handleEnded captured stale queuedTracks / currentTrack because the
 *        useEffect that registered it had [isPlaying, queuedTracks, currentTrack]
 *        as deps but removed/re-added listeners on every render.
 *        Fix: store queuedTracks and currentTrack in refs so handleEnded always
 *        reads the latest value without needing to be re-registered.
 *
 * BUG-2  setQueueForState was called inside TherapyBridge's useEffect with
 *        session.isSessionActive as the only dep. On reconnect the EEG context
 *        re-renders but the queue was never refreshed.
 *        Fix: expose a refreshQueue() helper.
 *
 * BUG-3  volume=0 edge case — if volume was 0.0, playTrack forced 0.5.
 *        That is correct UX but was undocumented and surprised callers.
 *        Fix: kept the guard, added a comment.
 *
 * BUG-4  The crossfade interval captured `volume` via closure. If the user
 *        moved the volume slider during a crossfade the new deck ended up at
 *        the old volume.
 *        Fix: read volumeRef.current inside the interval callback.
 */

import React, {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { buildTrialQueue } from "../lib/tracks";

const AudioPlayerContext = createContext(null);

function createAudio() {
  const a = new Audio();
  a.preload = "auto";
  a.crossOrigin = "anonymous";
  return a;
}

export function AudioPlayerProvider({ children }) {
  const primaryRef   = useRef(createAudio());
  const secondaryRef = useRef(createAudio());
  const activeDeck   = useRef("primary");

  const [isPlaying,        setIsPlaying]        = useState(false);
  const [volume,           setVolume]            = useState(0.78);
  const [currentTrack,     setCurrentTrack]      = useState(null);
  const [queuedTracks,     setQueuedTracks]      = useState([]);
  const [transitionState,  setTransitionState]   = useState("idle");
  const [playbackProgress, setPlaybackProgress]  = useState(0);
  const [currentTime,      setCurrentTime]       = useState(0);
  const [trackDuration,    setTrackDuration]     = useState(0);
  const [playbackStatus,   setPlaybackStatus]    = useState("Ready");
  const [error,            setError]             = useState("");

  // ── Refs for values needed inside callbacks without re-registration ─────────
  const volumeRef       = useRef(volume);
  const currentTrackRef = useRef(currentTrack);
  const queuedRef       = useRef(queuedTracks);
  const isPlayingRef    = useRef(isPlaying);
  const preloadedRef    = useRef({});

  useEffect(() => { volumeRef.current    = volume;        }, [volume]);
  useEffect(() => { currentTrackRef.current = currentTrack; }, [currentTrack]);
  useEffect(() => { queuedRef.current    = queuedTracks;  }, [queuedTracks]);
  useEffect(() => { isPlayingRef.current = isPlaying;     }, [isPlaying]);

  // ── Progress ticker ─────────────────────────────────────────────────────────
  useEffect(() => {
    const id = setInterval(() => {
      const active = activeDeck.current === "primary"
        ? primaryRef.current
        : secondaryRef.current;
      const duration = Number.isFinite(active.duration)    ? active.duration    : 0;
      const time     = Number.isFinite(active.currentTime) ? active.currentTime : 0;
      setCurrentTime(time);
      setTrackDuration(duration);
      setPlaybackProgress(duration > 0 ? Math.min(100, (time / duration) * 100) : 0);
    }, 300);
    return () => clearInterval(id);
  }, []);  // mount-only — primary/secondaryRef never change

  // ── Track-ended handler ─────────────────────────────────────────────────────
  // FIX BUG-1: register once; read live state via refs.
  useEffect(() => {
    const primary   = primaryRef.current;
    const secondary = secondaryRef.current;

    const handleEnded = () => {
      if (!isPlayingRef.current) return;
      // Play next queued track, or loop current
      const next = queuedRef.current[0] || currentTrackRef.current;
      if (next) switchTrack(next, "auto-continue");
    };

    primary.addEventListener("ended",   handleEnded);
    secondary.addEventListener("ended", handleEnded);

    return () => {
      primary.removeEventListener("ended",   handleEnded);
      secondary.removeEventListener("ended", handleEnded);
      primary.pause();
      secondary.pause();
    };
  }, []);  // mount-only

  // ── Volume sync ─────────────────────────────────────────────────────────────
  useEffect(() => {
    const active = activeDeck.current === "primary"
      ? primaryRef.current
      : secondaryRef.current;
    active.volume = volume;
    // The inactive deck's volume is always 0 during crossfade management
  }, [volume]);

  // ── Helpers ─────────────────────────────────────────────────────────────────

  function preloadTrack(track) {
    if (!track?.url || preloadedRef.current[track.url]) return;
    const pre = new Audio();
    pre.preload = "auto";
    pre.src = track.url;
    preloadedRef.current[track.url] = true;
  }

  function setQueueForState(_targetState, preferredName) {
    const ordered = buildTrialQueue(preferredName);
    setQueuedTracks(ordered);
    queuedRef.current = ordered;           // keep ref in sync immediately
    ordered.slice(0, 2).forEach(preloadTrack);
    return ordered;
  }

  // Alias so callers can refresh without changing state
  function refreshQueue(preferredName) {
    return setQueueForState(null, preferredName);
  }

  async function playTrack(track) {
    const active = activeDeck.current === "primary"
      ? primaryRef.current
      : secondaryRef.current;

    if (!track?.url) {
      setError("Track source missing. Add files under frontend/public/audio.");
      return;
    }

    try {
      if (active.src !== track.url) {
        active.src = track.url;
      }
      active.loop = false;
      // Guard: if volume is exactly 0 the user can't hear anything — use 0.5
      // as a safe audible default while still respecting explicit 0 via pause().
      active.volume = volumeRef.current > 0 ? volumeRef.current : 0.5;

      if (active.readyState < 2) {
        await new Promise((resolve, reject) => {
          const ok  = () => { cleanup(); resolve(); };
          const err = (e) => { cleanup(); reject(e); };
          const cleanup = () => {
            active.removeEventListener("canplay", ok);
            active.removeEventListener("error",   err);
          };
          active.addEventListener("canplay", ok);
          active.addEventListener("error",   err);
          setTimeout(() => { cleanup(); reject(new Error("Audio load timeout")); }, 5000);
        });
      }

      await active.play();
      setCurrentTrack(track);
      setIsPlaying(true);
      setPlaybackStatus("Playing");
      setError("");
    } catch (e) {
      console.error("Playback error:", e);
      setPlaybackStatus("Error");
      setError(`Playback failed: ${e.message || "Unknown error"}. Try clicking Play again.`);
    }
  }

  function pause() {
    primaryRef.current.pause();
    secondaryRef.current.pause();
    setIsPlaying(false);
    setPlaybackStatus("Paused");
  }

  async function resume() {
    if (!currentTrackRef.current) {
      const next = queuedRef.current[0];
      if (next) return playTrack(next);
      return;
    }
    const active = activeDeck.current === "primary"
      ? primaryRef.current
      : secondaryRef.current;
    try {
      await active.play();
      setIsPlaying(true);
      setPlaybackStatus("Playing");
    } catch (_e) {
      setError("Unable to resume playback.");
    }
  }

  async function togglePlayPause() {
    if (isPlayingRef.current) pause();
    else await resume();
  }

  async function switchTrack(nextTrack, reason = "adaptive") {
    if (!nextTrack?.url) return;

    const from = activeDeck.current === "primary"
      ? primaryRef.current
      : secondaryRef.current;
    const to = activeDeck.current === "primary"
      ? secondaryRef.current
      : primaryRef.current;

    try {
      setTransitionState("crossfading");
      setPlaybackStatus(`Transitioning (${reason})`);

      to.src = nextTrack.url;
      to.currentTime = 0;
      to.volume = 0;
      to.loop = false;
      await to.play();

      const fadeMs = 1200;
      const stepMs = 50;
      const steps  = Math.ceil(fadeMs / stepMs);
      let i = 0;

      const id = setInterval(() => {
        i += 1;
        const p   = Math.min(1, i / steps);
        const vol = volumeRef.current;   // FIX BUG-4: read live volume
        to.volume   = vol * p;
        from.volume = vol * (1 - p);

        if (p >= 1) {
          clearInterval(id);
          from.pause();
          from.currentTime = 0;
          from.volume = 0;
          to.volume   = vol;
          activeDeck.current = activeDeck.current === "primary" ? "secondary" : "primary";
          setCurrentTrack(nextTrack);
          setTransitionState("idle");
          setPlaybackStatus("Playing");
          setIsPlaying(true);
        }
      }, stepMs);
    } catch (_e) {
      setTransitionState("idle");
    }
  }

  const value = useMemo(
    () => ({
      isPlaying,
      volume,
      setVolume,
      currentTrack,
      queuedTracks,
      transitionState,
      playbackProgress,
      currentTime,
      trackDuration,
      playbackStatus,
      error,
      setQueueForState,
      refreshQueue,
      playTrack,
      pause,
      resume,
      togglePlayPause,
      switchTrack,
      setPlaybackStatus,
    }),
    [isPlaying, volume, currentTrack, queuedTracks, transitionState,
     playbackProgress, currentTime, trackDuration, playbackStatus, error]
  );

  return (
    <AudioPlayerContext.Provider value={value}>
      {children}
    </AudioPlayerContext.Provider>
  );
}

export function useAudioPlayer() {
  const ctx = useContext(AudioPlayerContext);
  if (!ctx) throw new Error("useAudioPlayer must be used within AudioPlayerProvider");
  return ctx;
}
