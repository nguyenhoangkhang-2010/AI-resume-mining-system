from unittest.mock import Mock

import pytest

from app.extraction import extraction_engine as engine_module
from app.extraction.extraction_engine import ExtractionEngine
from tests.fakes.fake_llm_extractor import FakeLLMExtractor


@pytest.fixture
def engine(monkeypatch):
    """
    Engine whose heavy collaborators (NER models, semantic skill
    matcher) are replaced, so only the orchestration is exercised.
    """

    monkeypatch.setattr(engine_module, "NERService", Mock())
    monkeypatch.setattr(engine_module, "SkillExtractor", Mock())

    engine = ExtractionEngine(llm_extractor=FakeLLMExtractor())

    engine.extractors = {
        name: Mock(extract=Mock(return_value=f"{name}-result"))
        for name in engine.extractors
    }

    return engine


def test_extract_resume_runs_every_extractor(engine):
    result = engine.extract_resume(
        {
            "personal_info": ["Nguyen Van A", "a@gmail.com"],
            "education": ["Bachelor of IT"],
        }
    )

    assert set(result) == {
        "personal_info",
        "summary",
        "education",
        "experience",
        "projects",
        "certifications",
        "skills",
    }


def test_extract_resume_passes_section_text_to_extractor(engine):
    engine.extract_resume({"education": ["Bachelor of IT", "HCMUT"]})

    engine.extractors["education"].extract.assert_called_once_with(
        "Bachelor of IT\nHCMUT"
    )


def test_skills_extractor_receives_full_text(engine):
    engine.extract_resume(
        {"education": ["Bachelor of IT"], "summary": ["Python developer"]}
    )

    full_text = engine.extractors["skills"].extract.call_args.args[0]

    assert "Bachelor of IT" in full_text
    assert "Python developer" in full_text


def test_personal_info_falls_back_to_full_text(engine):
    engine.extract_resume({"summary": ["Contact: a@gmail.com"]})

    engine.extractors["personal_info"].extract.assert_called_once_with(
        "Contact: a@gmail.com"
    )


def test_empty_sections_return_empty_result(engine):
    assert engine.extract_resume({}) == {}


def test_extractor_failure_is_propagated(engine):
    engine.extractors["education"].extract.side_effect = RuntimeError("boom")

    with pytest.raises(RuntimeError):
        engine.extract_resume({"education": ["Bachelor of IT"]})
