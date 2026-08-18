import numpy as np

from app.vector_search.models.vector_record import (
    VectorRecord,
)

from app.vector_search.services.batch_vector_index_service import (
    BatchVectorIndexService,
)

from app.vector_search.pipelines.batch_vector_indexing_pipeline import (
    BatchVectorIndexingPipeline,
)


class FakeVectorRepository:

    def __init__(self):
        self.records = []


    def add(self, record):
        self.records.append(record)



def test_batch_vector_indexing_pipeline():

    repository = FakeVectorRepository()

    service = BatchVectorIndexService(
        repository
    )

    pipeline = BatchVectorIndexingPipeline(
        service
    )

    records = [
        VectorRecord(
            id="skill_python",
            vector=np.array([0.1]),
            entity_type="skill",
            metadata={}
        ),
        VectorRecord(
            id="skill_sql",
            vector=np.array([0.2]),
            entity_type="skill",
            metadata={}
        )
    ]

    pipeline.run(records)

    assert len(repository.records) == 2