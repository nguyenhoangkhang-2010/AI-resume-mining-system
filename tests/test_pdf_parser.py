import pytest
from unittest.mock import patch, MagicMock
from app.resume_processing.parsers.pdf_parser import PDFParser


def test_extract_text_success(tmp_path):
    with patch("app.resume_processing.parsers.pdf_parser.fitz.open") as mock_fitz_open:
        # Mock PDF Document and Page
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Mocked PDF text content"
        mock_doc.__iter__.return_value = [mock_page]
        mock_fitz_open.return_value.__enter__.return_value = mock_doc
        
        dummy_file = tmp_path / "dummy.pdf"
        dummy_file.touch()

        parser = PDFParser()
        result = parser.extract_text(dummy_file)
        
        assert "Mocked PDF text content" in result

def test_extract_text_file_not_found():
    with pytest.raises(FileNotFoundError):
        PDFParser.extract_text("non_existent_file_path.pdf")