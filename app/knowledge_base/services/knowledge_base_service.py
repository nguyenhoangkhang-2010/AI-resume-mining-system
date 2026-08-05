from app.knowledge_base.providers.mock_provider import MockTaxonomyProvider
from app.knowledge_base.repositories.taxonomy_repository import TaxonomyRepository


class KnowledgeBaseService:

    def __init__(self):
        self.repository = TaxonomyRepository()
        self.repository.register_provider(
            MockTaxonomyProvider(),
        )

    def load(self):
        return self.repository.load_all()