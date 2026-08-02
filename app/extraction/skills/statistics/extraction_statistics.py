from collections import Counter

from app.models.skill_match import SkillMatch


class ExtractionStatistics:

    def summarize(
        self,
        matches: list[SkillMatch],
    ) -> dict:

        if not matches:
            return {
                "total": 0,
                "average_confidence": 0.0,
                "sources": {},
            }

        counter = Counter(
            match.source
            for match in matches
        )

        average = sum(
            match.confidence
            for match in matches
        ) / len(matches)

        return {
            "total": len(matches),
            "average_confidence": round(
                average,
                3,
            ),
            "sources": dict(counter),
        }