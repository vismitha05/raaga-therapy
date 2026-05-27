from classifier import classify_raw

from adaptive_backend.domain.enums import BrainState


def classifier_label_to_brain_state(label: str) -> BrainState:
    if label == "Focused":
        return BrainState.focused
    if label == "Fatigued":
        return BrainState.sleepy
    return BrainState.relaxed


def ui_state_label(state: str) -> str:
    """Map backend classifier labels to UI labels."""
    if state in ("sleepy", "sleep", "Fatigued"):
        return "Sleep"
    if state in ("focused", "Focused"):
        return "Focused"
    if state in ("relaxed", "Relaxed"):
        return "Relaxed"
    return state


def detect_state(features: dict) -> tuple[BrainState, float]:
    alpha = features.get("alpha_mean", 0.0)
    beta = features.get("beta_mean", 0.0)
    theta = features.get("theta_mean", 0.0)
    label = classify_raw(alpha, beta, theta)
    state = classifier_label_to_brain_state(label)

    ba = features["beta_alpha_ratio"]
    ta = features["theta_alpha_ratio"]
    margin = max(abs(ba - 1.0), abs(ta - 1.0))
    confidence = min(0.98, max(0.5, 0.55 + margin * 0.25))
    return state, confidence
