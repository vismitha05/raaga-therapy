"""
raga_therapy_engine.py
--------------------
Manages raga-based therapeutic transitions with EEG state detection,
path calculation, and dynamic playlist generation with smooth transitions.

Playback rules:
- Ragas are chosen from morning (6:00–12:00) or evening/night (18:00–6:00) matrices.
- Transition path is built from the detected frequency band toward the target state band.
- Downward transitions (e.g. B2 at 21.1–30 Hz → sleep) step through bands in decreasing order.
- Each raga duration = selected_session_minutes / number_of_ragas_in_path.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Tuple

from adaptive_backend.domain.enums import BrainState, DayPart


# ─── Frequency Band Mapping ──────────────────────────────────────────────────

class FrequencyBand(str, Enum):
    """Brain frequency bands mapped to ragas (in Hz)."""
    T1 = "T1"  # 4.0–6.0 Hz
    T2 = "T2"  # 6.1–8.0 Hz
    A1 = "A1"  # 8.1–10.0 Hz
    A2 = "A2"  # 10.1–12.0 Hz
    B1 = "B1"  # 12.1–21.0 Hz
    B2 = "B2"  # 21.1–30.0 Hz


BAND_ORDER: List[FrequencyBand] = [
    FrequencyBand.T1,
    FrequencyBand.T2,
    FrequencyBand.A1,
    FrequencyBand.A2,
    FrequencyBand.B1,
    FrequencyBand.B2,
]

FREQUENCY_RANGES: Dict[FrequencyBand, Tuple[float, float]] = {
    FrequencyBand.T1: (4.0, 6.0),
    FrequencyBand.T2: (6.1, 8.0),
    FrequencyBand.A1: (8.1, 10.0),
    FrequencyBand.A2: (10.1, 12.0),
    FrequencyBand.B1: (12.1, 21.0),
    FrequencyBand.B2: (21.1, 30.0),
}

# Target therapeutic state → terminal frequency band
STATE_TO_BAND: Dict[BrainState, FrequencyBand] = {
    BrainState.sleepy: FrequencyBand.T1,
    BrainState.relaxed: FrequencyBand.A1,
    BrainState.focused: FrequencyBand.B1,
}

# ─── Production & style metadata (shared across all tracks) ─────────────────

PRODUCTION_PROFILE = {
    "style_genre": "Traditional Indian Classical, Hindustani Raga, Solo Instrument",
    "instruments": ["Sitar", "Santoor", "Flute (Bansuri)", "Tanpura drone"],
    "production": "High fidelity, clean audio, no vocals, organic acoustic timbre",
}

# ─── Raga matrices (morning vs evening/night) ───────────────────────────────

@dataclass(frozen=True)
class RagaSpec:
    name: str
    bpm: int
    lay: str
    feel: str


MORNING_RAGA_MATRIX: Dict[FrequencyBand, RagaSpec] = {
    FrequencyBand.T1: RagaSpec(
        "Ahir Bhairav", 60, "Vilambit Lay",
        "Deeply meditative, serene, heavy drone, soft attack, low brightness",
    ),
    FrequencyBand.T2: RagaSpec(
        "Todi", 70, "Vilambit Lay",
        "Introspective, creative drift, gentle sweeping rhythms, legato phrasing",
    ),
    FrequencyBand.A1: RagaSpec(
        "Bhairav", 85, "Madhyam Lay",
        "Warm, deeply relaxing, peaceful, rich mid-range harmonics",
    ),
    FrequencyBand.A2: RagaSpec(
        "Alhaiya Bilawal", 100, "Madhyam Lay",
        "Bright, mindful, clear alertness, crisp transitions",
    ),
    FrequencyBand.B1: RagaSpec(
        "Jaunpuri", 120, "Drut Lay",
        "Driving focus, sharp rhythmic attacks, highly structured patterns",
    ),
    FrequencyBand.B2: RagaSpec(
        "Hindol", 140, "Drut Lay",
        "High alertness, complex polyrhythms, urgent and sharp instrumentation",
    ),
}

EVENING_NIGHT_RAGA_MATRIX: Dict[FrequencyBand, RagaSpec] = {
    FrequencyBand.T1: RagaSpec(
        "Malkauns", 55, "Vilambit Lay",
        "Deeply grounding, hypnotic, spacey, slow pacing",
    ),
    FrequencyBand.T2: RagaSpec(
        "Darbari Kanada", 65, "Vilambit Lay",
        "Majestic, heavy resonant bass notes, slow oscillating microtones (meend)",
    ),
    FrequencyBand.A1: RagaSpec(
        "Yaman", 80, "Madhyam Lay",
        "Calming, emotionally soothing, warm harmonics, stable pacing",
    ),
    FrequencyBand.A2: RagaSpec(
        "Bhopali", 95, "Madhyam Lay",
        "Pentatonic clarity, bright yet restful, flowing string plucks",
    ),
    FrequencyBand.B1: RagaSpec(
        "Khamaj", 115, "Drut Lay",
        "Active cognitive alertness, fast structured patterns, sharp accents",
    ),
    FrequencyBand.B2: RagaSpec(
        "Shankara", 135, "Drut Lay",
        "Intense focus, rapid ascending scales, high acoustic brightness",
    ),
}

RAGA_MATRIX_BY_DAY: Dict[DayPart, Dict[FrequencyBand, RagaSpec]] = {
    DayPart.morning: MORNING_RAGA_MATRIX,
    DayPart.evening_night: EVENING_NIGHT_RAGA_MATRIX,
}


# ─── Data Classes ────────────────────────────────────────────────────────────

@dataclass
class EEGDetection:
    detected_band: FrequencyBand
    detected_state: BrainState
    alpha_power: float
    beta_power: float
    theta_power: float
    confidence: float
    timestamp: datetime
    dominant_hz: float | None = None


@dataclass
class RagaTrack:
    band: FrequencyBand
    raga_name: str
    duration_seconds: float
    frequency_range_hz: Tuple[float, float]
    order_in_sequence: int
    bpm: int
    lay: str
    feel: str
    file_slug: str = ""


@dataclass
class TherapyPlaylist:
    session_id: str
    start_band: FrequencyBand
    target_state: BrainState
    target_band: FrequencyBand
    total_duration_minutes: int
    day_part: DayPart
    tracks: List[RagaTrack]
    created_at: datetime
    total_transition_steps: int
    production_profile: dict = field(default_factory=lambda: dict(PRODUCTION_PROFILE))


# ─── EEG State Analyzer ──────────────────────────────────────────────────────

class EEGStateAnalyzer:
    @staticmethod
    def hz_to_band(hz: float) -> FrequencyBand:
        """Map a dominant frequency (Hz) to the active target-state band."""
        if hz <= 6.0:
            return FrequencyBand.T1
        if hz <= 8.0:
            return FrequencyBand.T2
        if hz <= 10.0:
            return FrequencyBand.A1
        if hz <= 12.0:
            return FrequencyBand.A2
        if hz <= 21.0:
            return FrequencyBand.B1
        return FrequencyBand.B2

    @staticmethod
    def classify_eeg_to_band(alpha: float, beta: float, theta: float) -> FrequencyBand:
        """Ratio-based bands aligned with classifier.py (not raw power sums)."""
        from classifier import classify_raw

        label = classify_raw(alpha, beta, theta)
        if label == "Fatigued":
            return FrequencyBand.T1 if theta >= alpha else FrequencyBand.T2
        if label == "Focused":
            beta_alpha = beta / (alpha + 1e-9)
            return FrequencyBand.B2 if beta_alpha >= 1.35 else FrequencyBand.B1
        beta_alpha = beta / (alpha + 1e-9)
        if beta_alpha >= 1.05:
            return FrequencyBand.A2
        return FrequencyBand.A1

    @staticmethod
    def band_to_brain_state(band: FrequencyBand) -> BrainState:
        if band in (FrequencyBand.T1, FrequencyBand.T2):
            return BrainState.sleepy
        if band in (FrequencyBand.A1, FrequencyBand.A2):
            return BrainState.relaxed
        return BrainState.focused

    @staticmethod
    def band_midpoint_hz(band: FrequencyBand) -> float:
        lo, hi = FREQUENCY_RANGES[band]
        return (lo + hi) / 2

    @staticmethod
    def create_detection(
        alpha: float,
        beta: float,
        theta: float,
        dominant_hz: float | None = None,
    ) -> EEGDetection:
        band = (
            EEGStateAnalyzer.hz_to_band(dominant_hz)
            if dominant_hz is not None
            else EEGStateAnalyzer.classify_eeg_to_band(alpha, beta, theta)
        )
        state = EEGStateAnalyzer.band_to_brain_state(band)

        total = alpha + beta + theta
        if total == 0:
            confidence = 0.0
        else:
            max_power = max(alpha, beta, theta)
            confidence = min(1.0, (max_power / total) + 0.3)

        return EEGDetection(
            detected_band=band,
            detected_state=state,
            alpha_power=alpha,
            beta_power=beta,
            theta_power=theta,
            confidence=confidence,
            timestamp=datetime.utcnow(),
            dominant_hz=dominant_hz,
        )


# ─── Raga Therapy Engine ──────────────────────────────────────────────────────

class RagaTherapyEngine:
    @staticmethod
    def resolve_day_part(dt: datetime | None = None) -> DayPart:
        """
        Morning matrix: 6:00–12:00.
        Evening/night matrix: 18:00–6:00.
        12:00–18:00 uses the morning matrix (daytime gap not in evening window).
        """
        hour = (dt or datetime.now()).hour
        if 6 <= hour < 12:
            return DayPart.morning
        if hour >= 18 or hour < 6:
            return DayPart.evening_night
        return DayPart.morning

    @staticmethod
    def get_raga_spec(band: FrequencyBand, day_part: DayPart) -> RagaSpec:
        key = (
            day_part
            if day_part in RAGA_MATRIX_BY_DAY
            else DayPart.evening_night
            if day_part in (DayPart.evening, DayPart.night, DayPart.afternoon)
            else DayPart.morning
        )
        return RAGA_MATRIX_BY_DAY[key][band]

    @staticmethod
    def raga_file_slug(name: str) -> str:
        return name.replace(" ", "_")

    @staticmethod
    def calculate_transition_path(
        start_band: FrequencyBand,
        target_state: BrainState,
    ) -> List[FrequencyBand]:
        """
        Build the sequence of bands whose ragas will play.

        Upward (toward focus): step through higher bands, excluding the start band.
        Downward (toward sleep/relax): step through lower bands in decreasing order,
        excluding the start band — e.g. B2 + sleep → B1, A2, A1, T2, T1.
        Already at target band: play the raga for the current band only.
        """
        target_band = STATE_TO_BAND[target_state]
        start_idx = BAND_ORDER.index(start_band)
        target_idx = BAND_ORDER.index(target_band)

        if start_idx == target_idx:
            return [start_band]
        if start_idx < target_idx:
            return BAND_ORDER[start_idx + 1 : target_idx + 1]
        return list(reversed(BAND_ORDER[target_idx:start_idx]))

    @staticmethod
    def get_frequency_range(band: FrequencyBand) -> Tuple[float, float]:
        return FREQUENCY_RANGES[band]

    @staticmethod
    def generate_therapy_playlist(
        session_id: str,
        detected_band: FrequencyBand,
        target_state: BrainState,
        duration_minutes: int,
        at_time: datetime | None = None,
    ) -> TherapyPlaylist:
        path = RagaTherapyEngine.calculate_transition_path(detected_band, target_state)
        target_band = STATE_TO_BAND[target_state]
        duration_per_raga_seconds = (duration_minutes * 60) / len(path)
        day_part = RagaTherapyEngine.resolve_day_part(at_time)

        tracks: List[RagaTrack] = []
        for order, band in enumerate(path):
            spec = RagaTherapyEngine.get_raga_spec(band, day_part)
            tracks.append(
                RagaTrack(
                    band=band,
                    raga_name=spec.name,
                    duration_seconds=duration_per_raga_seconds,
                    frequency_range_hz=RagaTherapyEngine.get_frequency_range(band),
                    order_in_sequence=order,
                    bpm=spec.bpm,
                    lay=spec.lay,
                    feel=spec.feel,
                    file_slug=RagaTherapyEngine.raga_file_slug(spec.name),
                )
            )

        return TherapyPlaylist(
            session_id=session_id,
            start_band=detected_band,
            target_state=target_state,
            target_band=target_band,
            total_duration_minutes=duration_minutes,
            day_part=day_part,
            tracks=tracks,
            created_at=datetime.utcnow(),
            total_transition_steps=len(path),
        )

    @staticmethod
    def estimate_session_duration(
        start_band: FrequencyBand,
        target_state: BrainState,
    ) -> Dict[int, int]:
        path_length = len(
            RagaTherapyEngine.calculate_transition_path(start_band, target_state)
        )
        return {
            10: int(50 + (path_length * 5)),
            20: int(75 + (path_length * 3)),
            30: int(90 + (path_length * 2)),
        }


class TransitionValidator:
    MAX_FREQ_JUMP = 10.0
    MIN_SAFE_DURATION = 10

    @staticmethod
    def validate_transition(
        start_band: FrequencyBand,
        target_state: BrainState,
        duration_minutes: int,
    ) -> Tuple[bool, str]:
        if duration_minutes < TransitionValidator.MIN_SAFE_DURATION:
            return (
                False,
                f"Minimum session duration is {TransitionValidator.MIN_SAFE_DURATION} minutes",
            )

        path = RagaTherapyEngine.calculate_transition_path(start_band, target_state)
        for i in range(len(path) - 1):
            mid1 = EEGStateAnalyzer.band_midpoint_hz(path[i])
            mid2 = EEGStateAnalyzer.band_midpoint_hz(path[i + 1])
            jump = abs(mid2 - mid1)
            if jump > TransitionValidator.MAX_FREQ_JUMP:
                return (
                    False,
                    f"Frequency jump too large: {jump:.1f} Hz > {TransitionValidator.MAX_FREQ_JUMP} Hz",
                )
        return True, "Transition is valid"


# ---------------------------------------------------------------------------
# Public helpers implementing the EXACT requested algorithms and math.
# ---------------------------------------------------------------------------

def state_transition_algorithm(start_band: FrequencyBand, target_state: BrainState) -> List[FrequencyBand]:
    """
    State transition algorithm (exact):

    - Use fixed cognitive ladder order: T1 -> T2 -> A1 -> A2 -> B1 -> B2
    - If start == target: return [start_band] (play the raga for the current band only)
    - If start < target (index lower): return the ordered list of bands
      from start+1 up to and including target (ascending order).
    - If start > target: return the ordered list of bands from start-1
      down to and including target (descending order). This preserves the
      intermediate steps and does NOT skip or jump.

    This function delegates to `RagaTherapyEngine.calculate_transition_path`
    which implements the exact same logic.
    """
    return RagaTherapyEngine.calculate_transition_path(start_band, target_state)


def state_transition_algorithm_to_band(start_band: FrequencyBand, target_band: FrequencyBand) -> List[FrequencyBand]:
    """
    State transition algorithm variant that accepts a target FrequencyBand
    directly (useful for examples like Current=T1, Target=A2).

    - If start == target: return [start_band]
    - If start < target: return BAND_ORDER[start_idx+1:target_idx+1]
    - If start > target: return reversed(BAND_ORDER[target_idx:start_idx])
    """
    start_idx = BAND_ORDER.index(start_band)
    target_idx = BAND_ORDER.index(target_band)
    if start_idx == target_idx:
        return [start_band]
    if start_idx < target_idx:
        return BAND_ORDER[start_idx + 1 : target_idx + 1]
    return list(reversed(BAND_ORDER[target_idx:start_idx]))


def mathematical_duration_calculation(session_duration_minutes: int, num_raagas: int) -> float:
    """
    Mathematical duration calculation (exact):

    - Let SessionDurationMinutes be the user-selected minutes (e.g. 20).
    - Let N be the number of transition raagas (len(path)).
    - DurationPerRaaga (minutes) = SessionDurationMinutes / N
    - DurationPerRaaga (seconds) = DurationPerRaaga (minutes) * 60

    Formula used (single-step):
        DurationPerRaaga_seconds = (SessionDurationMinutes * 60) / N

    Returns the duration in seconds (float). Caller may format or round
    for display or playback as required, but the calculation is exact.
    """
    if num_raagas <= 0:
        raise ValueError("num_raagas must be >= 1")
    return (session_duration_minutes * 60) / num_raagas


def raaga_ordering_algorithm(path: List[FrequencyBand], at_time: datetime | None = None) -> List[Tuple[FrequencyBand, RagaSpec]]:
    """
    Raaga ordering algorithm:

    - Determine the `DayPart` using `RagaTherapyEngine.resolve_day_part`.
    - For each band in `path` (order preserved), map the band to the
      corresponding `RagaSpec` from the day-part matrix.
    - Do NOT shuffle, randomize, or reorder the `path`.
    - Return a list of tuples (band, RagaSpec) in the same order as `path`.
    """
    day_part = RagaTherapyEngine.resolve_day_part(at_time)
    ordered: List[Tuple[FrequencyBand, RagaSpec]] = []
    for band in path:
        spec = RagaTherapyEngine.get_raga_spec(band, day_part)
        ordered.append((band, spec))
    return ordered


def playlist_generation_algorithm(
    session_id: str,
    detected_band: FrequencyBand,
    target_state: BrainState,
    session_duration_minutes: int,
    at_time: datetime | None = None,
) -> List[dict]:
    """
    Playlist generation algorithm (exact output structure described by user):

    Steps:
    1. Compute transition path using `state_transition_algorithm`.
    2. Compute N = number of ragas in path.
    3. Compute DurationPerRaaga_seconds using
       `mathematical_duration_calculation(session_duration_minutes, N)`.
    4. Map each band in the path -> `RagaSpec` according to current daypart
       using `raaga_ordering_algorithm` while preserving order.
    5. Produce the final list of dicts in the exact structure:
       [ { state: "T2", raaga: "Todi", durationSeconds: 400 }, ... ]

    This function implements the PLAYBACK RULES: when one raaga finishes
    play the next raaga in the generated order; do not reorder, reshuffle
    or repeat.
    """
    path = state_transition_algorithm(detected_band, target_state)
    N = len(path)
    duration_per_raaga_seconds = mathematical_duration_calculation(
        session_duration_minutes, N
    )
    ordered = raaga_ordering_algorithm(path, at_time)

    playlist: List[dict] = []
    for idx, (band, spec) in enumerate(ordered):
        seconds = duration_per_raaga_seconds
        # Preserve numeric precision but convert to int when it's effectively integer
        if abs(seconds - round(seconds)) < 1e-9:
            seconds_out: int | float = int(round(seconds))
        else:
            seconds_out = round(seconds, 6)

        playlist.append(
            {
                "state": band.value,
                "raaga": spec.name,
                "durationSeconds": seconds_out,
            }
        )

    return playlist


def playlist_generation_for_target_band(
    session_id: str,
    detected_band: FrequencyBand,
    target_band: FrequencyBand,
    session_duration_minutes: int,
    at_time: datetime | None = None,
) -> List[dict]:
    """
    Playlist generation that accepts a target FrequencyBand directly.

    Implements the same exact mathematical and ordering rules but lets
    callers specify the final band (e.g., Target = A2) as shown in the
    user's examples.
    """
    path = state_transition_algorithm_to_band(detected_band, target_band)
    N = len(path)
    duration_per_raaga_seconds = mathematical_duration_calculation(
        session_duration_minutes, N
    )
    ordered = raaga_ordering_algorithm(path, at_time)

    playlist: List[dict] = []
    for idx, (band, spec) in enumerate(ordered):
        seconds = duration_per_raaga_seconds
        if abs(seconds - round(seconds)) < 1e-9:
            seconds_out: int | float = int(round(seconds))
        else:
            seconds_out = round(seconds, 6)

        playlist.append(
            {
                "state": band.value,
                "raaga": spec.name,
                "durationSeconds": seconds_out,
            }
        )

    return playlist

