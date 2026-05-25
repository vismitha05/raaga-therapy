/**
 * TargetStateScreen.jsx
 * -------------------
 * Second screen: User selects target brain state (sleep, relaxed, focused).
 * Shows effectiveness estimates for each option.
 * Advances to duration selection screen.
 */

import React, { useState } from 'react';
import { GlassCard, CTAButton } from '../components/ui/Primitives';
import styles from '../styles/screens.module.css';

const STATE_OPTIONS = [
  {
    id: 'sleep',
    label: 'Deep Sleep',
    description: 'Theta waves (4-6 Hz) for deep relaxation and sleep prep',
    emoji: '😴',
    color: '#8b7fff',
    effects: ['Reduces cortisol', 'Promotes deep sleep', 'Full body relax'],
  },
  {
    id: 'relaxed',
    label: 'Relaxed State',
    description: 'Alpha waves (8-10 Hz) for meditation and calm focus',
    emoji: '🧘',
    color: '#5eead4',
    effects: ['Stress relief', 'Mental clarity', 'Balanced mind'],
  },
  {
    id: 'focused',
    label: 'Intense Focus',
    description: 'Beta waves (12-21 Hz) for productivity and concentration',
    emoji: '🎯',
    color: '#fbbf24',
    effects: ['Enhanced focus', 'Cognitive boost', 'Problem-solving'],
  },
];

export function TargetStateScreen({ 
  sessionId, 
  detection, 
  onStateSelected, 
  onBack 
}) {
  const [selectedState, setSelectedState] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleStateSelection = async (state) => {
    setSelectedState(state);
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/therapy/state-selection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          target_state: state,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to select state');
      }

      const data = await response.json();

      // Pass estimates to next screen
      onStateSelected({
        target_state: state,
        effectiveness_estimates: data.effectiveness_estimates,
      });
    } catch (err) {
      setError(err.message);
      setIsLoading(false);
      setSelectedState(null);
    }
  };

  // Get transition info
  const getTransitionInfo = (targetState) => {
    const transitions = {
      sleep: {
        sleep: 'Already in sleep state',
        relaxed: 'Gentle descent to deep relaxation',
        focused: 'Gradual wake-up and mental activation',
      },
      relaxed: {
        sleep: 'Deepen into sleep',
        relaxed: 'Stay in calm state',
        focused: 'Activate cognitive processing',
      },
      focused: {
        sleep: 'Full shift to sleep mode',
        relaxed: 'Come down to calm state',
        focused: 'Maintain high focus',
      },
    };

    return transitions[detection?.detected_state] || {};
  };

  const transitionInfo = getTransitionInfo(detection?.detected_state);

  return (
    <div className={styles.screenContainer}>
      <GlassCard title="Choose Target State">
        <h2 className={styles.screenTitle}>Where do you want to go?</h2>

        <p className={styles.subtitle}>
          Your current state: <strong>{detection?.detected_state || 'Unknown'}</strong> ({detection?.detected_band})
        </p>

        <div className={styles.stateGrid}>
          {STATE_OPTIONS.map((option) => (
            <button
              key={option.id}
              className={`${styles.stateCard} ${selectedState === option.id ? styles.active : ''}`}
              onClick={() => handleStateSelection(option.id)}
              disabled={isLoading}
              style={{
                borderColor: selectedState === option.id ? option.color : undefined,
                backgroundColor: selectedState === option.id ? `${option.color}10` : undefined,
              }}
            >
              <div className={styles.stateEmoji}>{option.emoji}</div>

              <h3 className={styles.stateLabel}>{option.label}</h3>

              <p className={styles.stateDescription}>{option.description}</p>

              <div className={styles.stateEffects}>
                {option.effects.map((effect, idx) => (
                  <span key={idx} className={styles.effectTag}>
                    {effect}
                  </span>
                ))}
              </div>

              {transitionInfo[option.id] && (
                <p className={styles.transitionNote}>
                  {transitionInfo[option.id]}
                </p>
              )}

              {selectedState === option.id && (
                <div className={styles.selectedIndicator}>
                  <span>✓ Selected</span>
                </div>
              )}
            </button>
          ))}
        </div>

        {error && (
          <div className={styles.errorMessage}>
            <p>Error: {error}</p>
          </div>
        )}

        {isLoading && selectedState && (
          <div className={styles.loadingMessage}>
            <div className={styles.spinner} />
            <p>Preparing therapy plan...</p>
          </div>
        )}

        <div className={styles.actionsRow}>
          <CTAButton kind="ghost" onClick={onBack} disabled={isLoading}>
            Back
          </CTAButton>
          {selectedState && !isLoading && (
            <CTAButton onClick={() => handleStateSelection(selectedState)}>
              Confirm
            </CTAButton>
          )}
        </div>

        <div className={styles.infoBox}>
          <h4>How it Works</h4>
          <ul>
            <li><strong>Sleep:</strong> Lowered brain frequencies (4-6 Hz) to induce sleep</li>
            <li><strong>Relaxed:</strong> Balanced alpha waves (8-10 Hz) for meditation</li>
            <li><strong>Focused:</strong> Elevated beta waves (12-21 Hz) for productivity</li>
          </ul>
        </div>
      </GlassCard>
    </div>
  );
}
