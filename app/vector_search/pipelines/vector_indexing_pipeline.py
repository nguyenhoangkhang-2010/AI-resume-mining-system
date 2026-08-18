from app.vector_search.models.vector_record import VectorRecord
from app.vector_search.services.vector_index_service import (
    VectorIndexService,
)


class VectorIndexingPipeline:
    """
    Pipeline for converting entities into indexed vectors.
    """

    def __init__(
        self,
        index_service: VectorIndexService,
    ):
        self.index_service = index_service


    def run(
        self,
        record: VectorRecord,
    ) -> None:

        self.index_service.index(record)