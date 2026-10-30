from app.extraction.education.education_extractor import (
    EducationExtractor,
)
from tests.fakes.fake_llm_extractor import FakeLLMExtractor


def test_extract_full_education():
    llm = FakeLLMExtractor(
        {
            "education": [
                {
                    "institution": "Ho Chi Minh City University",
                    "degree_level": ["Bachelor"],
                    "start_year": 2021,
                    "end_year": 2025,
                    "gpa": "3.6/4",
                }
            ]
        }
    )

    result = EducationExtractor(llm).extract(
        "Bachelor of Information Technology\n"
        "Ho Chi Minh City University\nGPA: 3.6"
    )

    assert len(result) == 1
    assert result[0]["institution"] == "Ho Chi Minh City University"
    assert result[0]["start_year"] == 2021
    assert result[0]["end_year"] == 2025
    assert result[0]["gpa"] == 3.6


def test_extract_multiple_entries():
    llm = FakeLLMExtractor(
        {
            "education": [
                {"institution": "University A", "degree_level": ["Bachelor"]},
                {"institution": "University B", "degree_level": ["Master"]},
            ]
        }
    )

    result = EducationExtractor(llm).extract("University A and University B")

    assert [item["institution"] for item in result] == [
        "University A",
        "University B",
    ]


def test_empty_entries_are_dropped():
    llm = FakeLLMExtractor(
        {"education": [{"institution": None, "degree_level": []}]}
    )

    assert EducationExtractor(llm).extract("text") == []


def test_invalid_output_returns_empty_list():
    llm = FakeLLMExtractor("not json")

    assert EducationExtractor(llm).extract("text") == []


def test_empty_text():
    llm = FakeLLMExtractor({"education": [{"institution": "X"}]})

    assert EducationExtractor(llm).extract("") == []
    assert EducationExtractor(llm).extract(None) == []
    assert llm.calls == []
