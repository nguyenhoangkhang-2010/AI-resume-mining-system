import re
from typing import List, Dict, Any

from loguru import logger


class CertificationExtractor:

    CERTIFICATION_SECTION_PATTERN = (
        r"(certifications?|certificates?|licenses?)"
        r"(.*?)(?="
        r"\n\s*(education|experience|projects|skills)"
        r"|$)"
    )


    @staticmethod
    def extract(
        text: str
    ) -> List[Dict[str, Any]]:
        if not text:
            return []
        logger.debug(
            "Starting certification extraction."
        )
        certifications = []
        match = re.search(
            CertificationExtractor.CERTIFICATION_SECTION_PATTERN,
            text,
            re.IGNORECASE | re.DOTALL
        )
        if not match:
            return []
        section = match.group(2)
        lines = [
            line.strip()
            for line in section.split("\n")
            if line.strip()
        ]
        for line in lines:
            clean_name = (
                line
                .replace("-", "")
                .strip()
            )
            if clean_name:
                certifications.append(
                    {
                        "name": clean_name
                    }
                )
        logger.debug(
            f"Extracted certifications: {len(certifications)}"
        )
        return certifications