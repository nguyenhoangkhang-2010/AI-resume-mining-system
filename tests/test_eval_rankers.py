import numpy as np
import pytest

from app.evaluation.dataset import EvalCandidate, EvalDataset, EvalExperience, EvalJob
from app.evaluation.extraction import evaluate_skill_extraction, weakest_skills
from app.evaluation.dataset import ExtractionDocument
from app.evaluation.rankers import (
    BM25Ranker,
    CachedEmbedder,
    HashingEmbedder,
    HybridRanker,
    SemanticRanker,
    SkillOverlapRanker,
    TfidfRanker,
    build_default_rankers,
    tokenize,
)
from app.evaluation.runner import (
    evaluate_all,
    paired_difference_table,
    results_table,
)


class IdentityNormalizer:
    def normalize(self, skill):
        return skill


def make_candidate(candidate_id, title, skills, start="2018", end="2024"):
    return EvalCandidate(
        id=candidate_id,
        title=title,
        summary=f"{title} with experience in {', '.join(skills)}.",
        skills=skills,
        experience=[
            EvalExperience(
                role=title,
                company="Acme",
                start_date=start,
                end_date=end,
                description=[f"Built systems using {skills[0]}."],
            )
        ],
        meta={"family": "x", "years": 6, "stuffer": False, "canonical_skills": skills},
    )


@pytest.fixture
def dataset():
    job = EvalJob(
        id="job-1",
        title="Backend Engineer",
        family="backend",
        description="Backend Engineer\n\nRequirements\n\npython\nsql\ndocker\n",
        required_skills=["python", "sql", "docker"],
        experience_years=3,
    )

    candidates = [
        make_candidate("good", "Backend Engineer", ["python", "sql", "docker"]),
        make_candidate("partial", "Backend Engineer", ["python", "git", "css"]),
        make_candidate("off", "Designer", ["figma", "css", "html"], "2023", "2024"),
    ]

    return EvalDataset(
        jobs=[job],
        candidates=candidates,
        qrels={"main": {"job-1": {"good": 3, "partial": 1}}},
    )


def test_tokenize_keeps_technical_tokens():
    assert tokenize("Node.js, C++ and CI/CD.") == [
        "node.js",
        "c++",
        "and",
        "ci/cd",
    ]


@pytest.mark.parametrize(
    "ranker",
    [
        BM25Ranker(),
        TfidfRanker(),
        SkillOverlapRanker(IdentityNormalizer()),
        SemanticRanker(HashingEmbedder(), IdentityNormalizer(), "skills"),
        SemanticRanker(HashingEmbedder(), IdentityNormalizer(), "fulltext"),
        HybridRanker(HashingEmbedder(), IdentityNormalizer(), use_experience=False),
        HybridRanker(HashingEmbedder(), IdentityNormalizer(), use_experience=True),
    ],
    ids=lambda ranker: ranker.name,
)
def test_each_ranker_puts_best_candidate_first(ranker, dataset):
    ranker.prepare(dataset)

    ranking = ranker.rank(dataset.jobs[0])

    assert ranking[0] == "good"
    assert ranking[-1] == "off"
    assert sorted(ranking) == ["good", "off", "partial"]


def test_ranking_order_is_deterministic_for_ties(dataset):
    ranker = BM25Ranker()
    ranker.prepare(dataset)

    assert ranker.rank(dataset.jobs[0]) == ranker.rank(dataset.jobs[0])


def test_unknown_semantic_mode_is_rejected():
    with pytest.raises(ValueError):
        SemanticRanker(HashingEmbedder(), IdentityNormalizer(), "images")


def test_hybrid_experience_changes_the_score(dataset):
    with_experience = HybridRanker(HashingEmbedder(), IdentityNormalizer(), True)
    without = HybridRanker(HashingEmbedder(), IdentityNormalizer(), False)

    with_experience.prepare(dataset)
    without.prepare(dataset)

    job = dataset.jobs[0]

    # "off" has one year of experience against a three-year requirement,
    # so the experience component (33/100) adds to its otherwise zero score
    assert without.scores(job)["off"] == 0.0
    assert with_experience.scores(job)["off"] == pytest.approx(6.67)


def test_hashing_embedder_is_normalised_and_deterministic():
    embedder = HashingEmbedder()

    vectors = embedder.encode(["python sql", "python sql", ""])

    assert np.allclose(vectors[0], vectors[1])
    assert np.linalg.norm(vectors[0]) == pytest.approx(1.0)
    assert np.linalg.norm(vectors[2]) == 0.0


def test_cached_embedder_encodes_each_text_once():
    class CountingEmbedder:
        calls = []

        def encode(self, texts):
            self.calls.append(list(texts))
            return HashingEmbedder().encode(texts)

    inner = CountingEmbedder()
    cached = CachedEmbedder(inner)

    cached.encode(["a b", "c d"])
    result = cached.encode(["c d", "a b", "e f"])

    assert inner.calls == [["a b", "c d"], ["e f"]]
    assert result.shape[0] == 3


def test_default_rankers_cover_baselines_and_ablations():
    names = [r.name for r in build_default_rankers(HashingEmbedder(), IdentityNormalizer())]

    assert names == [
        "bm25",
        "tfidf",
        "skill_overlap",
        "semantic_skills",
        "semantic_fulltext",
        "hybrid_no_experience",
        "hybrid",
    ]


def test_runner_produces_tables(dataset):
    rankers = build_default_rankers(HashingEmbedder(), IdentityNormalizer())

    results = evaluate_all(rankers, dataset, dataset.qrels["main"], cutoffs=(1, 3))

    assert {r.name for r in results} == {r.name for r in rankers}

    table = results_table(results, ["ndcg@1", "mrr"])

    assert table.startswith("| Ranker | ndcg@1 | mrr |")
    assert "| hybrid |" in table

    differences = paired_difference_table(results, "hybrid", "ndcg@1")

    assert "| bm25 |" in differences
    assert "hybrid |" not in differences.split("\n", 2)[2]


# ------------------------------------------------------- skill extraction


class FakeExtractor:
    def __init__(self, outputs):
        self.outputs = outputs

    def extract(self, text):
        return self.outputs[text]


def test_extraction_metrics_are_micro_averaged():
    documents = [
        ExtractionDocument("d1", "t1", ["python", "sql"]),
        ExtractionDocument("d2", "t2", ["docker"]),
    ]

    extractor = FakeExtractor(
        {
            "t1": ["Python", "docker", "teamwork"],
            "t2": [],
        }
    )

    report = evaluate_skill_extraction(
        extractor, documents, ["python", "sql", "docker"]
    )

    # python is a hit; docker in d1 is wrong; sql and docker (d2) missed
    assert report.true_positives == 1
    assert report.false_positives == 1
    assert report.false_negatives == 2
    assert report.precision == pytest.approx(0.5)
    assert report.recall == pytest.approx(1 / 3)
    assert report.f1 == pytest.approx(0.4)
    assert report.extra_skills_per_document == pytest.approx(0.5)
    assert report.skill_recall == {"docker": 0.0, "python": 1.0, "sql": 0.0}


def test_weakest_skills_are_listed_first():
    documents = [ExtractionDocument("d1", "t1", ["python", "sql"])]

    report = evaluate_skill_extraction(
        FakeExtractor({"t1": ["python"]}), documents, ["python", "sql"]
    )

    assert weakest_skills(report, limit=1) == [("sql", 0.0)]


def test_extraction_with_no_documents_is_zero():
    report = evaluate_skill_extraction(FakeExtractor({}), [], ["python"])

    assert (report.precision, report.recall, report.f1) == (0.0, 0.0, 0.0)
