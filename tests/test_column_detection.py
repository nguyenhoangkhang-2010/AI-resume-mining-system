import fitz

from app.resume_processing.layout.layout_analyzer import LayoutAnalyzer
from app.resume_processing.layout.layout_representation import LayoutDocument
from app.resume_processing.layout.semantic_region_analyzer import (
    SemanticRegionAnalyzer,
)
from app.resume_processing.parsers.pdf_parser import PDFParser


def page_columns(path):
    parsed = PDFParser.parse(path)
    layout = LayoutAnalyzer().analyze(LayoutDocument.from_parser_result(parsed))
    analyzer = SemanticRegionAnalyzer()

    return [
        analyzer._detect_columns(page.blocks, page.width) for page in layout.pages
    ]


def draw(path, left, right, left_x=30, right_x=215, size=10):
    document = fitz.open()
    page = document.new_page()

    for x, items in ((left_x, left), (right_x, right)):
        y = 60
        for text, font_size in items:
            if text is None:
                y += 24
                continue

            page.insert_text((x, y), text, fontsize=font_size or size)
            y += 15

    document.save(str(path))
    document.close()


NARROW_LEFT = [
    ("Skills", 14), ("Python, SQL", None), ("Docker", None), (None, None),
    ("Certificates", 14), ("AWS Practitioner", None), ("Scrum Master", None),
]
NARROW_RIGHT = [
    ("Experience", 14), ("Backend Engineer", None), ("Built APIs", None),
    (None, None),
    ("Education", 14), ("BSc Computer Science", None), ("2016 - 2020", None),
]


def test_two_plain_columns_are_two_columns(tmp_path):
    path = tmp_path / "plain.pdf"
    draw(path, NARROW_LEFT, NARROW_RIGHT)

    assert [len(columns) for columns in page_columns(path)] == [2]


def test_a_heading_reaching_into_the_gutter_does_not_merge_the_columns(tmp_path):
    """
    The left heading is 212 points wide, so the left column's extent covers
    the start of the right column. The right column's narrow blocks used to
    overlap it enough to be pulled in, and both columns were read as one.
    """

    wide_left = [
        ("LICENSES AND DESIGNATIONS", 14),
        ("ACCA Diploma in Accounting", None),
        (None, None),
        ("Skills", 14),
        ("Python", None),
    ]

    path = tmp_path / "wide.pdf"
    draw(path, wide_left, NARROW_RIGHT)

    columns = page_columns(path)[0]

    assert len(columns) == 2

    texts = [
        {block.text.split("\n")[0] for block in column} for column in columns
    ]

    assert "Experience" in texts[1]
    assert "Experience" not in texts[0]


def test_a_single_column_with_blocks_of_every_width_stays_one_column(tmp_path):
    left = [
        ("Skills", 14), ("Py", None), ("Python, SQL, Docker, Kubernetes", None),
        (None, None),
        ("Experience", 14),
        ("Backend Engineer at a company with a rather long name", None),
        ("Built APIs", None),
    ]

    path = tmp_path / "single.pdf"
    draw(path, left, [], left_x=72)

    assert [len(columns) for columns in page_columns(path)] == [1]


def test_indented_lines_stay_in_their_column(tmp_path):
    left = [("Experience", 14), ("Engineer", None), ("Built APIs", None)]

    path = tmp_path / "indented.pdf"
    document = fitz.open()
    page = document.new_page()
    y = 60

    for text, size in left:
        page.insert_text((72, y), text, fontsize=size or 10)
        y += 20

    page.insert_text((82, y), "- indented bullet", fontsize=10)
    y += 20
    page.insert_text((72, y + 20), "Education", fontsize=14)
    document.save(str(path))
    document.close()

    assert [len(columns) for columns in page_columns(path)] == [1]
