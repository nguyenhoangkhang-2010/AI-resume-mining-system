import json

import pytest

from app.core.config.settings import settings
from app.extraction.rules import vocabulary
from app.extraction.rules.dates import find_range, is_present
from app.extraction.rules.education_rules import parse_education
from app.extraction.rules.experience_rules import parse_experience
from app.extraction.rules.titles import (
    company_score,
    ends_with_company_suffix,
    is_degree,
    is_institution,
    is_location,
    role_score,
    split_location,
)
from app.extraction.rules.vocabulary import (
    BUILTIN_DIRECTORY,
    Terms,
    build,
    get_vocabulary,
    load_vocabulary,
    read_file,
)

FRENCH = {
    "language": "fr",
    "roles": {"words": ["ingénieur", "développeur"], "phrases": ["chef de projet"]},
    "companies": {"words": ["sarl"], "phrases": ["société", "groupe"]},
    "institutions": {"words": ["université", "école"]},
    "degrees": {"words": ["licence", "master"]},
    "months": ["janvier", "février", "mars"],
    "present": ["aujourd'hui", "à ce jour"],
    "places": {"words": ["france"], "phrases": ["paris"]},
}


@pytest.fixture
def french(tmp_path, monkeypatch):
    (tmp_path / "fr.json").write_text(json.dumps(FRENCH), encoding="utf-8")
    monkeypatch.setattr(settings, "VOCABULARY_DIR", str(tmp_path))
    vocabulary.clear_cache()

    yield tmp_path

    vocabulary.clear_cache()


# ----------------------------------------------------------------- loading


def test_the_built_in_files_cover_english_and_vietnamese():
    built_in = get_vocabulary()

    assert {"en", "vi"} <= set(built_in.languages)
    assert role_score("Senior Backend Engineer") >= 1
    assert role_score("Kỹ sư phần mềm") >= 1
    assert company_score("Công ty Cổ phần ABC") >= 1


def test_matching_ignores_case_and_accents():
    assert role_score("KY SU PHAN MEM") == role_score("kỹ sư phần mềm") >= 1
    assert is_institution("ĐẠI HỌC BÁCH KHOA") and is_institution("dai hoc bach khoa")
    assert is_degree("Cử nhân Kinh tế") and is_degree("BSc in Nursing")


def test_a_word_matches_whole_words_only():
    assert role_score("Engineering") == 0 and role_score("Engineer") == 1
    assert company_score("Universal") == 0


def test_terms_count_distinct_words_and_phrases():
    terms = Terms(frozenset({"engineer"}), ("project manager",))

    assert terms.count("Project Manager and Engineer, Engineer") == 2
    assert terms.count("nothing here") == 0


def test_covers_means_nothing_but_known_terms():
    terms = Terms(frozenset({"vietnam"}), ("ho chi minh city",))

    assert terms.covers("Ho Chi Minh City") and terms.covers("Vietnam")
    assert terms.covers("Ho Chi Minh City, Vietnam".replace(",", ""))
    assert not terms.covers("Vietnam Airlines")
    assert not terms.covers("")


def test_files_are_merged_and_duplicates_collapse():
    merged = build(
        [
            {"roles": {"words": ["Engineer"]}, "months": ["Jan"]},
            {"roles": {"words": ["engineer", "Nurse"]}, "months": ["jan", "Feb"]},
        ]
    )

    assert merged.roles.words == frozenset({"engineer", "nurse"})
    assert merged.months == ("jan", "feb")


# --------------------------------------------------------------- validation


@pytest.mark.parametrize(
    "content, message",
    [
        ("{not json", "cannot be read as JSON"),
        ("[1, 2]", "expected a JSON object"),
        ('{"colours": ["red"]}', "unknown keys"),
        ('{"roles": ["engineer"]}', "needs 'words' and/or 'phrases'"),
        ('{"roles": {"verbs": ["run"]}}', "needs 'words' and/or 'phrases'"),
        ('{"roles": {"words": "engineer"}}', "expected a list of non-empty strings"),
        ('{"months": ["jan", ""]}', "expected a list of non-empty strings"),
    ],
)
def test_a_bad_file_is_reported_by_name(tmp_path, content, message):
    path = tmp_path / "broken.json"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match=rf"broken\.json: .*{message}"):
        read_file(path)


def test_the_built_in_files_are_valid():
    for path in BUILTIN_DIRECTORY.glob("*.json"):
        read_file(path)


def test_a_missing_directory_is_ignored(tmp_path):
    assert load_vocabulary([tmp_path / "absent"]).languages == ()


# --------------------------------------------- a language added as data only


def test_another_language_is_added_with_a_file_and_no_code(french):
    vocab = get_vocabulary()

    assert "fr" in vocab.languages
    assert role_score("Ingénieur logiciel") == 1
    assert role_score("Chef de projet") == 1
    assert is_institution("Université de Lyon") and is_degree("Licence d'informatique")
    assert is_location("Paris, France")


def test_the_extra_language_reads_dates_and_jobs(french):
    assert find_range("janvier 2020 - aujourd'hui").end == "aujourd'hui"
    assert is_present("à ce jour")

    jobs = parse_experience(
        "Ingénieur logiciel - Société Dupont\njanvier 2020 - aujourd'hui\n"
        "- Développement d'API\n"
        "Chef de projet - Groupe Martin\nmars 2017 - février 2019\n- Pilotage"
    )

    assert [(job["role"], job["company"]) for job in jobs] == [
        ("Ingénieur logiciel", "Société Dupont"),
        ("Chef de projet", "Groupe Martin"),
    ]
    assert jobs[0]["end_date"] == "aujourd'hui"


def test_the_extra_language_reads_education(french):
    entries = parse_education("Licence d'informatique\nUniversité de Lyon\n2012 - 2015")

    assert entries[0]["institution"] == "Université de Lyon"
    assert entries[0]["degree_level"] == ["Licence d'informatique"]


def test_without_the_file_the_same_french_text_is_not_understood():
    assert parse_experience(
        "Ingénieur logiciel - Société Dupont\njanvier 2020 - aujourd'hui\n- API"
    ) is None


# ------------------------------------------------------------- date formats


@pytest.mark.parametrize(
    "line, start, end",
    [
        ("2021.04–pres.", "2021.04", "pres."),
        ("2018.02–2018.12", "2018.02", "2018.12"),
        ("Sep. 2018 – Present", "Sep. 2018", "Present"),
        ("Aug. 2012 – Dec. 2013", "Aug. 2012", "Dec. 2013"),
        ("June 2020 – Present", "June 2020", "Present"),
        ("2019 until 2021", "2019", "2021"),
    ],
)
def test_more_date_formats(line, start, end):
    found = find_range(line)

    assert (found.start, found.end) == (start, end)


def test_a_date_in_brackets_leaves_no_brackets_behind():
    assert find_range("Backend Engineer (2020 - 2023)").rest == "Backend Engineer"
    assert find_range("Role [Jan 2020 - Dec 2021]").rest == "Role"
    assert find_range("Engineer at Acme (France). 2021.04–pres.").rest == "Engineer at Acme (France)"


# ----------------------------------------------------------------- places


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Mountain View, CA", True),
        ("Georgetown, TX", True),
        ("Hanoi, Vietnam", True),
        ("Ho Chi Minh City", True),
        ("Hà Nội, Việt Nam", True),
        ("Remote", True),
        ("Luxembourg", True),
        ("Vietnam Airlines", False),
        ("BRITISH AMERICAN TOBACCO (BAT) VIETNAM - VINA-BAT", False),
        ("Brightside Agency", False),
        ("Suite 12, Floor 3", False),
        ("", False),
    ],
)
def test_places(text, expected):
    assert is_location(text) is expected


def test_a_trailing_country_is_split_off_a_name():
    assert split_location("Shockelasrull (Luxembourg).") == ("Shockelasrull", "Luxembourg")
    assert split_location("Acme (BAT) Vietnam") == ("Acme (BAT) Vietnam", None)


def test_company_suffixes_keep_their_full_stop():
    assert ends_with_company_suffix("Everlasting Gobstopper Ltd.")
    assert ends_with_company_suffix("Whipple Inc.")
    assert not ends_with_company_suffix("Built payment services.")
