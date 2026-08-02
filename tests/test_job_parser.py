from app.job_processing.parsers.job_parser import (
    JobDescriptionParser,
)


def test_parse_text():

    parser = JobDescriptionParser()

    text = parser.parse(
        "Python Developer"
    )

    assert text == "Python Developer"