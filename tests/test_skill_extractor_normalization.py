from app.matching.skills.normalization.skill_normalizer import SkillNormalizer

from app.matching.skills.normalization.alias_rule import AliasNormalizationRule

from app.extraction.skills.skill_extractor import SkillExtractor


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
    
def test_uppercase_alias():

    extractor = SkillExtractor()

    skills = extractor.extract(
        "Experienced in PYTHON3."
    )

    assert "python" in skills
    
def test_trim_and_case():

    extractor = SkillExtractor()

    skills = extractor.extract(
        "Experienced in   PYTHON3   ."
    )

    assert "python" in skills
    
def test_punctuation_normalization():

    extractor = SkillExtractor()

    skills = extractor.extract(
        "Experienced in Python, FastAPI."
    )

    assert "python" in skills
    assert "fastapi" in skills