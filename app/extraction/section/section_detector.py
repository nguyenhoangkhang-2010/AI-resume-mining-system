from __future__ import annotations

from typing import Dict, List, Optional

from loguru import logger

from app.extraction.section.section_classifier import SectionClassifier
from app.extraction.section.section_semantic_classifier import (
    SectionSemanticClassifier,
)
from app.resume_processing.layout.layout_analyzer import LayoutAnalysis
from app.resume_processing.layout.semantic_region_analyzer import (
    SemanticRegionAnalysis,
)


class SectionDetector:

    def __init__(
        self,
        semantic_classifier: SectionSemanticClassifier,
        llm_classifier: Optional[SectionClassifier] = None,
        min_confidence: float = 0.55,
    ) -> None:
        self.semantic_classifier = semantic_classifier

        self.llm_classifier = (
            llm_classifier
            if llm_classifier is not None
            else SectionClassifier()
        )

        self.min_confidence = min_confidence

    def detect(
        self,
        layout_analysis: LayoutAnalysis,
        region_analysis: SemanticRegionAnalysis,
        cleaned_text: str = "",
    ) -> Dict[str, List[str]]:

        if not region_analysis.regions:
            logger.warning(
                "No semantic regions available from layout analysis. "
                "Falling back to full-text LLM section detection."
            )
            return self._detect_from_plain_text(
                cleaned_text
            )

        block_text_by_id = self._index_block_text(
            layout_analysis
        )

        sections: Dict[str, List[str]] = {}
        project_regions: List[str] = []

        fallback_used = 0

        for region in region_analysis.regions:

            region_text = self._region_text(
                region,
                block_text_by_id,
            )

            if not region_text:
                continue

            section_type, confidence = (
                self.semantic_classifier.classify(
                    region_text
                )
            )

            if confidence < self.min_confidence:

                fallback_type, fallback_confidence = (
                    self.llm_classifier.classify_single(
                        region_text
                    )
                )

                logger.debug(
                    "Fallback LLM classification for region {}: "
                    "'{}' (embedding conf={:.2f}) -> '{}' "
                    "(llm conf={:.2f})",
                    region.region_id,
                    section_type,
                    confidence,
                    fallback_type,
                    fallback_confidence,
                )

                section_type = fallback_type
                confidence = fallback_confidence
                fallback_used += 1

            logger.info(
                "Region {} -> '{}' (confidence={:.2f})",
                region.region_id,
                section_type,
                confidence,
            )

            if section_type == "projects":
                project_regions.append(
                    region_text
                )
                continue

            if section_type == "other":
                continue

            sections.setdefault(
                section_type,
                [],
            ).append(region_text)

        if project_regions:
            sections["projects"] = project_regions
            sections["__projects_regions__"] = project_regions

        logger.info(
            "Section detection complete: {} sections, "
            "{} region(s) used LLM fallback.",
            len(
                [
                    key
                    for key in sections.keys()
                    if not key.startswith("__")
                ]
            ),
            fallback_used,
        )

        return sections

    def _detect_from_plain_text(
        self,
        text: str,
    ) -> Dict[str, List[str]]:

        if not text or not text.strip():
            return {}

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        if not lines:
            return {}

        logger.info(
            "Starting full-text LLM section detection for {} lines",
            len(lines),
        )

        classifications = self.llm_classifier.classify_document(
            lines
        )

        if not classifications:
            logger.warning(
                "No semantic sections detected",
            )
            return {}

        classifications = sorted(
            classifications,
            key=lambda item: item["line_index"],
        )

        result: Dict[str, List[str]] = {}

        for position, boundary in enumerate(
            classifications
        ):
            start = boundary["line_index"]

            end = (
                classifications[position + 1]["line_index"]
                if position + 1 < len(classifications)
                else len(lines)
            )

            implicit = bool(
                boundary.get("implicit", False)
            )

            content = (
                lines[start:end]
                if implicit
                else lines[start + 1:end]
            )

            section_type = boundary["section_type"]

            logger.info(
                "Detected section: line={} '{}' -> '{}'{}",
                start,
                boundary.get("heading") or "<implicit>",
                section_type,
                " [implicit]" if implicit else "",
            )

            if section_type == "other":
                continue

            result.setdefault(
                section_type,
                [],
            ).extend(content)

        if "projects" in result:
            result["__projects_regions__"] = [
                "\n".join(result["projects"])
            ]

        return result

    @staticmethod
    def _region_text(
        region,
        block_text_by_id: Dict[str, str],
    ) -> str:

        parts = [
            block_text_by_id[block_id]
            for block_id in region.block_ids
            if block_id in block_text_by_id
        ]

        return "\n".join(parts).strip()

    @staticmethod
    def _index_block_text(
        layout_analysis: LayoutAnalysis,
    ) -> Dict[str, str]:

        result: Dict[str, str] = {}

        for page in layout_analysis.pages:
            for block in page.blocks:
                result[block.block_id] = block.text

        return result