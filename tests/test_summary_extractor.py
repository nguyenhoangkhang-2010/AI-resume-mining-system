from app.extraction.summary import SummaryExtractor
from tests.fakes.fake_llm_extractor import FakeLLMExtractor


def test_extract_professional_summary():
    llm = FakeLLMExtractor(
        {"summary": "Data Engineer with experience in Python and SQL."}
    )

    result = SummaryExtractor(llm).extract(
        "PROFESSIONAL SUMMARY\nData Engineer with experience in Python and SQL."
    )

    assert result == "Data Engineer with experience in Python and SQL."


def test_extract_objective():
    llm = FakeLLMExtractor(
        '```json\n{"summary": "Looking for a Data Analyst position."}\n```'
    )

    result = SummaryExtractor(llm).extract("OBJECTIVE\nLooking for a Data Analyst position.")

    assert "Data Analyst" in result


def test_missing_summary():
    llm = FakeLLMExtractor({"summary": None})

    assert SummaryExtractor(llm).extract("EDUCATION\nBachelor Degree") is None


def test_blank_or_non_string_summary_is_none():
    assert SummaryExtractor(FakeLLMExtractor({"summary": "   "})).extract("text") is None
    assert SummaryExtractor(FakeLLMExtractor({"summary": 5})).extract("text") is None


def test_invalid_output_returns_none():
    assert SummaryExtractor(FakeLLMExtractor("not json")).extract("text") is None


def test_empty_text_skips_llm():
    llm = FakeLLMExtractor({"summary": "x"})

    assert SummaryExtractor(llm).extract("") is None
    assert llm.calls == []
