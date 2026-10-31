"""
Reads a Word (.docx) CV into the same layout structure the PDF parser makes.

A Word file has no page geometry, but it has what the later stages use the
geometry for: the order of paragraphs, their weight and size (headings),
spacing, tables (many CV templates lay a sidebar out as a two-column table)
and text boxes. The parser places every paragraph on a virtual A4 page, one
below the other in a column, tables as columns side by side, and lets the
existing layout analysis, section detection and extraction run on that. Bullet
and numbered paragraphs get a visible "•" because Word keeps the symbol out of
the text.

What is not read: text inside images (a CV pasted as a picture), footers,
comments and tracked deletions. A file with no text at all ends as
`needs_review` like a scanned PDF.
"""

import math
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Iterator, List, Optional, Tuple

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.hyperlink import Hyperlink
from docx.text.paragraph import Paragraph
from docx.text.run import Run
from loguru import logger

from app.resume_processing.parsers.pdf_parser import PDFParser, clean_pdf_text

# A .docx is a zip file; this bounds what unpacking it may cost.
MAX_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
MAX_ENTRIES = 2000
MAX_COMPRESSION_RATIO = 200

A4_WIDTH = 595.0
A4_HEIGHT = 842.0
DEFAULT_MARGIN = 54.0
DEFAULT_SIZE = 11.0
LINE_FACTOR = 1.2
CHAR_WIDTH_FACTOR = 0.5
EMU_PER_POINT = 12700.0
CELL_PADDING = 4.0

BOLD_FLAG = 16
ITALIC_FLAG = 2

HEADING_SIZES = {"title": 20.0, "heading 1": 16.0, "heading 2": 14.0, "heading 3": 12.0}


class UnreadableFileError(Exception):
    """The file is not a readable Word document (the message names no content)."""


@dataclass
class _Page:
    index: int
    blocks: List[Dict[str, Any]] = field(default_factory=list)
    texts: List[str] = field(default_factory=list)


class DocxParser:

    @staticmethod
    def parse(file_path: str | Path) -> Dict[str, Any]:
        path = Path(file_path)

        if not path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")

        DocxParser._check_archive(path)

        try:
            document = Document(str(path))
        except Exception as exc:
            raise UnreadableFileError("The Word document cannot be opened.") from exc

        logger.info("Parsing Word document with layout simulation: {}", path.name)

        try:
            layout = _Layout(document)
            layout.add_header()
            layout.add_body()
            layout.add_text_boxes()
        except UnreadableFileError:
            raise
        except Exception as exc:
            raise UnreadableFileError("The Word document cannot be read.") from exc

        result = layout.result()

        logger.info(
            "Word document parsed: {} pages, {} characters",
            len(result["pages"]),
            len(result["text"]),
        )

        return result

    @staticmethod
    def _check_archive(path: Path) -> None:
        problem = archive_problem(path)

        if problem:
            raise UnreadableFileError(problem)


def archive_problem(path: Path) -> Optional[str]:
    """
    Why the file cannot be a Word document we should open, or None: a real zip
    with a Word document inside, that does not expand beyond reason (a zip
    bomb is a few kilobytes that unpack to gigabytes).
    """

    try:
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            total = sum(entry.file_size for entry in entries)
            packed = sum(entry.compress_size for entry in entries) or 1

            if (
                len(entries) > MAX_ENTRIES
                or total > MAX_UNCOMPRESSED_BYTES
                or total / packed > MAX_COMPRESSION_RATIO
            ):
                return "The archive is too large to open safely."

            if "word/document.xml" not in archive.namelist():
                return "The file is not a Word document."
    except zipfile.BadZipFile:
        return "The file is not a valid Word document."

    return None


class _Layout:
    """Places the content of a document on virtual pages."""

    def __init__(self, document: Any) -> None:
        self.document = document
        section = document.sections[0] if document.sections else None

        self.width = _points(getattr(section, "page_width", None), A4_WIDTH)
        self.height = _points(getattr(section, "page_height", None), A4_HEIGHT)
        self.left = _points(getattr(section, "left_margin", None), DEFAULT_MARGIN)
        self.right = _points(getattr(section, "right_margin", None), DEFAULT_MARGIN)
        self.top = _points(getattr(section, "top_margin", None), DEFAULT_MARGIN)
        self.bottom = _points(getattr(section, "bottom_margin", None), DEFAULT_MARGIN)

        self.pages: List[_Page] = [_Page(0)]
        self.y = self.top
        self.previous_after = 0.0
        self.block_count = 0

    # --------------------------------------------------------------- pages

    @property
    def page(self) -> _Page:
        return self.pages[-1]

    def new_page(self) -> None:
        self.pages.append(_Page(len(self.pages)))
        self.y = self.top
        self.previous_after = 0.0

    # -------------------------------------------------------------- content

    def add_header(self) -> None:
        sections = self.document.sections

        if not sections:
            return

        header = sections[0].first_page_header if sections[0].different_first_page_header_footer else sections[0].header
        y = 18.0

        for item in header.iter_inner_content():
            if isinstance(item, Paragraph):
                y = self._paragraph(item, self.left, self.width - self.right, y, page=self.pages[0])[0]

    def add_body(self) -> None:
        self.y = self._flow(
            self.document.iter_inner_content(),
            self.left,
            self.width - self.right,
            self.y,
            paginate=True,
        )

    def add_text_boxes(self) -> None:
        """Text in boxes (sidebars of designed templates), placed where they are anchored."""

        body = self.document.element.body
        boxes = [
            element
            for element in body.iter(qn("w:txbxContent"))
            if not _inside(element, "Fallback")
        ]

        for box in boxes:
            x, y, width = _anchor(box, self.left, self.top, (self.width - self.left - self.right) / 3)
            paragraphs = (
                Paragraph(child, self.document._body)
                for child in box.iterchildren(qn("w:p"))
            )
            self._flow(paragraphs, x, x + width, y, page=self.pages[0])

    # ----------------------------------------------------------------- flow

    def _flow(
        self,
        items: Iterator[Any],
        x0: float,
        x1: float,
        y: float,
        paginate: bool = False,
        page: Optional[_Page] = None,
    ) -> float:
        """Lays out paragraphs and tables from y downwards; returns the end y."""

        for item in items:
            if isinstance(item, Paragraph):
                y, broke = self._paragraph(item, x0, x1, y, paginate=paginate, page=page)

                if broke and paginate:
                    self.new_page()
                    y = self.y
            elif isinstance(item, Table):
                y = self._table(item, x0, x1, y, paginate, page)

        return y

    def _table(
        self, table: Table, x0: float, x1: float, y: float, paginate: bool, page: Optional[_Page]
    ) -> float:
        columns = max(1, len(table.columns))
        widths = _column_widths(table, columns, x1 - x0)

        for row in table.rows:
            if paginate and y > self.height - self.bottom:
                self.new_page()
                y = self.y

            row_end = y
            seen = set()
            offset = 0.0

            for index, cell in enumerate(row.cells):
                width = widths[min(index, columns - 1)]

                if id(cell._tc) not in seen:
                    seen.add(id(cell._tc))
                    end = self._flow(
                        cell.iter_inner_content(),
                        x0 + offset + CELL_PADDING,
                        x0 + offset + width - CELL_PADDING,
                        y,
                        paginate=False,
                        page=page if page is not None else (self.page if paginate else None),
                    )
                    row_end = max(row_end, end)

                offset += width

            y = row_end

        return y

    def _paragraph(
        self,
        paragraph: Paragraph,
        x0: float,
        x1: float,
        y: float,
        paginate: bool = False,
        page: Optional[_Page] = None,
    ) -> Tuple[float, bool]:
        """Adds one paragraph as a block; returns the end y and whether a page break follows."""

        spans = _spans(paragraph)
        breaks_after = _page_break(paragraph)

        if not spans:
            # An empty paragraph is a blank line.
            return y + DEFAULT_SIZE * LINE_FACTOR, breaks_after

        size = max(span["size"] for span in spans)
        before, after = _spacing(paragraph)

        if paginate and paragraph.paragraph_format.page_break_before:
            self.new_page()
            y = self.y
        elif paginate:
            y += max(before, self.previous_after)

            if y + size * LINE_FACTOR > self.height - self.bottom and y > self.top + size:
                self.new_page()
                y = self.y
        else:
            y += before

        target = page or self.page
        lines, bottom = self._lines(spans, x0, x1, y, size)
        text = "\n".join(line["text"] for line in lines)

        target.blocks.append(
            {
                "type": "text",
                "block_index": self.block_count,
                "bbox": _bbox(x0, y, x1, bottom, self.width, self.height),
                "text": text,
                "lines": lines,
            }
        )
        target.texts.extend(line["text"] for line in lines)
        self.block_count += 1

        if paginate:
            self.previous_after = after
            return bottom, breaks_after

        return bottom + after, breaks_after

    def _lines(
        self, spans: List[Dict[str, Any]], x0: float, x1: float, y: float, size: float
    ) -> Tuple[List[Dict[str, Any]], float]:
        """The text lines of a paragraph (a line break starts a new one)."""

        grouped: List[List[Dict[str, Any]]] = [[]]

        for span in spans:
            parts = span["text"].split("\n")

            for number, part in enumerate(parts):
                if number:
                    grouped.append([])

                if part:
                    grouped[-1].append({**span, "text": part})

        lines: List[Dict[str, Any]] = []
        cursor = y
        capacity = max(10, int((x1 - x0) / (size * CHAR_WIDTH_FACTOR)))

        for group in grouped:
            text = "".join(span["text"] for span in group).strip()

            if not text:
                cursor += size * LINE_FACTOR
                continue

            wrapped = max(1, math.ceil(len(text) / capacity))
            bottom = cursor + wrapped * size * LINE_FACTOR
            line_bbox = _bbox(x0, cursor, x1, bottom, self.width, self.height)

            lines.append(
                {
                    "text": text,
                    "bbox": line_bbox,
                    "line_index": len(lines),
                    "spans": [
                        {
                            "text": span["text"],
                            "bbox": line_bbox,
                            "font": span["font"],
                            "size": span["size"],
                            "flags": span["flags"],
                            "color": span["color"],
                            "origin": (x0, cursor),
                        }
                        for span in group
                    ],
                }
            )
            cursor = bottom

        return lines, cursor

    # --------------------------------------------------------------- result

    def result(self) -> Dict[str, Any]:
        pages: List[Dict[str, Any]] = [
            {
                "page_index": page.index,
                "width": self.width,
                "height": self.height,
                "text": "\n".join(page.texts),
                "blocks": page.blocks,
                "images": [],
            }
            for page in self.pages
        ]
        properties = self.document.core_properties

        return {
            "text": "\n".join(page["text"] for page in pages if page["text"]).strip(),
            "pages": pages,
            "metadata": {
                "title": properties.title or None,
                "author": properties.author or None,
                "subject": properties.subject or None,
                "keywords": properties.keywords or None,
                "creator": None,
                "producer": "docx",
                "page_count": len(pages),
            },
        }


# ------------------------------------------------------------------ helpers


def _points(length: Any, default: float) -> float:
    try:
        return float(length.pt) if length is not None else default
    except (AttributeError, TypeError, ValueError):
        return default


def _bbox(x0: float, y0: float, x1: float, y1: float, width: float, height: float) -> Dict[str, float]:
    return PDFParser._normalize_bbox(
        (x0, y0, x1, y1), SimpleNamespace(width=width, height=height)
    )


def _column_widths(table: Table, columns: int, available: float) -> List[float]:
    widths = []

    for column in table.columns:
        widths.append(_points(column.width, 0.0))

    if len(widths) != columns or not all(widths):
        return [available / columns] * columns

    total = sum(widths)

    return [width * available / total for width in widths]


def _style_chain(paragraph: Paragraph) -> Iterator[Any]:
    style = paragraph.style

    while style is not None:
        yield style
        style = style.base_style


def _style_name(paragraph: Paragraph) -> str:
    style = paragraph.style

    return (style.name or "").lower() if style is not None else ""


def _spans(paragraph: Paragraph) -> List[Dict[str, Any]]:
    """The paragraph's text in runs with their font, size, weight and colour."""

    name = _style_name(paragraph)
    heading_size = HEADING_SIZES.get(name)
    is_heading = name.startswith(("heading", "title"))
    spans: List[Dict[str, Any]] = []

    if _is_list_item(paragraph, name):
        spans.append(_span("• ", paragraph, None, heading_size, is_heading))

    for item in paragraph.iter_inner_content():
        runs = item.runs if isinstance(item, Hyperlink) else [item]

        for run in runs:
            if isinstance(run, Run) and run.text:
                spans.append(_span(run.text, paragraph, run, heading_size, is_heading))

    return spans if any(span["text"].strip() for span in spans) else []


def _is_list_item(paragraph: Paragraph, style_name: str) -> bool:
    properties = paragraph._p.pPr

    return (properties is not None and properties.numPr is not None) or style_name.startswith("list")


def _span(
    text: str,
    paragraph: Paragraph,
    run: Optional[Run],
    heading_size: Optional[float],
    is_heading: bool,
) -> Dict[str, Any]:
    font = run.font if run is not None else None
    size = _points(font.size if font else None, 0.0)
    bold = font.bold if font else None
    italic = font.italic if font else None
    name = font.name if font else None
    color = _color(font)

    for style in _style_chain(paragraph):
        style_font = style.font

        size = size or _points(style_font.size, 0.0)
        bold = style_font.bold if bold is None else bold
        italic = style_font.italic if italic is None else italic
        name = name or style_font.name

    if run is not None and run.bold is None and run.style is not None and run.style.font.bold:
        bold = True

    flags = (BOLD_FLAG if (bold or (bold is None and is_heading)) else 0) | (
        ITALIC_FLAG if italic else 0
    )

    return {
        "text": clean_pdf_text(text.replace("\t", "  ")),
        "font": name or "Calibri",
        "size": size or heading_size or DEFAULT_SIZE,
        "flags": flags,
        "color": color,
    }


def _color(font: Any) -> int:
    try:
        rgb = font.color.rgb if font is not None else None

        return int(str(rgb), 16) if rgb is not None else 0
    except (AttributeError, TypeError, ValueError):
        return 0


def _spacing(paragraph: Paragraph) -> Tuple[float, float]:
    """Space before and after the paragraph, in points."""

    format_ = paragraph.paragraph_format
    before, after = _points(format_.space_before, -1.0), _points(format_.space_after, -1.0)

    for style in _style_chain(paragraph):
        style_format = style.paragraph_format

        if before < 0:
            before = _points(style_format.space_before, -1.0)

        if after < 0:
            after = _points(style_format.space_after, -1.0)

    return max(before, 0.0), max(after, 0.0)


def _page_break(paragraph: Paragraph) -> bool:
    return any(
        element.get(qn("w:type")) == "page" for element in paragraph._p.iter(qn("w:br"))
    )


def _inside(element: Any, *names: str) -> bool:
    """True when an ancestor of the element has one of the given local names."""

    parent = element.getparent()

    while parent is not None:
        if parent.tag.rsplit("}", 1)[-1] in names:
            return True

        parent = parent.getparent()

    return False


def _anchor(box: Any, default_x: float, default_y: float, default_width: float) -> Tuple[float, float, float]:
    """Position and width of a text box from its drawing anchor, when it has one."""

    parent = box.getparent()

    while parent is not None and parent.tag.rsplit("}", 1)[-1] not in ("anchor", "inline"):
        parent = parent.getparent()

    if parent is None:
        return default_x, default_y, default_width

    def offset(kind: str, fallback: float) -> float:
        for element in parent.iter():
            if element.tag.rsplit("}", 1)[-1] == kind:
                for child in element:
                    if child.tag.rsplit("}", 1)[-1] == "posOffset" and (child.text or "").lstrip("-").isdigit():
                        return int(child.text) / EMU_PER_POINT

        return fallback

    width = default_width

    for element in parent.iter():
        if element.tag.rsplit("}", 1)[-1] == "extent" and element.get("cx", "").isdigit():
            width = int(element.get("cx")) / EMU_PER_POINT
            break

    return offset("positionH", default_x), offset("positionV", default_y), max(width, 40.0)
