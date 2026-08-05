from app.knowledge_base.providers.mock_provider import MockTaxonomyProvider
from app.knowledge_base.repositories.taxonomy_repository import TaxonomyRepository


def test_repository_loads_registered_provider():
    repository = TaxonomyRepository()

    repository.register_provider(
        MockTaxonomyProvider(),
    )

    entries = repository.load_all()

    assert len(entries) == 2
    assert entries[0].name == "Python"