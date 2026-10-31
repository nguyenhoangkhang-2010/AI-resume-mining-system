import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS = [ROOT / "README.md", ROOT / "frontend" / "README.md", *sorted((ROOT / "docs").rglob("*.md"))]
LINK = re.compile(r"\]\(([^)#\s]+)(#[^)]*)?\)")


def relative_links(document: Path):
    for match in LINK.finditer(document.read_text(encoding="utf-8")):
        target = match.group(1)

        if not target.startswith(("http://", "https://", "mailto:")):
            yield target


@pytest.mark.parametrize("document", DOCUMENTS, ids=lambda path: str(path.relative_to(ROOT)))
def test_every_relative_link_points_at_a_file_that_exists(document):
    missing = [t for t in relative_links(document) if not (document.parent / t).resolve().exists()]

    assert missing == []


def test_the_report_the_readme_leans_on_exists():
    for name in ("technical-report.md", "platform.md", "api.md", "deployment.md", "vocabulary.md"):
        assert (ROOT / "docs" / name).is_file()
