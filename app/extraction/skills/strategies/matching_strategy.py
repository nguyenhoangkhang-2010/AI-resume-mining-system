from abc import ABC, abstractmethod


class MatchingStrategy(ABC):

    @abstractmethod
    def extract(self, text: str):
        pass