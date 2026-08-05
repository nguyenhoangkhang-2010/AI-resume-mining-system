from app.knowledge_graph.models.node import Node
from app.knowledge_graph.models.edge import Edge


def test_create_generic_node():

    node = Node(
        id="python",
        name="Python",
        type="skill",
        properties={
            "category": "programming_language"
        }
    )

    assert node.id == "python"
    assert node.type == "skill"



def test_create_generic_edge():

    edge = Edge(
        source="data_engineer",
        target="python",
        relation="requires_skill"
    )

    assert edge.source == "data_engineer"
    assert edge.relation == "requires_skill"