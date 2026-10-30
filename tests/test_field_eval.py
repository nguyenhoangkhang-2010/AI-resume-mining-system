import pytest

from app.evaluation.cv_industries import IndustryCorpusBuilder
from app.evaluation.field_eval import (
    FIELDS,
    aggregate_fields,
    entities_from_extraction,
    field_table,
    same_entity,
    score_fields,
)


def test_equal_ignoring_case_accents_and_punctuation():
    assert same_entity("Đại học Y Hà Nội", "dai hoc y ha noi")
    assert same_entity("Northwind Labs", "NORTHWIND LABS.")


def test_a_longer_text_containing_the_entity_matches():
    assert same_entity("Northwind Labs", "Backend Engineer at Northwind Labs")


def test_a_fragment_of_one_word_does_not_match():
    assert not same_entity("Hanoi University of Science", "Hanoi")
    assert not same_entity("Python", "Python developer with 5 years")


def test_unrelated_texts_do_not_match():
    assert not same_entity("Bluepeak Systems", "Orchid Software")
    assert not same_entity("", "anything")


def test_perfect_extraction_scores_one():
    expected = {name: ["a b c"] for name in FIELDS}

    scores = score_fields(expected, expected)

    assert all(score.f1 == 1.0 for score in scores.values())


def test_missing_and_extra_entities_lower_recall_and_precision():
    expected = {"companies": ["Northwind Labs", "Bluepeak Systems"]}
    extracted = {"companies": ["Northwind Labs", "Invented Corporation"]}

    score = score_fields(expected, extracted)["companies"]

    assert score.recall == 0.5
    assert score.precision == 0.5


def test_an_absent_field_scores_zero_not_an_error():
    score = score_fields({"skills": ["Python"]}, {})["skills"]

    assert (score.precision, score.recall, score.f1) == (0.0, 0.0, 0.0)
    assert score.expected == 1


def test_duplicates_are_counted_once():
    score = score_fields(
        {"skills": ["Python"]}, {"skills": ["Python", "python"]}
    )["skills"]

    assert score.precision == 1.0
    assert score.found == 1


def test_aggregate_sums_counts_before_dividing():
    first = score_fields({"skills": ["a1", "b1"]}, {"skills": ["a1"]})
    second = score_fields({"skills": ["c1"]}, {"skills": ["c1", "d1", "e1"]})

    total = aggregate_fields([first, second])["skills"]

    assert total.expected == 3 and total.found == 4
    assert total.recall == pytest.approx(2 / 3)
    assert total.precision == pytest.approx(2 / 4)


def test_entities_are_read_from_the_extraction_output():
    extracted = {
        "personal_info": {"full_name": "Nguyen Thi Lan"},
        "experience": [
            {"company": "Northwind Labs", "role": "Backend Engineer"},
            {"company": None, "role": "Intern"},
        ],
        "education": [
            {"institution": "Hanoi University", "degree_level": ["Bachelor"]},
        ],
        "skills": ["python", {"name": "SQL"}],
        "certifications": [{"name": "Scrum Master"}, "AWS"],
    }

    entities = entities_from_extraction(extracted)

    assert entities["name"] == ["Nguyen Thi Lan"]
    assert entities["companies"] == ["Northwind Labs"]
    assert entities["roles"] == ["Backend Engineer", "Intern"]
    assert entities["schools"] == ["Hanoi University"]
    assert entities["degrees"] == ["Bachelor"]
    assert entities["skills"] == ["python", "SQL"]
    assert entities["certifications"] == ["Scrum Master", "AWS"]


def test_empty_output_gives_empty_entities():
    assert all(not values for values in entities_from_extraction({}).values())


def test_corpus_entities_score_perfectly_against_themselves(tmp_path):
    documents = IndustryCorpusBuilder(
        seed=2, industries=["marketing"], layouts=["single"]
    ).build(tmp_path)

    scores = aggregate_fields(
        score_fields(d.entities, d.entities) for d in documents
    )

    assert all(score.f1 == 1.0 for score in scores.values())
    assert "| companies |" in field_table(scores)
