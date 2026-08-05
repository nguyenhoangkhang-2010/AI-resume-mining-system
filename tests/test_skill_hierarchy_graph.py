from app.knowledge_graph.repositories.in_memory_graph_repository import (
    InMemoryGraphRepository,
)

from app.knowledge_graph.builders.skill_graph_builder import (
    SkillGraphBuilder,
)


def test_create_skill_hierarchy():

    repo = InMemoryGraphRepository()

    builder = SkillGraphBuilder(repo)


    builder.add_skill(
        "ai",
        "Artificial Intelligence"
    )


    builder.add_skill(
        "ml",
        "Machine Learning"
    )


    builder.link_parent_skill(
        "ai",
        "ml"
    )


    assert len(repo.get_all_nodes()) == 2

    assert len(repo._edges) == 1

    edge = repo._edges[0]

    assert edge.source == "ai"
    assert edge.target == "ml"
    assert edge.relation == "parent_of"