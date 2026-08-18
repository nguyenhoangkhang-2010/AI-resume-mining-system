import re


class RequirementExtractor:

    SECTION_HEADERS = [
        "requirements",
        "qualification",
        "qualifications",
        "required qualifications",
        "minimum qualifications",
        "preferred qualifications",
    ]

    @staticmethod
    def extract(
        text: str,
    ) -> str | None:

        if not text:
            return None

        lines = [
            line.strip()
            for line in text.splitlines()
        ]

        collecting = False

        requirements = []

        stop_headers = {
            "responsibilities",
            "benefits",
            "about us",
            "preferred qualifications",
            "preferred skills",
            "nice to have",
        }

        for line in lines:

            if not line:
                continue

            lower = line.lower()

            if lower in RequirementExtractor.SECTION_HEADERS:
                collecting = True
                continue

            if collecting and lower in stop_headers:
                break

            if collecting:
                requirements.append(line)

        if not requirements:
            return None

        return "\n".join(requirements)