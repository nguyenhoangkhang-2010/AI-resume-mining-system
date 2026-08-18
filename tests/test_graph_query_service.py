from app.knowledge_graph.models.node import Node
from app.knowledge_graph.models.edge import Edge

from app.knowledge_graph.repositories.in_memory_graph_repository import (
    InMemoryGraphRepository,
)

from app.knowledge_graph.services.graph_query_service import (
    GraphQueryService,
)


def test_query_related_nodes():

    repo = InMemoryGraphRepository()


    repo.add_node(
        Node(
            id="node_a",
            name="A",
            type="entity",
        )
    )


    repo.add_node(
        Node(
            id="node_b",
            name="B",
            type="entity",
        )
    )


    repo.add_edge(
        Edge(
            source="node_a",
            target="node_b",
            relation="related_to",
        )
    )


    service = GraphQueryService(repo)


    result = service.find_related_nodes(
        "node_a",
        "related_to",
    )


    assert len(result) == 1
    assert result[0].id == "node_b"