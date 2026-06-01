def map_capsule_metrics(payload: dict) -> dict:
    return {
        "focus": payload.get("focus"),
        "relaxation": payload.get("relaxation"),
        "fatigue": payload.get("fatigue"),
        "stress": payload.get("stress"),
    }

