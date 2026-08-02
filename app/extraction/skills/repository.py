import json
from pathlib import Path
from typing import List, Dict
from loguru import logger


class SkillRepository:

    def __init__(self):
        self.taxonomy_path = (
            Path(__file__)
            .parents[3]
            / "data"
            / "taxonomy"
            / "generated"
            / "skills.json"
        )
        self.skill_objects = self._load()


    def _load(self):
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
        logger.info(
            f"Loaded {len(data)} skills from taxonomy."
        )
        return data


    def get_all_skills(self) -> List[str]:
        return [
            skill["name"]
            for skill in self.skill_objects
        ]


    def get_all_skill_objects(self) -> List[Dict]:
        return self.skill_objects
    
    def get_alias_map(self) -> dict[str, str]:
        alias_map = {}

        for skill in self.skill_objects:
            canonical = skill["name"]

            alias_map[canonical.lower()] = canonical

            for alias in skill.get("aliases", []):
                alias_map[alias.lower()] = canonical

        return alias_map