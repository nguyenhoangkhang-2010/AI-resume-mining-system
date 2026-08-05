from app.knowledge_base.models.taxonomy_entry import TaxonomyEntry
from app.knowledge_base.providers.base_provider import BaseTaxonomyProvider


class MockTaxonomyProvider(BaseTaxonomyProvider):

    def load(self) -> list[TaxonomyEntry]:
        return [
            TaxonomyEntry(
                id="skill_python",
                name="Python",
                category="skill",
                aliases=["python3"],
            ),
            TaxonomyEntry(
                id="skill_sql",
                name="SQL",
                category="skill",
                aliases=["mysql"],
            ),
        ]