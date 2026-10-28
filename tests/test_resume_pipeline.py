from unittest.mock import Mock

import pytest

from app.resume_processing.pipelines.resume_pipeline import (
    ResumePipeline,
)


class FakeSectionDetector:
    def __init__(self, sections=None):
        self.sections = sections or {}
        self.received_text = None

    def detect(self, layout_analysis, region_analysis, cleaned_text):
        self.received_text = cleaned_text
        return self.sections


class FakeExtractionEngine:
    def __init__(self):
        self.received_sections = None

    def extract_resume(self, sections):
        self.received_sections = sections
        return {"skills": ["python"], "sections_seen": list(sections)}


def build_pipeline(sections=None):
    detector = FakeSectionDetector(sections)
    engine = FakeExtractionEngine()

    pipeline = ResumePipeline(
        section_detector=detector,
        extraction_engine=engine,
    )

    return pipeline, detector, engine


def test_resume_pipeline_runs_all_stages(make_pdf):
    path = make_pdf(
        [
            "John Doe",
            "john@gmail.com",
            "EXPERIENCE",
            "3 years experience",
        ]
    )

    pipeline, detector, engine = build_pipeline(
        {"experience": ["3 years experience"]}
    )

    result = pipeline.process_pdf(path)

    assert "John Doe" in result["raw_text"]
    assert "John Doe" in result["cleaned_text"]
    assert "John Doe" in detector.received_text
    assert engine.received_sections == {
        "experience": ["3 years experience"]
    }
    assert result["skills"] == ["python"]


def test_resume_pipeline_includes_extraction_output(make_pdf):
    path = make_pdf(["CERTIFICATIONS", "AWS Certified Cloud Practitioner"])

    pipeline, _, _ = build_pipeline(
        {"certifications": ["AWS Certified Cloud Practitioner"]}
    )

    result = pipeline.process_pdf(path)

    assert result["sections_seen"] == ["certifications"]


def test_resume_pipeline_missing_file():
    pipeline, _, _ = build_pipeline()

    with pytest.raises(FileNotFoundError):
        pipeline.process_pdf("does_not_exist.pdf")


def test_resume_pipeline_parser_exception(make_pdf):
    pipeline, _, _ = build_pipeline()
    pipeline.parser.parse = Mock(side_effect=Exception("PDF parsing failed"))

    with pytest.raises(Exception, match="PDF parsing failed"):
        pipeline.process_pdf("sample.pdf")


def test_resume_pipeline_engine_exception_is_propagated(make_pdf):
    path = make_pdf(["John Doe"])

    pipeline, _, engine = build_pipeline()
    engine.extract_resume = Mock(side_effect=RuntimeError("engine failed"))

    with pytest.raises(RuntimeError, match="engine failed"):
        pipeline.process_pdf(path)
