"""
raga_therapy_engine.py
--------------------
Manages raga-based therapeutic transitions with EEG state detection,
path calculation, and dynamic playlist generation with smooth transitions.
"""

import time
from dataclasses import dataclass
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from enum import Enum

from adaptive_backend.domain.enums import BrainState, DayPart


# ─── Frequency Band Mapping ──────────────────────────────────────────────────

class FrequencyBand(str, Enum):
    """Brain frequency bands mapped to ragas (in Hz)"""
    T1 = "T1"      # 4-6 Hz (delta-theta border) - Deep sleep/relaxation
    T2 = "T2"      # 6-8 Hz (theta-alpha border)
    A1 = "A1"      # 8-10 Hz (alpha) - Relaxed baseline
    A2 = "A2"      # 10-12 Hz (alpha-beta border)
    B1 = "B1"      # 12-21 Hz (beta) - Focused cognitive
    B2 = "B2"      # 21-30 Hz (high beta/gamma) - Intense focus


# ─── Raga Matrix: 18 Ragas across all bands and time periods ──────────────────

RAGA_MATRIX = {
    FrequencyBand.T1: {
        DayPart.morning: "Ahir_Bhairav",
        DayPart.afternoon: "Madhmad_Sarang",
        DayPart.evening: "Malkauns",
        DayPart.night: "Malkauns",
    },
    FrequencyBand.T2: {
        DayPart.morning: "Todi",
        DayPart.afternoon: "Bhimpalasi",
        DayPart.evening: "Darbari_Kanada",
        DayPart.night: "Darbari_Kanada",
    },
    FrequencyBand.A1: {
        DayPart.morning: "Bhairav",
        DayPart.afternoon: "Shuddh_Sarang",
        DayPart.evening: "Yaman",
        DayPart.night: "Yaman",
    },
    FrequencyBand.A2: {
        DayPart.morning: "Alhaiya_Bilawal",
        DayPart.afternoon: "Multani",
        DayPart.evening: "Bhopali",
        DayPart.night: "Bhopali",
    },
    FrequencyBand.B1: {
        DayPart.morning: "Jaunpuri",
        DayPart.afternoon: "Kafi",
        DayPart.evening: "Khamaj",
        DayPart.night: "Khamaj",
    },
    FrequencyBand.B2: {
        DayPart.morning: "Hindol",
        DayPart.afternoon: "Marwa",
        DayPart.evening: "Shankara",
        DayPart.night: "Shankara",
    },
}

# Frequency band order for linear traversal
BAND_ORDER = [FrequencyBand.T1, FrequencyBand.T2, FrequencyBand.A1,
              FrequencyBand.A2, FrequencyBand.B1, FrequencyBand.B2]

# State to target frequency band mapping
STATE_TO_BAND = {
    BrainState.sleepy: FrequencyBand.T1,      # 4-6 Hz
    BrainState.relaxed: FrequencyBand.A1,     # 8-10 Hz
    BrainState.focused: FrequencyBand.B1,     # 12-21 Hz
}


# ─── Data Classes ────────────────────────────────────────────────────────────

@dataclass
class EEGDetection:
    """Results of EEG analysis over 15-second window"""
    detected_band: FrequencyBand
    detected_state: BrainState
    alpha_power: float
    beta_power: float
    theta_power: float
    confidence: float
    timestamp: datetime


@dataclass
class RagaTrack:
    """Single raga track in a therapy playlist"""
    band: FrequencyBand
    raga_name: str
    duration_seconds: float
    frequency_range_hz: Tuple[float, float]
    order_in_sequence: int


@dataclass
class TherapyPlaylist:
    """Complete therapy session playlist with smooth transitions"""
    session_id: str
    start_band: FrequencyBand
    target_state: BrainState
    target_band: FrequencyBand
    total_duration_minutes: int
    day_part: DayPart
    tracks: List[RagaTrack]
    created_at: datetime
    total_transition_steps: int


# ─── EEG State Analyzer ──────────────────────────────────────────────────────

class EEGStateAnalyzer:
    """
    Analyzes EEG power bands and detects current brain state.
    Maps frequency ranges to brain states.
    """

    @staticmethod
    def classify_eeg_to_band(alpha: float, beta: float, theta: float) -> FrequencyBand:
        """
        Classify raw power values to frequency band using weighted heuristics.

        Args:
            alpha: Alpha band power (8-12 Hz)
            beta: Beta band power (12-30 Hz)
            theta: Theta band power (4-8 Hz)

        Returns:
            FrequencyBand enum
        """
        # Normalize powers
        total = alpha + beta + theta
        if total == 0:
            return FrequencyBand.A1  # Default to relaxed

        alpha_norm = alpha / total
        beta_norm = beta / total
        theta_norm = theta / total

        # Classification logic based on power ratios
        if beta_norm > 0.4:  # High beta dominance
            if beta_norm > 0.5:
                return FrequencyBand.B2  # 21-30 Hz (intense focus)
            else:
                return FrequencyBand.B1  # 12-21 Hz (focused)

        elif alpha_norm > 0.35:  # High alpha dominance
            if theta_norm > 0.25:
                return FrequencyBand.A2  # 10-12 Hz (alpha-beta border)
            else:
                return FrequencyBand.A1  # 8-10 Hz (relaxed)

        else:  # Theta dominance (low frequency)
            if theta_norm > 0.5:
                return FrequencyBand.T1  # 4-6 Hz (deep relaxation)
            else:
                return FrequencyBand.T2  # 6-8 Hz (theta-alpha border)

    @staticmethod
    def band_to_brain_state(band: FrequencyBand) -> BrainState:
        """Convert frequency band to clinical brain state"""
        if band in [FrequencyBand.T1, FrequencyBand.T2]:
            return BrainState.sleepy
        elif band in [FrequencyBand.A1, FrequencyBand.A2]:
            return BrainState.relaxed
        else:  # B1, B2
            return BrainState.focused

    @staticmethod
    def create_detection(alpha: float, beta: float, theta: float) -> EEGDetection:
        """Create EEGDetection from raw power values"""
        band = EEGStateAnalyzer.classify_eeg_to_band(alpha, beta, theta)
        state = EEGStateAnalyzer.band_to_brain_state(band)

        # Calculate confidence (0.0-1.0) based on dominance
        total = alpha + beta + theta
        if total == 0:
            confidence = 0.0
        else:
            max_power = max(alpha, beta, theta)
            confidence = min(1.0, (max_power / total) + 0.3)  # Boost confidence

        return EEGDetection(
            detected_band=band,
            detected_state=state,
            alpha_power=alpha,
            beta_power=beta,
            theta_power=theta,
            confidence=confidence,
            timestamp=datetime.utcnow(),
        )


# ─── Raga Therapy Engine ──────────────────────────────────────────────────────

class RagaTherapyEngine:
    """
    Orchestrates therapeutic raga sequences based on EEG state detection
    and user-selected target states. Manages smooth transitions between ragas.
    """

    @staticmethod
    def calculate_transition_path(
        start_band: FrequencyBand,
        target_state: BrainState,
    ) -> List[FrequencyBand]:
        """
        Calculate linear traversal path between frequency bands.

        Supports bidirectional transitions:
        - Sleep ↔ Relaxed ↔ Focused
        - Long transitions: Sleep → Focused (gradual increase)
        - Short transitions: Relaxed → Sleep (quick decrease)

        Args:
            start_band: Current detected frequency band
            target_state: Desired brain state (sleep/relaxed/focused)

        Returns:
            List of FrequencyBand objects representing the transition path
        """
        target_band = STATE_TO_BAND[target_state]
        start_idx = BAND_ORDER.index(start_band)
        target_idx = BAND_ORDER.index(target_band)

        if start_idx < target_idx:
            # Upward transition (lower freq → higher freq)
            # Include intermediate bands for smooth progression
            path = BAND_ORDER[start_idx + 1 : target_idx + 1]
        elif start_idx > target_idx:
            # Downward transition (higher freq → lower freq)
            path = list(reversed(BAND_ORDER[target_idx : start_idx]))
        else:
            # Already at target state
            path = [start_band]

        return path

    @staticmethod
    def get_frequency_range(band: FrequencyBand) -> Tuple[float, float]:
        """Get Hz range for a frequency band"""
        ranges = {
            FrequencyBand.T1: (4.0, 6.0),
            FrequencyBand.T2: (6.1, 8.0),
            FrequencyBand.A1: (8.1, 10.0),
            FrequencyBand.A2: (10.1, 12.0),
            FrequencyBand.B1: (12.1, 21.0),
            FrequencyBand.B2: (21.1, 30.0),
        }
        return ranges[band]

    @staticmethod
    def get_current_day_part() -> DayPart:
        """Determine current Prahar (time period) for raga selection"""
        hour = datetime.now().hour

        if 6 <= hour < 12:
            return DayPart.morning
        elif 12 <= hour < 18:
            return DayPart.afternoon
        elif 18 <= hour < 21:
            return DayPart.evening
        else:
            return DayPart.night

    @staticmethod
    def generate_therapy_playlist(
        session_id: str,
        detected_band: FrequencyBand,
        target_state: BrainState,
        duration_minutes: int,
    ) -> TherapyPlaylist:
        """
        Generate a complete therapy playlist with ragas scheduled across
        the therapeutic timeline.

        Logic:
        - Calculate transition path from detected → target state
        - Divide total duration equally among transition steps
        - Each raga plays for (duration / steps) minutes
        - Ragas selected based on band and current time of day

        Example:
        - Current: Sleep (T1), Target: Focused (B1), Duration: 10 mins
        - Path: T1 → T2 → A1 → A2 → B1 (5 steps)
        - Per raga: 10 / 5 = 2 minutes each
        - Playlist: [Ahir_Bhairav(2m), Todi(2m), Bhairav(2m), Alhaiya_Bilawal(2m), Jaunpuri(2m)]

        Args:
            session_id: Unique session identifier
            detected_band: Current EEG frequency band
            target_state: Desired therapeutic state
            duration_minutes: Total session duration (10, 20, or 30)

        Returns:
            TherapyPlaylist with sequenced ragas and timing
        """
        # Calculate transition path
        path = RagaTherapyEngine.calculate_transition_path(detected_band, target_state)
        target_band = STATE_TO_BAND[target_state]

        # Calculate duration per raga (seconds)
        duration_per_raga_seconds = (duration_minutes * 60) / len(path)

        # Get current time period for raga selection
        day_part = RagaTherapyEngine.get_current_day_part()

        # Build playlist
        tracks: List[RagaTrack] = []
        for order, band in enumerate(path):
            raga_name = RAGA_MATRIX[band][day_part]
            freq_range = RagaTherapyEngine.get_frequency_range(band)

            track = RagaTrack(
                band=band,
                raga_name=raga_name,
                duration_seconds=duration_per_raga_seconds,
                frequency_range_hz=freq_range,
                order_in_sequence=order,
            )
            tracks.append(track)

        # Create playlist
        playlist = TherapyPlaylist(
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

        return playlist

    @staticmethod
    def estimate_session_duration(
        start_band: FrequencyBand,
        target_state: BrainState,
    ) -> Dict[int, int]:
        """
        Estimate optimal session duration for a given transition.

        Returns dict: {duration_minutes: estimated_effectiveness_score (0-100)}
        """
        path_length = len(
            RagaTherapyEngine.calculate_transition_path(start_band, target_state)
        )

        return {
            10: int(50 + (path_length * 5)),   # Shorter sessions, less effective
            20: int(75 + (path_length * 3)),   # Moderate sessions
            30: int(90 + (path_length * 2)),   # Longer sessions, most effective
        }


# ─── Transition Validator ────────────────────────────────────────────────────

class TransitionValidator:
    """Validates therapeutic transitions for safety and efficacy"""

    # Maximum frequency jump per transition step (Hz)
    MAX_FREQ_JUMP = 10.0

    # Minimum session duration for safe transitions (minutes)
    MIN_SAFE_DURATION = 10

    @staticmethod
    def validate_transition(
        start_band: FrequencyBand,
        target_state: BrainState,
        duration_minutes: int,
    ) -> Tuple[bool, str]:
        """
        Validate if a requested transition is safe and effective.

        Returns:
            Tuple[is_valid, reason_if_invalid]
        """
        if duration_minutes < TransitionValidator.MIN_SAFE_DURATION:
            return False, f"Minimum session duration is {TransitionValidator.MIN_SAFE_DURATION} minutes"

        path = RagaTherapyEngine.calculate_transition_path(start_band, target_state)

        # Check if frequency jumps are within safe limits
        for i in range(len(path) - 1):
            band1 = path[i]
            band2 = path[i + 1]

            freq1_mid = (RagaTherapyEngine.get_frequency_range(band1)[0] +
                        RagaTherapyEngine.get_frequency_range(band1)[1]) / 2
            freq2_mid = (RagaTherapyEngine.get_frequency_range(band2)[0] +
                        RagaTherapyEngine.get_frequency_range(band2)[1]) / 2

            jump = abs(freq2_mid - freq1_mid)
            if jump > TransitionValidator.MAX_FREQ_JUMP:
                return False, f"Frequency jump too large: {jump:.1f} Hz > {TransitionValidator.MAX_FREQ_JUMP} Hz"

        return True, "Transition is valid"
