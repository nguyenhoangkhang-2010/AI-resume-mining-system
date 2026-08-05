from app.knowledge_graph.models.node import Node
from app.knowledge_graph.models.edge import Edge

from app.knowledge_graph.repositories.in_memory_graph_repository import (
    InMemoryGraphRepository,
)

from app.knowledge_graph.services.graph_traversal_service import (
    GraphTraversalService,
)


def test_graph_traversal_depth():

    repo = InMemoryGraphRepository()


    repo.add_node(
        Node(
            id="a",
            name="A",
            type="entity",
        )
    )

    repo.add_node(
        Node(
            id="b",
            name="B",
            type="entity",
        )
    )

    repo.add_node(
        Node(
            id="c",
            name="C",
            type="entity",
        )
    )


    repo.add_edge(
        Edge(
            source="a",
            target="b",
            relation="related_to",
        )
    )


    repo.add_edge(
        Edge(
            source="b",
            target="c",
            relation="related_to",
        )
    )


    service = GraphTraversalService(repo)


    result = service.traverse(
        "a",
        depth=2,
    )


    ids = [
        node.id
        for node in result
    ]


    assert "b" in ids
    assert "c" in ids