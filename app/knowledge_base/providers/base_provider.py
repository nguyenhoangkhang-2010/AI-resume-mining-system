from abc import ABC, abstractmethod

from app.knowledge_base.models.taxonomy_entry import TaxonomyEntry


class BaseTaxonomyProvider(ABC):

    @abstractmethod
    def load(self) -> list[TaxonomyEntry]:
        pass