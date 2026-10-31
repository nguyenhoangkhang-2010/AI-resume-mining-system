"""
Finds section headings by how they look, whatever they say.

The heading lexicon knows the words of common headings. A CV from another
industry may head a section "Clinical Experience", "Campaigns" or "Tools and
Platforms". Such a heading is still easy to see on the page: it is set in the
same way as the headings the lexicon does know in the same document (same
size, weight, case and colour, or the same extra space above it).

So the style of the recognised headings is learned from the document itself,
and a short line that is set in that style but whose words are unknown is a
heading too. Only the boundary is decided here; which section the new
heading starts is decided from its words and its body text (see
SectionDetector).
"""

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from loguru import logger

from app.extraction.section.heading_classifier import is_heading_candidate
from app.extraction.section.heading_lexicon import (
    heading_section,
    looks_like_contact,
)

# A line more than this many font sizes below the previous one is "spaced":
# normal line spacing is about 0.2 of the font size.
SPACED_GAP = 0.9

# The CV header (name, contact lines) is never a heading, wherever it is set.
HEADER_LINES = 10
HEADER_TRAILING_LINES = 2

BOLD_FLAG = 16

# A CV has a handful of sections. If far more short lines than that are set
# like the known headings (for example every company name is bold), the
# style does not mark headings in this document and is not used.
MAX_UNKNOWN_HEADINGS = 10


@dataclass(frozen=True)
class StyledLine:
    text: str
    size: float = 0.0
    bold: bool = False
    upper: bool = False
    color: int = 0
    # Space between this line and the one above it, in points; None for the
    # first line of a column or page.
    gap_above: Optional[float] = None

    @property
    def key(self) -> Tuple[float, bool, bool, int]:
        return (round(self.size * 2) / 2, self.bold, self.upper, self.color)

    @property
    def spaced(self) -> bool:
        return (
            self.gap_above is not None
            and self.size > 0
            and self.gap_above > SPACED_GAP * self.size
        )


def styled_lines_from_block(
    lines: Sequence[Dict[str, Any]],
    previous_bottom: Optional[float] = None,
) -> Tuple[List[StyledLine], Optional[float]]:
    """
    Converts the line dictionaries of a layout block (text, bbox, spans) into
    styled lines. Returns them with the bottom edge of the last line, so the
    next block can compute its gap.
    """

    result: List[StyledLine] = []
    bottom = previous_bottom

    for line in lines:
        text = str(line.get("text", "")).strip()

        if not text:
            continue

        spans = [span for span in line.get("spans", []) if span.get("text")]
        bbox = line.get("bbox") or {}

        size = max((float(span.get("size") or 0.0) for span in spans), default=0.0)
        bold = bool(spans) and all(_is_bold(span) for span in spans)
        color = int(spans[0].get("color") or 0) if spans else 0

        top = bbox.get("y0")
        gap = None if bottom is None or top is None else float(top) - bottom

        letters = [char for char in text if char.isalpha()]
        upper = len(letters) >= 3 and all(char.isupper() for char in letters)

        result.append(
            StyledLine(
                text=text,
                size=size,
                bold=bold,
                upper=upper,
                color=color,
                gap_above=gap,
            )
        )

        bottom = float(bbox["y1"]) if bbox.get("y1") is not None else bottom

    return result, bottom


def _is_bold(span: Dict[str, Any]) -> bool:
    flags = span.get("flags")

    if isinstance(flags, int) and flags & BOLD_FLAG:
        return True

    return "bold" in str(span.get("font") or "").casefold()


def header_zone_end(lines: Sequence[StyledLine]) -> int:
    """
    Number of leading lines that belong to the CV header: everything up to
    the last contact line within the first HEADER_LINES lines, plus a short
    location line. With no contact line only the first line (the name) is
    protected.
    """

    last_contact = -1

    for index, line in enumerate(lines[:HEADER_LINES]):
        if looks_like_contact(line.text):
            last_contact = index

    if last_contact < 0:
        return 1 if lines else 0

    end = last_contact + 1

    while (
        end < len(lines)
        and end - last_contact <= HEADER_TRAILING_LINES
        and len(lines[end].text.split()) <= 5
        and not any(char.isdigit() for char in lines[end].text)
        and heading_section(lines[end].text) is None
    ):
        end += 1

    return end


@dataclass
class HeadingStyle:
    """Styles in which this document sets the headings the lexicon knows."""

    keys: Set[Tuple[float, bool, bool, int]]
    # When a heading is set exactly like body text, only space marks it.
    spaced_only_keys: Set[Tuple[float, bool, bool, int]]
    body_key: Optional[Tuple[float, bool, bool, int]]

    def matches(self, line: StyledLine) -> bool:
        key = line.key

        if key not in self.keys:
            return False

        if key in self.spaced_only_keys:
            return line.spaced

        return True


def learn_heading_style(
    lines: Sequence[StyledLine],
    protected: int = 0,
) -> Optional[HeadingStyle]:
    """
    The style of the known headings among `lines` (the whole document, in
    reading order), or None when the document has no known heading or the
    style also fits too many other lines to mark headings. The first
    `protected` lines (the CV header) are not counted.
    """

    if not lines:
        return None

    counts: Dict[Tuple[float, bool, bool, int], int] = {}

    for line in lines:
        counts[line.key] = counts.get(line.key, 0) + 1

    body_key = max(counts, key=lambda key: counts[key])

    known = [line for line in lines if heading_section(line.text) is not None]

    if not known:
        return None

    keys: Set[Tuple[float, bool, bool, int]] = set()
    spaced_only: Set[Tuple[float, bool, bool, int]] = set()

    for key in {line.key for line in known}:
        group = [line for line in known if line.key == key]

        keys.add(key)

        # A heading set like the body text is told apart by space alone, and
        # only if the known headings in that style really are spaced.
        if key == body_key:
            if sum(line.spaced for line in group) * 2 < len(group):
                keys.discard(key)
            else:
                spaced_only.add(key)

    if not keys:
        return None

    style = HeadingStyle(keys=keys, spaced_only_keys=spaced_only, body_key=body_key)

    lookalikes = sum(
        1
        for index, line in enumerate(lines)
        if index >= protected
        and heading_section(line.text) is None
        and is_heading_candidate(line.text)
        and style.matches(line)
    )

    if lookalikes > MAX_UNKNOWN_HEADINGS:
        logger.info(
            "Heading style ignored: {} other short lines share it.",
            lookalikes,
        )
        return None

    return style


@dataclass
class StyledSegment:
    section: Optional[str]
    heading: Optional[str]
    # True when the heading was recognised by its look, not its words
    unknown_heading: bool
    lines: List[str]

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


def split_styled(
    lines: Sequence[StyledLine],
    style: Optional[HeadingStyle],
    protected: int = 0,
    allow_unknown: bool = True,
) -> List[StyledSegment]:
    """
    Splits lines at headings. A line is a heading when the lexicon knows its
    words, or (if `style` is given) when it is a heading candidate set in the
    document's heading style. The first `protected` lines are only headings
    if the lexicon says so.

    Segments with no lines are kept when they carry an unknown heading, so
    the caller can see the boundary; the first segment has no heading.
    """

    segments: List[StyledSegment] = [StyledSegment(None, None, False, [])]

    for index, line in enumerate(lines):
        section = heading_section(line.text)

        if section is not None:
            segments.append(StyledSegment(section, line.text, False, []))
            continue

        if (
            allow_unknown
            and style is not None
            and index >= protected
            and is_heading_candidate(line.text)
            and style.matches(line)
        ):
            segments.append(StyledSegment(None, line.text, True, []))
            continue

        segments[-1].lines.append(line.text)

    return [
        segment
        for segment in segments
        if segment.lines or segment.unknown_heading
    ]


def candidate_texts(segments: Iterable[StyledSegment]) -> List[str]:
    return [s.heading for s in segments if s.unknown_heading and s.heading]
