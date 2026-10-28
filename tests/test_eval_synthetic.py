import json

import pytest

from app.evaluation.dataset import EvalDataset
from app.evaluation.synthetic import (
    FAMILIES,
    SyntheticDatasetGenerator,
    are_adjacent,
    relevance_family_only,
    relevance_with_seniority,
)


@pytest.fixture(scope="module")
def dataset():
    return SyntheticDatasetGenerator(
        seed=7,
        n_candidates=120,
        jobs_per_family=2,
        n_extraction_documents=20,
    ).generate()


def test_generation_is_deterministic():
    first = SyntheticDatasetGenerator(seed=3, n_candidates=30).generate()
    second = SyntheticDatasetGenerator(seed=3, n_candidates=30).generate()
    other = SyntheticDatasetGenerator(seed=4, n_candidates=30).generate()

    assert first == second
    assert first != other


def test_dataset_sizes(dataset):
    assert len(dataset.jobs) == len(FAMILIES) * 2
    assert len(dataset.candidates) == 120
    assert len(dataset.extraction_documents) == 20
    assert set(dataset.qrels) == {"seniority_aware", "family_only"}


def test_every_job_has_relevant_candidates(dataset):
    for name, qrels in dataset.qrels.items():
        for job in dataset.jobs:
            assert any(grade >= 2 for grade in qrels[job.id].values()), (
                name,
                job.id,
            )


def test_skills_belong_to_known_vocabulary(dataset):
    vocabulary = {
        skill
        for spec in FAMILIES.values()
        for skill in spec["core"] + spec["extra"]
    }

    for job in dataset.jobs:
        assert set(job.required_skills) <= vocabulary

    for candidate in dataset.candidates:
        assert set(candidate.meta["canonical_skills"]) <= vocabulary
        assert len(candidate.skills) >= 4


def test_experience_dates_match_latent_years(dataset):
    for candidate in dataset.candidates:
        years = candidate.meta["years"]

        if years == 0:
            continue

        start = min(int(entry.start_date) for entry in candidate.experience)
        end = max(int(entry.end_date) for entry in candidate.experience)

        assert end - start == years


def test_labels_do_not_depend_on_listed_skills(dataset):
    """
    Two candidates with the same latent family and years must get the
    same grade whatever skills they list (this is what stops a skill
    overlap ranker from being scored against labels it defines).
    """

    job = dataset.jobs[0]
    labels = dataset.qrels["seniority_aware"][job.id]

    for candidate in dataset.candidates:
        expected = relevance_with_seniority(
            job.family,
            job.experience_years,
            candidate.meta["family"],
            candidate.meta["years"],
        )

        assert labels.get(candidate.id, 0) == expected


def test_stuffers_are_not_rewarded(dataset):
    stuffers = [c for c in dataset.candidates if c.meta["stuffer"]]

    assert stuffers

    for job in dataset.jobs:
        for candidate in stuffers:
            if candidate.meta["family"] == job.family:
                continue

            if are_adjacent(candidate.meta["family"], job.family):
                continue

            assert dataset.qrels["family_only"][job.id].get(candidate.id, 0) == 0


@pytest.mark.parametrize(
    "job_family, required, candidate_family, years, expected",
    [
        ("backend", 3, "backend", 5, 3),
        ("backend", 3, "backend", 2, 2),
        ("backend", 3, "backend", 1, 1),
        ("backend", 3, "data_engineering", 4, 1),
        ("backend", 3, "data_engineering", 1, 0),
        ("backend", 3, "mobile", 10, 0),
    ],
)
def test_seniority_relevance(
    job_family, required, candidate_family, years, expected
):
    assert (
        relevance_with_seniority(job_family, required, candidate_family, years)
        == expected
    )


def test_family_only_relevance_ignores_years():
    assert relevance_family_only("backend", "backend") == 2
    assert relevance_family_only("backend", "devops") == 1
    assert relevance_family_only("backend", "mobile") == 0


def test_extraction_documents_gold_matches_skills_line(dataset):
    for document in dataset.extraction_documents:
        assert document.gold_skills == sorted(set(document.gold_skills))
        assert document.text.startswith("Skills: ")


def test_save_and_load_roundtrip(tmp_path, dataset):
    dataset.save(tmp_path)

    loaded = EvalDataset.load(tmp_path)

    assert loaded == dataset
    assert json.loads((tmp_path / "manifest.json").read_text())["seed"] == 7


def test_committed_dataset_matches_generator():
    """
    The committed data must be reproducible from its seed, otherwise
    published numbers cannot be checked.
    """

    loaded = EvalDataset.load("data/evaluation/synthetic_v1")

    regenerated = SyntheticDatasetGenerator(seed=loaded.seed).generate()

    assert loaded == regenerated
