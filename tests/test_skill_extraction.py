import pytest
from app.matching.recommendation.recommendation_engine import RecommendationEngine
from app.extraction.skills.skill_extractor import SkillExtractor


def test_analyze_skill_gaps_all_skills_present():
    required = ["Python", "FastAPI", "MongoDB"]
    candidate = ["python", "FASTAPI", "mongodb", "docker"]
    gaps = RecommendationEngine.analyze_skill_gaps(required, candidate)
    assert len(gaps) == 0

def test_analyze_skill_gaps_missing_skills():
    required = ["Python", "FastAPI", "MongoDB"]
    candidate = ["Python", "Docker"]
    gaps = RecommendationEngine.analyze_skill_gaps(required, candidate)
    assert len(gaps) == 2
    assert "FastAPI" in gaps
    assert "MongoDB" in gaps
    
def test_semantic_fallback():

    extractor = SkillExtractor()

    skills = extractor.extract(
        "Worked with Torch."
    )

    assert "pytorch" in skills
    
def test_unknown_skill():

    extractor = SkillExtractor()

    skills = extractor.extract(
        "I love pizza."
    )

    assert skills == []