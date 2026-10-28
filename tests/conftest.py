import fitz
import pytest


@pytest.fixture
def make_pdf(tmp_path):
    """
    Builds a small real PDF so parser/pipeline tests exercise
    PyMuPDF instead of mocking it.
    """

    def _make_pdf(lines, name="resume.pdf"):
        document = fitz.open()
        page = document.new_page()

        y = 72
        for line in lines:
            page.insert_text((72, y), line, fontsize=11)
            y += 18

        path = tmp_path / name
        document.save(str(path))
        document.close()

        return path

    return _make_pdf
