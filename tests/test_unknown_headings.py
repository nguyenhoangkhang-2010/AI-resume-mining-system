"""
Sections headed by words the lexicon does not know ("Clinical Experience",
"Publications") must still start a new section, so that their text does not
leak into the section above them.
"""

import pytest

from app.evaluation.cv_industries import INDUSTRY, IndustryCorpusBuilder
from app.evaluation.section_eval import aggregate, score_document
from app.extraction.section.heading_cache import HeadingCache
from app.extraction.section.heading_lexicon import normalise
from app.extraction.section.section_detector import SectionDetector
from app.resume_processing.pipelines.resume_pipeline import ResumePipeline

LAYOUTS = ["single", "two_column", "sidebar_right", "banner_two_column", "timeline", "long"]


class NeverConfident:
    def classify(self, text):
        return "other", 0.0


class StubLLM:
    """No model: every fallback says "other"; headings are answered from a table."""

    def __init__(self, answers=None):
        self.answers = answers or {}
        self.asked = []

    def classify_single(self, text):
        return "other", 0.0

    def classify_document(self, lines):
        return []

    def classify_heading(self, heading):
        self.asked.append(heading)

        return self.answers.get(normalise(heading))


@pytest.fixture(scope="module")
def corpus(tmp_path_factory):
    directory = tmp_path_factory.mktemp("unknown_headings")

    documents = IndustryCorpusBuilder(
        seed=5,
        industries=["healthcare", "finance", "education"],
        layouts=LAYOUTS,
        wordings=(INDUSTRY,),
    ).build(directory)

    return [d for d in documents if d.language == "en"]


def run(documents, **kwargs):
    llm = kwargs.pop("llm", None) or StubLLM()

    pipeline = ResumePipeline(
        SectionDetector(NeverConfident(), llm, **kwargs),
        extraction_engine=None,  # type: ignore[arg-type]
    )

    return [
        score_document(document, pipeline.detect_sections(document.path))
        for document in documents
    ]


def leaks(results):
    """Lines of ignored sections (references, publications ...) kept somewhere."""

    return sum(
        count
        for result in results
        for (truth, guess), count in result.confusion.items()
        if truth == "other" and guess not in ("other", "missing")
    )


def answers_for(documents):
    return {normalise(heading): section for d in documents for heading, section in d.headings}


def test_unfamiliar_headings_stop_text_leaking_into_the_section_above(corpus):
    words_only = run(corpus, use_heading_style=False)
    by_style = run(corpus, use_heading_style=True)

    assert leaks(words_only) > 0
    assert leaks(by_style) < leaks(words_only) / 2


def test_unfamiliar_headings_are_classified_by_the_model_when_it_answers(corpus):
    llm = StubLLM(answers_for(corpus))

    results = run(corpus, llm=llm)

    assert aggregate(results)["all"].f1 >= 0.9
    assert llm.asked, "unfamiliar headings should have been put to the model"


def test_each_distinct_heading_is_put_to_the_model_once_with_a_cache(corpus):
    llm = StubLLM(answers_for(corpus))
    cache = HeadingCache()

    run(corpus, llm=llm, heading_cache=cache)

    asked = [normalise(h) for h in llm.asked]

    assert len(asked) == len(set(asked))
    assert len(cache) == len(set(asked))


def test_without_a_cache_the_same_heading_is_asked_again(corpus):
    llm = StubLLM(answers_for(corpus))

    run(corpus, llm=llm)

    asked = [normalise(h) for h in llm.asked]

    assert len(asked) > len(set(asked))


def test_a_remembered_heading_needs_no_model(corpus):
    cache = HeadingCache()

    for heading, section in answers_for(corpus).items():
        cache.put(heading, section)

    llm = StubLLM()

    results = run(corpus, llm=llm, heading_cache=cache)

    assert llm.asked == []
    assert aggregate(results)["all"].f1 >= 0.9


def test_known_headings_never_reach_the_model(corpus):
    llm = StubLLM(answers_for(corpus))

    run(corpus, llm=llm)

    for heading in llm.asked:
        assert normalise(heading) not in {"education", "skills", "summary"}


def test_the_name_and_contact_lines_stay_in_personal_info(corpus):
    llm = StubLLM(answers_for(corpus))
    results = run(corpus, llm=llm)

    personal = [
        result.confusion[("personal_info", "personal_info")]
        for result in results
    ]
    total = [
        sum(n for (truth, _), n in result.confusion.items() if truth == "personal_info")
        for result in results
    ]

    assert sum(personal) / sum(total) >= 0.95


# ------------------------------------------------------ catch-all headings


class SureOf:
    def __init__(self, section, confidence=0.9):
        self.result = (section, confidence)

    def classify(self, text):
        return self.result


def test_a_catch_all_heading_is_decided_by_the_text_under_it():
    llm = StubLLM({normalise("Additional Information"): "mixed"})
    detector = SectionDetector(SureOf("skills"), llm)

    assert detector._resolve_heading("Additional Information", "Python, SQL") == (
        "skills",
        0.9,
    )


def test_a_catch_all_heading_over_unclear_text_is_dropped_without_the_model():
    llm = StubLLM({normalise("Additional Information"): "mixed"})
    detector = SectionDetector(SureOf("skills", 0.1), llm)

    assert detector._resolve_heading("Additional Information", "???") == ("other", 0.0)


def test_a_catch_all_answer_is_remembered_and_not_asked_twice():
    llm = StubLLM({normalise("More Details"): "mixed"})
    cache = HeadingCache()
    detector = SectionDetector(SureOf("education"), llm, heading_cache=cache)

    detector._resolve_heading("More Details", "BSc")
    detector._resolve_heading("MORE DETAILS", "BSc")

    assert len(llm.asked) == 1
    assert cache.get("more details") == "mixed"


@pytest.mark.parametrize(
    "response, expected",
    [
        ('{"section_type": "experience"}', "experience"),
        ('{"section_type": "Mixed"}', "mixed"),
        ('```json\n{"section_type": "other"}\n```', "other"),
        ('{"section_type": "hobbies"}', None),
        ("I think it is experience", None),
        ("", None),
    ],
)
def test_heading_answers_are_parsed_strictly(response, expected):
    from app.extraction.section.section_classifier import SectionClassifier

    assert SectionClassifier._parse_heading_response(response) == expected


def test_classify_heading_puts_only_the_heading_to_the_model():
    from app.extraction.section.section_classifier import SectionClassifier
    from tests.fakes.fake_llm_extractor import FakeLLMExtractor

    llm = FakeLLMExtractor('{"section_type": "experience"}')

    answer = SectionClassifier(llm).classify_heading("  Clinical Experience ")

    assert answer == "experience"
    assert llm.calls == ["Clinical Experience"]


def test_classify_heading_survives_a_failing_model():
    from app.extraction.section.section_classifier import SectionClassifier

    class Broken:
        def extract_info(self, *args, **kwargs):
            raise RuntimeError("model gone")

    assert SectionClassifier(Broken()).classify_heading("Skills") is None
    assert SectionClassifier(Broken()).classify_heading("  ") is None
