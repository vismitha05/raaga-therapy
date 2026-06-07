"""
Resistance Quality Analyzer for EEG Channels
==============================================
Maps impedance/resistance values to quality indicators (GOOD/WARNING/BAD).
Inspired by Neiry's official quality indicators.
"""

from typing import Dict, Literal

# Resistance thresholds in Ohms (typical for EEG electrode quality)
# NOTE: These thresholds are temporary development values based on observed
# Capsule headset resistance readings (June 2026). They MUST be validated
# against the official Capsule application and vendor-provided guidance.
#
# Use the `GOOD_THRESHOLD` and `WARNING_THRESHOLD` constants to configure
# the classification boundaries. Quality mapping is:
#   - `GOOD`: resistance <= GOOD_THRESHOLD
#   - `WARNING`: GOOD_THRESHOLD < resistance <= WARNING_THRESHOLD
#   - `BAD`: resistance > WARNING_THRESHOLD

# Temporary development thresholds (observed device resistances):
# GOOD <= 500,000 Ω, WARNING <= 800,000 Ω, BAD > 800,000 Ω
GOOD_THRESHOLD = 500_000
WARNING_THRESHOLD = 800_000

ChannelQuality = Literal["GOOD", "WARNING", "BAD"]


class ResistanceQualityAnalyzer:
    """
    Analyzes EEG channel resistance and provides quality indicators.
    """

    @staticmethod
    def analyze_channel(resistance_ohms: float) -> ChannelQuality:
        """
        Classify a single channel's resistance.
        
        Args:
            resistance_ohms: Resistance value in Ohms
            
        Returns:
            Quality indicator: "GOOD", "WARNING", or "BAD"
        """
        if resistance_ohms <= GOOD_THRESHOLD:
            return "GOOD"
        elif resistance_ohms <= WARNING_THRESHOLD:
            return "WARNING"
        else:
            return "BAD"

    @staticmethod
    def analyze_all(channel_resistance: Dict[str, float]) -> Dict[str, ChannelQuality]:
        """
        Analyze all channels and return quality for each.
        
        Args:
            channel_resistance: Dict mapping channel names to resistance in Ohms
            
        Returns:
            Dict mapping channel names to quality indicators
        """
        return {
            channel: ResistanceQualityAnalyzer.analyze_channel(value)
            for channel, value in channel_resistance.items()
        }

    @staticmethod
    def is_headset_ready(channel_quality: Dict[str, ChannelQuality]) -> bool:
        """
        Determine if all required channels have acceptable quality.
        
        Criteria:
        - No GOOD channels is acceptable (user may have minimal electrodes)
        - All channels must be GOOD or WARNING (no BAD channels)
        - At least 1 channel must be present
        
        Args:
            channel_quality: Dict mapping channel names to quality indicators
            
        Returns:
            True if headset is ready for use, False otherwise
        """
        if not channel_quality:
            return False
        
        # All channels must be GOOD or WARNING (no BAD allowed)
        has_bad = any(q == "BAD" for q in channel_quality.values())
        return not has_bad

    @staticmethod
    def get_quality_stats(channel_quality: Dict[str, ChannelQuality]) -> Dict[str, int]:
        """
        Get count of channels by quality level.
        
        Args:
            channel_quality: Dict mapping channel names to quality indicators
            
        Returns:
            Dict with counts of each quality level
        """
        stats = {"GOOD": 0, "WARNING": 0, "BAD": 0}
        for quality in channel_quality.values():
            stats[quality] += 1
        return stats
