from typing import List

from app.vector_search.models.vector_record import VectorRecord

from app.vector_search.services.batch_vector_index_service import (
    BatchVectorIndexService,
)


class BatchVectorIndexingPipeline:
    """
    Pipeline for batch vector indexing.
    """

    def __init__(
        self,
        service: BatchVectorIndexService,
    ):
        self.service = service


    def run(
        self,
        records: List[VectorRecord],
    ) -> None:

        self.service.index_many(records)