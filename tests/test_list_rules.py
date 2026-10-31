import pytest

from app.core.config.settings import settings
from app.extraction.certifications.certification_extractor import (
    CertificationExtractor,
)
from app.extraction.projects.project_extractor import ProjectExtractor
from app.extraction.rules import stats
from app.extraction.rules.list_rules import parse_certifications, parse_projects
from tests.fakes.fake_llm_extractor import FakeLLMExtractor

# ---------------------------------------------------------- certifications


def test_one_certificate_per_line():
    certs = parse_certifications(
        "AWS Certified Cloud Practitioner\nProfessional Scrum Master I\nGoogle Data Analytics Certificate"
    )

    assert [c["name"] for c in certs] == [
        "AWS Certified Cloud Practitioner",
        "Professional Scrum Master I",
        "Google Data Analytics Certificate",
    ]


def test_bullets_are_removed_and_years_become_the_issue_date():
    certs = parse_certifications("- TESOL Certificate (2021)\n- IELTS 8.0 - 2019")

    assert certs[0]["name"] == "TESOL Certificate"
    assert certs[0]["issue_date"] == "2021"
    assert certs[1]["issue_date"] == "2019"


def test_an_issuer_is_split_off_when_it_looks_like_an_organisation():
    cert = parse_certifications("Data Analytics - Google Education Institute")[0]

    assert cert["name"] == "Data Analytics"
    assert cert["issuer"] == "Google Education Institute"


def test_a_pair_without_an_organisation_stays_one_name():
    cert = parse_certifications("Project Management - Level 2")[0]

    assert cert["name"] == "Project Management - Level 2"
    assert cert["issuer"] is None


def test_a_link_is_kept():
    cert = parse_certifications("Cloud Practitioner https://example.com/verify/123")[0]

    assert cert["credential_url"] == "https://example.com/verify/123"


@pytest.mark.parametrize(
    "text",
    [
        "",
        "I completed many courses and earned several certificates over the years.",
        # the second line may be the wrapped end of the first
        "Chartered Financial Analyst\nLevel II",
        "One certificate\n" + "word " * 20,
    ],
)
def test_unclear_certificate_lists_go_to_the_model(text):
    assert parse_certifications(text) is None


def test_a_short_certificate_after_a_short_one_is_still_a_certificate():
    certs = parse_certifications("PMP\nCSM")

    assert [c["name"] for c in certs] == ["PMP", "CSM"]


# ---------------------------------------------------------------- projects


def test_titles_with_bullets():
    projects = parse_projects(
        "Order tracking platform\n- Built the API\n- Added tests\n"
        "Log analysis toolkit\n- Parsed nightly logs"
    )

    assert [p["title"] for p in projects] == [
        "Order tracking platform",
        "Log analysis toolkit",
    ]
    assert projects[0]["description"] == ["Built the API", "Added tests"]


def test_a_title_followed_by_a_paragraph():
    projects = parse_projects(
        "Hand hygiene audit\nChecked compliance on four wards and reported the results."
    )

    assert projects[0]["description"] == [
        "Checked compliance on four wards and reported the results."
    ]


def test_dates_technologies_and_links_are_read():
    project = parse_projects(
        "Order tracking platform\n2023 - 2024\nTech stack: Python, FastAPI; Redis\n"
        "- Built the API\n- Source: https://github.com/example/orders."
    )[0]

    assert (project["start_date"], project["end_date"]) == ("2023", "2024")
    assert project["technologies"] == ["Python", "FastAPI", "Redis"]
    assert project["url"] == "https://github.com/example/orders"
    assert "Tech stack" not in " ".join(project["description"])


def test_wrapped_bullets_stay_in_one_description_item():
    project = parse_projects(
        "Search features\n- Built the ranking service for the\nproduct catalogue"
    )[0]

    assert project["description"] == [
        "Built the ranking service for the product catalogue"
    ]


@pytest.mark.parametrize(
    "text",
    [
        "",
        "- bullet without a title\n- another",
        "Title one\nTitle two\n- bullet",
        "Title with nothing under it",
        "A long first line that is a sentence and not a title at all, so it cannot be one.",
    ],
)
def test_unclear_project_sections_go_to_the_model(text):
    assert parse_projects(text) is None


# ------------------------------------------------- inside the extractors


@pytest.fixture
def rules_on(monkeypatch):
    monkeypatch.setattr(settings, "EXTRACTION_RULES_FIRST", True)
    stats.reset()


def test_extractors_use_the_rules_without_the_model(rules_on):
    llm = FakeLLMExtractor("{}")

    certs = CertificationExtractor(llm).extract("AWS Certified Cloud Practitioner")
    projects = ProjectExtractor(llm).extract("Search features\n- Built the ranking service")

    assert certs[0]["name"] == "AWS Certified Cloud Practitioner"
    assert projects[0]["title"] == "Search features"
    assert llm.calls == []
    assert stats.snapshot() == {"certifications.rules": 1, "projects.rules": 1}


def test_extractors_ask_the_model_when_the_rules_give_up(rules_on):
    llm = FakeLLMExtractor('{"certifications": [{"name": "PMP"}]}')

    certs = CertificationExtractor(llm).extract("Chartered Financial Analyst\nLevel II")

    assert certs[0]["name"] == "PMP"
    assert len(llm.calls) == 1
    assert stats.snapshot() == {"certifications.model": 1}
