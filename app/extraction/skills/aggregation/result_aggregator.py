from collections import defaultdict

from app.models.skill_match import SkillMatch


class ResultAggregator:

    def aggregate(
        self,
        matches: list[SkillMatch],
    ) -> list[SkillMatch]:

        grouped = defaultdict(list)

        for match in matches:
            grouped[match.skill].append(match)

        results = []

        for skill, items in grouped.items():

            best = max(
                items,
                key=lambda item: item.confidence,
            )

            results.append(best)

        return sorted(
            results,
            key=lambda item: item.skill,
        )