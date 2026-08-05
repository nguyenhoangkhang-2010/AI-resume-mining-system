from pathlib import Path
import csv

from app.knowledge_base.models.taxonomy_entry import TaxonomyEntry
from app.knowledge_base.providers.base_provider import BaseTaxonomyProvider


class ONETProvider(BaseTaxonomyProvider):
    """
    Provider for loading O*NET taxonomy data.

    Supports:
    - essential skills
    - software skills
    - knowledge
    - abilities
    """

    def __init__(
        self,
        csv_paths: dict[str, str | Path] | None = None,
    ):
        if csv_paths is None:
            root = (
                Path(__file__).resolve().parents[3]
                / "data"
                / "onet"
                / "raw"
            )

            csv_paths = {
                "essential_skill": root / "essential_skills.csv",
                "software_skill": root / "software_skills.csv",
                "knowledge": root / "knowledge.csv",
                "ability": root / "abilities.csv",
                "work_activity": root / "work_activities.csv",
            }

        self.csv_paths = {
            category: Path(path)
            for category, path in csv_paths.items()
        }

    def load(self) -> list[TaxonomyEntry]:
        entries: list[TaxonomyEntry] = []

        for category, path in self.csv_paths.items():
            entries.extend(
                self._load_entries(
                    path,
                    category,
                )
            )

        return entries

    def _load_entries(
        self,
        csv_path: Path,
        category: str,
    ) -> list[TaxonomyEntry]:

        entries: list[TaxonomyEntry] = []

        with csv_path.open(
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                if category == "software_skill":
                    name = row["Workplace Example"]
                else:
                    name = row["Element Name"]

                entries.append(
                    TaxonomyEntry(
                        id=row["Element ID"],
                        name=name,
                        category=category,
                        aliases=[],
                    )
                )

        return entries