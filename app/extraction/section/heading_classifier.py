"""
Recognises section headings whose wording is not in the heading lexicon.

The lexicon (heading_lexicon.py) is exact and cheap but closed: "Clinical
Experience" or "Tools and Platforms" are not in it. For a short line that
looks like a heading but is not in the lexicon, this classifier compares the
line with example headings of each section using the multilingual sentence
embedding model that is already loaded. A line becomes a heading only when
it is clearly closer to one section than to the others; anything doubtful
stays body text, because a wrong heading splits a section in two.

Results are cached per line, and the lines of a document are encoded in one
batch.
"""

import re
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from app.extraction.section.heading_lexicon import normalise

# Example headings per section. Vietnamese examples are also used without
# diacritics, because PDF text sometimes loses them.
HEADING_EXAMPLES: Dict[str, Sequence[str]] = {
    "personal_info": (
        "Contact", "Contact Information", "Personal Details",
        "Personal Information",
        "Thông tin cá nhân", "Thông tin liên hệ", "Liên hệ",
    ),
    "summary": (
        "Summary", "Professional Summary", "Career Summary", "Profile",
        "Personal Profile", "Objective", "Career Objective", "About Me",
        "Introduction", "Overview",
        "Mục tiêu nghề nghiệp", "Giới thiệu bản thân", "Tóm tắt",
        "Tổng quan", "Về tôi",
    ),
    "experience": (
        "Work Experience", "Professional Experience", "Employment History",
        "Work History", "Career History", "Experience", "Relevant Experience",
        "Internships", "Positions Held",
        "Kinh nghiệm làm việc", "Quá trình làm việc",
        "Kinh nghiệm chuyên môn", "Lịch sử làm việc", "Thực tập",
    ),
    "education": (
        "Education", "Academic Background", "Educational Background",
        "Degrees", "Academic Record", "Education and Training",
        "Học vấn", "Trình độ học vấn", "Quá trình học tập", "Đào tạo",
        "Bằng cấp",
    ),
    "skills": (
        "Skills", "Key Skills", "Technical Skills", "Core Competencies",
        "Skill Set", "Competencies", "Technologies", "Tools", "Tech Stack",
        "Strengths",
        "Kỹ năng", "Kỹ năng chuyên môn", "Công nghệ", "Năng lực",
        "Điểm mạnh",
    ),
    "projects": (
        "Projects", "Personal Projects", "Academic Projects", "Side Projects",
        "Portfolio", "Project Experience", "Open Source", "Case Studies",
        "Dự án", "Dự án cá nhân", "Dự án đã tham gia",
    ),
    "certifications": (
        "Certifications", "Certificates", "Licenses", "Credentials",
        "Courses", "Training", "Awards", "Honors", "Achievements",
        "Scholarships",
        "Chứng chỉ", "Giải thưởng", "Thành tích", "Khóa học", "Học bổng",
    ),
    "other": (
        "References", "Referees", "Interests", "Hobbies", "Languages",
        "Language Skills", "Publications", "Research Papers", "Memberships",
        "Affiliations", "Additional Information", "Declaration",
        "Availability",
        "Sở thích", "Ngoại ngữ", "Người tham chiếu", "Công bố",
        "Bài báo", "Thông tin khác", "Cam đoan",
    ),
}

MAX_WORDS = 6
MAX_CHARS = 50
MIN_LETTERS = 3

DEFAULT_THRESHOLD = 0.62
DEFAULT_MARGIN = 0.05

_ALLOWED = re.compile(r"^[^\W\d_][\w &/'’\-]*:?$", re.UNICODE)
_BULLET = re.compile(r"^\s*[-•*▪●◦·]")


def is_heading_candidate(line: str) -> bool:
    """
    True for a short line that could be a heading: a few words, no digits,
    no sentence punctuation, not a bullet. It says nothing about the meaning.
    """

    text = line.strip()

    if not text or len(text) > MAX_CHARS or _BULLET.match(text):
        return False

    if any(char.isdigit() for char in text):
        return False

    if sum(char.isalpha() for char in text) < MIN_LETTERS:
        return False

    words = text.rstrip(":").split()

    if not 1 <= len(words) <= MAX_WORDS:
        return False

    # " - " separates a role from a company, a degree from a school, etc.
    if " - " in text or "@" in text:
        return False

    return bool(_ALLOWED.match(text))


Encoder = Callable[[List[str]], np.ndarray]


class HeadingClassifier:
    """Maps heading-like lines to a section, or to None when unsure."""

    def __init__(
        self,
        encode: Optional[Encoder] = None,
        threshold: float = DEFAULT_THRESHOLD,
        margin: float = DEFAULT_MARGIN,
        examples: Optional[Dict[str, Sequence[str]]] = None,
    ) -> None:
        self._encode = encode or _default_encoder
        self.threshold = threshold
        self.margin = margin

        examples = examples or HEADING_EXAMPLES

        texts: List[str] = []
        owners: List[str] = []

        for section, phrases in examples.items():
            variants = set()

            for phrase in phrases:
                variants.add(phrase)
                variants.add(_strip_diacritics(phrase))

            for phrase in sorted(variants):
                texts.append(phrase)
                owners.append(section)

        self._sections = sorted(set(owners))
        self._owner_index = np.array(
            [self._sections.index(owner) for owner in owners]
        )
        self._prototypes = self._encode(texts)
        self._cache: Dict[str, Optional[str]] = {}

    def prefetch(self, lines: Iterable[str]) -> None:
        """Classifies several lines with one encoder call."""

        pending: List[str] = []
        seen = set()

        for line in lines:
            key = _key(line)

            if key and key not in self._cache and key not in seen:
                seen.add(key)
                pending.append(key)

        if not pending:
            return

        scores = self._similarities(self._encode(pending))

        for key, row in zip(pending, scores):
            self._cache[key] = self._decide(row)

    def classify(self, line: str) -> Optional[str]:
        """The section the line introduces, or None if it is not a heading."""

        if not is_heading_candidate(line):
            return None

        key = _key(line)

        if key not in self._cache:
            self.prefetch([line])

        return self._cache.get(key)

    def scores(self, line: str) -> Dict[str, float]:
        """Best similarity per section (for threshold tuning and debugging)."""

        row = self._similarities(self._encode([_key(line)]))[0]

        return dict(zip(self._sections, (float(v) for v in row)))

    # ------------------------------------------------------------------

    def _similarities(self, vectors: np.ndarray) -> np.ndarray:
        similarity = vectors @ self._prototypes.T

        best = np.full((len(vectors), len(self._sections)), -1.0)

        for column, owner in enumerate(self._owner_index):
            best[:, owner] = np.maximum(best[:, owner], similarity[:, column])

        return best

    def _decide(self, row: np.ndarray) -> Optional[str]:
        order = np.argsort(row)[::-1]
        top, runner_up = row[order[0]], row[order[1]]

        if top < self.threshold or top - runner_up < self.margin:
            return None

        return self._sections[int(order[0])]


def _key(line: str) -> str:
    return " ".join(line.strip().rstrip(":").split())


def _strip_diacritics(text: str) -> str:
    # normalise() also lowercases and drops punctuation, which suits a
    # second set of examples for text that lost its accents.
    return normalise(text)


def _default_encoder(texts: List[str]) -> np.ndarray:
    from app.embeddings.models.embedding_model import EmbeddingModelSingleton

    return np.asarray(
        EmbeddingModelSingleton().model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
    )


def best_scores(
    classifier: HeadingClassifier, lines: Sequence[str]
) -> List[Tuple[str, Dict[str, float]]]:
    return [(line, classifier.scores(line)) for line in lines]
