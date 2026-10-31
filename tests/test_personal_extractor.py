import pytest

from app.extraction.personal.personal_extractor import PersonalExtractor


class FakeNERService:
    def __init__(self, entities=None):
        self.entities = entities or []

    def extract(self, text):
        return self.entities


@pytest.fixture
def extractor():
    return PersonalExtractor(ner_service=FakeNERService())


def test_extract_email(extractor):
    result = extractor.extract("Email: john@gmail.com")

    assert result["email"] == "john@gmail.com"


def test_extract_phone(extractor):
    result = extractor.extract("Phone: +84 912345678")

    assert result["phone"] is not None


def test_extract_social_links(extractor):
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


def test_markdown_email_is_unwrapped(extractor):
    result = extractor.extract("[a@gmail.com](mailto:a@gmail.com)")

    assert result["email"] == "a@gmail.com"


def test_name_falls_back_to_ner_person_entity():
    extractor = PersonalExtractor(
        ner_service=FakeNERService(
            [{"label": "PERSON", "text": "Nguyen Van A", "score": 0.99}]
        )
    )

    result = extractor.extract("Contact: a@gmail.com")

    assert result["full_name"] == "Nguyen Van A"


def test_empty_text_returns_empty_result(extractor):
    result = extractor.extract("   ")

    assert result == {
        "full_name": None,
        "email": None,
        "phone": None,
        "linkedin": None,
        "github": None,
    }


def test_year_is_not_mistaken_for_phone(extractor):
    result = extractor.extract("Graduated in 2023")

    assert result["phone"] is None
