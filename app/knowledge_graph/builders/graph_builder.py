from abc import ABC, abstractmethod

from app.knowledge_graph.repositories.graph_repository import (
    GraphRepository,
)


class GraphBuilder(ABC):
    """
    Abstract graph builder.

    Converts external knowledge sources
    into graph structures.

    Does not contain domain-specific logic.
    """


    def __init__(
        self,
        repository: GraphRepository,
    ):
        self.repository = repository


    @abstractmethod
    def build(
        self,
        source,
    ) -> None:
        pass