import unicodedata
from collections import Counter

import fitz
import pytest

from app.evaluation.cv_corpus import (
    ALTERNATE_STYLES,
    HEADING_STYLES,
    LAYOUTS,
    CorpusDocument,
    CVCorpusBuilder,
    TruthLine,
    find_unicode_fonts,
)
from app.evaluation.section_eval import (
    aggregate,
    group_accuracy,
    predicted_line_labels,
    score_document,
)
from app.extraction.section.section_detector import SectionDetector
from app.resume_processing.parsers.pdf_parser import PDFParser, clean_pdf_text
from app.resume_processing.pipelines.resume_pipeline import ResumePipeline


class NeverConfident:
    def classify(self, text):
        return "other", 0.0


class NoLLM:
    def classify_single(self, text):
        return "other", 0.0

    def classify_document(self, lines):
        return []


@pytest.fixture(scope="module")
def corpus(tmp_path_factory):
    directory = tmp_path_factory.mktemp("corpus")

    return CVCorpusBuilder(seed=11, per_variant=1).build(directory)


def test_corpus_covers_styles_layouts_and_languages(corpus):
    standard = [d for d in corpus if d.wording == "standard"]

    assert {d.style for d in standard} == set(HEADING_STYLES)
    assert {d.layout for d in standard} == set(LAYOUTS)
    assert "en" in {d.language for d in standard}
    assert {d.style for d in corpus if d.wording == "alternate"} == set(
        ALTERNATE_STYLES
    )


def test_corpus_is_deterministic(tmp_path):
    first = CVCorpusBuilder(seed=5, per_variant=1).build(tmp_path / "a")
    second = CVCorpusBuilder(seed=5, per_variant=1).build(tmp_path / "b")

    assert [d.truth for d in first] == [d.truth for d in second]


def test_truth_lines_are_unique_within_a_document(corpus):
    for document in corpus:
        counts = Counter(line.text for line in document.truth)

        assert max(counts.values()) == 1, document.id


def test_every_document_has_all_sections(corpus):
    expected = {
        "personal_info", "summary", "experience", "education",
        "skills", "projects", "certifications",
    }

    for document in corpus:
        assert {line.section for line in document.truth} == expected


def test_documents_are_real_pdfs_with_extractable_text(corpus):
    for document in corpus:
        with fitz.open(document.path) as pdf:
            assert len(pdf) >= 1
            assert pdf[0].get_text().strip()


def test_multi_page_documents_have_several_pages(corpus):
    pages = {
        d.id: len(fitz.open(d.path))
        for d in corpus
        if d.layout == "multi_page"
    }

    assert any(count > 1 for count in pages.values())


@pytest.mark.skipif(
    find_unicode_fonts() is None, reason="needs a TrueType font with Vietnamese glyphs"
)
def test_vietnamese_documents_keep_their_diacritics(corpus):
    document = next(d for d in corpus if d.language == "vi")

    text = PDFParser.parse(document.path)["text"]

    assert "Học vấn" in text or "HỌC VẤN" in text.upper()


def test_standard_wording_is_detected_whatever_the_layout(corpus):
    """
    The regression this corpus exists for: with the heading wording known,
    bold same-size, uppercase and tight headings in single, two-column and
    multi-page layouts must all be split correctly, with no model involved.
    """

    pipeline = ResumePipeline(
        SectionDetector(NeverConfident(), NoLLM()),
        extraction_engine=None,  # type: ignore[arg-type]
    )

    standard = [d for d in corpus if d.wording == "standard"]

    results = [
        score_document(document, pipeline.detect_sections(document.path))
        for document in standard
    ]

    scores = aggregate(results)

    assert scores["all"].f1 >= 0.97

    by_style = group_accuracy(standard, results, "style")

    assert min(by_style.values()) >= 0.95


# ------------------------------------------------------------- evaluation


def _document(truth):
    return CorpusDocument(
        id="d", style="s", layout="single", language="en", path=None, truth=truth
    )


def test_predicted_labels_ignore_case_whitespace_and_private_keys():
    labels = predicted_line_labels(
        {"skills": ["Python,   SQL"], "__projects_regions__": ["hidden"]}
    )

    assert labels == {"python, sql": "skills"}


def test_score_document_counts_correct_wrong_and_missing_lines():
    document = _document(
        [
            TruthLine("skills", "Python"),
            TruthLine("education", "BSc"),
            TruthLine("experience", "Built APIs"),
        ]
    )

    result = score_document(
        document, {"skills": ["Python"], "projects": ["BSc"]}
    )

    assert result.correct == 1
    assert result.total == 3
    assert result.confusion[("education", "projects")] == 1
    assert result.confusion[("experience", "missing")] == 1


def test_aggregate_reports_precision_recall_and_micro_accuracy():
    document = _document(
        [
            TruthLine("skills", "a"),
            TruthLine("skills", "b"),
            TruthLine("education", "c"),
        ]
    )

    result = score_document(document, {"skills": ["a", "c"]})

    scores = aggregate([result])

    assert scores["skills"].precision == 0.5
    assert scores["skills"].recall == 0.5
    assert scores["education"].recall == 0.0
    assert scores["all"].f1 == pytest.approx(1 / 3)


# ------------------------------------------------------------ text cleaning


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Software Developer", "Software Developer"),
        ("2020­2023", "2020-2023"),
        ("certiﬁcate", "certificate"),
        ("zero​width", "zerowidth"),
        ("Hello world", "Hello world"),
    ],
)
def test_clean_pdf_text(raw, expected):
    assert clean_pdf_text(raw) == expected


def test_decomposed_vietnamese_is_composed():
    decomposed = unicodedata.normalize("NFD", "Kinh nghiệm")

    assert decomposed != "Kinh nghiệm"
    assert clean_pdf_text(decomposed) == "Kinh nghiệm"
