from app.vector_search.models.vector_record import VectorRecord
from app.vector_search.repositories.vector_repository import (
    VectorRepository,
)


class VectorIndexService:
    """
    Service responsible for indexing entities into vector storage.
    """

    def __init__(
        self,
        repository: VectorRepository,
    ):
        self.repository = repository


    def index(
        self,
        record: VectorRecord,
    ) -> None:

        self.repository.add(record)