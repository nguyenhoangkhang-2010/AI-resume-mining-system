import numpy as np


from app.vector_search.pipelines.candidate_embedding_pipeline import (
    CandidateEmbeddingPipeline,
)


class FakeEmbeddingService:


    def generate_embedding(
        self,
        text,
    ):
        return np.array(
            [0.1, 0.2, 0.3]
        )



class FakeRepository:


    def __init__(self):
        self.saved = None


    def add(
        self,
        record,
    ):
        self.saved = record



def test_candidate_embedding_pipeline():


    repository = FakeRepository()


    pipeline = CandidateEmbeddingPipeline(
        FakeEmbeddingService(),
        repository,
    )


    result = pipeline.index_candidate(
        candidate_id="candidate_1",
        text="python developer",
        metadata={
            "name": "Khang"
        }
    )


    assert result.id == "candidate_1"

    assert result.entity_type == "candidate"

    assert repository.saved.id == "candidate_1"

    assert len(result.vector) == 3