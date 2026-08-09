from app.extraction.contact.contact_extractor import ContactExtractor


def test_markdown_email():
    text = "[a@gmail.com](mailto:a@gmail.com)"

    extractor = ContactExtractor()

    print("INPUT:", repr(text))
    print(
        "PATTERN:",
        repr(extractor.MARKDOWN_LINK_PATTERN.pattern),
    )

    match = extractor.MARKDOWN_LINK_PATTERN.search(text)

    print(
        "MATCH:",
        match.group(0) if match else None,
    )

    print(
        "GROUPS:",
        match.groups() if match else None,
    )

    print(
        "NORMALIZED:",
        repr(extractor._normalize_text(text)),
    )

    print(
        "RESULT:",
        extractor.extract(text),
    )

    assert extractor.extract(text) == {
        "email": "a@gmail.com"
    }