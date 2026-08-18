from app.extraction.skills.skill_extractor import SkillExtractor


def test_extract_many():

    extractor = SkillExtractor()

    results = extractor.extract_many(
        [
            "Python Django",
            "Torch",
            "Pizza",
        ]
    )

    assert len(results) == 3