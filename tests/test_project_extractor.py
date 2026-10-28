from app.extraction.projects.project_extractor import ProjectExtractor
from tests.fakes.fake_llm_extractor import FakeLLMExtractor


def test_project_extraction():
    llm = FakeLLMExtractor(
        {
            "projects": [
                {
                    "title": "AI Resume Mining System",
                    "description": ["Built NLP pipeline using FastAPI"],
                    "technologies": ["FastAPI", "FAISS"],
                }
            ]
        }
    )

    result = ProjectExtractor(llm_extractor=llm).extract(
        "PROJECTS\nAI Resume Mining System\n"
        "- Built NLP pipeline using FastAPI"
    )

    assert len(result) == 1
    assert result[0]["title"] == "AI Resume Mining System"
    assert "Built NLP pipeline using FastAPI" in result[0]["description"]
    assert result[0]["technologies"] == ["FastAPI", "FAISS"]


def test_invalid_output_returns_empty_list():
    llm = FakeLLMExtractor("not json")

    assert ProjectExtractor(llm_extractor=llm).extract("text") == []


def test_empty_text_skips_llm():
    llm = FakeLLMExtractor({"projects": [{"title": "X"}]})

    assert ProjectExtractor(llm_extractor=llm).extract("") == []
    assert llm.calls == []
