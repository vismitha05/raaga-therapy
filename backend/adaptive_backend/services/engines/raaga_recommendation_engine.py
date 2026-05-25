from adaptive_backend.domain.enums import BrainState, TempoLevel, DayPart

RAAGA_LIBRARY = [
    {"name": "Hamsadhwani", "state": BrainState.focused, "day_part": DayPart.morning, "tempo": TempoLevel.low, "intensity": 0.4, "energy": 0.5},
    {"name": "Desh", "state": BrainState.focused, "day_part": DayPart.evening, "tempo": TempoLevel.medium, "intensity": 0.6, "energy": 0.7},
    {"name": "Bhairavi", "state": BrainState.relaxed, "day_part": DayPart.afternoon, "tempo": TempoLevel.low, "intensity": 0.4, "energy": 0.4},
    {"name": "Yaman", "state": BrainState.relaxed, "day_part": DayPart.night, "tempo": TempoLevel.medium, "intensity": 0.5, "energy": 0.5},
    {"name": "Darbari", "state": BrainState.sleepy, "day_part": DayPart.night, "tempo": TempoLevel.very_low, "intensity": 0.3, "energy": 0.2},
    {"name": "Ahir Bhairav", "state": BrainState.sleepy, "day_part": DayPart.morning, "tempo": TempoLevel.low, "intensity": 0.35, "energy": 0.3},
]


class RaagaRecommendationEngine:
    def choose(self, target_state: BrainState, day_part: DayPart, tempo: TempoLevel) -> dict:
        ranked = [r for r in RAAGA_LIBRARY if r["state"] == target_state]
        exact = [r for r in ranked if r["day_part"] == day_part and r["tempo"] == tempo]
        if exact:
            return exact[0]
        by_tempo = [r for r in ranked if r["tempo"] == tempo]
        if by_tempo:
            return by_tempo[0]
        return ranked[0] if ranked else RAAGA_LIBRARY[0]
