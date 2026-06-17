import pytest
from app.resume_processing.cleaners.text_cleaner import TextCleaner


@pytest.fixture
def text_cleaner():
    return TextCleaner()

def test_clean_whitespaces(text_cleaner):
    raw_text = "This   is \t a text \n with  many  spaces."
    cleaned_text = text_cleaner.clean(raw_text)
    assert type(cleaned_text) is str
    assert len(cleaned_text) > 0

def test_clean_empty_string(text_cleaner):
    assert text_cleaner.clean("") == ""