class CrossfadePlayer:
    def crossfade(self, from_track: str, to_track: str, duration_seconds: float = 3.0) -> dict:
        return {
            "from": from_track,
            "to": to_track,
            "duration_seconds": duration_seconds,
            "status": "queued",
        }

