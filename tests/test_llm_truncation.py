"""
LLM output is cut off at the token limit. A cut list must keep the entries
that were completed, whichever character the cut falls on.
"""

import json

import pytest

from app.core.config.settings import settings
from app.extraction.certifications.certification_extractor import (
    CertificationExtractor,
)
from app.extraction.education.education_extractor import EducationExtractor
from app.extraction.experience.experience_extractor import ExperienceExtractor
from app.extraction.llm.json_recovery import recover_array_objects
from app.extraction.projects.project_extractor import ProjectExtractor
from tests.fakes.fake_llm_extractor import FakeLLMExtractor

EXPERIENCE = {
    "experience": [
        {
            "company": "Acme",
            "role": "Backend Engineer",
            "start_date": "2020",
            "end_date": "2023",
            "description": ["Built APIs, with \"quotes\" and a [bracket]", "Wrote tests"],
        },
        {
            "company": "Globex",
            "role": "Data Engineer",
            "start_date": "2017",
            "end_date": "2020",
            "description": ["Ran {pipelines} nightly"],
        },
        {
            "company": "Initech",
            "role": "Intern",
            "start_date": "2016",
            "end_date": "2017",
            "description": [],
        },
    ]
}


def object_end_positions(text):
    """Where each object of the first array ends, found with the json module."""

    decoder = json.JSONDecoder()
    position = text.index("[") + 1
    ends = []

    while True:
        while text[position].isspace() or text[position] == ",":
            position += 1

        if text[position] != "{":
            return ends

        _, position = decoder.raw_decode(text, position)
        ends.append(position)


def complete_objects_before(text, cut):
    """How many objects of the array are fully written before the cut."""

    return sum(1 for end in object_end_positions(text) if end <= cut)


# ----------------------------------------------------------- the helper


@pytest.mark.parametrize("pretty", [False, True])
def test_recovery_keeps_complete_objects_at_every_cut(pretty):
    text = json.dumps(EXPERIENCE, indent=2 if pretty else None)
    items = EXPERIENCE["experience"]

    for cut in range(len(text) + 1):
        recovered = recover_array_objects(text[:cut], "experience")

        expected = complete_objects_before(text, cut)

        assert len(recovered or []) == expected, (cut, text[:cut][-30:])

        if recovered:
            assert recovered == items[:expected]


def test_recovery_without_a_key_uses_the_first_array():
    text = '[{"a": 1}, {"a": 2}, {"a": 3'

    assert recover_array_objects(text) == [{"a": 1}, {"a": 2}]


def test_recovery_returns_none_without_an_array_or_key():
    assert recover_array_objects('{"other": [{"a": 1}]', "experience") is None
    assert recover_array_objects("no json at all") is None
    assert recover_array_objects('{"experience": [') is None


def test_recovery_ignores_braces_and_brackets_inside_strings():
    text = '{"experience": [{"role": "a } b ] c"}, {"role": "x'

    assert recover_array_objects(text, "experience") == [{"role": "a } b ] c"}]


# --------------------------------------------------------- the extractors


# The extractors keep only names that appear in the section they were given.
SECTION_TEXT = (
    "Acme Backend Engineer. Globex Data Engineer. Initech Intern. "
    "University A. University B."
)


def run(extractor_class, text, **kwargs):
    llm = FakeLLMExtractor(text)

    return extractor_class(llm, **kwargs).extract(SECTION_TEXT), llm


def test_experience_keeps_completed_entries_when_cut():
    full = json.dumps(EXPERIENCE)
    second_end = object_end_positions(full)[1]

    result, _ = run(ExperienceExtractor, full[: second_end + 25])

    assert [entry["company"] for entry in result] == ["Acme", "Globex"]
    assert result[0]["description"][0].startswith("Built APIs")


def test_experience_cut_inside_the_first_entry_gives_nothing():
    full = json.dumps(EXPERIENCE)

    result, _ = run(ExperienceExtractor, full[:60])

    assert result == []


def test_experience_untruncated_output_is_unchanged():
    result, _ = run(ExperienceExtractor, json.dumps(EXPERIENCE))

    assert len(result) == 3


def test_experience_cut_inside_a_code_fence():
    full = "```json\n" + json.dumps(EXPERIENCE)
    cut = full.index("Globex") + 10

    result, _ = run(ExperienceExtractor, full[:cut])

    assert [entry["company"] for entry in result] == ["Acme"]


EDUCATION = {
    "education": [
        {"institution": "University A", "degree_level": ["Bachelor"], "start_year": 2012, "end_year": 2016},
        {"institution": "University B", "degree_level": ["Master"], "start_year": 2016, "end_year": 2018},
    ]
}


def test_education_keeps_completed_entries_when_cut():
    full = json.dumps(EDUCATION)
    cut = full.index("University B") + 5

    result, _ = run(EducationExtractor, full[:cut])

    assert [entry["institution"] for entry in result] == ["University A"]


def test_education_cut_inside_the_only_entry_gives_nothing():
    result, _ = run(EducationExtractor, json.dumps(EDUCATION)[:40])

    assert result == []


PROJECTS = {
    "projects": [
        {"title": "Resume Miner", "technologies": ["fastapi"]},
        {"title": "Lakehouse", "technologies": ["spark"]},
    ]
}


def test_projects_keep_completed_entries_when_cut():
    full = json.dumps(PROJECTS)
    cut = full.index("Lakehouse") + 3

    result, _ = run(ProjectExtractor, full[:cut])

    assert [entry["title"] for entry in result] == ["Resume Miner"]


CERTIFICATIONS = {
    "certifications": [{"name": "AWS Certified Cloud Practitioner"}, {"name": "PMP"}]
}


def test_certifications_still_recover_after_the_refactor():
    full = json.dumps(CERTIFICATIONS)
    cut = full.index("PMP") + 1

    result, _ = run(CertificationExtractor, full[:cut])

    assert [entry["name"] for entry in result] == ["AWS Certified Cloud Practitioner"]


# ----------------------------------------------------------- the limits


class RecordingLLM(FakeLLMExtractor):
    def extract_info(self, text, prompt_template=None, max_new_tokens=None):
        self.limit = max_new_tokens

        return super().extract_info(text, prompt_template, max_new_tokens)


@pytest.mark.parametrize(
    "extractor_class, setting",
    [
        (ExperienceExtractor, "LLM_EXPERIENCE_MAX_TOKENS"),
        (EducationExtractor, "LLM_EDUCATION_MAX_TOKENS"),
        (ProjectExtractor, "LLM_PROJECTS_MAX_TOKENS"),
    ],
)
def test_token_limits_come_from_settings(extractor_class, setting, monkeypatch):
    monkeypatch.setattr(settings, setting, 1234)

    llm = RecordingLLM({})

    extractor_class(llm).extract("some text")

    assert llm.limit == 1234


def test_default_experience_limit_is_larger_than_the_old_180():
    assert settings.LLM_EXPERIENCE_MAX_TOKENS > 180
