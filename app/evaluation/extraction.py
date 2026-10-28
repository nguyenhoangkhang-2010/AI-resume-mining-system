from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Sequence

from app.evaluation.dataset import ExtractionDocument


def _clean(skill: str) -> str:
    return " ".join(skill.casefold().split())


@dataclass
class ExtractionReport:
    precision: float
    recall: float
    f1: float
    true_positives: int
    false_positives: int
    false_negatives: int

    # per gold skill: [documents containing it, documents where it was found]
    skill_recall: Dict[str, float] = field(default_factory=dict)

    # skills the extractor returned that are outside the evaluated
    # vocabulary, averaged per document (reported, not scored)
    extra_skills_per_document: float = 0.0

    documents: int = 0


def evaluate_skill_extraction(
    extractor,
    documents: Sequence[ExtractionDocument],
    vocabulary: Iterable[str],
) -> ExtractionReport:
    """
    Micro-averaged precision/recall/F1 of a skill extractor.

    Only skills in `vocabulary` are scored. The extractor draws on a large
    taxonomy and legitimately returns skills the synthetic documents never
    mention, so counting those as errors would measure the taxonomy size
    rather than extraction quality. They are reported separately as
    extra_skills_per_document.
    """

    vocabulary = {_clean(skill) for skill in vocabulary}

    true_positives = false_positives = false_negatives = 0
    extra_total = 0

    present: Dict[str, int] = defaultdict(int)
    found: Dict[str, int] = defaultdict(int)

    for document in documents:
        gold = {_clean(skill) for skill in document.gold_skills}
        predicted = {_clean(skill) for skill in extractor.extract(document.text)}

        scored_prediction = predicted & vocabulary

        true_positives += len(scored_prediction & gold)
        false_positives += len(scored_prediction - gold)
        false_negatives += len(gold - scored_prediction)
        extra_total += len(predicted - vocabulary)

        for skill in gold:
            present[skill] += 1

            if skill in scored_prediction:
                found[skill] += 1

    precision = _ratio(true_positives, true_positives + false_positives)
    recall = _ratio(true_positives, true_positives + false_negatives)

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    return ExtractionReport(
        precision=precision,
        recall=recall,
        f1=f1,
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        skill_recall={
            skill: found[skill] / count
            for skill, count in sorted(present.items())
        },
        extra_skills_per_document=(
            extra_total / len(documents) if documents else 0.0
        ),
        documents=len(documents),
    )


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def extraction_table(report: ExtractionReport) -> str:
    rows = [
        "| Metric | Value |",
        "|---|---|",
        f"| Documents | {report.documents} |",
        f"| Precision | {report.precision:.3f} |",
        f"| Recall | {report.recall:.3f} |",
        f"| F1 | {report.f1:.3f} |",
        f"| Extra skills outside vocabulary / document | "
        f"{report.extra_skills_per_document:.1f} |",
    ]

    return "\n".join(rows)


def weakest_skills(
    report: ExtractionReport,
    limit: int = 15,
) -> List[tuple[str, float]]:

    return sorted(
        report.skill_recall.items(),
        key=lambda item: (item[1], item[0]),
    )[:limit]
