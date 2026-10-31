import pytest
from loguru import logger

from app.core.logger.redaction import (
    EMAIL_MASK,
    PHONE_MASK,
    PROFILE_URL_MASK,
    redact_pii,
    redaction_patcher,
)


def test_redact_email():
    result = redact_pii("contact: trucnguyen250109@gmail.com ok")

    assert "trucnguyen250109@gmail.com" not in result
    assert EMAIL_MASK in result


@pytest.mark.parametrize(
    "phone",
    [
        "+84) 981 379 105",
        "+84 981 379 105",
        "0981379105",
        "(028) 3822 1234",
        "+1-415-555-0132",
    ],
)
def test_redact_phone(phone):
    result = redact_pii(f"phone: {phone}")

    assert phone not in result
    assert PHONE_MASK in result


@pytest.mark.parametrize(
    "url",
    [
        "https://www.linkedin.com/in/some-person",
        "github.com/some-person",
    ],
)
def test_redact_profile_url(url):
    result = redact_pii(f"profile {url} end")

    assert url not in result
    assert PROFILE_URL_MASK in result


@pytest.mark.parametrize(
    "message",
    [
        "Resume pipeline completed in 12.345s",
        "Loaded 14253 skills from taxonomy.",
        "Created at 2026-08-15 22:43:20",
        "Generated 1000 characters.",
        "Education 2019 - 2023",
    ],
)
def test_non_pii_messages_unchanged(message):
    assert redact_pii(message) == message


def test_redact_empty_string():
    assert redact_pii("") == ""


def test_patcher_masks_record_message():
    record = {"message": "email a.b@example.com phone 0981379105"}

    redaction_patcher(record)

    assert "a.b@example.com" not in record["message"]
    assert "0981379105" not in record["message"]


def test_logger_sink_hides_pii_and_local_variables():
    captured = []

    logger.remove()
    logger.configure(patcher=redaction_patcher)
    sink_id = logger.add(
        captured.append,
        format="{message}",
        backtrace=False,
        diagnose=False,
    )

    try:
        contact = {"email": "leak.me@example.com"}  # noqa: F841

        try:
            raise RuntimeError("boom")
        except RuntimeError:
            logger.exception("failed for leak.me@example.com")
    finally:
        logger.remove(sink_id)
        logger.configure(patcher=lambda record: None)

    output = "".join(str(item) for item in captured)

    assert "leak.me@example.com" not in output
    assert EMAIL_MASK in output
