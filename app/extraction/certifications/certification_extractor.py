import re
from typing import List, Dict, Any

from loguru import logger


class CertificationExtractor:

    CERTIFICATION_SECTION_PATTERN = re.compile(
        r"(?im)"
        r"^\s*(?:certifications?|certificates?|licenses?)\s*:?\s*$"
        r"(.*?)"
        r"(?="
        r"^\s*(?:education|experience|work experience|"
        r"professional experience|employment history|"
        r"projects?|academic projects?|personal projects?|"
        r"skills?|technical skills|professional skills|"
        r"languages?|publications?|references?|"
        r"awards?|honors?\s+and\s+awards?|"
        r"additional information|interests?|hobbies?)"
        r"\s*:?\s*$"
        r"|$)",
        re.DOTALL,
    )

    @staticmethod
    def _clean_line(line: str) -> str:
        line = line.strip()

        line = re.sub(
            r"^\s*[•●▪◦‣\-*]\s*",
            "",
            line,
        )

        line = re.sub(r"\s+", " ", line)

        return line.strip()

    @staticmethod
    def _extract_lines(section: str) -> List[Dict[str, Any]]:
        certifications: List[Dict[str, Any]] = []

        for raw_line in section.splitlines():
            line = CertificationExtractor._clean_line(raw_line)

            if not line:
                continue

            certifications.append(
                {
                    "name": line,
                }
            )

        return certifications

    @staticmethod
    def extract(text: str) -> List[Dict[str, Any]]:
        if not text or not text.strip():
            return []

        logger.debug("Starting certification extraction.")

        text = text.strip()

        match = CertificationExtractor.CERTIFICATION_SECTION_PATTERN.search(
            text
        )

        if match:
            section = match.group(1).strip()

            certifications = CertificationExtractor._extract_lines(
                section
            )

            logger.debug(
                f"Extracted certifications from full resume: "
                f"{len(certifications)}"
            )

            return certifications

        certifications = CertificationExtractor._extract_lines(text)

        logger.debug(
            f"Extracted certifications from isolated section: "
            f"{len(certifications)}"
        )

        return certifications