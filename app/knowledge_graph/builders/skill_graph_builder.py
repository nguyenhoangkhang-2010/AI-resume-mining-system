from app.knowledge_graph.models.node import Node
from app.knowledge_graph.models.edge import Edge

from app.knowledge_graph.repositories.graph_repository import (
    GraphRepository,
)

from app.knowledge_graph.ontology.definitions import (
    RelationshipTypes,
)


class SkillGraphBuilder:
    """
    Builds skill hierarchy relationships.

    Example:

    AI
      |
      parent_of
      |
    Machine Learning
    """

    def __init__(
        self,
        repository: GraphRepository,
    ):
        self.repository = repository


    def add_skill(
        self,
        skill_id: str,
        name: str,
        properties: dict | None = None,
    ) -> None:

        node = Node(
            id=skill_id,
            type="skill",
            name=name,
            properties=properties or {},
        )

        self.repository.add_node(
            node
        )


    def link_parent_skill(
        self,
        parent_skill_id: str,
        child_skill_id: str,
    ) -> None:

        edge = Edge(
            source=parent_skill_id,
            target=child_skill_id,
            relation=RelationshipTypes.PARENT_OF,
        )

        self.repository.add_edge(
            edge
        )