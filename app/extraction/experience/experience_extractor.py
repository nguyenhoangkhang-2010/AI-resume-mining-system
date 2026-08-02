import re
from typing import List, Dict, Any

from loguru import logger


class ExperienceExtractor:

    YEARS_PATTERN = (
        r"(\d+)"
        r"\+?\s*"
        r"(years|yrs)"
        r"\s*(of)?"
        r"\s*(experience|exp)"
    )


    RANGE_PATTERN = (
        r"(\d{4})"
        r"\s*-\s*"
        r"(\d{4}|present)"
    )


    ROLE_KEYWORDS = [
        "software engineer",
        "backend developer",
        "frontend developer",
        "data analyst",
        "data scientist",
        "machine learning engineer",
        "ai engineer",
        "intern",
        "developer",
    ]


    @staticmethod
    def extract(
        text: str
    ) -> List[Dict[str, Any]]:
        if not text:
            return []
        logger.debug(
            "Starting experience extraction."
        )
        text_lower = text.lower()
        result = {
            "total_years_extracted": 0,
            "experience_periods": []
        }

        # -------------------------
        # Years of experience
        # -------------------------
        years_matches = re.findall(
            ExperienceExtractor.YEARS_PATTERN,
            text_lower
        )
        if years_matches:
            result["total_years_extracted"] = max(
                int(year[0])
                for year in years_matches
            )

        # -------------------------
        # Work periods
        # -------------------------
        periods = re.findall(
            ExperienceExtractor.RANGE_PATTERN,
            text_lower
        )

        # -------------------------
        # Role extraction
        # -------------------------
        roles = []
        for role in (
            ExperienceExtractor.ROLE_KEYWORDS
        ):
            if role in text_lower:
                roles.append(
                    role.title()
                )

        # -------------------------
        # Company heuristic
        # -------------------------
        companies = []
        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]
        for line in lines:
            if any(
                role in line.lower()
                for role in ExperienceExtractor.ROLE_KEYWORDS
            ):
                continue
            if re.search(
                r"[A-Z][a-z]+",
                line
            ):
                companies.append(
                    line
                )

        # -------------------------
        # Build experience records
        # -------------------------
        for start, end in periods:
            record = {
                "start": start,
                "end": end
            }
            if companies:
                record["company"] = (
                    companies[0]
                )
            if roles:
                record["role"] = (
                    roles[0]
                )
            result[
                "experience_periods"
            ].append(
                record
            )

        # If no period found
        # but role exists
        if (
            not result["experience_periods"]
            and roles
        ):
            result[
                "experience_periods"
            ].append(
                {
                    "role": roles[0]
                }
            )
        logger.debug(
            f"Experience extracted: {result}"
        )
        return [
            result
        ]