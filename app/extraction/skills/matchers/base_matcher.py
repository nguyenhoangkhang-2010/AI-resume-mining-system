from abc import ABC, abstractmethod

from loguru import logger


class BaseMatcher(ABC):

    def match(self, text: str):

        if not text:
            logger.warning(
                "Empty text provided."
            )
            return set()

        logger.debug(
            f"Running {self.__class__.__name__}."
        )

        return self._match(text)

    @abstractmethod
    def _match(self, text: str):
        pass