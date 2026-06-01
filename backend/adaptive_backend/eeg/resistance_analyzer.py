"""
Resistance Quality Analyzer for EEG Channels
==============================================
Maps impedance/resistance values to quality indicators (GOOD/WARNING/BAD).
Inspired by Neiry's official quality indicators.
"""

from typing import Dict, Literal

# Resistance thresholds in Ohms (typical for EEG electrode quality)
# These values are empirically derived from Capsule API documentation
# and match Neiry's quality indicators

QUALITY_THRESHOLDS = {
    # Good impedance: < 50 kOhms (excellent signal quality)
    "GOOD": 50_000,
    # Warning: 50-100 kOhms (acceptable but marginal)
    "WARNING": 100_000,
    # Bad: > 100 kOhms (poor contact, high noise)
}

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
        if resistance_ohms <= QUALITY_THRESHOLDS["GOOD"]:
            return "GOOD"
        elif resistance_ohms <= QUALITY_THRESHOLDS["WARNING"]:
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
