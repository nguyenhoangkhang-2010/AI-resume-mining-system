from app.knowledge_graph.services.occupation_graph_builder import (
    OccupationGraphBuilder
)

from app.knowledge_graph.repositories.in_memory_graph_repository import (
    InMemoryGraphRepository
)


def test_create_occupation_skill_relation():

    repo = InMemoryGraphRepository()

    builder = OccupationGraphBuilder(repo)

    builder.add_occupation(
        "data_engineer",
        "Data Engineer"
    )

    builder.link_skill(
        "data_engineer",
        "python"
    )

    nodes = repo.get_all_nodes()

    assert len(nodes) == 1

    assert nodes[0].id == "data_engineer"
    assert nodes[0].name == "Data Engineer"

    assert len(repo._edges) == 1

    assert repo._edges[0].source == "data_engineer"
    assert repo._edges[0].target == "python"
    assert repo._edges[0].relation == "requires_skill"