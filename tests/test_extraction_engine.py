from app.extraction.extraction_engine import ExtractionEngine


def test_resume_extraction():

    text = """
    Nguyễn Thanh Trúc

    Email:
    nguyenhoangkhang.241105@gmail.com

    Education

    Bachelor of Information Technology
    """

    engine = ExtractionEngine()

    result = engine.extract_resume(text)


    print(result)


    assert result["personal"]["full_name"] is not None

    assert (
        result["personal"]["email"]
        ==
        "nguyenhoangkhang.241105@gmail.com"
    )