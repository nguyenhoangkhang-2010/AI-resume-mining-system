from loguru import logger


class SkillExtractionPipeline:

    def __init__(self, matchers):
        self.matchers = matchers

    def extract(self, text):
        logger.debug("Starting skill extraction pipeline.")

        skills = set()

        for matcher in self.matchers:

            result = matcher.match(text)

            if result:
                skills.update(result)

        logger.debug(
            f"Pipeline extracted {len(skills)} skills."
        )

        return sorted(skills)