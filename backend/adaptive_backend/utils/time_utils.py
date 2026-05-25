from datetime import datetime

from adaptive_backend.domain.enums import DayPart


def get_day_part(now: datetime | None = None) -> DayPart:
    now = now or datetime.now()
    h = now.hour
    if 5 <= h < 12:
        return DayPart.morning
    if 12 <= h < 17:
        return DayPart.afternoon
    if 17 <= h < 21:
        return DayPart.evening
    return DayPart.night
