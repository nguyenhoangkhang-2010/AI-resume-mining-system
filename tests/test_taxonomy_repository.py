from app.knowledge_base.repositories.taxonomy_repository import (
    TaxonomyRepository,
)

from app.knowledge_base.models.taxonomy_entry import (
    TaxonomyEntry,
)


class FakeProvider:

    def load(self):
        return [
            TaxonomyEntry(
                id="1",
                name="Python",
                category="skill",
                aliases=[],
            ),
            TaxonomyEntry(
                id="2",
                name="SQL",
                category="skill",
                aliases=[],
            ),
        ]


def test_find_by_name():

    repository = TaxonomyRepository()

    repository.register_provider(
        FakeProvider()
    )

    repository.load_all()

    result = repository.find_by_name(
        " python "
    )

    assert len(result) == 1
    assert result[0].name == "Python"