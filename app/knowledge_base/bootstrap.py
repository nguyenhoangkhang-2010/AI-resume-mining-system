from app.knowledge_base.providers.onet_provider import ONETProvider
from app.knowledge_base.repositories.taxonomy_repository import TaxonomyRepository


def build_taxonomy_repository() -> TaxonomyRepository:
    repository = TaxonomyRepository()

    repository.register_provider(
        ONETProvider(),
    )

    return repository