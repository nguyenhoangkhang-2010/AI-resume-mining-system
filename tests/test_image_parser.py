import io
import shutil

import fitz
import pytest

from app.core.config.settings import settings
from app.core.exceptions import InvalidUploadError
from app.resume_processing.parsers.document_parser import DocumentParser
from app.resume_processing.parsers.docx_parser import UnreadableFileError
from app.resume_processing.parsers.image_parser import (
    A4_HEIGHT,
    A4_WIDTH,
    MAX_IMAGE_PIXELS,
    ImageParser,
    image_problem,
    image_to_pdf,
)
from app.services.upload_validation import (
    allowed_extensions,
    save_upload,
    validate_signature,
)


def make_image(path, width=300, height=400, fmt="png"):
    """A solid-colour picture; text-free on purpose."""

    pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, width, height), False)
    pixmap.set_rect(pixmap.irect, (200, 220, 240))
    path.write_bytes(pixmap.tobytes(fmt))

    return path


def test_a_png_becomes_an_a4_page_with_an_image_and_no_text(tmp_path):
    path = make_image(tmp_path / "cv.png")

    parsed = ImageParser.parse(path)

    assert len(parsed["pages"]) == 1
    page = parsed["pages"][0]
    assert (page["width"], page["height"]) == (A4_WIDTH, A4_HEIGHT)
    assert any(block["type"] == "image" for block in page["blocks"])
    assert parsed["text"] == ""


def test_a_wide_picture_gets_a_landscape_page(tmp_path):
    path = make_image(tmp_path / "wide.png", width=800, height=300)

    page = ImageParser.parse(path)["pages"][0]

    assert (page["width"], page["height"]) == (A4_HEIGHT, A4_WIDTH)


def test_the_picture_is_scaled_into_the_page(tmp_path):
    path = make_image(tmp_path / "huge.png", width=3000, height=4000)

    with fitz.open("pdf", image_to_pdf(path)) as document:
        rect = document[0].get_image_rects(document[0].get_images()[0][0])[0]

    assert rect.x1 <= A4_WIDTH and rect.y1 <= A4_HEIGHT


def test_the_document_parser_dispatches_images(tmp_path):
    path = make_image(tmp_path / "cv.jpg", fmt="jpeg")

    assert len(DocumentParser().parse(path)["pages"]) == 1


def test_a_file_that_is_not_an_image_is_unreadable(tmp_path):
    path = tmp_path / "fake.png"
    path.write_bytes(b"\x89PNG\r\n\x1a\nnot really")

    assert image_problem(path) is not None

    with pytest.raises(UnreadableFileError):
        ImageParser.parse(path)


def test_a_huge_picture_is_refused(tmp_path, monkeypatch):
    path = make_image(tmp_path / "big.png", width=300, height=400)
    monkeypatch.setattr(
        "app.resume_processing.parsers.image_parser.MAX_IMAGE_PIXELS", 1000
    )

    assert "too large" in image_problem(path)
    assert MAX_IMAGE_PIXELS > 1_000_000


def test_images_are_only_accepted_when_ocr_is_on(monkeypatch):
    monkeypatch.setattr(settings, "OCR_ENABLED", False)
    assert ".png" not in allowed_extensions()

    monkeypatch.setattr(settings, "OCR_ENABLED", True)
    assert {".png", ".jpg", ".jpeg", ".pdf", ".docx"} <= allowed_extensions()


def test_image_signatures_are_checked():
    validate_signature(".png", b"\x89PNG\r\n\x1a\n....")
    validate_signature(".jpg", b"\xff\xd8\xff\xe0....")

    with pytest.raises(InvalidUploadError):
        validate_signature(".png", b"\xff\xd8\xff\xe0....")


def test_a_valid_image_upload_is_saved_and_a_broken_one_removed(tmp_path):
    good = make_image(tmp_path / "source.png").read_bytes()
    destination = tmp_path / "saved.png"

    assert save_upload(io.BytesIO(good), destination, ".png", 1_000_000) == len(good)

    broken = tmp_path / "broken.png"

    with pytest.raises(InvalidUploadError):
        save_upload(io.BytesIO(b"\x89PNG\r\n\x1a\ngarbage"), broken, ".png", 1_000_000)

    assert not broken.exists()


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract is not installed")
def test_text_in_a_picture_is_read_with_ocr(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "OCR_ENABLED", True)
    monkeypatch.setattr(settings, "OCR_LANGUAGES", "eng")

    with fitz.open() as document:
        page = document.new_page()
        page.insert_text((72, 100), "Backend Engineer at Northwind Labs", fontsize=24)
        picture = page.get_pixmap(dpi=200)

    path = tmp_path / "scan.png"
    path.write_bytes(picture.tobytes("png"))

    parsed = ImageParser.parse(path)

    assert "northwind" in parsed["text"].lower()
    assert parsed["pages"][0]["ocr"] is True
