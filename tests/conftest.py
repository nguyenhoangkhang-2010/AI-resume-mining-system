from pathlib import Path

import fitz
import pytest

ONET_RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "onet" / "raw"


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


def pytest_collection_modifyitems(config, items):
    """
    The O*NET dataset is downloaded separately and is not in git, so tests
    that read it are skipped on a fresh checkout (and in CI).
    """

    if ONET_RAW_DIR.exists():
        return

    skip = pytest.mark.skip(
        reason=f"O*NET data not found at {ONET_RAW_DIR}"
    )

    for item in items:
        if "requires_onet" in item.keywords:
            item.add_marker(skip)
