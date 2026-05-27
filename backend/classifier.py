"""
classifier.py
-------------
EEG band-power -> brain-state classifier for the Neiry Capsule headband.

States:
  Focused   -> beta dominant over alpha  (active concentration)
  Relaxed   -> alpha dominant over beta  (calm, awake rest)
  Fatigued  -> theta dominant over alpha (drowsiness / mental fatigue)
"""

from dataclasses import dataclass


@dataclass
class BandPowers:
    alpha: float   # 8-12 Hz
    beta: float    # 12-30 Hz
    theta: float   # 4-8 Hz


# Ratios tuned for bandwidth-normalized Welch band means (see eeg_listener._band_power).
FOCUS_RATIO = 1.15
FATIGUE_RATIO = 1.12
RELAXED_BETA_ALPHA_MAX = 1.05


def classify(bands: BandPowers) -> str:
    """Return one of: 'Focused' | 'Relaxed' | 'Fatigued'"""
    eps = 1e-9
    alpha = max(bands.alpha, eps)
    beta_alpha = bands.beta / alpha
    theta_alpha = bands.theta / alpha

    total = bands.alpha + bands.beta + bands.theta + eps
    beta_share = bands.beta / total
    theta_share = bands.theta / total
    alpha_share = bands.alpha / total

    if theta_share >= 0.38 and theta_alpha >= FATIGUE_RATIO:
        return "Fatigued"
    if beta_alpha >= FOCUS_RATIO and beta_share >= alpha_share:
        return "Focused"
    if beta_alpha <= RELAXED_BETA_ALPHA_MAX and alpha_share >= 0.28:
        return "Relaxed"
    if theta_alpha >= FATIGUE_RATIO:
        return "Fatigued"
    if beta_alpha >= FOCUS_RATIO:
        return "Focused"
    return "Relaxed"


def classify_raw(alpha: float, beta: float, theta: float) -> str:
    return classify(BandPowers(alpha=alpha, beta=beta, theta=theta))