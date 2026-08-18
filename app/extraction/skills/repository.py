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

        # Build lookup indexes once.
        self._skill_lookup = self._build_skill_lookup()
        self._alias_lookup = self._build_alias_lookup()

    def _load(self):

        if not self.taxonomy_path.exists():
            raise FileNotFoundError(
                f"Skill taxonomy not found: {self.taxonomy_path}"
            )

        with open(
            self.taxonomy_path,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        logger.info(
            f"Loaded {len(data)} skills from taxonomy."
        )

        return data

    def _build_skill_lookup(self) -> Dict[str, Dict]:

        lookup = {}

        for skill in self.skill_objects:

            name = skill.get("name")

            if not name:
                continue

            normalized = name.casefold().strip()

            lookup[normalized] = skill

        logger.info(
            f"Built skill lookup with {len(lookup)} entries."
        )

        return lookup

    def _build_alias_lookup(self) -> Dict[str, Dict]:

        lookup = {}

        for skill in self.skill_objects:

            canonical_name = skill.get("name")

            if not canonical_name:
                continue

            for alias in skill.get("aliases", []):

                normalized = alias.casefold().strip()

                if not normalized:
                    continue

                lookup[normalized] = skill

        logger.info(
            f"Built alias lookup with {len(lookup)} entries."
        )

        return lookup

    def get_all_skills(self) -> List[str]:

        return [
            skill["name"]
            for skill in self.skill_objects
        ]

    def get_all_skill_objects(self) -> List[Dict]:

        return self.skill_objects

    def get_skill(
        self,
        name: str,
    ) -> Dict | None:

        normalized = name.casefold().strip()

        return self._skill_lookup.get(
            normalized
        )

    def get_by_alias(
        self,
        alias: str,
    ) -> Dict | None:

        normalized = alias.casefold().strip()

        return self._alias_lookup.get(
            normalized
        )

    def find(
        self,
        text: str,
    ) -> Dict | None:

        normalized = text.casefold().strip()

        skill = self._skill_lookup.get(
            normalized
        )

        if skill:
            return skill

        return self._alias_lookup.get(
            normalized
        )

    def get_alias_map(self) -> dict[str, str]:

        alias_map = {}

        for skill in self.skill_objects:

            canonical = skill["name"]

            alias_map[
                canonical.casefold()
            ] = canonical

            for alias in skill.get(
                "aliases",
                []
            ):

                alias_map[
                    alias.casefold()
                ] = canonical

        return alias_map