from collections import defaultdict


class OccupationAliasStatistics:


    def build_frequency(
        self,
        occupations
    ):
        frequency = defaultdict(int)
        for occupation in occupations:
            unique_aliases = set(
                occupation.aliases
            )
            for alias in unique_aliases:
                normalized = (
                    alias
                    .casefold()
                    .strip()
                )
                if normalized:
                    frequency[normalized] += 1
        return dict(frequency)