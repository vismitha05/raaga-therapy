/**
 * SessionCompletionScreen.jsx
 * --------------------------
 * Final screen: Shows session completion summary and therapeutic benefits.
 * Allows user to start a new session or exit.
 */

import React, { useState } from 'react';
import { GlassCard, CTAButton } from '../components/ui/Primitives';
import styles from '../styles/screens.module.css';

export function SessionCompletionScreen({
  detection,
  targetState,
  duration,
  playlist,
  onNewSession,
}) {
  const [showDetails, setShowDetails] = useState(false);

  const getBenefits = (state) => {
    const benefits = {
      sleep: [
        '✓ Reduced cortisol and stress hormones',
        '✓ Prepared mind for deep sleep',
        '✓ Relaxed nervous system',
        '✓ Better sleep quality tonight',
      ],
      relaxed: [
        '✓ Reduced anxiety and tension',
        '✓ Enhanced mental clarity',
        '✓ Improved focus and concentration',
        '✓ Balanced emotional state',
      ],
      focused: [
        '✓ Heightened cognitive function',
        '✓ Improved problem-solving ability',
        '✓ Enhanced productivity',
        '✓ Better attention span',
      ],
    };
    return benefits[state] || [];
  };

  const getSessionRating = (state, duration) => {
    const baseScore = 75;
    const durationBonus = duration === 10 ? 0 : duration === 20 ? 10 : 20;
    return baseScore + durationBonus;
  };

  const sessionRating = getSessionRating(targetState?.target_state, duration);

  return (
    <div className={styles.screenContainer}>
      <GlassCard title="Session Complete">
        {/* Celebration Header */}
        <div className={styles.completionHeader}>
          <div className={styles.completionEmoji}>🎉</div>
          <h2 className={styles.completionTitle}>Therapy Complete!</h2>
          <p className={styles.completionSubtitle}>
            You successfully transitioned from {detection?.detected_state} to {targetState?.target_state}
          </p>
        </div>

        {/* Session Summary */}
        <div className={styles.sessionSummary}>
          <h3>Session Summary</h3>

          <div className={styles.summaryGrid}>
            <div className={styles.summaryItem}>
              <label>Duration</label>
              <span className={styles.summaryValue}>{duration} minutes</span>
            </div>

            <div className={styles.summaryItem}>
              <label>Ragas Played</label>
              <span className={styles.summaryValue}>{playlist?.total_steps || 0}</span>
            </div>

            <div className={styles.summaryItem}>
              <label>Frequency Transition</label>
              <span className={styles.summaryValue}>
                {playlist?.start_band} → {playlist?.target_band}
              </span>
            </div>

            <div className={styles.summaryItem}>
              <label>Effectiveness Score</label>
              <span className={styles.summaryValue} style={{ color: '#10b981' }}>
                {sessionRating}%
              </span>
            </div>
          </div>
        </div>

        {/* Therapeutic Benefits */}
        <div className={styles.benefitsSection}>
          <h3>You Should Feel...</h3>
          <ul className={styles.benefitsList}>
            {getBenefits(targetState?.target_state).map((benefit, idx) => (
              <li key={idx} className={styles.benefitItem}>
                {benefit}
              </li>
            ))}
          </ul>
        </div>

        {/* Detailed Playlist */}
        {showDetails && (
          <div className={styles.detailedPlaylist}>
            <h4>Detailed Raga Sequence</h4>
            <div className={styles.playlistDetails}>
              {playlist?.tracks?.map((track, idx) => (
                <div key={idx} className={styles.playlistItemDetail}>
                  <div className={styles.itemStep}>{idx + 1}</div>
                  <div className={styles.itemInfo}>
                    <span className={styles.itemRaga}>{track.raga}</span>
                    <span className={styles.itemBand}>{track.band}</span>
                    <span className={styles.itemFreq}>
                      {track.frequency_range[0]}-{track.frequency_range[1]} Hz
                    </span>
                  </div>
                  <div className={styles.itemDuration}>
                    {(track.duration_seconds / 60).toFixed(1)}m
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <CTAButton
          kind="secondary"
          onClick={() => setShowDetails(!showDetails)}
          className={styles.detailsToggle}
        >
          {showDetails ? 'Hide' : 'Show'} Raga Sequence
        </CTAButton>

        {/* Recommendations */}
        <div className={styles.recommendations}>
          <h4>Next Steps</h4>
          <ul className={styles.recommendationsList}>
            {targetState?.target_state === 'sleep' && (
              <>
                <li>Go to bed within 30 minutes for best results</li>
                <li>Keep the ambient temperature cool (65-68°F)</li>
                <li>Avoid screens for 20 minutes</li>
              </>
            )}
            {targetState?.target_state === 'relaxed' && (
              <>
                <li>Hydrate and take some deep breaths</li>
                <li>Try some light stretching or yoga</li>
                <li>Repeat this session 1-2 times daily for best results</li>
              </>
            )}
            {targetState?.target_state === 'focused' && (
              <>
                <li>Jump into your task immediately while in focused state</li>
                <li>Minimize distractions for the next 30-45 minutes</li>
                <li>Take regular breaks (pomodoro technique recommended)</li>
              </>
            )}
          </ul>
        </div>

        {/* Repeated Sessions Notice */}
        <div className={styles.infoBox}>
          <h4>💡 Pro Tip</h4>
          <p>
            Regular sessions (3-5 times per week) significantly increase the effectiveness
            of binaural beat therapy. Your brain learns to respond faster to therapeutic frequencies.
          </p>
        </div>

        {/* Action Buttons */}
        <div className={styles.actionsRow}>
          <CTAButton kind="secondary" onClick={() => window.location.reload()}>
            Exit
          </CTAButton>
          <CTAButton onClick={onNewSession}>
            Start New Session
          </CTAButton>
        </div>

        {/* Footer Stats */}
        <div className={styles.footerStats}>
          <p>
            Thanks for using Raga Therapy. Your session data helps us improve personalization.
          </p>
        </div>
      </GlassCard>
    </div>
  );
}
