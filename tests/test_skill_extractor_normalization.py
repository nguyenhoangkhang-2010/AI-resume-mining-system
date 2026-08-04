from app.matching.skills.normalization.skill_normalizer import SkillNormalizer

from app.matching.skills.normalization.alias_rule import AliasNormalizationRule


class FakeRepository:

    def get_alias(self, skill):

        mapping = {
            "python3": "python"
        }

        return mapping.get(skill)


def test_alias_rule():

    normalizer = SkillNormalizer(
        rules=[
            AliasNormalizationRule(
                FakeRepository()
            )
        ]
    )

    assert normalizer.normalize("python3") == "python"

    assert normalizer.normalize("fastapi") == "fastapi"