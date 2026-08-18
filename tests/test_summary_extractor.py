from app.extraction.summary import SummaryExtractor



def test_extract_professional_summary():

    extractor = SummaryExtractor()

    text = """
    PROFESSIONAL SUMMARY

    Data Engineer with experience in Python,
    SQL and Machine Learning.

    EDUCATION

    Bachelor of IT
    """

    result = extractor.extract(
        text
    )

    assert result is not None
    assert "Data Engineer" in result



def test_extract_objective():

    extractor = SummaryExtractor()

    text = """
    OBJECTIVE

    Looking for a Data Analyst position.

    EXPERIENCE

    Company ABC
    """

    result = extractor.extract(
        text
    )

    assert result is not None
    assert "Data Analyst" in result



def test_missing_summary():

    extractor = SummaryExtractor()

    result = extractor.extract(
        """
        EDUCATION

        Bachelor Degree
        """
    )

    assert result is None