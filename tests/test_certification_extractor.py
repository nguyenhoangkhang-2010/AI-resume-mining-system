from app.extraction.certifications.certification_extractor import (
    CertificationExtractor,
)
from tests.fakes.fake_llm_extractor import FakeLLMExtractor


def test_certification_extraction():
    llm = FakeLLMExtractor(
        {
            "certifications": [
                {
                    "name": "AWS Certified Cloud Practitioner",
                    "issuer": "Amazon Web Services",
                },
                {"name": "Google Data Analytics Certificate"},
            ]
        }
    )

    result = CertificationExtractor(llm).extract(
        "CERTIFICATIONS\nAWS Certified Cloud Practitioner\n"
        "Google Data Analytics Certificate"
    )

    assert len(result) == 2
    assert result[0]["name"] == "AWS Certified Cloud Practitioner"
    assert result[0]["issuer"] == "Amazon Web Services"
    assert result[1]["name"] == "Google Data Analytics Certificate"


def test_certification_accepts_bare_list_and_code_fence():
    llm = FakeLLMExtractor(
        '```json\n[{"name": "PMP", "issuer": "PMI"}]\n```'
    )

    result = CertificationExtractor(llm).extract("PMP")

    assert [item["name"] for item in result] == ["PMP"]


def test_certification_invalid_output_returns_empty_list():
    llm = FakeLLMExtractor("this is not json")

    assert CertificationExtractor(llm).extract("some text") == []


def test_certification_empty_text_skips_llm():
    llm = FakeLLMExtractor({"certifications": [{"name": "X"}]})

    assert CertificationExtractor(llm).extract("   ") == []
    assert llm.calls == []
