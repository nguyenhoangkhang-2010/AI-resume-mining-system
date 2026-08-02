class ResponsibilityExtractor:

    SECTION_HEADERS = [
        "responsibilities",
        "responsibility",
        "key responsibilities",
        "job responsibilities",
        "duties",
        "what you'll do",
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

        responsibilities = []

        stop_headers = {
            "requirements",
            "qualifications",
            "required qualifications",
            "preferred qualifications",
            "benefits",
            "about us",
        }

        for line in lines:

            if not line:
                continue

            lower = line.lower()

            if lower in ResponsibilityExtractor.SECTION_HEADERS:
                collecting = True
                continue

            if collecting and lower in stop_headers:
                break

            if collecting:
                responsibilities.append(line)

        if not responsibilities:
            return None

        return "\n".join(responsibilities)