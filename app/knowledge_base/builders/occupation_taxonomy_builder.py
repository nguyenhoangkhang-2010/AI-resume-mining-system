from pathlib import Path
import json
from dataclasses import asdict

from app.knowledge_base.providers.onet_occupation_provider import (
    ONETOccupationProvider
)


class OccupationTaxonomyBuilder:

    def __init__(
        self,
        provider=None,
        output_path: str | Path | None = None
    ):

        self.provider = (
            provider
            if provider
            else ONETOccupationProvider()
        )

        if output_path is None:
            self.output_path = (
                Path(__file__)
                .resolve()
                .parents[3]
                / "data"
                / "taxonomy"
                / "generated"
                / "occupations.json"
            )
        else:
            self.output_path = Path(output_path)


    def build(self):

        occupations = self.provider.load()

        data = [
            asdict(occupation)
            for occupation in occupations
        ]


        self.output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )


        with self.output_path.open(
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False
            )


        return len(data)