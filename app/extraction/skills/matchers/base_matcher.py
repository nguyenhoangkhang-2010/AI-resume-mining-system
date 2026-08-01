from abc import ABC, abstractmethod

from app.models.skill_match import SkillMatch

from loguru import logger


class BaseMatcher(ABC):

    def match(self, text: str):
        
        logger.debug(
            f"Running {self.__class__.__name__}."
        )
        
        matches = self.match_with_confidence(text)

        return {
            item.skill
            for item in matches
        }

    @abstractmethod
    def match_with_confidence(
        self,
        text: str,
    ) -> list[SkillMatch]:
        pass