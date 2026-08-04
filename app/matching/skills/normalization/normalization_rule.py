from abc import ABC, abstractmethod


class NormalizationRule(ABC):

    @abstractmethod
    def apply(
        self,
        skill: str
    ) -> str:
        pass