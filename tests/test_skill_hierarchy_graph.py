from app.knowledge_graph.repositories.in_memory_graph_repository import (
    InMemoryGraphRepository,
)

from app.knowledge_graph.services.hierarchy_service import (
    HierarchyService,
)


def test_create_generic_parent_relation():

    repo = InMemoryGraphRepository()

    service = HierarchyService(repo)

    service.add_parent_relation(
        "entity_parent",
        "entity_child",
    )

    edges = repo.get_edges()

    assert len(edges) == 1

    edge = edges[0]

    assert edge.source == "entity_parent"
    assert edge.target == "entity_child"
    assert edge.relation == "parent_of"