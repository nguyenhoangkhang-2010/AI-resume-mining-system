from app.extraction.experience.experience_extractor import ExperienceExtractor
from app.extraction.summary.summary_extractor import SummaryExtractor
from scripts.benchmark_extraction import (
    CallRecord,
    DocumentTiming,
    RecordingLLM,
    TimedExtractor,
    _label,
    report,
)


class Inner:
    def extract_info(self, text, prompt_template=None, max_new_tokens=None):
        return "x" * 5

    other = "attribute"


def test_prompts_are_recognised_by_extractor():
    assert _label(ExperienceExtractor.EXTRACTION_PROMPT) == "experience"
    assert _label(SummaryExtractor.EXTRACTION_PROMPT) == "summary"
    assert _label(None) == "raw"
    assert _label("something else entirely") == "other"


def test_every_call_is_recorded_with_sizes_and_time():
    recorder = RecordingLLM(Inner())

    recorder.extract_info("hello", ExperienceExtractor.EXTRACTION_PROMPT, 8)

    call = recorder.calls[0]

    assert (call.label, call.input_chars, call.output_chars) == ("experience", 5, 5)
    assert call.seconds >= 0
    assert recorder.other == "attribute"


def test_extractor_time_is_added_up():
    sink = {}

    class Fast:
        def extract(self, text):
            return text

    timed = TimedExtractor("skills", Fast(), sink)

    assert timed.extract("a") == "a"
    timed.extract("b")

    assert set(sink) == {"skills"} and sink["skills"] >= 0


def test_report_without_truth_has_no_field_table():
    entry = DocumentTiming(
        "cv-1",
        total=10.0,
        sections=4.0,
        extractors={"experience": 6.0},
        calls=[CallRecord("experience", 10, 5, 6.0)],
        answered_by={"experience.model": 1},
    )

    text = "\n".join(report([entry], "Title"))

    assert "Seconds per CV: mean 10" in text
    assert "| experience | 6.0 | 1.0 | 6.0 |" in text
    assert "| experience | 0 | 1 |" in text
    assert "Fields found" not in text
