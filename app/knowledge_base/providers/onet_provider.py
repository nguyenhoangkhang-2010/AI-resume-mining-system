from pathlib import Path
import csv

from app.knowledge_base.models.taxonomy_entry import TaxonomyEntry
from app.knowledge_base.providers.base_provider import BaseTaxonomyProvider


class ONETProvider(BaseTaxonomyProvider):
    """
    Provider for loading O*NET taxonomy data.

    Currently supports loading software skills only.
    """

    def __init__(self, csv_path: str | Path | None = None):
        if csv_path is None:
            csv_path = (
                Path(__file__).resolve().parents[3]
                / "data"
                / "onet"
                / "raw"
                / "essential_skills.csv"
            )

        self.csv_path = Path(csv_path)

    def load(self) -> list[TaxonomyEntry]:
        skills: list[TaxonomyEntry] = []

        with self.csv_path.open(
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:
                skills.append(
                    TaxonomyEntry(
                        id=row["Element ID"],
                        name=row["Element Name"],
                        category="essential_skill",
                        aliases=[]
                    )
                )

        return skills