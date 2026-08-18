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
    
def test_extract_experience_detail():

    text = """
    Google

    Machine Learning Engineer

    2024 - 2026

    Built ML pipelines
    Developed backend APIs

    3 years experience
    """


    result = ExperienceExtractor.extract(
        text
    )


    assert (
        result[0]["total_years_extracted"]
        == 3
    )


    assert len(
        result[0]["experience_periods"]
    ) == 1


    experience = (
        result[0]["experience_periods"][0]
    )


    assert (
        experience["start"]
        == "2024"
    )


    assert (
        experience["end"]
        == "2026"
    )


    assert (
        experience["role"]
        == "Machine Learning Engineer"
    )