/**
 * EEGMonitoringScreen.jsx
 * ----------------------
 * First screen: Shows 15-second EEG scan timer.
 * Polls API for scan progress, then retrieves results.
 * Automatically advances to state selection when complete.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { GlassCard, CTAButton } from '../components/ui/Primitives';
import styles from '../styles/screens.module.css';

export function EEGMonitoringScreen({ onScanComplete, sessionId, setSessionId }) {
  const [timeRemaining, setTimeRemaining] = useState(15);
  const [isScanning, setIsScanning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [detection, setDetection] = useState(null);
  const [error, setError] = useState(null);
  const [useSimulation, setUseSimulation] = useState(true);

  // Start EEG scan
  const startScan = useCallback(async () => {
    try {
      setError(null);
      setIsScanning(true);
      setProgress(0);
      setTimeRemaining(15);

      // Request EEG scan start
      const response = await fetch('/api/therapy/eeg-scan/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          duration_seconds: 15,
          simulate: useSimulation,
        }),
      });

      if (!response.ok) throw new Error('Failed to start scan');

      const data = await response.json();
      setSessionId(data.session_id);

      // Poll for progress
      pollScanProgress(data.session_id);
    } catch (err) {
      setError(err.message);
      setIsScanning(false);
    }
  }, [useSimulation, setSessionId]);

  // Poll scan progress
  const pollScanProgress = useCallback(async (sid) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/therapy/eeg-scan/progress/${sid}`);
        if (!response.ok) throw new Error('Progress polling failed');

        const data = await response.json();
        setProgress(data.progress_percent);
        setTimeRemaining(Math.ceil(data.time_remaining_seconds));

        // Check if scan is complete
        if (data.progress_percent >= 100) {
          clearInterval(pollInterval);
          setIsScanning(false);

          // Fetch final results
          const resultResponse = await fetch(`/api/therapy/eeg-scan/result/${sid}`);
          if (resultResponse.ok) {
            const resultData = await resultResponse.json();
            setDetection(resultData);

            // Auto-advance to next screen
            setTimeout(() => {
              onScanComplete(resultData);
            }, 1000);
          }
        }
      } catch (err) {
        console.error('Polling error:', err);
        clearInterval(pollInterval);
      }
    }, 500); // Poll every 500ms
  }, [onScanComplete]);

  useEffect(() => {
    // Don't auto-start; wait for user to click button
  }, []);

  const progressPercent = (progress / 100) * 360; // For circular progress

  return (
    <div className={styles.screenContainer}>
      <GlassCard title="Brain State Detection">
        <h2 className={styles.screenTitle}>EEG Scan (15 seconds)</h2>

        {!isScanning && !detection && (
          <div className={styles.setupPhase}>
            <p className={styles.instructions}>
              This scan analyzes your current brain state using EEG frequencies.
              Stay relaxed and still for 15 seconds.
            </p>

            <div className={styles.toggleOption}>
              <label>
                <input
                  type="checkbox"
                  checked={useSimulation}
                  onChange={(e) => setUseSimulation(e.target.checked)}
                />
                Use Simulated EEG (for demo)
              </label>
            </div>

            <CTAButton onClick={startScan} size="large" className={styles.primaryButton}>
              Start Scan
            </CTAButton>
          </div>
        )}

        {isScanning && (
          <div className={styles.scanningPhase}>
            {/* Circular Progress */}
            <div className={styles.circularProgress}>
              <svg viewBox="0 0 120 120" className={styles.progressSvg}>
                {/* Background circle */}
                <circle cx="60" cy="60" r="55" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="8" />
                
                {/* Progress circle */}
                <circle
                  cx="60"
                  cy="60"
                  r="55"
                  fill="none"
                  stroke="url(#gradient)"
                  strokeWidth="8"
                  strokeDasharray={`${progressPercent} 360`}
                  strokeLinecap="round"
                  className={styles.animatingCircle}
                />

                {/* Gradient definition */}
                <defs>
                  <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#8b7fff" />
                    <stop offset="100%" stopColor="#5e72e4" />
                  </linearGradient>
                </defs>
              </svg>

              {/* Center text */}
              <div className={styles.progressText}>
                <div className={styles.timeRemaining}>{timeRemaining}s</div>
                <div className={styles.progressLabel}>Scanning...</div>
              </div>
            </div>

            {/* Progress bar */}
            <div className={styles.progressBar}>
              <div className={styles.progressFill} style={{ width: `${progress}%` }} />
            </div>

            {/* Status message */}
            <p className={styles.statusMessage}>
              {progress < 50 && "Calibrating sensors..."}
              {progress >= 50 && progress < 100 && "Analyzing brain waves..."}
              {progress >= 100 && "Scan complete!"}
            </p>
          </div>
        )}

        {detection && (
          <div className={styles.detectionResults}>
            <h3 className={styles.resultTitle}>Scan Complete!</h3>

            <div className={styles.resultGrid}>
              <div className={styles.resultItem}>
                <label>Current State</label>
                <span className={styles.resultValue}>{detection.detected_state}</span>
              </div>

              <div className={styles.resultItem}>
                <label>Frequency Band</label>
                <span className={styles.resultValue}>{detection.detected_band}</span>
              </div>

              <div className={styles.resultItem}>
                <label>Confidence</label>
                <span className={styles.resultValue}>{(detection.confidence * 100).toFixed(0)}%</span>
              </div>
            </div>

            <div className={styles.bandAnalysis}>
              <h4>Brain Wave Analysis</h4>
              <div className={styles.waveItem}>
                <label>Alpha (8-12 Hz)</label>
                <div className={styles.waveBar}>
                  <div style={{ width: `${detection.alpha_power * 100}%` }} className={styles.waveAlpha} />
                </div>
                <span>{detection.alpha_power.toFixed(2)}</span>
              </div>

              <div className={styles.waveItem}>
                <label>Beta (12-30 Hz)</label>
                <div className={styles.waveBar}>
                  <div style={{ width: `${detection.beta_power * 100}%` }} className={styles.waveBeta} />
                </div>
                <span>{detection.beta_power.toFixed(2)}</span>
              </div>

              <div className={styles.waveItem}>
                <label>Theta (4-8 Hz)</label>
                <div className={styles.waveBar}>
                  <div style={{ width: `${detection.theta_power * 100}%` }} className={styles.waveTheta} />
                </div>
                <span>{detection.theta_power.toFixed(2)}</span>
              </div>
            </div>

            <p className={styles.nextStepMessage}>
              Proceeding to state selection...
            </p>
          </div>
        )}

        {error && (
          <div className={styles.errorMessage}>
            <p>Error: {error}</p>
            <CTAButton onClick={startScan} kind="ghost">
              Try Again
            </CTAButton>
          </div>
        )}
      </GlassCard>
    </div>
  );
}
