import re
from collections import Counter

import fitz
import pytest

from app.evaluation.cv_industries import (
    INDUSTRIES,
    LAYOUTS,
    EXTRA_TITLES,
    INDUSTRY,
    STANDARD,
    IndustryCorpusBuilder,
)
from app.evaluation.cv_corpus import CorpusDocument, TruthLine
from app.evaluation.section_eval import score_document
from app.resume_processing.parsers.pdf_parser import clean_pdf_text


@pytest.fixture(scope="module")
def corpus(tmp_path_factory):
    directory = tmp_path_factory.mktemp("industries")

    return IndustryCorpusBuilder(seed=3, per_variant=1).build(directory)


def test_corpus_covers_every_industry_layout_and_wording(corpus):
    assert {d.industry for d in corpus} == set(INDUSTRIES)
    assert {d.layout for d in corpus} == set(LAYOUTS)
    assert {d.wording for d in corpus} == {STANDARD, INDUSTRY}
    assert "en" in {d.language for d in corpus}


def test_corpus_is_deterministic(tmp_path):
    kwargs = dict(seed=9, industries=["finance"], layouts=["timeline", "single"])

    first = IndustryCorpusBuilder(**kwargs).build(tmp_path / "a")
    second = IndustryCorpusBuilder(**kwargs).build(tmp_path / "b")

    assert [d.truth for d in first] == [d.truth for d in second]
    assert [d.headings for d in first] == [d.headings for d in second]


def test_truth_lines_are_unique_within_a_document(corpus):
    for document in corpus:
        counts = Counter(line.text for line in document.truth)

        assert max(counts.values()) == 1, document.id


def test_every_truth_line_is_really_on_the_page(corpus):
    """
    A column that runs past the bottom of a page silently loses text; the
    truth would then claim lines the PDF does not contain.
    """

    for document in corpus:
        with fitz.open(document.path) as pdf:
            text = " ".join(
                " ".join(clean_pdf_text(page.get_text()).split()) for page in pdf
            )

        missing = [
            line.text
            for line in document.truth
            if " ".join(line.text.split()) not in text
        ]

        assert not missing, (document.id, missing[:3])


def test_documents_have_all_main_sections_and_some_extras(corpus):
    main = {
        "personal_info", "summary", "experience", "education",
        "skills", "projects", "certifications",
    }

    for document in corpus:
        sections = {line.section for line in document.truth}

        assert main <= sections, document.id
        assert "other" in sections or any(
            heading for heading, section in document.headings
            if section == "certifications"
        )


def test_extra_sections_are_labelled_other_except_awards(corpus):
    for key, titles in EXTRA_TITLES.items():
        for _, truth in titles.values():
            assert truth == ("certifications" if key == "awards" else "other")


def test_headings_match_the_sections_in_the_truth(corpus):
    for document in corpus:
        sections = {line.section for line in document.truth}

        for _, section in document.headings:
            assert section in sections, document.id


def test_industry_wording_differs_from_standard_wording(corpus):
    standard = {
        d.industry: {h for h, _ in d.headings}
        for d in corpus
        if d.wording == STANDARD and d.language == "en"
    }
    industry = {
        d.industry: {h.lower() for h, _ in d.headings}
        for d in corpus
        if d.wording == INDUSTRY and d.language == "en"
    }

    assert any(
        "clinical experience" in headings
        for headings in industry.values()
    )
    assert standard


def test_entities_are_recorded_for_field_level_checks(corpus):
    for document in corpus:
        assert document.entities["companies"]
        assert document.entities["schools"]
        assert document.entities["skills"]
        assert document.entities["name"]


def test_layouts_with_two_columns_use_two_columns(corpus):
    for document in corpus:
        if document.layout not in ("two_column", "sidebar_right", "banner_two_column"):
            continue

        with fitz.open(document.path) as pdf:
            x_starts = {
                round(block[0] / 50)
                for block in pdf[0].get_text("blocks")
            }

        assert len(x_starts) >= 2, document.id


def test_long_layout_runs_to_several_pages(corpus):
    pages = [
        len(fitz.open(d.path)) for d in corpus if d.layout == "long"
    ]

    assert max(pages) >= 2


def test_timeline_puts_dates_beside_the_text(corpus):
    document = next(d for d in corpus if d.layout == "timeline")

    with fitz.open(document.path) as pdf:
        lines = [
            (line["bbox"][0], "".join(span["text"] for span in line["spans"]))
            for page in pdf
            for block in page.get_text("dict")["blocks"]
            for line in block.get("lines", [])
        ]

    date_range = re.compile(r"^\d{4}\D+\d{4}$")
    dates = [x for x, text in lines if date_range.match(clean_pdf_text(text).strip())]

    assert dates and max(dates) < 60, "dates belong in the left-hand column"


# ------------------------------------------------------- scoring of "other"


def _document(truth):
    return CorpusDocument(
        id="d", style="s", layout="single", language="en", path=None, truth=truth
    )


def test_dropping_a_line_of_an_ignored_section_is_correct():
    document = _document([TruthLine("other", "Available on request")])

    result = score_document(document, {"skills": []})

    assert result.correct == 1


def test_leaking_an_ignored_line_into_a_real_section_is_an_error():
    document = _document([TruthLine("other", "Available on request")])

    result = score_document(document, {"certifications": ["Available on request"]})

    assert result.correct == 0
    assert result.confusion[("other", "certifications")] == 1
