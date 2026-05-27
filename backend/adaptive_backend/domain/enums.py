from enum import Enum


class BrainState(str, Enum):
    focused = "focused"
    relaxed = "relaxed"
    sleepy = "sleep"


class TempoLevel(str, Enum):
    very_low = "very_low"
    low = "low"
    medium = "medium"
    high = "high"


class DayPart(str, Enum):
    """Prahar windows for raga selection."""
    morning = "morning"  # 6:00 AM – 12:00 PM
    evening_night = "evening_night"  # 6:00 PM – 6:00 AM
    # Legacy aliases (mapped to evening_night in therapy engine)
    afternoon = "afternoon"
    evening = "evening"
    night = "night"
