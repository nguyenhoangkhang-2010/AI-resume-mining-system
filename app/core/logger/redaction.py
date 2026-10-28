import re


EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
)

PHONE_CANDIDATE_PATTERN = re.compile(
    r"\+?\d[\d\s().\-]{7,}\d"
)

DATE_PATTERN = re.compile(
    r"\d{4}-\d{2}-\d{2}"
)

PROFILE_URL_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?"
    r"(?:linkedin\.com|github\.com)/[^\s\"'<>,)]+",
    re.IGNORECASE,
)

MIN_PHONE_DIGITS = 9
MAX_PHONE_DIGITS = 15

EMAIL_MASK = "[EMAIL]"
PHONE_MASK = "[PHONE]"
PROFILE_URL_MASK = "[PROFILE_URL]"


def _mask_phone(match: re.Match) -> str:
    candidate = match.group(0)

    if DATE_PATTERN.search(candidate):
        return candidate

    digit_count = sum(
        char.isdigit()
        for char in candidate
    )

    if MIN_PHONE_DIGITS <= digit_count <= MAX_PHONE_DIGITS:
        return PHONE_MASK

    return candidate


def redact_pii(text: str) -> str:
    """
    Masks emails, phone numbers and LinkedIn/GitHub profile
    URLs so candidate contact details never reach the logs.
    """

    if not text:
        return text

    text = EMAIL_PATTERN.sub(EMAIL_MASK, text)
    text = PROFILE_URL_PATTERN.sub(PROFILE_URL_MASK, text)

    return PHONE_CANDIDATE_PATTERN.sub(_mask_phone, text)


def redaction_patcher(record: dict) -> None:
    """
    Loguru patcher applied to every log record before it
    reaches any sink.
    """

    record["message"] = redact_pii(record["message"])
