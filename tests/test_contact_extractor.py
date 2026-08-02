from app.extraction.contact import ContactExtractor


def test_extract_email():

    extractor = ContactExtractor()

    result = extractor.extract(
        "Email: john@gmail.com"
    )

    assert result["email"] == "john@gmail.com"



def test_extract_phone():

    extractor = ContactExtractor()

    result = extractor.extract(
        "Phone: +84 912345678"
    )

    assert result["phone"] is not None



def test_extract_social_links():

    extractor = ContactExtractor()

    result = extractor.extract(
        """
        Github:
        https://github.com/khang

        LinkedIn:
        https://linkedin.com/in/khang
        """
    )

    assert result["github"] is not None
    assert result["linkedin"] is not None