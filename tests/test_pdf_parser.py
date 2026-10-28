import pytest

from app.resume_processing.parsers.pdf_parser import PDFParser


def test_extract_text_success(make_pdf):
    path = make_pdf(["Mocked PDF text content", "Second line"])

    result = PDFParser.extract_text(path)

    assert "Mocked PDF text content" in result
    assert "Second line" in result


def test_parse_returns_pages_and_metadata(make_pdf):
    path = make_pdf(["Hello resume"])

    parsed = PDFParser.parse(path)

    assert "Hello resume" in parsed["text"]
    assert len(parsed["pages"]) == 1
    assert parsed["metadata"]["page_count"] == 1


def test_extract_text_file_not_found():
    with pytest.raises(FileNotFoundError):
        PDFParser.extract_text("non_existent_file_path.pdf")
