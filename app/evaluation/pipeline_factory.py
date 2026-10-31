"""
Builds the resume pipeline the way the API does, for scripts that measure it.

The LLM is passed in, so a script can hand over the real model, a recorder
around it, or `NoModel` to see what the rules and the embedding models
achieve without it.
"""

from typing import Any, Callable, Optional

from app.extraction.section.heading_cache import HeadingCache


class NoModel:
    """An LLM that never answers: every fallback is "unknown"."""

    def extract_info(
        self,
        text: str,
        prompt_template: Optional[str] = None,
        max_new_tokens: Optional[int] = None,
    ) -> str:
        return ""


def build_pipeline(llm: Any, extractor_wrapper: Optional[Callable[[str, Any], Any]] = None):
    """
    The pipeline with `llm` as its language model. `extractor_wrapper`, if
    given, is called as wrapper(name, extractor) -> extractor for each
    extractor (used to time them).
    """

    from app.extraction.extraction_engine import ExtractionEngine
    from app.extraction.section.heading_classifier import HeadingClassifier
    from app.extraction.section.section_classifier import SectionClassifier
    from app.extraction.section.section_detector import SectionDetector
    from app.extraction.section.section_semantic_classifier import (
        SectionSemanticClassifier,
    )
    from app.resume_processing.pipelines.resume_pipeline import ResumePipeline

    detector = SectionDetector(
        semantic_classifier=SectionSemanticClassifier(),
        llm_classifier=SectionClassifier(llm_extractor=llm),
        heading_classifier=HeadingClassifier(),
        heading_cache=HeadingCache(),
    )
    engine = ExtractionEngine(llm_extractor=llm)

    if extractor_wrapper is not None:
        engine.extractors = {
            name: extractor_wrapper(name, extractor)
            for name, extractor in engine.extractors.items()
        }

    return ResumePipeline(detector, engine)
