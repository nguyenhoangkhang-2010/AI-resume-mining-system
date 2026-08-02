import re
from typing import List, Dict, Any

from loguru import logger


class ProjectExtractor:

    PROJECT_SECTION_PATTERN = (
        r"(projects?|personal projects?|academic projects?)"
        r"(.*?)(?="
        r"\n\s*(education|experience|skills|certifications?)"
        r"|$)"
    )


    @staticmethod
    def extract(
        text: str
    ) -> List[Dict[str, Any]]:
        if not text:
            return []
        logger.debug(
            "Starting project extraction."
        )
        projects = []
        matches = re.search(
            ProjectExtractor.PROJECT_SECTION_PATTERN,
            text,
            re.IGNORECASE | re.DOTALL
        )
        if not matches:
            return []
        project_text = matches.group(2)
        lines = [
            line.strip()
            for line in project_text.split("\n")
            if line.strip()
        ]
        current_project = None
        for line in lines:
            if (
                not line.startswith("-")
                and len(line.split()) <= 8
            ):
                if current_project:
                    projects.append(
                        current_project
                    )
                current_project = {
                    "name": line,
                    "description": []
                }
            elif current_project:
                current_project[
                    "description"
                ].append(
                    line.replace("-", "").strip()
                )
        if current_project:
            projects.append(
                current_project
            )
        logger.debug(
            f"Extracted projects: {len(projects)}"
        )
        return projects