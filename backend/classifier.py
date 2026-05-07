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


FOCUS_RATIO   = 1.1
FATIGUE_RATIO = 1.1


def classify(bands: BandPowers) -> str:
    """Return one of: 'Focused' | 'Relaxed' | 'Fatigued'"""
    eps = 1e-9
    beta_alpha  = bands.beta  / (bands.alpha + eps)
    theta_alpha = bands.theta / (bands.alpha + eps)

    if beta_alpha >= FOCUS_RATIO:
        return "Focused"
    elif theta_alpha >= FATIGUE_RATIO:
        return "Fatigued"
    else:
        return "Relaxed"


def classify_raw(alpha: float, beta: float, theta: float) -> str:
    return classify(BandPowers(alpha=alpha, beta=beta, theta=theta))