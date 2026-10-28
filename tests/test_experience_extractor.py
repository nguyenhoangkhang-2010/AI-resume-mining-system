from app.extraction.experience.experience_extractor import (
    ExperienceExtractor,
)
from tests.fakes.fake_llm_extractor import FakeLLMExtractor


def test_extract_experience_detail():
    llm = FakeLLMExtractor(
        {
            "experience": [
                {
                    "company": "Google",
                    "role": "Software Engineer",
                    "start_date": "2023",
                    "end_date": "Present",
                    "description": ["Built backend APIs"],
                    "achievements": ["Cut latency by 30%"],
                }
            ]
        }
    )

    result = ExperienceExtractor(llm).extract(
        "Google\nSoftware Engineer\n2023 - Present"
    )

    assert len(result) == 1
    assert result[0]["company"] == "Google"
    assert result[0]["role"] == "Software Engineer"
    assert result[0]["start_date"] == "2023"
    assert result[0]["description"] == ["Built backend APIs"]
    assert result[0]["achievements"] == ["Cut latency by 30%"]


def test_accepts_bare_list_output():
    llm = FakeLLMExtractor(
        [{"company": "ACME", "role": "Backend Developer"}]
    )

    result = ExperienceExtractor(llm).extract("ACME")

    assert result[0]["company"] == "ACME"


def test_entries_without_content_are_dropped():
    llm = FakeLLMExtractor({"experience": [{}, "not-a-dict"]})

    assert ExperienceExtractor(llm).extract("text") == []


def test_invalid_output_returns_empty_list():
    llm = FakeLLMExtractor("not json at all")

    assert ExperienceExtractor(llm).extract("text") == []


def test_empty_text_skips_llm():
    llm = FakeLLMExtractor({"experience": [{"company": "X"}]})

    assert ExperienceExtractor(llm).extract("  ") == []
    assert llm.calls == []
