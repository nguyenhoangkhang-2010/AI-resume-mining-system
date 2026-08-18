from pathlib import Path
import csv

from app.knowledge_base.models.occupation_entry import (
    OccupationEntry
)

from app.knowledge_base.providers.base_provider import (
    BaseTaxonomyProvider
)

from app.knowledge_base.services.occupation_alias_generator import (
    OccupationAliasGenerator
)


from app.knowledge_base.services.occupation_alias_filter import (
    OccupationAliasFilter
)


from app.knowledge_base.services.occupation_alias_frequency import (
    OccupationAliasFrequencyAnalyzer
)


class ONETOccupationProvider(BaseTaxonomyProvider):

    def __init__(
        self,
        csv_path: str | Path | None = None,
        job_titles_path: str | Path | None = None
    ):

        root = (
            Path(__file__)
            .resolve()
            .parents[3]
            / "data"
            / "onet"
            / "raw"
        )

        if csv_path is None:
            csv_path = root / "occupation_data.csv"

        if job_titles_path is None:
            job_titles_path = root / "job_titles.csv"


        self.csv_path = Path(csv_path)
        
        self.job_title_path = (
            Path(__file__)
            .resolve()
            .parents[3]
            / "data"
            / "onet"
            / "raw"
            / "job_titles.csv"
        )

        self.alias_generator = (
            OccupationAliasGenerator()
        )

        self.alias_filter = (
            OccupationAliasFilter()
        )

        self.job_titles_path = Path(
            job_titles_path
        )

    def _load_job_titles(self):

        titles = {}
        with self.job_title_path.open(
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:
            reader = csv.DictReader(file)
            for row in reader:
                code = row["O*NET-SOC Code"]
                title = row["Job Title"]
                if not title:
                    continue
                titles.setdefault(
                    code,
                    []
                ).append(title)
        return titles

    def load(self):

        occupations = []

        job_titles = (
            self._load_job_titles()
        )


        with self.csv_path.open(
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:


            reader = csv.DictReader(file)


            for row in reader:


                code = row["O*NET-SOC Code"]


                raw_aliases = (
                    job_titles.get(
                        code,
                        []
                    )
                )


                aliases = (
                    self.alias_generator.generate(
                        row["Title"],
                        raw_aliases
                    )
                )


                occupations.append(
                    OccupationEntry(
                        id=code,
                        name=row["Title"],
                        description=row.get(
                            "Description",
                            ""
                        ),
                        aliases=aliases,
                        source="onet"
                    )
                )


        analyzer = (
            OccupationAliasFrequencyAnalyzer()
        )


        coverage = (
            analyzer.occupation_coverage(
                occupations
            )
        )

        filtered = []

        for occupation in occupations:

            occupation.aliases = (
                self.alias_filter.filter(
                    occupation.name,
                    occupation.aliases,
                    coverage,
                    len(occupations)
                )
            )

            filtered.append(
                occupation
            )

        return filtered
    
    def load_raw(self):

        occupations = []

        job_titles = self._load_job_titles()

        with self.csv_path.open(
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                code = row["O*NET-SOC Code"]

                raw_aliases = job_titles.get(
                    code,
                    []
                )

                aliases = self.alias_generator.generate(
                    row["Title"],
                    raw_aliases
                )

                occupations.append(
                    OccupationEntry(
                        id=code,
                        name=row["Title"],
                        description=row.get(
                            "Description",
                            ""
                        ),
                        aliases=aliases,
                        source="onet"
                    )
                )

        return occupations