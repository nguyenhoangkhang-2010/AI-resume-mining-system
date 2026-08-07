import json
from pathlib import Path
from typing import List, Dict

from loguru import logger


class OccupationRepository:

    def __init__(self):

        self.taxonomy_path = (
            Path(__file__)
            .parents[3]
            / "data"
            / "taxonomy"
            / "generated"
            / "occupations.json"
        )

        self.occupation_objects = self._load()

        # Build lookup indexes once.
        self._occupation_lookup = (
            self._build_occupation_lookup()
        )

        self._alias_lookup = (
            self._build_alias_lookup()
        )

    def _load(self):

        if not self.taxonomy_path.exists():
            raise FileNotFoundError(
                f"Occupation taxonomy not found: "
                f"{self.taxonomy_path}"
            )

        with open(
            self.taxonomy_path,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        logger.info(
            f"Loaded {len(data)} occupations from taxonomy."
        )

        return data

    def _build_occupation_lookup(
        self,
    ) -> Dict[str, Dict]:

        lookup = {}

        for occupation in self.occupation_objects:

            name = occupation.get("name")

            if not name:
                continue

            normalized = name.casefold().strip()

            lookup[normalized] = occupation

        logger.info(
            "Built occupation lookup with "
            f"{len(lookup)} entries."
        )

        return lookup

    def _build_alias_lookup(
        self,
    ) -> Dict[str, Dict]:

        lookup = {}

        for occupation in self.occupation_objects:

            for alias in occupation.get(
                "aliases",
                [],
            ):

                normalized = alias.casefold().strip()

                if not normalized:
                    continue

                lookup[normalized] = occupation

        logger.info(
            "Built occupation alias lookup with "
            f"{len(lookup)} entries."
        )

        return lookup

    def get_all_occupations(
        self,
    ) -> List[str]:

        return [
            occupation["name"]
            for occupation in self.occupation_objects
        ]

    def get_all_occupation_objects(
        self,
    ) -> List[Dict]:

        return self.occupation_objects

    def get_occupation(
        self,
        name: str,
    ) -> Dict | None:

        normalized = name.casefold().strip()

        return self._occupation_lookup.get(
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

        occupation = self._occupation_lookup.get(
            normalized
        )

        if occupation:
            return occupation

        return self._alias_lookup.get(
            normalized
        )

    def get_alias_map(
        self,
    ) -> dict[str, str]:

        alias_map = {}

        for occupation in self.occupation_objects:

            canonical = occupation["name"]

            alias_map[
                canonical.casefold()
            ] = canonical

            for alias in occupation.get(
                "aliases",
                []
            ):

                alias_map[
                    alias.casefold()
                ] = canonical

        return alias_map