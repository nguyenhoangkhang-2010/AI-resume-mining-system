"""
Synthetic CV corpus in many layouts, for measuring section detection.

Every document is a real PDF drawn with PyMuPDF from generated content, so
the true section of each body line is known. The variants differ in the
things that make real CVs hard to segment:

- heading style: UPPERCASE or Title Case, large or body-sized, bold or plain,
  generous or tight spacing;
- layout: single column, two columns (sidebar), several pages;
- language: English and Vietnamese (with diacritics).

The content is synthetic. Results measure how well headings and layout are
understood, not accuracy on real resumes.
"""

import random
import textwrap
from dataclasses import dataclass, field
from itertools import product
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import fitz

from app.evaluation.synthetic import FAMILIES


@dataclass(frozen=True)
class HeadingStyle:
    name: str
    upper: bool
    size: float
    bold: bool
    gap: float


HEADING_STYLES: Dict[str, HeadingStyle] = {
    style.name: style
    for style in [
        HeadingStyle("upper_large", upper=True, size=14, bold=False, gap=22),
        HeadingStyle("upper_small", upper=True, size=10, bold=False, gap=18),
        HeadingStyle("title_bold_large", upper=False, size=14, bold=True, gap=22),
        HeadingStyle("title_bold_same", upper=False, size=10, bold=True, gap=18),
        HeadingStyle("title_bold_tight", upper=False, size=10.5, bold=True, gap=8),
        HeadingStyle("title_plain_gap", upper=False, size=10, bold=False, gap=34),
    ]
}

LAYOUTS = ("single", "two_column", "multi_page")
LANGUAGES = ("en", "vi")

SECTION_TITLES: Dict[str, Dict[str, str]] = {
    "en": {
        "summary": "Summary",
        "experience": "Work Experience",
        "education": "Education",
        "skills": "Skills",
        "projects": "Projects",
        "certifications": "Certifications",
    },
    "vi": {
        "summary": "Mục tiêu nghề nghiệp",
        "experience": "Kinh nghiệm làm việc",
        "education": "Học vấn",
        "skills": "Kỹ năng",
        "projects": "Dự án",
        "certifications": "Chứng chỉ",
    },
}

# Different wording for the same sections. The heading lexicon was written
# with the standard titles in mind, so this set shows how the detector copes
# with headings it was not designed around.
SECTION_TITLES_ALTERNATE: Dict[str, Dict[str, str]] = {
    "en": {
        "summary": "Personal Statement",
        "experience": "Professional Background",
        "education": "Academic Qualifications",
        "skills": "Technical Proficiencies",
        "projects": "Selected Work",
        "certifications": "Training and Courses",
    },
    "vi": {
        "summary": "Định hướng nghề nghiệp",
        "experience": "Lịch sử công tác",
        "education": "Quá trình đào tạo",
        "skills": "Năng lực chuyên môn",
        "projects": "Sản phẩm đã thực hiện",
        "certifications": "Bằng cấp và chứng nhận",
    },
}

ALTERNATE_STYLES = ("upper_large", "title_bold_same")

BODY_SIZE = 10.0
LINE_PITCH = 14.0
PAGE_BOTTOM = 780.0
PAGE_TOP = 60.0

# The "multi_page" layout breaks pages early so that every document runs to
# several pages and sections continue across page breaks.
MULTI_PAGE_BOTTOM = 330.0

FONT_CANDIDATES: Sequence[Tuple[str, str]] = (
    ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ("/usr/share/fonts/dejavu/DejaVuSans.ttf",
     "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"),
    ("/Library/Fonts/Arial.ttf", "/Library/Fonts/Arial Bold.ttf"),
)


def find_unicode_fonts() -> Optional[Tuple[str, str]]:
    """Regular and bold TrueType fonts with Vietnamese glyphs, if installed."""

    for regular, bold in FONT_CANDIDATES:
        if Path(regular).exists() and Path(bold).exists():
            return regular, bold

    return None


@dataclass(frozen=True)
class TruthLine:
    section: str
    text: str


@dataclass
class CorpusDocument:
    id: str
    style: str
    layout: str
    language: str
    path: Path
    truth: List[TruthLine] = field(default_factory=list)
    wording: str = "standard"


# ---------------------------------------------------------------- content

NAMES = ["Nguyen Van An", "Tran Thi Binh", "Le Hoang Cuong", "Pham Minh Duc"]
CITIES = ["Ha Noi", "Da Nang", "Ho Chi Minh City", "Can Tho"]
COMPANIES = [
    "Northwind Labs", "Bluepeak Systems", "Orchid Software", "Helix Digital",
    "Quartz Analytics", "Ember Cloud", "Lumen Works", "Vertex Soft",
]
SCHOOLS = [
    "Hanoi University of Science", "Da Nang University of Technology",
    "HCMC University of Information Technology", "Can Tho University",
]
DEGREES = {
    "en": ["BSc in Computer Science", "BEng in Software Engineering"],
    "vi": ["Cử nhân Khoa học Máy tính", "Kỹ sư Công nghệ Phần mềm"],
}
ROLES = {
    "en": ["Backend Engineer", "Data Engineer", "Software Developer"],
    "vi": ["Kỹ sư phần mềm", "Kỹ sư dữ liệu", "Lập trình viên"],
}
VERBS = {
    "en": ["Built", "Designed", "Maintained", "Improved", "Automated", "Migrated"],
    "vi": ["Xây dựng", "Thiết kế", "Bảo trì", "Cải thiện", "Tự động hóa", "Chuyển đổi"],
}
OBJECTS = {
    "en": ["payment services", "reporting pipelines", "internal tools",
           "search features", "data models", "deployment scripts"],
    "vi": ["dịch vụ thanh toán", "luồng báo cáo", "công cụ nội bộ",
           "tính năng tìm kiếm", "mô hình dữ liệu", "tập lệnh triển khai"],
}
CERTIFICATES = {
    "en": ["AWS Certified Cloud Practitioner", "Google Data Analytics Certificate",
           "Professional Scrum Master I"],
    "vi": ["Chứng chỉ AWS Cloud Practitioner", "Chứng chỉ Phân tích dữ liệu Google",
           "Chứng chỉ Scrum Master"],
}
SUMMARY = {
    "en": "Engineer with a focus on reliable backend systems and clear communication.",
    "vi": "Kỹ sư tập trung vào hệ thống backend ổn định và giao tiếp rõ ràng.",
}
SKILL_POOL = sorted(
    {s for spec in FAMILIES.values() for s in spec["core"]}
)


class _Content:
    """Generated sections: name -> list of already-wrapped text lines."""

    def __init__(self, rng: random.Random, language: str, wrap_width: int):
        self.rng = rng
        self.language = language
        self.width = wrap_width
        self.sections: Dict[str, List[str]] = {}
        self._used: set = set()

    def build(self) -> Dict[str, List[str]]:
        lang = self.language
        rng = self.rng
        name = rng.choice(NAMES)
        handle = name.lower().replace(" ", ".")

        self.sections["personal_info"] = [
            name,
            f"{handle}@example.com",
            f"+84 9{rng.randint(10, 99)} {rng.randint(100, 999)} {rng.randint(100, 999)}",
            rng.choice(CITIES),
        ]
        self.sections["summary"] = self._wrap(SUMMARY[lang])
        self.sections["experience"] = self._experience()
        self.sections["education"] = self._education()
        self.sections["skills"] = self._wrap(
            ", ".join(rng.sample(SKILL_POOL, rng.randint(7, 10)))
        )
        self.sections["projects"] = self._projects()
        self.sections["certifications"] = [
            self._unique(c)
            for c in rng.sample(CERTIFICATES[lang], rng.randint(1, 2))
        ]

        return self.sections

    def _wrap(self, text: str) -> List[str]:
        return [self._unique(line) for line in textwrap.wrap(text, self.width)]

    def _unique(self, line: str) -> str:
        candidate = line
        counter = 2

        while candidate in self._used:
            candidate = f"{line} ({counter})"
            counter += 1

        self._used.add(candidate)

        return candidate

    def _bullet(self) -> List[str]:
        lang = self.language
        text = (
            f"- {self.rng.choice(VERBS[lang])} {self.rng.choice(OBJECTS[lang])} "
            f"using {self.rng.choice(SKILL_POOL)}"
            if lang == "en"
            else f"- {self.rng.choice(VERBS[lang])} {self.rng.choice(OBJECTS[lang])} "
                 f"bằng {self.rng.choice(SKILL_POOL)}"
        )

        return self._wrap(text)

    def _experience(self) -> List[str]:
        lines: List[str] = []
        year = 2024

        for _ in range(self.rng.randint(2, 3)):
            span = self.rng.randint(1, 3)
            lines.append(self._unique(
                f"{self.rng.choice(ROLES[self.language])} - {self.rng.choice(COMPANIES)}"
            ))
            lines.append(self._unique(f"{year - span} - {year}"))

            for _ in range(self.rng.randint(2, 3)):
                lines.extend(self._bullet())

            year -= span

        return lines

    def _education(self) -> List[str]:
        return [
            self._unique(self.rng.choice(DEGREES[self.language])),
            self._unique(self.rng.choice(SCHOOLS)),
            self._unique("2016 - 2020"),
        ]

    def _projects(self) -> List[str]:
        lines: List[str] = []

        for index in range(self.rng.randint(1, 2)):
            lines.append(self._unique(f"Project {chr(65 + index)}: {self.rng.choice(OBJECTS[self.language])}"))
            lines.extend(self._bullet())

        return lines


# ---------------------------------------------------------------- drawing


class _Writer:
    """Draws lines top to bottom in a column, adding pages when needed."""

    def __init__(
        self,
        document: fitz.Document,
        page: fitz.Page,
        x: float,
        fonts: Dict[str, str],
        allow_new_pages: bool,
        bottom: float = PAGE_BOTTOM,
    ):
        self.document = document
        self.page = page
        self.x = x
        self.y = PAGE_TOP
        self.fonts = fonts
        self.allow_new_pages = allow_new_pages
        self.bottom = bottom

    def _ensure_room(self, needed: float) -> None:
        if self.y + needed <= self.bottom or not self.allow_new_pages:
            return

        self.page = self.document.new_page()
        self._register_fonts(self.page)
        self.y = PAGE_TOP

    def _register_fonts(self, page: fitz.Page) -> None:
        register_fonts(page, self.fonts)

    def keep_together(self, needed: float) -> None:
        """Starts a new page now if the next `needed` points would not fit."""

        self._ensure_room(needed)

    def gap(self, amount: float) -> None:
        self.y += amount

    def line(self, text: str, size: float = BODY_SIZE, bold: bool = False) -> None:
        self._ensure_room(LINE_PITCH)
        alias = "B" if bold else "R"
        source = self.fonts[alias]

        self.page.insert_text(
            (self.x, self.y),
            text,
            fontsize=size,
            fontname=source if source in ("helv", "hebo") else alias,
        )
        self.y += max(LINE_PITCH, size * 1.3)


def register_fonts(page: fitz.Page, fonts: Dict[str, str]) -> None:
    for alias, source in fonts.items():
        if source in ("helv", "hebo"):
            continue

        page.insert_font(fontname=alias, fontfile=source)


def _font_sources(language: str) -> Optional[Dict[str, str]]:
    found = find_unicode_fonts()

    if found:
        return {"R": found[0], "B": found[1]}

    if language == "en":
        return {"R": "helv", "B": "hebo"}

    return None


def _draw(
    path: Path,
    sections: Dict[str, List[str]],
    style: HeadingStyle,
    layout: str,
    language: str,
    titles: Dict[str, str],
) -> None:

    fonts = _font_sources(language)

    if fonts is None:
        raise RuntimeError("No Unicode font available for this language")

    document = fitz.open()
    page = document.new_page()

    # base-14 fonts are referenced by name, not registered
    if fonts["R"] == "helv":
        fonts_for_writer = {"R": "helv", "B": "hebo"}
    else:
        fonts_for_writer = fonts
        register_fonts(page, fonts)

    def heading_text(section: str) -> str:
        title = titles[section]
        return title.upper() if style.upper else title

    def write_section(writer: _Writer, section: str) -> None:
        writer.gap(style.gap)
        writer.line(heading_text(section), size=style.size, bold=style.bold)

        for text in sections[section]:
            writer.line(text)

    def write_personal(writer: _Writer) -> None:
        lines = sections["personal_info"]
        writer.line(lines[0], size=16, bold=True)

        for text in lines[1:]:
            writer.line(text)

    if layout == "two_column":
        left = _Writer(document, page, 30, fonts_for_writer, allow_new_pages=False)
        right = _Writer(document, page, 215, fonts_for_writer, allow_new_pages=False)

        write_personal(left)
        write_section(left, "skills")
        write_section(left, "certifications")

        for section in ("summary", "experience", "education", "projects"):
            write_section(right, section)
    else:
        writer = _Writer(
            document, page, 72, fonts_for_writer,
            allow_new_pages=(layout == "multi_page"),
            bottom=MULTI_PAGE_BOTTOM,
        )

        write_personal(writer)

        for section in (
            "summary", "experience", "education", "skills", "projects", "certifications",
        ):
            write_section(writer, section)

    document.save(str(path))
    document.close()


# ---------------------------------------------------------------- builder


class CVCorpusBuilder:

    def __init__(self, seed: int = 42, per_variant: int = 2):
        self.seed = seed
        self.per_variant = per_variant

    def variants(self) -> List[Tuple[str, str, str, str]]:
        """(heading style, layout, language, wording) combinations."""

        languages = [
            language for language in LANGUAGES if _font_sources(language) is not None
        ]

        standard = [
            (style, layout, language, "standard")
            for style, layout, language in product(HEADING_STYLES, LAYOUTS, languages)
        ]

        alternate = [
            (style, layout, language, "alternate")
            for style, layout, language in product(ALTERNATE_STYLES, LAYOUTS, languages)
        ]

        return standard + alternate

    def build(self, directory: Path) -> List[CorpusDocument]:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        documents: List[CorpusDocument] = []

        for style_name, layout, language, wording in self.variants():
            titles = (
                SECTION_TITLES_ALTERNATE[language]
                if wording == "alternate"
                else SECTION_TITLES[language]
            )

            for index in range(self.per_variant):
                rng = random.Random(
                    f"{self.seed}-{style_name}-{layout}-{language}-{wording}-{index}"
                )

                wrap_width = 34 if layout == "two_column" else 78
                sections = _Content(rng, language, wrap_width).build()

                identifier = f"{wording}__{style_name}__{layout}__{language}__{index}"
                path = directory / f"{identifier}.pdf"

                _draw(
                    path, sections, HEADING_STYLES[style_name], layout, language, titles
                )

                truth = [
                    TruthLine(section, text)
                    for section, lines in sections.items()
                    for text in lines
                ]

                documents.append(
                    CorpusDocument(
                        id=identifier,
                        style=style_name,
                        layout=layout,
                        language=language,
                        path=path,
                        truth=truth,
                        wording=wording,
                    )
                )

        return documents
