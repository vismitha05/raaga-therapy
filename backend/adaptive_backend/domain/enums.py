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
    morning = "morning"
    afternoon = "afternoon"
    evening = "evening"
    night = "night"
