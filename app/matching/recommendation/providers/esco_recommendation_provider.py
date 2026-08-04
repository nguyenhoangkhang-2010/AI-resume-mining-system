import json
from pathlib import Path

from app.matching.recommendation.providers.recommendation_provider import (
    RecommendationProvider,
)

from app.schemas.recommendation_schema import RecommendationItem


class EscoRecommendationProvider(
    RecommendationProvider,
):

    def __init__(
        self,
        data_path: str = "data/esco/processed/esco_skills.json",
    ):
        self.data_path = Path(data_path)

        self.skills = self._load_skills()


    def _load_skills(self) -> list[dict]:

        if not self.data_path.exists():
            raise FileNotFoundError(
                f"ESCO dataset not found: {self.data_path}"
            )

        with open(
            self.data_path,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)


    def get_recommendations(
        self,
        skill: str,
    ) -> list[RecommendationItem]:

        skill_lower = skill.lower()

        results = []

        for esco_skill in self.skills:

            name = esco_skill.get(
                "name",
                "",
            ).lower()


            aliases = [
                alias.lower()
                for alias in esco_skill.get(
                    "aliases",
                    []
                )
            ]


            if (
                skill_lower == name
                or skill_lower in aliases
            ):

                results.append(
                    RecommendationItem(
                        type="skill",
                        title=esco_skill["name"],
                        priority="medium",
                        source="ESCO",
                    )
                )


        return results