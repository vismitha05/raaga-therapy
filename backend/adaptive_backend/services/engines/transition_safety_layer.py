from adaptive_backend.domain.enums import BrainState, TempoLevel


class TransitionSafetyLayer:
    def target_tempo_for_state(self, state: BrainState) -> TempoLevel:
        if state == BrainState.focused:
            return TempoLevel.high
        if state == BrainState.relaxed:
            return TempoLevel.medium
        return TempoLevel.very_low

    def dampen_if_overshoot(self, confidence: float, current: TempoLevel) -> TempoLevel:
        if confidence < 0.55 and current == TempoLevel.high:
            return TempoLevel.medium
        return current
