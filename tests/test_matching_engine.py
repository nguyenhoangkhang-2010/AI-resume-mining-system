import pytest
from datetime import datetime
from app.matching.similarity.similarity_engine import SimilarityEngine
from app.matching.ranking.ranking_engine import RankingEngine
from app.models.job import JobModel
from app.models.candidate import CandidateModel


def test_normalize_score():
    engine = SimilarityEngine()
    assert engine.normalize_score(0.854) == 85.4
    assert engine.normalize_score(-0.1) == 0.0
    assert engine.normalize_score(1.2) == 100.0

def test_ranking_engine_filtering_and_sorting():
    job = JobModel(title="Test Job", description="Test", required_skills=["Python"], created_at=datetime.utcnow())
    job.id = "job1"
    
    # Create mock candidates
    cand1 = CandidateModel(resume_id="r1", personal_info={"name": "A"}, skills=["Python"], faiss_id=1)
    cand2 = CandidateModel(resume_id="r2", personal_info={"name": "B"}, skills=["Java"], faiss_id=2)
    cand3 = CandidateModel(resume_id="r3", personal_info={"name": "C"}, skills=["Python"], faiss_id=3)
    
    candidates = [cand1, cand2, cand3]
    
    # Mock FAISS results
    faiss_results = [
        {"faiss_id": 1, "similarity_score": 0.8},
        {"faiss_id": 2, "similarity_score": 0.5},
        {"faiss_id": 3, "similarity_score": 0.9}
    ]
    
    engine = RankingEngine()
    response = engine.rank_candidates(job, candidates, faiss_results)
    
    results = response.results
    assert len(results) == 2 # cand2 is filtered out
    
    # Check sorting descending
    assert results[0].similarity_score > results[1].similarity_score