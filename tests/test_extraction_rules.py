import pytest

from app.core.config.settings import settings
from app.extraction.education.education_extractor import EducationExtractor
from app.extraction.experience.experience_extractor import ExperienceExtractor
from app.extraction.rules import stats
from app.extraction.rules.dates import find_range, is_present, year_of
from app.extraction.rules.education_rules import parse_education
from app.extraction.rules.experience_rules import (
    explain_experience,
    parse_experience,
)
from app.extraction.rules.summary_rules import parse_summary
from app.extraction.summary.summary_extractor import SummaryExtractor
from tests.fakes.fake_llm_extractor import FakeLLMExtractor


@pytest.fixture
def rules_on(monkeypatch):
    monkeypatch.setattr(settings, "EXTRACTION_RULES_FIRST", True)
    stats.reset()


# ----------------------------------------------------------------- dates


@pytest.mark.parametrize(
    "line, start, end",
    [
        ("2020 - 2023", "2020", "2023"),
        ("2020–2023", "2020", "2023"),
        ("Jan 2020 - Present", "Jan 2020", "Present"),
        ("March, 2019 to June 2021", "March, 2019", "June 2021"),
        ("03/2020 – 05/2022", "03/2020", "05/2022"),
        ("Tháng 3/2020 - nay", "Tháng 3/2020", "nay"),
        ("2018 - Hiện tại", "2018", "Hiện tại"),
    ],
)
def test_date_ranges_are_found(line, start, end):
    found = find_range(line)

    assert (found.start, found.end) == (start, end)


@pytest.mark.parametrize(
    "line", ["2021", "Python 3.10", "Backend Engineer", "Grew sales 40% in 2020"]
)
def test_lines_without_a_range_have_none(line):
    assert find_range(line) is None


def test_the_rest_of_a_line_is_kept_without_separators():
    found = find_range("Backend Engineer | 2020 - 2023")

    assert found.rest == "Backend Engineer"
    assert found.share < 0.5


def test_present_and_year_helpers():
    assert is_present("Present") and is_present("nay") and not is_present("2023")
    assert year_of("2019 - 2021") == 2021
    assert year_of("no year") is None


# ------------------------------------------------------------ experience

HEADER_FIRST = """Backend Engineer - Northwind Labs
2022 - 2025
- Built payment services
- Designed reporting pipelines using
Python and SQL
Data Engineer - Bluepeak Systems
Jan 2019 - Dec 2021
- Automated deployment scripts"""


def test_header_dates_bullets_layout():
    jobs = parse_experience(HEADER_FIRST)

    assert [(j["role"], j["company"]) for j in jobs] == [
        ("Backend Engineer", "Northwind Labs"),
        ("Data Engineer", "Bluepeak Systems"),
    ]
    assert jobs[0]["start_date"] == "2022"
    assert jobs[1]["end_date"] == "Dec 2021"


def test_wrapped_bullets_are_joined():
    jobs = parse_experience(HEADER_FIRST)

    assert jobs[0]["description"] == [
        "Built payment services",
        "Designed reporting pipelines using Python and SQL",
    ]


def test_dates_then_header_layout():
    text = """2022 - 2025
Backend Engineer
Northwind Labs
- Built payment services
2019 - 2022
Data Engineer
Bluepeak Systems
- Automated deployment scripts"""

    jobs = parse_experience(text)

    assert [(j["role"], j["company"]) for j in jobs] == [
        ("Backend Engineer", "Northwind Labs"),
        ("Data Engineer", "Bluepeak Systems"),
    ]
    assert jobs[1]["description"] == ["Automated deployment scripts"]


def test_header_and_dates_on_one_line():
    jobs = parse_experience(
        "Staff Nurse | 2021 - Present\n- Monitored patients\n"
        "Ward Manager | 2018 - 2021\n- Led a team"
    )

    assert [(j["role"], j["company"]) for j in jobs] == [
        ("Staff Nurse", None),
        ("Ward Manager", None),
    ]
    assert jobs[0]["end_date"] == "Present"


def test_two_header_lines_in_either_order():
    jobs = parse_experience(
        "St Mary General Hospital\nStaff Nurse\n2021 - 2024\n- Monitored patients"
    )

    assert (jobs[0]["role"], jobs[0]["company"]) == (
        "Staff Nurse",
        "St Mary General Hospital",
    )


def test_vietnamese_roles_and_dates():
    jobs = parse_experience(
        "Kỹ sư phần mềm - Công ty FPT\nTháng 3/2020 - nay\n- Xây dựng dịch vụ"
    )

    assert (jobs[0]["role"], jobs[0]["company"]) == ("Kỹ sư phần mềm", "Công ty FPT")
    assert jobs[0]["end_date"] == "nay"


def test_a_bullet_that_mentions_years_is_not_a_job():
    jobs = parse_experience(
        "Backend Engineer - Northwind Labs\n2022 - 2025\n- Migrated systems 2023-2024"
    )

    assert len(jobs) == 1
    assert jobs[0]["description"] == ["Migrated systems 2023-2024"]


@pytest.mark.parametrize(
    "text, reason",
    [
        ("Built things\nWrote code", "no date range"),
        ("", "no date range"),
        ("Some stray line\nBackend Engineer - Northwind Labs\n2022 - 2025", "role and company not told apart"),
        ("BAT - British American Tobacco\n2020 - 2022\n- Sold", "role and company not told apart"),
        ("Acme\nBackend Engineer\nNorth\n2020 - 2022", "role and company not told apart"),
    ],
)
def test_unclear_layouts_are_left_to_the_model(text, reason):
    assert parse_experience(text) is None
    assert explain_experience(text) == reason


def test_a_clear_layout_has_no_reason_to_give_up():
    assert explain_experience(HEADER_FIRST) == ""


def test_one_unclear_job_hands_the_whole_section_to_the_model():
    text = HEADER_FIRST + "\nBAT - British American Tobacco\n2015 - 2018\n- Sold"

    assert parse_experience(text) is None


# ------------------------------------------------------------- education


def test_degree_school_years_layout():
    entries = parse_education(
        "BSc in Computer Science\nHanoi University of Science\n2016 - 2020"
    )

    assert entries == [
        {
            "institution": "Hanoi University of Science",
            "degree_level": ["BSc in Computer Science"],
            "start_year": 2016,
            "end_year": 2020,
            "gpa": None,
        }
    ]


def test_school_degree_years_layout_with_gpa():
    entries = parse_education(
        "Da Nang University of Technology\nBachelor of Engineering\n2014 - 2018\nGPA: 3.6/4.0"
    )

    assert entries[0]["degree_level"] == ["Bachelor of Engineering"]
    assert entries[0]["gpa"] == 3.6
    assert (entries[0]["start_year"], entries[0]["end_year"]) == (2014, 2018)


def test_school_and_degree_on_one_line():
    entries = parse_education("BSc in Nursing, Hanoi Medical University\n2015 - 2019")

    assert entries[0]["institution"] == "Hanoi Medical University"
    assert entries[0]["degree_level"] == ["BSc in Nursing"]


def test_two_schools_keep_their_own_degrees_and_years():
    entries = parse_education(
        "MSc in Data Science\nCan Tho University\n2020 - 2022\n"
        "BSc in Mathematics\nHue University\n2016 - 2020"
    )

    assert [(e["institution"], e["degree_level"][0], e["end_year"]) for e in entries] == [
        ("Can Tho University", "MSc in Data Science", 2022),
        ("Hue University", "BSc in Mathematics", 2020),
    ]


def test_vietnamese_education():
    entries = parse_education("Cử nhân Khoa học Máy tính\nĐại học Bách khoa Hà Nội\n2015 - 2019")

    assert entries[0]["institution"] == "Đại học Bách khoa Hà Nội"
    assert entries[0]["degree_level"] == ["Cử nhân Khoa học Máy tính"]


def test_a_single_year_is_an_end_year():
    entries = parse_education("Hue University\nBSc\n2019")

    assert (entries[0]["start_year"], entries[0]["end_year"]) == (None, 2019)


@pytest.mark.parametrize(
    "text",
    ["", "Self taught", "Some course on the internet\n2019", "Lots of unrelated words here\nHue University"],
)
def test_education_it_cannot_read_goes_to_the_model(text):
    assert parse_education(text) is None


# --------------------------------------------------------------- summary


def test_a_paragraph_is_its_own_summary():
    assert parse_summary("Engineer focused on\nreliable systems.") == (
        "Engineer focused on reliable systems."
    )


@pytest.mark.parametrize(
    "text",
    [
        "",
        "Engineer.\nreach me at a@b.co",
        "- skill one\n- skill two",
        "word " * 400,
        "\n".join(["line"] * 20),
    ],
)
def test_other_text_is_left_to_the_model(text):
    assert parse_summary(text) is None


# ------------------------------------------------- inside the extractors


def test_the_extractors_skip_the_model_when_the_rules_answer(rules_on):
    llm = FakeLLMExtractor("{}")

    assert ExperienceExtractor(llm).extract(HEADER_FIRST)[0]["role"] == "Backend Engineer"
    assert EducationExtractor(llm).extract("BSc\nHue University\n2016 - 2020")
    assert SummaryExtractor(llm).extract("Engineer focused on reliable systems.")
    assert llm.calls == []
    assert stats.snapshot() == {
        "experience.rules": 1,
        "education.rules": 1,
        "summary.rules": 1,
    }


def test_the_extractors_ask_the_model_when_the_rules_give_up(rules_on):
    llm = FakeLLMExtractor(
        '{"experience": [{"company": "BAT", "role": null, "description": []}]}'
    )

    result = ExperienceExtractor(llm).extract("BAT - British American Tobacco\n2020 - 2022")

    assert len(llm.calls) == 1
    assert stats.snapshot() == {"experience.model": 1}
    assert result[0]["company"] == "BAT"


def test_the_rules_can_be_turned_off(monkeypatch):
    monkeypatch.setattr(settings, "EXTRACTION_RULES_FIRST", False)
    llm = FakeLLMExtractor('{"experience": []}')

    ExperienceExtractor(llm).extract(HEADER_FIRST)

    assert len(llm.calls) == 1


# ------------------------------------- layouts seen in real CVs (invented data)


def pairs(jobs):
    return [(job["role"], job["company"]) for job in jobs]


def test_role_at_company_with_the_country_and_a_dotted_date():
    jobs = parse_experience(
        "Senior data scientist at Acme Corp (Luxembourg). 2021.04–pres.\n"
        "⋄Natural language processing, topic modelling\n"
        "Data analyst at Globex Ltd. (France).\n"
        "2018.02–2018.12\n"
        "⋄Data collection processes"
    )

    assert pairs(jobs) == [
        ("Senior data scientist", "Acme Corp"),
        ("Data analyst", "Globex Ltd."),
    ]
    assert [job["location"] for job in jobs] == ["Luxembourg", "France"]
    assert jobs[0]["end_date"] == "pres."
    assert jobs[1]["description"] == ["Data collection processes"]


def test_title_dates_employer_and_city_in_that_order():
    jobs = parse_experience(
        "Undergraduate Research Assistant\nJune 2020 – Present\nTexas Tech University\n"
        "Lubbock, TX\n• Developed a REST API\n"
        "Information Technology Support Specialist\nSep. 2018 – Present\n"
        "Southern University\nGeorgetown, TX\n• Maintained campus computers"
    )

    assert pairs(jobs) == [
        ("Undergraduate Research Assistant", "Texas Tech University"),
        ("Information Technology Support Specialist", "Southern University"),
    ]
    assert jobs[0]["location"] == "Lubbock, TX"
    assert jobs[1]["description"] == ["Maintained campus computers"]


def test_a_word_for_a_sector_in_a_title_does_not_make_it_an_employer():
    jobs = parse_experience(
        "Information Technology Support Specialist\n2018 - 2020\nSouthern University\n- Fixed printers"
    )

    assert pairs(jobs) == [("Information Technology Support Specialist", "Southern University")]


MARKED = (
    "• Alpha Systems\nAustin, TX\nSoftware Engineer\nOct 2016 - Present\n"
    "◦Built pipelines for training the models used in production every day\n"
    "• Beta Labs\nAustin, TX\nSenior Software Engineer\nJan 2014 - Oct 2016\n"
    "◦Wrote the notification services that send millions of emails per day\n"
)


def test_employers_marked_with_their_own_symbol():
    jobs = parse_experience(MARKED)

    assert pairs(jobs) == [
        ("Software Engineer", "Alpha Systems"),
        ("Senior Software Engineer", "Beta Labs"),
    ]
    assert jobs[0]["description"][0].startswith("Built pipelines")


def test_an_employer_without_a_readable_date_hands_the_section_to_the_model():
    text = MARKED + "• Gamma Works\nBoston, MA\nData Scientist\nSummer 2012 and 2013\n◦Created models for hedging\n"

    assert parse_experience(text) is None


def test_employer_line_with_a_dash_dates_then_the_title():
    jobs = parse_experience(
        "BIG BANK PLC - HEAD OFFICE\nFeb 2026 - Present\nProduction Intern\n- Coordinated project documents"
    )

    assert pairs(jobs) == [("Production Intern", "BIG BANK PLC - HEAD OFFICE")]


@pytest.mark.parametrize(
    "text",
    [
        "Engineer\nManager\n2020 - 2022\n- Did things",
        "Some Team\nOther Team\n2020 - 2022\n- Did things",
        "Backend Engineer - Acme Systems\nStray Words\n2020 - 2022\n- Did things",
    ],
)
def test_headers_that_cannot_be_typed_go_to_the_model(text):
    assert parse_experience(text) is None


def test_a_short_bullet_per_job_is_not_mistaken_for_an_employer_marker():
    jobs = parse_experience(
        "Backend Engineer - Acme Systems\n2022 - 2025\n- Wrote tests\n"
        "Data Engineer - Globex Labs\n2019 - 2022\n- Fixed bugs\n"
        "Intern - Initech Software\n2018 - 2019\n- Learned"
    )

    assert pairs(jobs) == [
        ("Backend Engineer", "Acme Systems"),
        ("Data Engineer", "Globex Labs"),
        ("Intern", "Initech Software"),
    ]


# ------------------------------------------------------ education: safeguards


@pytest.mark.parametrize(
    "text",
    [
        # a school line cut off in the middle of a word
        "Bachelor of Science in Biology. Faculty of Experimental Confec-\ntionery. State Technical University.\n2006-2010",
        # a degree and a school run together as two sentences
        "Master in Economics. University of Sweets and Treats.\n2013-2015",
        # the wrapped end of a line
        "BSc in Nursing\nHue University\n2015 - 2019\nof Medicine and Pharmacy University",
        # a mention of a university that is not an education entry
        "Took part in writing, University Newsletter",
        # a school with neither a degree nor a year
        "Hue University\nPlease contact the office",
    ],
)
def test_education_that_may_be_misread_goes_to_the_model(text):
    assert parse_education(text) is None


def test_clean_education_is_still_read():
    entries = parse_education("BSc in Nursing\nHue University\n2015 - 2019")

    assert entries[0]["institution"] == "Hue University"
