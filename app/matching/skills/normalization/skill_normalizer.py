from abc import ABC, abstractmethod


class SkillNormalizer(ABC):

    @abstractmethod
    def normalize(
        self,
        skill: str
    ) -> str:
        pass