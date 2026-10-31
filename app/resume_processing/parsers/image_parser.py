"""
Photographs and scans of a CV (PNG, JPEG) as a one-page PDF.

An image has no text layer, so it is placed on an A4 page and read the way a
scanned PDF is: by the PDF parser, which runs OCR on a page that has only an
image (see `OCR_ENABLED`). Without OCR the text stays empty and the resume is
flagged `needs_review`, so uploads of images are only accepted when OCR is on.
"""

import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import fitz

from app.resume_processing.parsers.docx_parser import UnreadableFileError
from app.resume_processing.parsers.pdf_parser import PDFParser

IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg"})

# A decompression bomb is a small file that unpacks to a huge bitmap.
MAX_IMAGE_PIXELS = 40_000_000

A4_WIDTH = 595.0
A4_HEIGHT = 842.0
PAGE_MARGIN = 18.0


def image_problem(path: Path) -> Optional[str]:
    """Why the file cannot be used as an image of a CV, or None if it can."""

    try:
        with fitz.open(path) as image:
            if image.page_count != 1:
                return "The file is not a single image."

            rect = image[0].rect
    except Exception:
        return "The file is not a readable image."

    if rect.width <= 0 or rect.height <= 0:
        return "The file is not a readable image."

    if rect.width * rect.height > MAX_IMAGE_PIXELS:
        return "The image is too large."

    return None


def image_to_pdf(path: Path) -> bytes:
    """The image on an A4 page (landscape if it is wider than tall)."""

    with fitz.open(path) as image:
        rect = image[0].rect

    landscape = rect.width > rect.height
    width, height = (A4_HEIGHT, A4_WIDTH) if landscape else (A4_WIDTH, A4_HEIGHT)

    scale = min(
        (width - 2 * PAGE_MARGIN) / rect.width,
        (height - 2 * PAGE_MARGIN) / rect.height,
    )
    target_width, target_height = rect.width * scale, rect.height * scale
    left = (width - target_width) / 2
    top = (height - target_height) / 2

    with fitz.open() as document:
        page = document.new_page(width=width, height=height)
        page.insert_image(
            fitz.Rect(left, top, left + target_width, top + target_height),
            filename=str(path),
        )

        return document.tobytes()


class ImageParser:
    """Same interface as PDFParser.parse."""

    @staticmethod
    def parse(file_path: str | Path) -> Dict[str, Any]:
        path = Path(file_path)

        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")

        problem = image_problem(path)

        if problem:
            raise UnreadableFileError(problem)

        with tempfile.TemporaryDirectory() as directory:
            converted = Path(directory) / "page.pdf"
            converted.write_bytes(image_to_pdf(path))

            return PDFParser.parse(converted)
