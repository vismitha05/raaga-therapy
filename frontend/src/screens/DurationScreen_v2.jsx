/**
 * DurationScreen.jsx (Updated)
 * ---------------------------
 * Third screen: User selects session duration (10, 20, 30 minutes).
 * Shows effectiveness estimates from backend.
 * Generates playlist and advances to player screen.
 */

import React, { useState, useEffect } from 'react';
import { GlassCard, CTAButton } from '../components/ui/Primitives';
import styles from '../styles/screens.module.css';

const DURATION_OPTIONS = [
  {
    minutes: 10,
    label: '10 Minutes',
    description: 'Quick therapeutic session',
    icon: '⏱️',
    notes: 'Light adjustment, good for breaks',
  },
  {
    minutes: 20,
    label: '20 Minutes',
    description: 'Standard therapy session',
    icon: '⏲️',
    notes: 'Moderate regulation, recommended',
    recommended: true,
  },
  {
    minutes: 30,
    label: '30 Minutes',
    description: 'Deep therapeutic session',
    icon: '🕐',
    notes: 'Deep neural relaxation, most effective',
  },
];

export function DurationScreen({
  sessionId,
  targetState,
  detection,
  onDurationSelected,
  onBack,
}) {
  const [selectedDuration, setSelectedDuration] = useState(20); // Default to 20
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [estimates, setEstimates] = useState(null);

  // Get effectiveness estimates from previous step
  useEffect(() => {
    if (targetState?.effectiveness_estimates) {
      setEstimates(targetState.effectiveness_estimates);
    }
  }, [targetState]);

  const handleDurationSelection = async (duration) => {
    setSelectedDuration(duration);
    setIsLoading(true);
    setError(null);

    try {
      // Request playlist generation
      const response = await fetch('/api/therapy/duration-selection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          duration_minutes: duration,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate playlist');
      }

      const playlist = await response.json();

      // Pass to player screen
      onDurationSelected({
        duration_minutes: duration,
        playlist: playlist,
      });
    } catch (err) {
      setError(err.message);
      setIsLoading(false);
    }
  };

  const getEffectivenessColor = (score) => {
    if (score >= 85) return '#10b981'; // Green
    if (score >= 70) return '#f59e0b'; // Amber
    return '#ef4444'; // Red
  };

  return (
    <div className={styles.screenContainer}>
      <GlassCard title="Session Duration">
        <h2 className={styles.screenTitle}>How long should we go?</h2>

        <p className={styles.subtitle}>
          Target: <strong>{targetState?.target_state || 'Unknown'}</strong> |
          Duration: {selectedDuration} minutes
        </p>

        <div className={styles.durationGrid}>
          {DURATION_OPTIONS.map((option) => {
            const effectivenessScore = estimates?.[option.minutes] || 75;
            const isSelected = selectedDuration === option.minutes;

            return (
              <button
                key={option.minutes}
                className={`${styles.durationCard} ${isSelected ? styles.active : ''} ${
                  option.recommended ? styles.recommended : ''
                }`}
                onClick={() => handleDurationSelection(option.minutes)}
                disabled={isLoading}
              >
                <div className={styles.durationIcon}>{option.icon}</div>

                <h3 className={styles.durationLabel}>{option.label}</h3>

                <p className={styles.durationDescription}>{option.description}</p>

                {/* Effectiveness Score */}
                <div className={styles.effectivenessContainer}>
                  <label className={styles.scoreLabel}>Effectiveness</label>
                  <div className={styles.scoreBar}>
                    <div
                      className={styles.scoreFill}
                      style={{
                        width: `${effectivenessScore}%`,
                        backgroundColor: getEffectivenessColor(effectivenessScore),
                      }}
                    />
                  </div>
                  <span className={styles.scoreValue}>{effectivenessScore}%</span>
                </div>

                <p className={styles.durationNotes}>{option.notes}</p>

                {option.recommended && (
                  <div className={styles.recommendedBadge}>
                    Recommended
                  </div>
                )}

                {isSelected && (
                  <div className={styles.selectedIndicator}>
                    <span>✓ Selected</span>
                  </div>
                )}
              </button>
            );
          })}
        </div>

        {/* Transition Timeline */}
        {DURATION_OPTIONS.map((option) => selectedDuration === option.minutes && (
          <div key={option.minutes} className={styles.transitionTimeline}>
            <h4>Your Therapeutic Timeline</h4>
            <p className={styles.timelineDescription}>
              The session will smoothly transition your brain from <strong>{detection?.detected_state}</strong> to <strong>{targetState?.target_state}</strong> over {option.minutes} minutes.
            </p>
            <div className={styles.timelineBar}>
              <div className={styles.timelineStart}>
                <span>{detection?.detected_band}</span>
                <small>Current</small>
              </div>
              <div className={styles.timelineArrow}>→</div>
              <div className={styles.timelineEnd}>
                <span>Target</span>
                <small>{targetState?.target_state}</small>
              </div>
            </div>
          </div>
        ))}

        {error && (
          <div className={styles.errorMessage}>
            <p>Error: {error}</p>
          </div>
        )}

        {isLoading && (
          <div className={styles.loadingMessage}>
            <div className={styles.spinner} />
            <p>Generating personalized raga playlist...</p>
          </div>
        )}

        <div className={styles.actionsRow}>
          <CTAButton kind="ghost" onClick={onBack} disabled={isLoading}>
            Back
          </CTAButton>
          {!isLoading && (
            <CTAButton onClick={() => handleDurationSelection(selectedDuration)}>
              Generate Playlist
            </CTAButton>
          )}
        </div>

        <div className={styles.infoBox}>
          <h4>About Session Duration</h4>
          <ul>
            <li><strong>10 Min:</strong> Quick therapy for busy schedules</li>
            <li><strong>20 Min:</strong> Sweet spot for balanced effectiveness</li>
            <li><strong>30 Min:</strong> Maximum therapeutic benefits</li>
          </ul>
        </div>
      </GlassCard>
    </div>
  );
}
