import io
from types import SimpleNamespace

import fitz
import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from app.api.dependencies import get_resume_service
from app.core.config.settings import settings
from app.core.exceptions import (
    FileTooLargeError,
    InvalidUploadError,
    UnsupportedFileTypeError,
)
from app.database.mongodb.connection import mongo_db
from app.main import app
from app.resume_processing.parsers.pdf_parser import PDFParser
from app.services.resume_quality import (
    FAILED,
    NEEDS_REVIEW,
    PROCESSED,
    assess_extraction,
    failure_reason,
)
from app.services.resume_service import ResumeService
from app.services.upload_validation import save_upload, validate_signature

LONG_TEXT = "Backend engineer with several years of experience. " * 3


# ------------------------------------------------------------ assessment


def test_empty_text_needs_review_as_no_text_extracted():
    result = assess_extraction({"raw_text": "  ", "cleaned_text": ""})

    assert result.status == NEEDS_REVIEW
    assert result.reason == "no_text_extracted"


def test_text_without_any_extracted_content_needs_review():
    result = assess_extraction({"raw_text": LONG_TEXT})

    assert result.status == NEEDS_REVIEW
    assert result.reason == "no_content_extracted"


def test_complete_resume_has_no_warnings():
    result = assess_extraction(
        {
            "raw_text": LONG_TEXT,
            "skills": ["python"],
            "experience": [{"role": "Engineer"}],
            "education": [{"institution": "HCMUT"}],
            "personal_info": {"full_name": "An", "email": "an@example.com"},
        }
    )

    assert result.status == PROCESSED
    assert result.warnings == []


def test_partial_resume_is_processed_with_warnings():
    result = assess_extraction(
        {"raw_text": LONG_TEXT, "skills": ["python"], "personal_info": {}}
    )

    assert result.status == PROCESSED
    assert set(result.warnings) == {
        "no_experience_found",
        "no_education_found",
        "no_name_found",
        "no_contact_found",
    }


def test_phone_alone_counts_as_contact():
    result = assess_extraction(
        {
            "raw_text": LONG_TEXT,
            "education": [{"institution": "X"}],
            "personal_info": {"full_name": "An", "phone": "+84 912 345 678"},
        }
    )

    assert "no_contact_found" not in result.warnings


class FileDataError(Exception):
    pass


@pytest.mark.parametrize(
    "error, reason",
    [
        (FileNotFoundError("x"), "file_missing"),
        (FileDataError("broken"), "unreadable_file"),
        (ValueError("Failed to decrypt PDF 'a.pdf'."), "password_protected"),
        (RuntimeError("anything else"), "processing_error"),
    ],
)
def test_failure_reasons(error, reason):
    assert failure_reason(error) == reason


def test_failure_reason_never_contains_the_exception_message():
    assert "secret" not in failure_reason(RuntimeError("secret resume text"))


# --------------------------------------------------- ResumeService flow


class FakeCollection:
    def __init__(self, document):
        self.document = document
        self.updates = []

    def find_one(self, query, projection=None):
        return self.document

    def update_one(self, query, update):
        self.updates.append(update["$set"])


def make_service(monkeypatch, pipeline_result=None, error=None):
    resumes = FakeCollection({"_id": ObjectId(), "file_path": "x.pdf", "filename": "x.pdf"})

    class Pipeline:
        def process_pdf(self, path):
            if error:
                raise error

            return pipeline_result

    service = ResumeService.__new__(ResumeService)
    service.resume_pipeline = Pipeline()
    service.saved = []
    service._build_candidate = lambda resume_id, extracted_data: SimpleNamespace()
    service._save_candidate = lambda candidate: service.saved.append(candidate)

    monkeypatch.setattr(ResumeService, "resumes_col", property(lambda self: resumes))

    return service, resumes


def test_unusable_result_is_not_indexed_and_is_marked_needs_review(monkeypatch):
    service, resumes = make_service(monkeypatch, {"raw_text": "", "cleaned_text": ""})

    service.process_resume(str(ObjectId()))

    assert service.saved == []

    last = resumes.updates[-1]

    assert last["upload_status"] == NEEDS_REVIEW
    assert last["status_reason"] == "no_text_extracted"


def test_usable_result_is_indexed_and_keeps_warnings(monkeypatch):
    service, resumes = make_service(
        monkeypatch, {"raw_text": LONG_TEXT, "skills": ["python"]}
    )

    service.process_resume(str(ObjectId()))

    assert len(service.saved) == 1

    last = resumes.updates[-1]

    assert last["upload_status"] == PROCESSED
    assert last["status_reason"] is None
    assert "no_experience_found" in last["warnings"]


def test_failure_stores_a_reason_and_still_raises(monkeypatch):
    service, resumes = make_service(monkeypatch, error=FileDataError("broken"))

    with pytest.raises(FileDataError):
        service.process_resume(str(ObjectId()))

    last = resumes.updates[-1]

    assert last["upload_status"] == FAILED
    assert last["status_reason"] == "unreadable_file"


# ------------------------------------------------------------ status API


def test_status_endpoint_returns_reason_and_warnings(monkeypatch):
    document = {
        "_id": ObjectId(),
        "upload_status": "needs_review",
        "status_reason": "no_text_extracted",
        "warnings": [],
    }

    class Collection:
        def find_one(self, query):
            return document

    monkeypatch.setattr(
        mongo_db, "get_db", lambda: {"resumes": Collection()}
    )

    response = TestClient(app).get(f"/api/v1/resumes/{document['_id']}/status")

    assert response.status_code == 200
    assert response.json() == {
        "resume_id": str(document["_id"]),
        "status": "needs_review",
        "reason": "no_text_extracted",
        "warnings": [],
    }


# ----------------------------------------------------- upload validation


PDF_BYTES = b"%PDF-1.7\n" + b"x" * 100
DOCX_BYTES = b"PK\x03\x04" + b"x" * 100


@pytest.mark.parametrize(
    "extension, header",
    [
        (".pdf", PDF_BYTES),
        (".pdf", b"junk" + PDF_BYTES),
        (".docx", DOCX_BYTES),
    ],
)
def test_valid_signatures_pass(extension, header):
    validate_signature(extension, header)


@pytest.mark.parametrize(
    "extension, header",
    [
        (".pdf", b"<html>not a pdf</html>"),
        (".pdf", b"PK\x03\x04zip"),
        (".docx", PDF_BYTES),
    ],
)
def test_wrong_content_is_rejected(extension, header):
    with pytest.raises(InvalidUploadError):
        validate_signature(extension, header)


def test_empty_and_unknown_types_are_rejected():
    with pytest.raises(InvalidUploadError):
        validate_signature(".pdf", b"")

    with pytest.raises(UnsupportedFileTypeError):
        validate_signature(".exe", b"MZ")


def test_save_upload_writes_the_file(tmp_path):
    destination = tmp_path / "cv.pdf"

    written = save_upload(io.BytesIO(PDF_BYTES), destination, ".pdf", 10_000)

    assert written == len(PDF_BYTES)
    assert destination.read_bytes() == PDF_BYTES


def test_oversized_upload_is_rejected_and_removed(tmp_path):
    destination = tmp_path / "cv.pdf"

    with pytest.raises(FileTooLargeError):
        save_upload(io.BytesIO(PDF_BYTES), destination, ".pdf", 50)

    assert not destination.exists()


def test_upload_with_wrong_content_leaves_no_file(tmp_path):
    destination = tmp_path / "cv.pdf"

    with pytest.raises(InvalidUploadError):
        save_upload(io.BytesIO(b"not a pdf"), destination, ".pdf", 10_000)

    assert not destination.exists()


def test_empty_upload_leaves_no_file(tmp_path):
    destination = tmp_path / "cv.pdf"

    with pytest.raises(InvalidUploadError):
        save_upload(io.BytesIO(b""), destination, ".pdf", 10_000)

    assert not destination.exists()


class UploadOnlyService:
    def __init__(self):
        self.created = []

    def create_resume(self, file_path, filename):
        self.created.append((file_path, filename))

        return SimpleNamespace(
            id="665f1c2b8e4a4b0012345678",
            filename=filename,
            upload_status="pending",
            created_at="2026-01-01T00:00:00",
        )

    def process_resume(self, resume_id):
        pass


@pytest.fixture
def upload_client(tmp_path, monkeypatch):
    from app.api.routes.v1 import resume_routes

    monkeypatch.setattr(resume_routes, "UPLOAD_DIR", tmp_path)

    service = UploadOnlyService()
    app.dependency_overrides[get_resume_service] = lambda: service

    yield TestClient(app, raise_server_exceptions=False), service, tmp_path

    app.dependency_overrides.clear()


def test_upload_accepts_a_real_pdf(upload_client):
    client, service, directory = upload_client

    response = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("cv.pdf", PDF_BYTES, "application/pdf")},
    )

    assert response.status_code == 202
    assert len(service.created) == 1
    assert len(list(directory.iterdir())) == 1


def test_upload_rejects_unknown_extension_with_415(upload_client):
    client, service, _ = upload_client

    response = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("cv.exe", b"MZ....", "application/octet-stream")},
    )

    assert response.status_code == 415
    assert response.json()["code"] == "unsupported_file_type"
    assert service.created == []


def test_upload_rejects_a_renamed_file_with_400(upload_client):
    client, service, directory = upload_client

    response = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("cv.pdf", b"<html>hello</html>", "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "invalid_upload"
    assert service.created == []
    assert list(directory.iterdir()) == []


def test_upload_rejects_a_large_file_with_413(upload_client, monkeypatch):
    client, service, directory = upload_client

    monkeypatch.setattr(settings, "MAX_UPLOAD_MB", 1)

    big = b"%PDF-1.7\n" + b"0" * (1024 * 1024 + 10)

    response = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("cv.pdf", big, "application/pdf")},
    )

    assert response.status_code == 413
    assert response.json()["code"] == "file_too_large"
    assert list(directory.iterdir()) == []


# --------------------------------------------------------------------- OCR


@pytest.fixture
def scanned_pdf(tmp_path):
    source = fitz.open()
    page = source.new_page()
    page.insert_text((72, 100), "WORK EXPERIENCE", fontsize=14)
    page.insert_text((72, 130), "Backend Engineer at Acme", fontsize=10)

    text_dict = page.get_text("dict")

    pixmap = page.get_pixmap(dpi=100)

    scan = fitz.open()
    scanned_page = scan.new_page()
    scanned_page.insert_image(scanned_page.rect, pixmap=pixmap)

    path = tmp_path / "scan.pdf"
    scan.save(str(path))
    scan.close()
    source.close()

    return path, text_dict


def test_scanned_pdf_has_no_text_without_ocr(scanned_pdf, monkeypatch):
    path, _ = scanned_pdf

    monkeypatch.setattr(settings, "OCR_ENABLED", False)

    assert PDFParser.parse(path)["text"] == ""


def test_ocr_text_is_used_for_image_only_pages(scanned_pdf, monkeypatch):
    path, text_dict = scanned_pdf

    monkeypatch.setattr(settings, "OCR_ENABLED", True)

    calls = []

    def fake_textpage_ocr(self, **kwargs):
        calls.append(kwargs)
        return "textpage"

    original_get_text = fitz.Page.get_text

    def fake_get_text(self, option="text", *args, **kwargs):
        if kwargs.get("textpage") == "textpage":
            return text_dict

        return original_get_text(self, option, *args, **kwargs)

    monkeypatch.setattr(fitz.Page, "get_textpage_ocr", fake_textpage_ocr)
    monkeypatch.setattr(fitz.Page, "get_text", fake_get_text)

    parsed = PDFParser.parse(path)

    assert "WORK EXPERIENCE" in parsed["text"]
    assert calls[0]["language"] == settings.OCR_LANGUAGES


def test_missing_tesseract_degrades_to_empty_text(scanned_pdf, monkeypatch):
    path, _ = scanned_pdf

    monkeypatch.setattr(settings, "OCR_ENABLED", True)

    def no_tesseract(self, **kwargs):
        raise RuntimeError("Tesseract is not installed")

    monkeypatch.setattr(fitz.Page, "get_textpage_ocr", no_tesseract)

    assert PDFParser.parse(path)["text"] == ""


def test_ocr_is_not_attempted_for_pages_that_have_text(tmp_path, make_pdf, monkeypatch):
    monkeypatch.setattr(settings, "OCR_ENABLED", True)

    def fail(self, **kwargs):
        raise AssertionError("OCR must not run on a page with text")

    monkeypatch.setattr(fitz.Page, "get_textpage_ocr", fail)

    assert "Hello resume" in PDFParser.parse(make_pdf(["Hello resume"]))["text"]
