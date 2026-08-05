from app.knowledge_base.models.taxonomy_entry import TaxonomyEntry
from app.knowledge_base.providers.base_provider import BaseTaxonomyProvider


class TaxonomyRepository:

    def __init__(self):
        self._providers: list[BaseTaxonomyProvider] = []

    def register_provider(
        self,
        provider: BaseTaxonomyProvider,
    ) -> None:
        self._providers.append(provider)

    def load_all(self) -> list[TaxonomyEntry]:
        entries: list[TaxonomyEntry] = []

        for provider in self._providers:
            entries.extend(provider.load())

        return entries