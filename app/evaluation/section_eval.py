"""
Line-level evaluation of section detection against a labelled CV corpus.

Each body line of a document has a true section. The detector's output is a
mapping from section name to the text it assigned; a line is correct when it
appears under its true section. Lines the detector dropped (or assigned to
the ignored "other" section) count as misses for their true section.
"""

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Sequence

from app.evaluation.cv_corpus import CorpusDocument

MISSING = "missing"


def _normalise(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip().casefold()


def predicted_line_labels(
    sections: Mapping[str, Sequence[str]],
) -> Dict[str, str]:
    """Maps each distinct predicted line to the section it was placed in."""

    labels: Dict[str, str] = {}

    for section, chunks in sections.items():
        if section.startswith("__"):
            continue

        for chunk in chunks:
            for line in chunk.splitlines():
                key = _normalise(line)

                if key and key not in labels:
                    labels[key] = section

    return labels


@dataclass
class SectionScores:
    precision: float
    recall: float
    f1: float
    support: int


@dataclass
class DocumentResult:
    document_id: str
    correct: int
    total: int
    confusion: Counter = field(default_factory=Counter)

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else 0.0


def score_document(
    document: CorpusDocument,
    sections: Mapping[str, Sequence[str]],
) -> DocumentResult:

    predicted = predicted_line_labels(sections)

    result = DocumentResult(document.id, correct=0, total=len(document.truth))

    for truth in document.truth:
        guess = predicted.get(_normalise(truth.text), MISSING)

        result.confusion[(truth.section, guess)] += 1

        if guess == truth.section:
            result.correct += 1

    return result


def aggregate(results: Iterable[DocumentResult]) -> Dict[str, SectionScores]:
    """Per-section precision/recall/F1 plus a micro average under "all"."""

    confusion: Counter = Counter()

    for result in results:
        confusion.update(result.confusion)

    sections = sorted({truth for truth, _ in confusion})

    scores: Dict[str, SectionScores] = {}

    for section in sections:
        true_positive = confusion[(section, section)]
        support = sum(n for (t, _), n in confusion.items() if t == section)
        predicted = sum(n for (_, g), n in confusion.items() if g == section)

        precision = true_positive / predicted if predicted else 0.0
        recall = true_positive / support if support else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )

        scores[section] = SectionScores(precision, recall, f1, support)

    total = sum(confusion.values())
    correct = sum(n for (t, g), n in confusion.items() if t == g)

    micro = correct / total if total else 0.0

    scores["all"] = SectionScores(micro, micro, micro, total)

    return scores


def group_accuracy(
    documents: Sequence[CorpusDocument],
    results: Sequence[DocumentResult],
    key: str,
) -> Dict[str, float]:
    """Line accuracy grouped by a document attribute (style, layout, language)."""

    grouped: Dict[str, List[DocumentResult]] = defaultdict(list)

    for document, result in zip(documents, results):
        grouped[getattr(document, key)].append(result)

    return {
        name: sum(r.correct for r in items) / max(1, sum(r.total for r in items))
        for name, items in sorted(grouped.items())
    }
