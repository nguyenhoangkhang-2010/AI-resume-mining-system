from app.knowledge_graph.models.node import Node
from app.knowledge_graph.models.edge import Edge
from app.knowledge_graph.repositories.graph_repository import GraphRepository
from app.knowledge_graph.ontology.definitions import RelationshipTypes


class OccupationGraphBuilder:

    def __init__(
        self,
        repository: GraphRepository
    ):
        self.repository = repository


    def add_occupation(
        self,
        occupation_id: str,
        name: str,
    ):

        node = Node(
            id=occupation_id,
            type="occupation",
            name=name,
            properties={}
        )

        self.repository.add_node(node)


    def link_skill(
        self,
        occupation_id: str,
        skill_id: str,
    ):

        edge = Edge(
            source=occupation_id,
            target=skill_id,
            relation=RelationshipTypes.REQUIRES_SKILL
        )

        self.repository.add_edge(edge)