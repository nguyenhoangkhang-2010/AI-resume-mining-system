import json
from pathlib import Path
from typing import List
from loguru import logger


class SkillRepository:

    def __init__(self):
        self.taxonomy_path = (
            Path(__file__)
            .parents[3]
            / "data"
            / "taxonomy"
            / "skills.json"
        )

        self.skills = self._load()


    def _load(self) -> List[str]:

        if not self.taxonomy_path.exists():
            raise FileNotFoundError(
                f"Skill taxonomy not found: {self.taxonomy_path}"
            )

        with open(
            self.taxonomy_path,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)


        skills = self._flatten(data)

        logger.info(
            f"Loaded {len(skills)} skills from taxonomy."
        )

        return skills



    def _flatten(self, data) -> List[str]:

        skills = []


        if isinstance(data, dict):

            for value in data.values():
                skills.extend(
                    self._flatten(value)
                )


        elif isinstance(data, list):

            for item in data:

                if isinstance(item, str):
                    skills.append(item)

                elif isinstance(item, (dict, list)):
                    skills.extend(
                        self._flatten(item)
                    )


        return skills



    def get_all_skills(self):
        return self.skills