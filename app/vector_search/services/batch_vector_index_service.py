from typing import List

from app.vector_search.models.vector_record import VectorRecord
from app.vector_search.repositories.vector_repository import (
    VectorRepository,
)


class BatchVectorIndexService:
    """
    Handles batch insertion of vector records.
    """

    def __init__(
        self,
        repository: VectorRepository,
    ):
        self.repository = repository


    def index_many(
        self,
        records: List[VectorRecord],
    ) -> None:

        for record in records:
            self.repository.add(record)