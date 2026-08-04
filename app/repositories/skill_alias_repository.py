from abc import ABC, abstractmethod


class SkillAliasRepository(ABC):

    @abstractmethod
    def get_alias(
        self,
        skill: str
    ) -> str | None:
        pass