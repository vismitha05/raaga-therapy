/**
 * EEGValidationEngine.js
 * ─────────────────────────────────────────────────────────────
 * REAL EEG-based therapy validation engine
 *
 * This validates therapy outcome using:
 * - Alpha
 * - Beta
 * - Theta
 * - Gamma
 *
 * Instead of fake mathematical progress.
 */

export function average(arr = []) {
  if (!arr.length) return 0;
  return arr.reduce((a, b) => a + b, 0) / arr.length;
}

/**
 * Extract EEG band powers
 */
export function extractBands(eegSeries = []) {
  if (!eegSeries.length) {
    return {
      alpha: 0,
      beta: 0,
      theta: 0,
      gamma: 0,
    };
  }

  return {
    alpha: average(eegSeries.map(v => v.alpha || 0)),
    beta: average(eegSeries.map(v => v.beta || 0)),
    theta: average(eegSeries.map(v => v.theta || 0)),
    gamma: average(eegSeries.map(v => v.gamma || 0)),
  };
}

/**
 * REAL focus score
 * Focus increases when:
 * - beta increases
 * - theta decreases
 */
export function calculateFocusScore(bands) {
  const score =
    (bands.beta * 1.8) -
    (bands.theta * 0.8);

  return clamp(score);
}

/**
 * REAL relaxation score
 * Relaxation increases when alpha increases
 */
export function calculateRelaxationScore(bands) {
  const score =
    (bands.alpha * 2) -
    (bands.beta * 0.5);

  return clamp(score);
}

/**
 * Sleep readiness
 * Sleep improves when theta increases
 */
export function calculateSleepScore(bands) {
  const score =
    (bands.theta * 2.2) -
    (bands.beta * 0.7);

  return clamp(score);
}

/**
 * Stability score
 */
export function calculateStabilityScore(bands) {
  const score =
    (bands.alpha + bands.theta) / 2;

  return clamp(score * 2);
}

/**
 * Stress reduction
 * Stress decreases when alpha rises and beta lowers
 */
export function calculateStressReduction(bands) {
  const stress =
    (bands.beta * 1.5) -
    (bands.alpha * 1.2);

  return clamp(100 - stress);
}

/**
 * Therapy effectiveness validation
 */
export function calculateTherapyEffectiveness(
  baseline,
  current,
  targetState
) {
  let score = 0;

  // Relaxation validation
  if (targetState === "Relaxed") {
    const alphaGain =
      current.alpha - baseline.alpha;

    score += alphaGain * 2;

    if (current.beta < baseline.beta) {
      score += 15;
    }
  }

  // Focus validation
  if (targetState === "Focused") {
    const betaGain =
      current.beta - baseline.beta;

    const thetaDrop =
      baseline.theta - current.theta;

    score += betaGain * 2;
    score += thetaDrop * 1.5;
  }

  // Sleep validation
  if (targetState === "Sleep") {
    const thetaGain =
      current.theta - baseline.theta;

    score += thetaGain * 2;

    if (current.beta < baseline.beta) {
      score += 10;
    }
  }

  return clamp(score);
}

/**
 * Clamp score between 0–100
 */
function clamp(value) {
  return Math.max(
    0,
    Math.min(100, Math.round(value))
  );
}