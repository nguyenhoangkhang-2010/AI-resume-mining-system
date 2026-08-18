from app.services.matching_service import MatchingService


def get_matching_service() -> MatchingService:
    return MatchingService()