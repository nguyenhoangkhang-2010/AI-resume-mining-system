from pathlib import Path

import fitz
import pytest

ONET_RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "onet" / "raw"


@pytest.fixture(autouse=True)
def open_api_by_default(monkeypatch):
    """
    Most tests exercise endpoints, not authentication, so the API is open and
    unthrottled unless a test (tests/test_api_security.py) turns it on.
    """

    from app.core.config.settings import settings
    from app.core.security.rate_limit import limiter

    monkeypatch.setattr(settings, "AUTH_ENABLED", False)
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", False)

    limiter.reset()

    yield

    limiter.reset()


@pytest.fixture(autouse=True)
def model_reads_extraction_sections(monkeypatch):
    """
    The extractor tests drive the model-backed path with a fake model, so the
    rules that answer before the model are off unless a test turns them on.
    """

    from app.core.config.settings import settings

    monkeypatch.setattr(settings, "EXTRACTION_RULES_FIRST", False)
    # Tests that index jobs pass their own indexer; the rest must not load
    # the embedding model.
    monkeypatch.setattr(settings, "JOB_INDEXING_ENABLED", False)


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
