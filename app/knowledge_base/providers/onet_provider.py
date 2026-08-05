from app.knowledge_base.models.taxonomy_entry import TaxonomyEntry
from app.knowledge_base.providers.base_provider import BaseTaxonomyProvider


class ONETProvider(BaseTaxonomyProvider):
    """
    Loads taxonomy data from the O*NET dataset.
    """

    def load(self) -> list[TaxonomyEntry]:
        raise NotImplementedError