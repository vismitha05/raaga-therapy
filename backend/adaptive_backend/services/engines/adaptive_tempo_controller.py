from adaptive_backend.domain.enums import TempoLevel

ORDER = [TempoLevel.very_low, TempoLevel.low, TempoLevel.medium, TempoLevel.high]


class AdaptiveTempoController:
    def step_toward(self, current: TempoLevel, target: TempoLevel) -> TempoLevel:
        c_idx = ORDER.index(current)
        t_idx = ORDER.index(target)
        if c_idx == t_idx:
            return current
        return ORDER[c_idx + 1] if c_idx < t_idx else ORDER[c_idx - 1]
