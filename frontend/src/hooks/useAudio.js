import { useState, useRef, useCallback, useEffect } from "react";

/**
 * useAudio Hook
 * Provides basic audio playback controls for therapy sessions
 */
export function useAudio() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [volume, setVolume] = useState(0.7);
  const [currentTime, setCurrentTime] = useState(0);
  const [trackDuration, setTrackDuration] = useState(0);
  const audioRef = useRef(new Audio());
  const animationFrameRef = useRef(null);

  // Update current time during playback
  useEffect(() => {
    const audio = audioRef.current;
    if (!isPlaying) return;

    const updateTime = () => {
      setCurrentTime(audio.currentTime || 0);
      setTrackDuration(audio.duration || 0);
      animationFrameRef.current = requestAnimationFrame(updateTime);
    };

    animationFrameRef.current = requestAnimationFrame(updateTime);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isPlaying]);

  const togglePlayPause = useCallback(() => {
    const audio = audioRef.current;
    if (isPlaying) {
      audio.pause();
      setIsPlaying(false);
    } else {
      audio.play().catch((e) => console.error("Playback failed:", e));
      setIsPlaying(true);
    }
  }, [isPlaying]);

  const setQueueForState = useCallback((state) => {
    // Returns a queue of ragas for the target state
    const queues = {
      Focused: [
        { id: 1, name: "Yaman", duration: 180 },
        { id: 2, name: "Bhairav", duration: 180 },
      ],
      Relaxed: [
        { id: 3, name: "Yaman Kalyan", duration: 240 },
        { id: 4, name: "Jor", duration: 240 },
      ],
      Sleep: [
        { id: 5, name: "Bhupali", duration: 300 },
        { id: 6, name: "Ahir Bhairav", duration: 300 },
      ],
    };
    return queues[state] || queues.Relaxed;
  }, []);

  const playTrack = useCallback((track) => {
    const audio = audioRef.current;
    if (track && track.path) {
      audio.src = track.path;
      audio.load();
      audio.play().catch((e) => console.error("Playback failed:", e));
      setIsPlaying(true);
    }
  }, []);

  return {
    isPlaying,
    volume,
    setVolume: (v) => {
      setVolume(v);
      if (audioRef.current) {
        audioRef.current.volume = v;
      }
    },
    togglePlayPause,
    currentTime,
    trackDuration,
    setQueueForState,
    playTrack,
  };
}
