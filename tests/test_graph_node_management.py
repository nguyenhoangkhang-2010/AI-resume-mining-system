from app.knowledge_graph.models.node import Node

from app.knowledge_graph.repositories import (
    InMemoryGraphRepository,
)

from app.knowledge_graph.services.graph_service import (
    GraphService,
)


def test_add_and_get_node():

    repository = InMemoryGraphRepository()

    service = GraphService(
        repository
    )


    node = Node(
        id="python",
        name="Python",
        type="skill",
        properties={
            "category": "programming_language"
        }
    )


    service.add_node(node)


    result = service.get_node(
        "python"
    )


    assert result is not None
    assert result.name == "Python"