from app.extraction.education.education_extractor import (
    EducationExtractor,
)



def test_extract_degree_levels():

    text = """
    EDUCATION

    Bachelor of Information Technology

    Master of Computer Science

    PhD in Artificial Intelligence
    """


    result = EducationExtractor.extract(
        text
    )


    assert len(result) == 1


    assert result[0]["degree_level"] == [
        "Bachelor",
        "Master",
        "Doctorate"
    ]



def test_empty_text():

    result = EducationExtractor.extract(
        ""
    )


    assert result == []