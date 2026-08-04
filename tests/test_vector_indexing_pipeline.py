import numpy as np

from app.vector_search.models.vector_record import (
    VectorRecord,
)

from app.vector_search.pipelines.vector_indexing_pipeline import (
    VectorIndexingPipeline,
)

from app.vector_search.services.vector_index_service import (
    VectorIndexService,
)


class FakeVectorRepository:

    def __init__(self):
        self.records = []


    def add(self, record):
        self.records.append(record)



def test_vector_indexing_pipeline():

    repository = FakeVectorRepository()

    service = VectorIndexService(
        repository
    )

    pipeline = VectorIndexingPipeline(
        service
    )


    record = VectorRecord(
        id="candidate_001",
        vector=np.array([0.1, 0.2]),
        entity_type="candidate",
        metadata={}
    )


    pipeline.run(record)


    assert len(repository.records) == 1
    assert repository.records[0].id == "candidate_001"