from app.extraction.experience.experience_extractor import (
    ExperienceExtractor,
)


def test_extract_years_experience():

    text = """
    Backend Developer
    3 years of experience
    """

    result = ExperienceExtractor.extract(
        text
    )


    assert (
        result[0]["total_years_extracted"]
        == 3
    )


def test_extract_experience_period():

    text = """
    Software Engineer
    2023 - Present
    """

    result = ExperienceExtractor.extract(
        text
    )


    assert (
        result[0]["experience_periods"][0]["start"]
        == "2023"
    )