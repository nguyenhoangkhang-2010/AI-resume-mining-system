import json

import numpy as np
import pytest

from app.extraction.section.heading_cache import MAX_ENTRIES, HeadingCache
from app.extraction.section.heading_classifier import (
    HeadingClassifier,
    is_heading_candidate,
)
from app.extraction.section.heading_style import (
    StyledLine,
    header_zone_end,
    learn_heading_style,
    split_styled,
    styled_lines_from_block,
)


def body(text, gap=2.5):
    return StyledLine(text, size=10.0, gap_above=gap)


def heading(text, size=10.0, bold=True, upper=False, gap=12.0):
    return StyledLine(text, size=size, bold=bold, upper=upper, gap_above=gap)


# ----------------------------------------------------------- typography


def span(text, size=10.0, flags=0, font="Arial", color=0):
    return {"text": text, "size": size, "flags": flags, "font": font, "color": color}


def line(text, y0, y1, spans):
    return {"text": text, "bbox": {"y0": y0, "y1": y1}, "spans": spans}


def test_bold_comes_from_the_flag_or_the_font_name():
    lines, _ = styled_lines_from_block(
        [
            line("Flagged", 0, 10, [span("Flagged", flags=16)]),
            line("Named", 14, 24, [span("Named", font="Arial-BoldMT")]),
            line("Plain", 28, 38, [span("Plain")]),
        ]
    )

    assert [item.bold for item in lines] == [True, True, False]


def test_gap_is_measured_from_the_previous_line_across_blocks():
    first, bottom = styled_lines_from_block([line("a", 0, 10, [span("a")])])
    second, _ = styled_lines_from_block(
        [line("b", 40, 50, [span("b")])], previous_bottom=bottom
    )

    assert first[0].gap_above is None
    assert second[0].gap_above == 30


def test_uppercase_needs_letters_to_count():
    lines, _ = styled_lines_from_block(
        [
            line("SKILLS", 0, 10, [span("SKILLS")]),
            line("2020 - 2023", 14, 24, [span("2020 - 2023")]),
        ]
    )

    assert [item.upper for item in lines] == [True, False]


def test_a_mixed_weight_line_is_not_bold():
    lines, _ = styled_lines_from_block(
        [line("Role: Nurse", 0, 10, [span("Role: ", flags=16), span("Nurse")])]
    )

    assert lines[0].bold is False


# -------------------------------------------------- learning the style


def document():
    return [
        body("Nguyen Thi Lan"),
        body("lan@example.com"),
        heading("Education"),
        body("BSc in Nursing"),
        body("Hanoi Medical University"),
        heading("Clinical Experience"),
        body("Staff Nurse - St Mary Hospital"),
        body("- Monitored post-operative patients"),
        heading("Skills"),
        body("Wound care, IV therapy"),
    ]


def test_unknown_heading_in_the_style_of_known_ones_is_a_boundary():
    lines = document()
    style = learn_heading_style(lines)

    segments = split_styled(lines, style, protected=2)

    unknown = [s for s in segments if s.unknown_heading]

    assert [s.heading for s in unknown] == ["Clinical Experience"]
    assert unknown[0].lines == [
        "Staff Nurse - St Mary Hospital",
        "- Monitored post-operative patients",
    ]


def test_known_headings_still_carry_their_section():
    lines = document()
    segments = split_styled(lines, learn_heading_style(lines), protected=2)

    assert [s.section for s in segments if not s.unknown_heading] == [
        None, "education", "skills",
    ]


def test_without_a_known_heading_nothing_is_learned():
    lines = [body("a b"), heading("Clinical Experience"), body("details")]

    assert learn_heading_style(lines) is None


def test_body_text_is_never_taken_for_a_heading():
    lines = document()
    segments = split_styled(lines, learn_heading_style(lines), protected=2)

    heads = {s.heading for s in segments if s.heading}

    assert "BSc in Nursing" not in heads
    assert "Hanoi Medical University" not in heads


def test_a_different_style_is_not_a_heading():
    lines = document()
    lines.insert(4, heading("Honours Course", size=12.0, bold=False))

    segments = split_styled(lines, learn_heading_style(lines), protected=2)

    assert not any(s.heading == "Honours Course" for s in segments)


def test_header_lines_are_protected():
    lines = [heading("Nguyen Thi Lan"), body("lan@example.com"), *document()[2:]]
    style = learn_heading_style(lines)

    segments = split_styled(lines, style, protected=header_zone_end(lines))

    assert not any(s.heading == "Nguyen Thi Lan" for s in segments)


def test_header_zone_ends_after_the_last_contact_line_and_a_location():
    lines = [
        body("Nguyen Thi Lan"),
        body("lan@example.com"),
        body("+84 912 345 678"),
        body("Hai Phong"),
        body("Summary"),
    ]

    assert header_zone_end(lines) == 4


def test_without_contact_lines_only_the_name_is_protected():
    assert header_zone_end([body("Nguyen Thi Lan"), body("Summary")]) == 1
    assert header_zone_end([]) == 0


def test_headings_set_like_body_text_are_told_apart_by_space():
    lines = [
        body("Nguyen Thi Lan"),
        body("lan@example.com"),
        body("Education", gap=30.0),
        body("BSc in Nursing"),
        body("Clinical Experience", gap=30.0),
        body("Staff Nurse"),
        body("Hospital Ward"),
    ]
    style = learn_heading_style(lines)

    segments = split_styled(lines, style, protected=2)

    assert [s.heading for s in segments if s.unknown_heading] == [
        "Clinical Experience"
    ]
    assert "Hospital Ward" in segments[-1].lines


def test_unspaced_headings_in_body_style_teach_nothing():
    lines = [
        body("Nguyen Thi Lan"),
        body("Education", gap=2.0),
        body("BSc in Nursing"),
        body("Clinical Experience", gap=2.0),
        body("Staff Nurse"),
    ]

    assert learn_heading_style(lines) is None


# ------------------------------------------------------ heading candidates


@pytest.mark.parametrize(
    "text",
    [
        "Clinical Experience", "Kinh nghiệm lâm sàng", "TOOLS AND PLATFORMS",
        "Tools & Platforms", "Skills:",
    ],
)
def test_headings_are_candidates(text):
    assert is_heading_candidate(text)


@pytest.mark.parametrize(
    "text",
    [
        "", "2020 - 2023", "Backend Engineer - Northwind Labs", "lan@example.com",
        "- Built payment services", "Built payment services for the bank.",
        "One two three four five six seven", "Use of Python in 2021",
    ],
)
def test_other_lines_are_not_candidates(text):
    assert not is_heading_candidate(text)


# ------------------------------------------------------ heading classifier

AXES = {"experience": 0, "education": 1, "skills": 2}


def toy_encoder(texts):
    vectors = []

    for text in texts:
        words = text.lower()
        vector = np.array(
            [
                1.0 if "experience" in words or "work" in words else 0.0,
                1.0 if "education" in words or "degree" in words else 0.0,
                1.0 if "skill" in words or "tool" in words else 0.0,
            ]
        )
        norm = np.linalg.norm(vector)
        vectors.append(vector / norm if norm else np.array([0.0, 0.0, 0.0]))

    return np.array(vectors)


EXAMPLES = {
    "experience": ["Work Experience"],
    "education": ["Education", "Degrees"],
    "skills": ["Skills", "Tools"],
}


def make_classifier(**kwargs):
    return HeadingClassifier(encode=toy_encoder, examples=EXAMPLES, **kwargs)


def test_classifier_maps_a_similar_heading_to_its_section():
    classifier = make_classifier(threshold=0.5, margin=0.1)

    assert classifier.classify("Clinical Experience") == "experience"
    assert classifier.classify("Tools and Platforms") == "skills"


def test_classifier_stays_silent_when_nothing_is_close():
    classifier = make_classifier(threshold=0.5, margin=0.1)

    assert classifier.classify("Northwind Labs") is None


def test_classifier_ignores_lines_that_cannot_be_headings():
    classifier = make_classifier(threshold=0.1, margin=0.0)

    assert classifier.classify("Worked experience at ACME in 2020") is None


def test_classifier_needs_a_clear_margin():
    classifier = make_classifier(threshold=0.5, margin=0.5)

    assert classifier.classify("Education and Work Experience") is None


def test_prefetch_encodes_each_line_once():
    calls = []

    def counting(texts):
        calls.append(list(texts))
        return toy_encoder(texts)

    classifier = HeadingClassifier(encode=counting, examples=EXAMPLES)
    calls.clear()

    classifier.prefetch(["Clinical Experience", "clinical experience", "Skills"])
    classifier.classify("Clinical Experience")

    assert len(calls) == 1
    assert len(calls[0]) == 3 or len(calls[0]) == 2


# ------------------------------------------------------------ the cache


def test_cache_ignores_case_accents_and_punctuation():
    cache = HeadingCache()

    cache.put("Kinh nghiệm lâm sàng", "experience")

    assert cache.get("KINH NGHIEM LAM SANG:") == "experience"
    assert cache.get("Something else") is None


def test_cache_survives_a_restart(tmp_path):
    path = tmp_path / "cache" / "headings.json"

    HeadingCache(path).put("Clinical Experience", "experience")

    assert HeadingCache(path).get("clinical experience") == "experience"
    assert not list(path.parent.glob("*.tmp"))


def test_cache_starts_empty_when_the_file_is_damaged(tmp_path):
    path = tmp_path / "headings.json"
    path.write_text("{not json", encoding="utf-8")

    cache = HeadingCache(path)

    assert len(cache) == 0

    cache.put("Campaigns", "projects")

    assert json.loads(path.read_text(encoding="utf-8")) == {"campaigns": "projects"}


def test_cache_has_a_size_limit():
    cache = HeadingCache()

    for number in range(MAX_ENTRIES + 10):
        cache.put(f"heading {number}", "other")

    assert len(cache) == MAX_ENTRIES

    cache.put("heading 1", "skills")

    assert cache.get("heading 1") == "skills"


# -------------------------------------------- lines that only look like headings


def bold_entities(count):
    return [heading(f"Company Number {chr(65 + number)}") for number in range(count)]


def test_a_style_shared_by_many_other_lines_is_not_used():
    # Every employer name is bold, like the headings: bold marks nothing here.
    lines = document()[:6] + bold_entities(12) + document()[6:]

    assert learn_heading_style(lines, protected=2) is None


def test_a_few_lookalikes_are_still_boundaries():
    lines = document()[:6] + bold_entities(3) + document()[6:]

    assert learn_heading_style(lines, protected=2) is not None


def test_header_lines_are_not_counted_as_lookalikes():
    lines = bold_entities(2) + document()

    assert learn_heading_style(lines, protected=2) is not None
