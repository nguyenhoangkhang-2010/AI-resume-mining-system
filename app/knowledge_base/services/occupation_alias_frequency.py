from collections import Counter, defaultdict

from app.knowledge_base.models.occupation_entry import (
    OccupationEntry,
)


class OccupationAliasFrequencyAnalyzer:

    def analyze(
        self,
        occupations: list[OccupationEntry],
    ) -> Counter[str]:

        return Counter(
            alias.casefold().strip()
            for occupation in occupations
            for alias in occupation.aliases
            if alias.strip()
        )

    def occupation_coverage(
        self,
        occupations: list[OccupationEntry],
    ) -> dict[str, int]:

        coverage: dict[str, set[str]] = defaultdict(set)

        for occupation in occupations:

            occupation_id = occupation.id

            for alias in occupation.aliases:

                normalized = alias.casefold().strip()

                if not normalized:
                    continue

                coverage[normalized].add(
                    occupation_id
                )

        return {
            alias: len(occupation_ids)
            for alias, occupation_ids in coverage.items()
        }
        
    def token_coverage(
        self,
        occupations: list[OccupationEntry],
    ) -> dict[str, int]:

        coverage: dict[str, set[str]] = defaultdict(set)

        for occupation in occupations:

            for alias in occupation.aliases:

                tokens = (
                    alias
                    .casefold()
                    .split()
                )

                for token in tokens:

                    coverage[token].add(
                        occupation.id
                    )

        return {
            token: len(ids)
            for token, ids in coverage.items()
        }