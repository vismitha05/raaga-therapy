from adaptive_backend.domain.enums import BrainState


def detect_state(features: dict) -> tuple[BrainState, float]:
    ba = features["beta_alpha_ratio"]
    ta = features["theta_alpha_ratio"]
    if ba >= 1.1:
        return BrainState.focused, min(1.0, (ba - 1.0) * 0.8)
    if ta >= 1.1:
        return BrainState.sleepy, min(1.0, (ta - 1.0) * 0.8)
    conf = 1.0 - min(1.0, abs(ba - 1.0) + abs(ta - 1.0))
    return BrainState.relaxed, max(0.5, conf)
