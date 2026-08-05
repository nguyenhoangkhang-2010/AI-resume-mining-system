from app.knowledge_base.models.taxonomy_entry import TaxonomyEntry
from app.knowledge_base.providers.base_provider import BaseTaxonomyProvider
from app.knowledge_base.services.taxonomy_normalizer import (
    TaxonomyNormalizer,
)


class TaxonomyRepository:

    def __init__(self):
        self._providers: list[BaseTaxonomyProvider] = []
        self._entries: list[TaxonomyEntry] = []

        self._normalizer = TaxonomyNormalizer()

    def register_provider(
        self,
        provider: BaseTaxonomyProvider,
    ) -> None:
        self._providers.append(provider)

    def load_all(self) -> list[TaxonomyEntry]:
        entries: list[TaxonomyEntry] = []

        for provider in self._providers:
            entries.extend(provider.load())

        self._entries = entries

        return entries

    def find_by_name(
        self,
        name: str,
    ) -> list[TaxonomyEntry]:

        normalized_name = (
            self._normalizer.normalize(name)
        )

        return [
            entry
            for entry in self._entries
            if self._normalizer.normalize(
                entry.name
            ) == normalized_name
        ]