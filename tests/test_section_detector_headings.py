from types import SimpleNamespace

from app.extraction.section.section_detector import SectionDetector
from app.resume_processing.layout.semantic_region_analyzer import (
    SemanticRegion,
    SemanticRegionAnalysis,
)


class FakeClassifier:
    """Embedding classifier stand-in that is never confident."""

    def __init__(self, label="other", confidence=0.2):
        self.label = label
        self.confidence = confidence
        self.calls = []

    def classify(self, text):
        self.calls.append(text)
        return self.label, self.confidence


class FakeLLM:
    def __init__(self, label="other"):
        self.label = label
        self.calls = []

    def classify_single(self, text):
        self.calls.append(text)
        return self.label, 0.9

    def classify_document(self, lines):
        self.calls.append("\n".join(lines))
        return []


def make_layout(texts):
    """One block per region; block ids are b0, b1, ..."""

    blocks = [SimpleNamespace(block_id=f"b{i}", text=t) for i, t in enumerate(texts)]

    return SimpleNamespace(pages=[SimpleNamespace(blocks=blocks)])


def region(index, page=0, x0=50, x1=500):
    return SemanticRegion(
        region_id=f"r{index}",
        page_index=page,
        block_ids=[f"b{index}"],
        x0=x0,
        y0=0,
        x1=x1,
        y1=10,
    )


def detect(texts, regions=None, classifier=None, llm=None, cleaned_text=""):
    classifier = classifier or FakeClassifier()
    llm = llm or FakeLLM()

    detector = SectionDetector(classifier, llm)

    regions = regions or [region(i) for i in range(len(texts))]

    sections = detector.detect(
        make_layout(texts),
        SemanticRegionAnalysis(regions=regions),
        cleaned_text,
    )

    return sections, classifier, llm


def test_headings_inside_one_region_split_it_by_wording():
    sections, classifier, llm = detect(
        [
            "Work Experience\nBackend Engineer\nBuilt APIs\n"
            "Education\nBSc Computer Science\n"
            "Skills\nPython, SQL"
        ]
    )

    assert sections["experience"] == ["Backend Engineer\nBuilt APIs"]
    assert sections["education"] == ["BSc Computer Science"]
    assert sections["skills"] == ["Python, SQL"]
    assert classifier.calls == []
    assert llm.calls == []


def test_vietnamese_headings_are_recognised():
    sections, _, llm = detect(
        ["Kinh nghiệm làm việc\nKỹ sư phần mềm\nHọc vấn\nCử nhân Khoa học Máy tính"]
    )

    assert "experience" in sections
    assert "education" in sections
    assert llm.calls == []


def test_cv_header_with_contact_details_is_personal_info():
    sections, classifier, _ = detect(
        [
            "Nguyen Van An\nan@example.com\n+84 912 345 678\nHa Noi\n"
            "Work Experience\nBackend Engineer"
        ]
    )

    assert sections["personal_info"] == [
        "Nguyen Van An\nan@example.com\n+84 912 345 678\nHa Noi"
    ]
    assert sections["experience"] == ["Backend Engineer"]
    assert classifier.calls == []


def test_text_after_the_header_is_not_swallowed_as_personal_info():
    sections, classifier, llm = detect(
        [
            "an@example.com\nBuilt payment services using Python for banks.\n"
            "Skills\nPython"
        ]
    )

    assert sections["personal_info"] == ["an@example.com"]
    # the remaining lead-in text goes through the normal classification
    assert classifier.calls == ["Built payment services using Python for banks."]
    assert "skills" in sections


def test_region_without_heading_uses_the_classifier_then_the_llm():
    classifier = FakeClassifier(label="projects", confidence=0.3)
    llm = FakeLLM(label="education")

    sections, _, llm = detect(
        ["Some text without any heading wording"],
        classifier=classifier,
        llm=llm,
    )

    assert sections["education"] == ["Some text without any heading wording"]
    assert not {name for name in sections if not name.startswith("__")} - {
        "education"
    }
    assert len(llm.calls) == 1


def test_confident_classifier_result_is_kept_without_the_llm():
    sections, _, llm = detect(
        ["Some text without any heading wording"],
        classifier=FakeClassifier(label="skills", confidence=0.9),
    )

    assert "skills" in sections
    assert llm.calls == []


def test_other_sections_are_dropped_and_projects_are_tracked_separately():
    sections, _, _ = detect(
        ["References\nAvailable on request", "Projects\nResume Miner"]
    )

    assert "other" not in sections
    assert sections["projects"] == ["Resume Miner"]
    assert sections["__projects_regions__"] == ["Resume Miner"]


def test_headingless_region_on_the_next_page_continues_the_section():
    regions = [region(0, page=0), region(1, page=1)]

    sections, classifier, llm = detect(
        [
            "Work Experience\nBackend Engineer\nBuilt APIs",
            "Maintained reporting pipelines\nMigrated services",
        ],
        regions=regions,
    )

    assert sections["experience"] == [
        "Backend Engineer\nBuilt APIs",
        "Maintained reporting pipelines\nMigrated services",
    ]
    assert classifier.calls == []
    assert llm.calls == []


def test_continuation_requires_the_same_column():
    regions = [region(0, page=0, x0=30, x1=200), region(1, page=1, x0=300, x1=560)]

    _, classifier, _ = detect(
        ["Skills\nPython", "Some other column text"],
        regions=regions,
    )

    assert classifier.calls == ["Some other column text"]


def test_continuation_does_not_apply_on_the_same_page():
    regions = [region(0, page=0), region(1, page=0)]

    _, classifier, _ = detect(
        ["Skills\nPython", "Unrelated text below"],
        regions=regions,
    )

    assert classifier.calls == ["Unrelated text below"]


def test_plain_text_fallback_uses_headings_without_the_llm():
    detector = SectionDetector(FakeClassifier(), FakeLLM())

    sections = detector.detect(
        make_layout([]),
        SemanticRegionAnalysis(regions=[]),
        "Work Experience\nBackend Engineer\nSkills\nPython",
    )

    assert sections["experience"] == ["Backend Engineer"]
    assert sections["skills"] == ["Python"]
    assert detector.llm_classifier.calls == []


def test_plain_text_without_headings_still_goes_to_the_llm():
    llm = FakeLLM()
    detector = SectionDetector(FakeClassifier(), llm)

    sections = detector.detect(
        make_layout([]),
        SemanticRegionAnalysis(regions=[]),
        "just some text\nwith no heading wording",
    )

    assert sections == {}
    assert len(llm.calls) == 1


def test_provenance_says_how_each_section_was_found():
    sections, _, _ = detect(
        [
            "Nguyen Van An\nan@example.com\n+84 912 345 678\n"
            "Work Experience\nBackend Engineer\nSkills\nPython"
        ]
    )

    assert sections["__provenance__"] == [
        "personal_info:contact_header:1.00",
        "experience:heading_words:1.00",
        "skills:heading_words:1.00",
    ]


def test_provenance_marks_a_section_guessed_by_the_model():
    sections, _, _ = detect(
        ["Some text without any heading wording"],
        classifier=FakeClassifier(label="projects", confidence=0.3),
        llm=FakeLLM(label="education"),
    )

    assert sections["__provenance__"] == ["education:model_guess:0.90"]


class UnsureLLM(FakeLLM):
    """A model that cannot tell what a fragment is."""

    def classify_single(self, text):
        self.calls.append(text)
        return "other", 0.0


def placed(index, x0, y0, x1, y1, page=0):
    return SemanticRegion(
        region_id=f"r{index}",
        page_index=page,
        block_ids=[f"b{index}"],
        x0=x0,
        y0=y0,
        x1=x1,
        y1=y1,
    )


def detect_placed(texts, regions, llm=None, **options):
    detector = SectionDetector(
        FakeClassifier(),
        llm or UnsureLLM(),
        **options,
    )

    return detector.detect(
        make_layout(texts),
        SemanticRegionAnalysis(regions=regions),
        "",
    )


HEADING = "Work Experience\nBackend Engineer"
LOOSE = "Built payment services for banks."


def test_a_region_under_a_heading_in_the_same_column_joins_its_section():
    sections = detect_placed(
        [HEADING, LOOSE],
        [placed(0, 200, 100, 320, 130), placed(1, 210, 200, 500, 260)],
    )

    assert sections["experience"] == ["Backend Engineer", LOOSE]
    assert "experience:column:0.60" in sections["__provenance__"]


def test_the_closest_heading_above_decides_not_the_last_one_read():
    # The regions are read column by column, so "Education" comes last.
    sections = detect_placed(
        [HEADING, "Education\nBSc", LOOSE],
        [
            placed(0, 200, 100, 320, 130),
            placed(1, 20, 400, 140, 430),
            placed(2, 210, 200, 500, 260),
        ],
    )

    assert LOOSE in sections["experience"]
    assert LOOSE not in sections.get("education", [])


def test_a_region_in_another_column_is_not_placed_by_position():
    sections = detect_placed(
        [HEADING, LOOSE],
        [placed(0, 200, 100, 320, 130), placed(1, 400, 200, 560, 260)],
    )

    assert sections["experience"] == ["Backend Engineer"]


def test_a_region_above_the_heading_is_not_placed_by_position():
    sections = detect_placed(
        [HEADING, LOOSE],
        [placed(0, 200, 300, 320, 330), placed(1, 210, 100, 500, 160)],
    )

    assert sections["experience"] == ["Backend Engineer"]


def test_a_region_on_another_page_is_not_placed_by_position():
    sections = detect_placed(
        [HEADING, LOOSE],
        [placed(0, 200, 100, 320, 130), placed(1, 210, 200, 500, 260, page=1)],
    )

    # the cross-page rule handles this case; the column rule must not.
    assert sections["experience"] == ["Backend Engineer", LOOSE]
    assert "experience:continued:1.00" in sections["__provenance__"]


def test_the_header_block_is_not_extended_by_position():
    sections = detect_placed(
        ["Nguyen Van An\nan@example.com\n+84 912 345 678", LOOSE],
        [placed(0, 200, 50, 400, 90), placed(1, 210, 200, 500, 260)],
    )

    assert LOOSE not in sections.get("personal_info", [])


def test_a_confident_model_answer_wins_over_position():
    sections = detect_placed(
        [HEADING, LOOSE],
        [placed(0, 200, 100, 320, 130), placed(1, 210, 200, 500, 260)],
        llm=FakeLLM(label="education"),
    )

    assert sections["education"] == [LOOSE]


def test_column_placement_can_be_switched_off():
    sections = detect_placed(
        [HEADING, LOOSE],
        [placed(0, 200, 100, 320, 130), placed(1, 210, 200, 500, 260)],
        use_column_continuation=False,
    )

    assert sections["experience"] == ["Backend Engineer"]
