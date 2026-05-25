from adaptive_backend.domain.enums import BrainState
from adaptive_backend.services.engines.raaga_recommendation_engine import RaagaRecommendationEngine
from adaptive_backend.utils.time_utils import get_day_part


class PlaybackDecisionEngine:
    def __init__(self):
        self.recommender = RaagaRecommendationEngine()

    def decide(self, target_state: BrainState, tempo):
        day_part = get_day_part()
        return self.recommender.choose(target_state, day_part, tempo)
