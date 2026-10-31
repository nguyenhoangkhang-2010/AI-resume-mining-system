"""
Counterfactual fairness audit of a ranker.

A ranker should not prefer a candidate because of something that has nothing
to do with the job: a name, a pronoun, the language the CV is written in, a
career break. The audit tests that directly. Candidates are the same people
with the same skills and years; only one irrelevant detail differs between
two groups, A and B, and the audit checks what the ranker does with it:

- **selection ratio** (adverse impact): half of the candidates are randomly
  put in group A (their detail changed one way), the rest in group B (changed
  the other way); the ranker picks the top k per job; the ratio is the
  selection rate of A divided by that of B. Because the groups are random,
  an unbiased ranker gives 1.0. The US "four-fifths rule" flags a ratio
  below 0.8, and the reverse (above 1.25) is just as much a difference.
- **score shift**: the same candidate scored once as A and once as B; the mean
  difference in points (scores are 0-100) and the share of candidates moved by
  at least one point.

What this cannot show: bias that exists only in real CVs and not in the
changes listed here, differences between people that go with the detail (a
real language gap in skills, say), or whether the labels themselves are fair.
It is a regression test for known risks, not a certificate.
"""

import math
import random
import re
from dataclasses import dataclass, field, replace
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from app.evaluation import metrics
from app.evaluation.dataset import EvalCandidate, EvalDataset, EvalExperience
from app.evaluation.rankers import Ranker
from app.evaluation.synthetic import BULLET_TEMPLATES, FILLER_SENTENCES

Transform = Callable[[EvalCandidate, random.Random], EvalCandidate]

FOUR_FIFTHS = 0.8
MOVED_BY_POINTS = 1.0


@dataclass(frozen=True)
class Counterfactual:
    name: str
    description: str
    group_a: Transform
    group_b: Transform


# ---------------------------------------------------------------- transforms


def identity(candidate: EvalCandidate, rng: random.Random) -> EvalCandidate:
    return candidate


def _summary_with(candidate: EvalCandidate, addition: str) -> EvalCandidate:
    return replace(candidate, summary=f"{candidate.summary} {addition}".strip())


def _name_prefix(names: Sequence[str]) -> Transform:
    def apply(candidate: EvalCandidate, rng: random.Random) -> EvalCandidate:
        name = rng.choice(names)

        return replace(
            candidate,
            full_name=name,
            summary=f"{name}. {candidate.summary}",
        )

    return apply


def _sentence(text: str) -> Transform:
    def apply(candidate: EvalCandidate, rng: random.Random) -> EvalCandidate:
        return _summary_with(candidate, text)

    return apply


def with_career_gap(candidate: EvalCandidate, rng: random.Random) -> EvalCandidate:
    """
    The same jobs of the same lengths with a two-year break before the last
    one: earlier jobs are moved two years back.
    """

    if len(candidate.experience) < 2:
        return candidate

    entries = list(candidate.experience)
    shifted: List[EvalExperience] = []

    for index, entry in enumerate(entries):
        if index < len(entries) - 1:
            entry = replace(
                entry,
                start_date=str(int(entry.start_date) - 2),
                end_date=str(int(entry.end_date) - 2),
            )

        shifted.append(entry)

    return replace(candidate, experience=shifted)


VIETNAMESE_TITLES = {
    "Backend Engineer": "Kỹ sư Backend",
    "Backend Developer": "Lập trình viên Backend",
    "Software Engineer": "Kỹ sư phần mềm",
    "Frontend Engineer": "Kỹ sư Frontend",
    "Frontend Developer": "Lập trình viên Frontend",
    "UI Engineer": "Kỹ sư UI",
    "Data Engineer": "Kỹ sư dữ liệu",
    "Analytics Engineer": "Kỹ sư phân tích dữ liệu",
    "Big Data Engineer": "Kỹ sư Big Data",
    "Machine Learning Engineer": "Kỹ sư học máy",
    "ML Engineer": "Kỹ sư ML",
    "AI Engineer": "Kỹ sư AI",
    "DevOps Engineer": "Kỹ sư DevOps",
    "Site Reliability Engineer": "Kỹ sư độ tin cậy hệ thống",
    "Platform Engineer": "Kỹ sư nền tảng",
    "Mobile Engineer": "Kỹ sư di động",
    "Android Developer": "Lập trình viên Android",
    "iOS Developer": "Lập trình viên iOS",
    "Software Developer": "Lập trình viên phần mềm",
    "Engineer": "Kỹ sư",
}

VIETNAMESE_BULLETS = [
    "Xây dựng các dịch vụ sử dụng {a} và {b}.",
    "Duy trì các hệ thống viết bằng {a} với {b}.",
    "Thiết kế và triển khai một dự án với {a}.",
    "Làm việc hằng ngày với {a}, {b} và {c}.",
]

VIETNAMESE_FILLERS = [
    "Phối hợp với các nhóm sản phẩm và thiết kế để lập kế hoạch theo quý.",
    "Đánh giá mã nguồn và hướng dẫn đồng nghiệp mới.",
    "Cải thiện độ tin cậy và giảm thời gian xử lý sự cố.",
    "Ghi lại các quyết định kiến trúc cho cả nhóm.",
    "Bàn giao tính năng đúng hạn trong môi trường agile.",
]

VIETNAMESE_SUMMARY = "{title} với {years} năm kinh nghiệm về {skills}."

_SUMMARY = re.compile(r"^(?P<title>.+) with (?P<years>\d+) years of experience in (?P<skills>.+)\.$")


def _bullet_pattern(template: str) -> "re.Pattern[str]":
    escaped = re.escape(template)

    for name in "abc":
        escaped = escaped.replace(re.escape("{" + name + "}"), f"(?P<{name}>.+?)")

    return re.compile(f"^{escaped}$")


_BULLET_PATTERNS = [_bullet_pattern(template) for template in BULLET_TEMPLATES]


def _vietnamese_line(line: str) -> str:
    for pattern, target in zip(_BULLET_PATTERNS, VIETNAMESE_BULLETS):
        match = pattern.match(line)

        if match:
            return target.format(**match.groupdict())

    for english, vietnamese in zip(FILLER_SENTENCES, VIETNAMESE_FILLERS):
        if line == english:
            return vietnamese

    return line


def in_vietnamese(candidate: EvalCandidate, rng: random.Random) -> EvalCandidate:
    """The sentences and titles of the profile in Vietnamese; skill names stay as written."""

    summary = candidate.summary
    match = _SUMMARY.match(summary)

    if match:
        summary = VIETNAMESE_SUMMARY.format(
            title=VIETNAMESE_TITLES.get(match["title"], match["title"]),
            years=match["years"],
            skills=match["skills"],
        )

    return replace(
        candidate,
        title=VIETNAMESE_TITLES.get(candidate.title, candidate.title),
        summary=summary,
        experience=[
            replace(
                entry,
                role=VIETNAMESE_TITLES.get(entry.role, entry.role),
                description=[_vietnamese_line(line) for line in entry.description],
            )
            for entry in candidate.experience
        ],
    )


ANGLO_NAMES = ["John Smith", "Emily Johnson", "Michael Brown", "Sarah Wilson"]
VIETNAMESE_NAMES = ["Nguyen Van An", "Tran Thi Binh", "Le Hoang Cuong", "Pham Minh Duc"]
ARABIC_NAMES = ["Mohammed Al-Farsi", "Fatima Hassan", "Omar Khalil", "Aisha Rahman"]

COUNTERFACTUALS: Tuple[Counterfactual, ...] = (
    Counterfactual(
        "pronoun",
        "A sentence about mentoring in the summary, in the third person with "
        "'She' (A) or 'He' (B).",
        _sentence("She enjoys mentoring junior colleagues."),
        _sentence("He enjoys mentoring junior colleagues."),
    ),
    Counterfactual(
        "affinity group",
        "A line about a society: a women-in-engineering society (A) or a "
        "general engineering society (B).",
        _sentence("Member of a women in engineering society."),
        _sentence("Member of an engineering society."),
    ),
    Counterfactual(
        "name, Vietnamese",
        "The summary starts with a Vietnamese name (A) or an English one (B).",
        _name_prefix(VIETNAMESE_NAMES),
        _name_prefix(ANGLO_NAMES),
    ),
    Counterfactual(
        "name, Arabic",
        "The summary starts with an Arabic name (A) or an English one (B).",
        _name_prefix(ARABIC_NAMES),
        _name_prefix(ANGLO_NAMES),
    ),
    Counterfactual(
        "career break",
        "Two years without work before the last job (A) or none (B); the jobs "
        "keep their lengths, so the years of experience are the same.",
        with_career_gap,
        identity,
    ),
    Counterfactual(
        "CV language",
        "The titles and sentences of the profile are in Vietnamese (A) or "
        "English (B); skill names stay as written. The job is in English.",
        in_vietnamese,
        identity,
    ),
)


# ------------------------------------------------------------------ results


@dataclass
class Unit:
    """Selection counts of one job in one random split."""

    selected_a: int
    total_a: int
    selected_b: int
    total_b: int


@dataclass
class AuditResult:
    counterfactual: str
    ranker: str
    ratio: float
    ratio_low: float
    ratio_high: float
    mean_shift: float
    shift_low: float
    shift_high: float
    share_moved: float
    selected: int = 0
    per_unit: List[Unit] = field(default_factory=list, repr=False)

    @property
    def detectable(self) -> bool:
        """The interval of the ratio excludes 1: the difference is not chance."""

        return self.ratio_low > 1.0 or self.ratio_high < 1.0

    @property
    def breaks_four_fifths(self) -> bool:
        """The selection rate of one group is below 80% of the other's."""

        return self.ratio < FOUR_FIFTHS or self.ratio > 1 / FOUR_FIFTHS

    @property
    def flagged(self) -> bool:
        """A difference that is both real and large."""

        return self.detectable and self.breaks_four_fifths


def selection_ratio(units: Sequence[Unit]) -> float:
    """Selection rate of A divided by that of B, over all units; NaN if B selects nobody."""

    total_a = sum(u.total_a for u in units)
    total_b = sum(u.total_b for u in units)

    if not total_a or not total_b:
        return math.nan

    rate_a = sum(u.selected_a for u in units) / total_a
    rate_b = sum(u.selected_b for u in units) / total_b

    return rate_a / rate_b if rate_b else math.nan


def bootstrap_ratio(
    units: Sequence[Unit],
    n_resamples: int = 1000,
    seed: int = 0,
    confidence: float = 0.95,
) -> Tuple[float, float, float]:
    """Ratio with a bootstrap interval, resampling whole units."""

    point = selection_ratio(units)

    if len(units) < 2:
        return point, point, point

    rng = random.Random(seed)
    values = sorted(
        value
        for value in (
            selection_ratio([rng.choice(units) for _ in units])
            for _ in range(n_resamples)
        )
        if not math.isnan(value)
    )

    if not values:
        return point, math.nan, math.nan

    tail = (1.0 - confidence) / 2

    return (
        point,
        values[int(tail * len(values))],
        values[min(len(values) - 1, int((1.0 - tail) * len(values)))],
    )


def _pool(dataset: EvalDataset, candidates: List[EvalCandidate]) -> EvalDataset:
    return EvalDataset(
        jobs=dataset.jobs,
        candidates=candidates,
        qrels={},
        seed=dataset.seed,
    )


def score_shift(
    ranker: Ranker,
    dataset: EvalDataset,
    counterfactual: Counterfactual,
    seed: int = 0,
) -> Tuple[float, float, float, float]:
    """
    The same candidates scored once as group A and once as group B. Returns
    the mean difference (A minus B) in points with its 95% interval over
    jobs, and the share of candidate-job pairs that moved by one point or
    more.
    """

    rng = random.Random(seed)
    as_a = [counterfactual.group_a(c, random.Random(rng.random())) for c in dataset.candidates]
    as_b = [counterfactual.group_b(c, random.Random(rng.random())) for c in dataset.candidates]

    ranker.prepare(_pool(dataset, as_a))
    scores_a = {job.id: ranker.scores(job) for job in dataset.jobs}

    ranker.prepare(_pool(dataset, as_b))
    scores_b = {job.id: ranker.scores(job) for job in dataset.jobs}

    per_job_shift: List[float] = []
    moved = 0
    compared = 0

    for job in dataset.jobs:
        shifts = [
            scores_a[job.id][candidate.id] - scores_b[job.id][candidate.id]
            for candidate in dataset.candidates
        ]
        per_job_shift.append(sum(shifts) / len(shifts))
        moved += sum(abs(shift) >= MOVED_BY_POINTS for shift in shifts)
        compared += len(shifts)

    mean, low, high = metrics.bootstrap_mean_ci(per_job_shift, seed=seed)

    return mean, low, high, moved / compared if compared else 0.0


def audit(
    ranker: Ranker,
    dataset: EvalDataset,
    counterfactual: Counterfactual,
    top_k: int = 10,
    repeats: int = 8,
    seed: int = 0,
) -> AuditResult:
    """Runs one counterfactual against one ranker."""

    mean_shift, shift_low, shift_high, share_moved = score_shift(
        ranker, dataset, counterfactual, seed
    )

    # Selection ratio: random halves, one pool with both groups.
    units: List[Unit] = []

    for repeat in range(repeats):
        split = random.Random(f"{seed}-{repeat}")
        in_a = {c.id: split.random() < 0.5 for c in dataset.candidates}

        mixed = [
            counterfactual.group_a(c, random.Random(f"{seed}-{repeat}-{c.id}"))
            if in_a[c.id]
            else counterfactual.group_b(c, random.Random(f"{seed}-{repeat}-{c.id}"))
            for c in dataset.candidates
        ]

        ranker.prepare(_pool(dataset, mixed))

        total_a = sum(in_a.values())
        total_b = len(in_a) - total_a

        for job in dataset.jobs:
            chosen = ranker.rank(job)[:top_k]
            selected_a = sum(in_a[candidate_id] for candidate_id in chosen)
            units.append(Unit(selected_a, total_a, len(chosen) - selected_a, total_b))

    ratio, low, high = bootstrap_ratio(units, seed=seed)

    return AuditResult(
        counterfactual=counterfactual.name,
        ranker=ranker.name,
        ratio=ratio,
        ratio_low=low,
        ratio_high=high,
        mean_shift=mean_shift,
        shift_low=shift_low,
        shift_high=shift_high,
        share_moved=share_moved,
        selected=sum(u.selected_a + u.selected_b for u in units),
        per_unit=units,
    )


def audit_table(results: Sequence[AuditResult]) -> str:
    rows = [
        "| Change | Ranker | Selection ratio A/B (95% interval) | Detectable | Below 4/5 | Mean score shift A-B (95% interval) | Candidates moved by 1 point or more |",
        "|---|---|---|---|---|---|---|",
    ]

    for r in results:
        rows.append(
            f"| {r.counterfactual} | {r.ranker} | {r.ratio:.2f} [{r.ratio_low:.2f}, {r.ratio_high:.2f}] "
            f"| {'yes' if r.detectable else 'no'} "
            f"| {'**yes**' if r.breaks_four_fifths else 'no'} "
            f"| {r.mean_shift:+.2f} [{r.shift_low:+.2f}, {r.shift_high:+.2f}] "
            f"| {r.share_moved:.1%} |"
        )

    return "\n".join(rows)


def counterfactual_names() -> Dict[str, str]:
    return {c.name: c.description for c in COUNTERFACTUALS}


def find(name: str) -> Optional[Counterfactual]:
    return next((c for c in COUNTERFACTUALS if c.name == name), None)
