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


from app.extraction.education.education_extractor import (
    EducationExtractor
)


def test_extract_full_education():

    text = """
    Bachelor of Information Technology
    Ho Chi Minh City University
    GPA: 3.6
    Expected Graduation 2027
    """

    result = EducationExtractor.extract(
        text
    )


    assert result[0]["degree_level"] == [
        "Bachelor"
    ]

    assert (
        "Information Technology"
        in result[0]["major"]
    )

    assert result[0]["gpa"] == 3.6

    assert 2027 in result[0]["years"]


def test_empty_text():

    result = EducationExtractor.extract(
        ""
    )


    assert result == []