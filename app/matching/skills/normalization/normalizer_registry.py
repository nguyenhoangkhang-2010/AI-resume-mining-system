from app.matching.skills.normalization.skill_normalizer import (
    SkillNormalizer,
)


class SkillNormalizerRegistry:

    def __init__(
        self,
        normalizer: SkillNormalizer
    ):
        self.normalizer = normalizer


    def normalize(
        self,
        skill: str
    ):

        return self.normalizer.normalize(skill)