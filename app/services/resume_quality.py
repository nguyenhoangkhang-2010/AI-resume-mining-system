"""
Decides how a processed resume should be reported.

A resume is only "processed" when something usable was extracted from it.
Otherwise it is marked "needs_review" (the file was readable but yielded
nothing, for example a scanned PDF) so it is not silently indexed as an
empty candidate, and the reason is stored so the user can see why.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.security.prompt_safety import detect_prompt_injection

PROCESSED = "processed"
NEEDS_REVIEW = "needs_review"
FAILED = "failed"

NO_TEXT_EXTRACTED = "no_text_extracted"
NO_CONTENT_EXTRACTED = "no_content_extracted"

UNREADABLE_FILE = "unreadable_file"
PASSWORD_PROTECTED = "password_protected"
FILE_MISSING = "file_missing"
PROCESSING_ERROR = "processing_error"

POSSIBLE_PROMPT_INJECTION = "possible_prompt_injection"

MIN_TEXT_CHARS = 40


@dataclass
class ExtractionAssessment:
    status: str
    reason: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


def assess_extraction(extracted: Dict[str, Any]) -> ExtractionAssessment:
    """Classifies the output of the resume pipeline."""

    text = extracted.get("raw_text") or ""

    if len(text.strip()) < MIN_TEXT_CHARS:
        return ExtractionAssessment(NEEDS_REVIEW, NO_TEXT_EXTRACTED)

    skills = extracted.get("skills") or []
    experience = extracted.get("experience") or []
    education = extracted.get("education") or []

    if not (skills or experience or education):
        return ExtractionAssessment(NEEDS_REVIEW, NO_CONTENT_EXTRACTED)

    warnings: List[str] = []

    if not experience:
        warnings.append("no_experience_found")

    if not education:
        warnings.append("no_education_found")

    if not skills:
        warnings.append("no_skills_found")

    personal = extracted.get("personal_info") or {}

    if not personal.get("full_name"):
        warnings.append("no_name_found")

    if not (personal.get("email") or personal.get("phone")):
        warnings.append("no_contact_found")

    if detect_prompt_injection(text):
        warnings.append(POSSIBLE_PROMPT_INJECTION)

    return ExtractionAssessment(PROCESSED, warnings=warnings)


def failure_reason(error: BaseException) -> str:
    """
    A short machine-readable reason for a processing failure. The message of
    the exception is deliberately not stored: it can contain resume content.
    """

    if isinstance(error, FileNotFoundError):
        return FILE_MISSING

    name = type(error).__name__

    if name in {"FileDataError", "EmptyFileError"}:
        return UNREADABLE_FILE

    if isinstance(error, ValueError) and "decrypt" in str(error).lower():
        return PASSWORD_PROTECTED

    return PROCESSING_ERROR
