from adaptive_backend.domain.enums import BrainState, TempoLevel
from adaptive_backend.services.engines.adaptive_tempo_controller import AdaptiveTempoController
from adaptive_backend.services.engines.transition_safety_layer import TransitionSafetyLayer


class StateTransitionEngine:
    def __init__(self):
        self.tempo_controller = AdaptiveTempoController()
        self.safety = TransitionSafetyLayer()

    def next_tempo(self, detected_state: BrainState, target_state: BrainState, current_tempo: TempoLevel, confidence: float) -> TempoLevel:
        desired = self.safety.target_tempo_for_state(target_state)
        stepped = self.tempo_controller.step_toward(current_tempo, desired)
        if detected_state == BrainState.focused and target_state == BrainState.relaxed:
            stepped = self.tempo_controller.step_toward(stepped, TempoLevel.low)
        if detected_state == BrainState.sleepy and target_state == BrainState.focused:
            stepped = self.tempo_controller.step_toward(stepped, TempoLevel.high)
        return self.safety.dampen_if_overshoot(confidence, stepped)
