from app.extraction.certifications.certification_extractor import (
    CertificationExtractor
)


def test_certification_extraction():

    text = """
    CERTIFICATIONS

    AWS Certified Cloud Practitioner

    Google Data Analytics Certificate

    EDUCATION

    Bachelor Computer Science
    """


    result = CertificationExtractor.extract(
        text
    )


    assert len(result) == 2


    assert (
        result[0]["name"]
        ==
        "AWS Certified Cloud Practitioner"
    )


    assert (
        result[1]["name"]
        ==
        "Google Data Analytics Certificate"
    )