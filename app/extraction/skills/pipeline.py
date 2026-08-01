from loguru import logger


class SkillExtractionPipeline:

    def __init__(self, strategy):
        self.strategy = strategy

    def extract(self, text):

        logger.debug(
            "Starting skill extraction pipeline."
        )

        return self.strategy.extract(text)