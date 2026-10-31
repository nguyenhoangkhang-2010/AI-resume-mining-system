import math
import random

import pytest

from app.evaluation.dataset import EvalCandidate, EvalDataset, EvalExperience, EvalJob
from app.evaluation.fairness import (
    COUNTERFACTUALS,
    Counterfactual,
    Unit,
    audit,
    audit_table,
    bootstrap_ratio,
    find,
    in_vietnamese,
    selection_ratio,
    with_career_gap,
)
from app.evaluation.rankers import Ranker
from app.evaluation.synthetic import SyntheticDatasetGenerator
from app.matching.scoring.experience_scorer import ExperienceCalculator


class ScoreByText(Ranker):
    """Scores a profile with a function of its text, so a test can plant a bias."""

    name = "toy"

    def __init__(self, bonus=None):
        self.bonus = bonus or {}

    def scores(self, job):
        result = {}

        for candidate in self.dataset.candidates:
            score = float(len(candidate.skills))

            for word, points in self.bonus.items():
                if word in candidate.text:
                    score += points

            result[candidate.id] = score

        return result


def dataset(n=120, jobs=6):
    candidates = [
        EvalCandidate(
            id=f"c{i:03d}",
            title="Backend Engineer",
            summary="Backend Engineer with 3 years of experience in python, sql.",
            # the same skill count for many: ties are broken by id, not by group
            skills=["python"] * (1 + i % 7),
            experience=[
                EvalExperience("Backend Engineer", "Acme", "2020", "2022", ["Built services using python and sql."]),
                EvalExperience("Backend Engineer", "Beta", "2022", "2025", ["Reviewed code and mentored junior colleagues."]),
            ],
        )
        for i in range(n)
    ]
    job_list = [
        EvalJob(id=f"j{j}", title="Backend Engineer", family="backend", description="x", required_skills=["python"])
        for j in range(jobs)
    ]

    return EvalDataset(jobs=job_list, candidates=candidates, qrels={})


def test_selection_ratio_is_the_rate_of_a_over_the_rate_of_b():
    units = [Unit(3, 50, 6, 50), Unit(3, 50, 6, 50)]

    assert selection_ratio(units) == pytest.approx(0.5)


def test_selection_ratio_is_nan_when_b_selects_nobody():
    assert math.isnan(selection_ratio([Unit(2, 10, 0, 10)]))


def test_the_interval_covers_the_point_estimate():
    units = [Unit(i % 3, 50, 2, 50) for i in range(40)]

    ratio, low, high = bootstrap_ratio(units, seed=1)

    assert low <= ratio <= high


def test_a_ranker_that_ignores_the_change_is_not_flagged():
    pairing = find("pronoun")

    result = audit(ScoreByText(), dataset(), pairing, top_k=10, repeats=6)

    assert result.mean_shift == 0.0
    assert result.share_moved == 0.0
    assert 0.6 < result.ratio < 1.6
    assert not result.flagged


def test_a_planted_bias_is_found_in_both_measures():
    pairing = find("pronoun")
    biased = ScoreByText(bonus={"He enjoys": 5.0})

    result = audit(biased, dataset(), pairing, top_k=10, repeats=6)

    assert result.mean_shift == pytest.approx(-5.0)
    assert result.share_moved == 1.0
    assert result.ratio < 0.8
    assert result.flagged


def test_a_change_with_an_equal_effect_on_both_groups_has_no_shift():
    same = Counterfactual("same", "", lambda c, r: c, lambda c, r: c)

    result = audit(ScoreByText(), dataset(), same, top_k=5, repeats=2)

    assert result.mean_shift == 0.0


def test_the_audit_is_repeatable():
    first = audit(ScoreByText(), dataset(), find("pronoun"), repeats=3, seed=5)
    second = audit(ScoreByText(), dataset(), find("pronoun"), repeats=3, seed=5)

    assert (first.ratio, first.mean_shift) == (second.ratio, second.mean_shift)


def test_every_counterfactual_changes_only_what_it_says():
    base = dataset(5).candidates[0]
    rng = random.Random(0)

    for pairing in COUNTERFACTUALS:
        for transform in (pairing.group_a, pairing.group_b):
            changed = transform(base, rng)

            assert changed.skills == base.skills
            assert changed.id == base.id
            assert changed.meta == base.meta


def test_a_career_break_keeps_the_years_of_experience():
    candidate = dataset(1).candidates[0]
    gap = with_career_gap(candidate, random.Random(0))
    calculator = ExperienceCalculator()

    assert gap.experience[0].start_date == "2018"
    assert calculator.total_years(gap.experience, current_year=2025) == calculator.total_years(
        candidate.experience, current_year=2025
    )


def test_the_vietnamese_version_translates_every_generated_sentence():
    data = SyntheticDatasetGenerator(seed=3, n_candidates=60).generate()

    for candidate in data.candidates:
        translated = in_vietnamese(candidate, random.Random(0))
        lines = [translated.title, translated.summary]
        lines += [entry.role for entry in translated.experience]
        lines += [line for entry in translated.experience for line in entry.description]

        assert translated.skills == candidate.skills
        # no English sentence is left behind (skill names are allowed)
        assert "years of experience" not in translated.summary
        assert not any(
            word in " ".join(lines)
            for word in ("Built", "Maintained", "Designed", "Worked daily", "Reviewed", "Collaborated")
        )


def test_the_table_lists_every_result():
    results = [audit(ScoreByText(), dataset(40, 3), find("pronoun"), repeats=2)]

    table = audit_table(results)

    assert "pronoun" in table and "toy" in table


def test_the_name_field_of_a_profile_never_reaches_the_embedding_text():
    from app.matching.embedding_text import CandidateTextBuilder
    from app.models.candidate import CandidateModel

    candidate = CandidateModel(resume_id="r", faiss_id=1, personal_info={"full_name": "Zxqv Unique"}, skills=["python"])

    assert "Zxqv" not in CandidateTextBuilder().text(candidate)
