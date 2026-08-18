from app.knowledge_graph.models.node import Node


class PromptBuilder:
    """
    Build prompts for LLM-based knowledge graph enrichment.

    Prompt generation is isolated so different prompt
    strategies can be introduced without modifying
    the enrichment pipeline.
    """

    def build(
        self,
        node: Node,
    ) -> str:

        return f"""
You are an ontology expert.

Analyze the following knowledge graph entity.

Entity Name:
{node.name}

Entity Type:
{node.type}

Existing Properties:
{node.properties}

Return concise metadata describing:

- summary
- related concepts
- important keywords

Output plain text only.
"""