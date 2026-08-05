from app.knowledge_graph.ontology import (
    OntologyRegistry,
    OntologyDefinition,
)


def test_register_ontology():

    registry = OntologyRegistry()

    skill = OntologyDefinition(
        name="skill",
        description="Professional skill entity"
    )

    registry.register(skill)

    result = registry.get("skill")

    assert result is not None
    assert result.name == "skill"



def test_unknown_ontology():

    registry = OntologyRegistry()

    assert registry.exists(
        "occupation"
    ) is False