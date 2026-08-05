from app.knowledge_graph.models.node import Node


class OccupationNode(Node):
    """
    Represents an occupation entity.

    Example:
    Data Engineer
    Software Developer
    Data Scientist
    """

    node_type: str = "occupation"

    industry: str | None = None

    description: str | None = None