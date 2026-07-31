import re
from typing import List
from loguru import logger
from app.extraction.skills.repository import SkillRepository


class SkillExtractor:

    def __init__(self):

        self.skill_repository = SkillRepository()

        self.skills = (
            self.skill_repository
            .get_all_skills()
        )

        logger.info(
            f"SkillExtractor initialized with {len(self.skills)} skills."
        )
        
    def _build_pattern(self, skill: str):
        escaped = re.escape(skill)

        escaped = escaped.replace(
            r"\ ",
            r"\s+"
        )

        return escaped

    def extract(self, text: str) -> List[str]:
        if not text:
            logger.warning("Empty text provided to SkillExtractor.")
            return []
            
        logger.debug("Starting skill extraction process.")
        extracted_skills = set()
        
        for skill in self.skills:
            pattern = self._build_pattern(skill)

            if re.search(
                pattern,
                text,
                re.IGNORECASE
            ):
                extracted_skills.add(skill)
                
        logger.debug(f"Extracted {len(extracted_skills)} skills.")
        return sorted(list(extracted_skills))