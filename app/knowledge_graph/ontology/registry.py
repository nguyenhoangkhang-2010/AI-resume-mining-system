from app.knowledge_graph.ontology.definitions import (
    OntologyDefinition,
)


class OntologyRegistry:
    """
    Registry for ontology definitions.

    Ontology is data-driven and can be extended
    without modifying graph models.
    """

    def __init__(self):
        self._definitions: dict[str, OntologyDefinition] = {}


    def register(
        self,
        definition: OntologyDefinition,
    ) -> None:

        self._definitions[
            definition.name
        ] = definition


    def get(
        self,
        name: str,
    ) -> OntologyDefinition | None:

        return self._definitions.get(name)


    def exists(
        self,
        name: str,
    ) -> bool:

        return name in self._definitions