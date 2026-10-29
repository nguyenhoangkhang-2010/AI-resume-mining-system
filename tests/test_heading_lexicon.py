import unicodedata

import pytest

from app.extraction.section.heading_lexicon import (
    heading_section,
    looks_like_contact,
    normalise,
    split_by_headings,
    split_contact_header,
)


@pytest.mark.parametrize(
    "line, section",
    [
        ("Work Experience", "experience"),
        ("WORK EXPERIENCE", "experience"),
        ("Professional Experience", "experience"),
        ("Employment History", "experience"),
        ("Internships", "experience"),
        ("Kinh nghiệm làm việc", "experience"),
        ("KINH NGHIỆM LÀM VIỆC", "experience"),
        ("Quá trình công tác", "experience"),
        ("Education", "education"),
        ("Education and Training", "education"),
        ("Học vấn", "education"),
        ("Quá trình học tập", "education"),
        ("Skills", "skills"),
        ("Technical Skills", "skills"),
        ("Core Competencies", "skills"),
        ("Kỹ năng", "skills"),
        ("Kỹ năng chuyên môn", "skills"),
        ("Projects", "projects"),
        ("Personal Projects", "projects"),
        ("Dự án", "projects"),
        ("Certifications", "certifications"),
        ("Licenses & Certifications", "certifications"),
        ("Chứng chỉ", "certifications"),
        ("Giải thưởng", "certifications"),
        ("Summary", "summary"),
        ("Career Objective", "summary"),
        ("About Me", "summary"),
        ("Mục tiêu nghề nghiệp", "summary"),
        ("Contact Information", "personal_info"),
        ("Thông tin cá nhân", "personal_info"),
        ("References", "other"),
        ("Hobbies", "other"),
    ],
)
def test_recognises_headings(line, section):
    assert heading_section(line) == section


@pytest.mark.parametrize(
    "line",
    [
        "Education:",
        "1. Education",
        "II) Skills",
        "  Work   Experience  ",
        "Relevant Work Experience",
        "My Skills",
    ],
)
def test_ignores_punctuation_numbering_and_qualifiers(line):
    assert heading_section(line) is not None


def test_composite_heading_uses_the_first_section():
    assert heading_section("Skills and Certifications") == "skills"
    assert heading_section("Education & Training") == "education"


def test_decomposed_unicode_is_recognised():
    decomposed = unicodedata.normalize("NFD", "Kinh nghiệm làm việc")

    assert decomposed != "Kinh nghiệm làm việc"
    assert heading_section(decomposed) == "experience"


def test_text_without_diacritics_is_recognised():
    assert heading_section("Hoc van") == "education"
    assert heading_section("Ky nang") == "skills"


@pytest.mark.parametrize(
    "line",
    [
        "Skills in Python and SQL",
        "Experience with Docker and Kubernetes",
        "Built an education platform for schools.",
        "Senior Project Manager at Acme",
        "Backend Engineer - Acme",
        "2020 - 2023",
        "Education 2019",
        "Nguyen Van An",
        "Python, SQL, Docker",
        "",
        "   ",
        "Work Experience Summary of Achievements in Several Companies Worldwide",
    ],
)
def test_ordinary_lines_are_not_headings(line):
    assert heading_section(line) is None


def test_normalise_strips_accents_and_punctuation():
    assert normalise("Đào tạo & Học vấn:") == "dao tao hoc van"


def test_split_by_headings_removes_headings_and_keeps_lead_in():
    text = "\n".join(
        [
            "Nguyen Van An",
            "Work Experience",
            "Backend Engineer",
            "Built APIs",
            "Education",
            "BSc Computer Science",
        ]
    )

    assert split_by_headings(text) == [
        (None, "Nguyen Van An"),
        ("experience", "Backend Engineer\nBuilt APIs"),
        ("education", "BSc Computer Science"),
    ]


def test_split_by_headings_drops_empty_sections():
    assert split_by_headings("Skills\nEducation\nBSc") == [("education", "BSc")]


def test_split_by_headings_without_headings():
    assert split_by_headings("just some text") == [(None, "just some text")]


@pytest.mark.parametrize(
    "text",
    [
        "someone@example.com",
        "+84 912 345 678",
        "linkedin.com/in/someone",
        "github.com/someone",
    ],
)
def test_looks_like_contact(text):
    assert looks_like_contact(text)


@pytest.mark.parametrize("text", ["Backend Engineer", "2020 - 2023", "Built APIs"])
def test_ordinary_text_is_not_contact(text):
    assert not looks_like_contact(text)


def test_contact_header_ends_after_contact_and_location_lines():
    text = "\n".join(
        [
            "Nguyen Van An",
            "an@example.com",
            "+84 912 345 678",
            "Ha Noi",
            "Experienced engineer who builds reliable services for banks.",
        ]
    )

    header, rest = split_contact_header(text)

    assert header == "Nguyen Van An\nan@example.com\n+84 912 345 678\nHa Noi"
    assert rest == "Experienced engineer who builds reliable services for banks."


def test_contact_header_does_not_swallow_body_text():
    text = "\n".join(
        [
            "an@example.com",
            "Built payment services using Python for several years.",
        ]
    )

    header, rest = split_contact_header(text)

    assert header == "an@example.com"
    assert rest.startswith("Built payment services")


def test_no_contact_means_no_header():
    header, rest = split_contact_header("Backend Engineer\nBuilt APIs")

    assert header == ""
    assert rest == "Backend Engineer\nBuilt APIs"
