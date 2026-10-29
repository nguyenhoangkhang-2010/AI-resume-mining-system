from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from loguru import logger

from app.extraction.section.heading_lexicon import (
    looks_like_contact,
    split_by_headings,
    split_contact_header,
)
from app.extraction.section.section_classifier import SectionClassifier
from app.extraction.section.section_semantic_classifier import (
    SectionSemanticClassifier,
)
from app.resume_processing.layout.layout_analyzer import LayoutAnalysis
from app.resume_processing.layout.semantic_region_analyzer import (
    SemanticRegion,
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
        heading_used = 0
        continued = 0

        # Section and region of the most recent heading found by wording.
        last_heading: Optional[Tuple[str, SemanticRegion]] = None

        for region in region_analysis.regions:

            region_text = self._region_text(
                region,
                block_text_by_id,
            )

            if not region_text:
                continue

            # Headings are recognised by their wording, whatever their style,
            # and split the region wherever they appear.
            segments = split_by_headings(
                region_text
            )

            # Text before the first heading that carries an email, phone
            # number or profile link starts with the CV header (name and
            # contact lines); what follows it is classified separately.
            if (
                last_heading is None
                and segments
                and segments[0][0] is None
                and looks_like_contact(segments[0][1])
            ):
                header, rest = split_contact_header(
                    segments[0][1]
                )

                segments = [
                    ("personal_info", header),
                    *(
                        [(None, rest)]
                        if rest.strip()
                        else []
                    ),
                    *segments[1:],
                ]

                header_forced = True
            else:
                header_forced = False

            for position, (heading, segment_text) in enumerate(
                segments
            ):

                if header_forced and position == 0:
                    section_type, confidence = "personal_info", 1.0

                elif heading is not None:
                    section_type, confidence = heading, 1.0
                    heading_used += 1
                    last_heading = (heading, region)

                elif (
                    continued_type := self._continuation(
                        last_heading,
                        region,
                    )
                ) is not None:
                    section_type = continued_type
                    confidence = 1.0
                    continued += 1
                    last_heading = (section_type, region)

                else:
                    section_type, confidence = (
                        self.semantic_classifier.classify(
                            segment_text
                        )
                    )

                    if confidence < self.min_confidence:

                        fallback_type, fallback_confidence = (
                            self.llm_classifier.classify_single(
                                segment_text
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
                        segment_text
                    )
                    continue

                if section_type == "other":
                    continue

                sections.setdefault(
                    section_type,
                    [],
                ).append(segment_text)

        if project_regions:
            sections["projects"] = project_regions
            sections["__projects_regions__"] = project_regions

        logger.info(
            "Section detection complete: {} sections, {} by heading "
            "wording, {} continued across pages, {} region(s) used LLM "
            "fallback.",
            len(
                [
                    key
                    for key in sections.keys()
                    if not key.startswith("__")
                ]
            ),
            heading_used,
            continued,
            fallback_used,
        )

        return sections

    @staticmethod
    def _continuation(
        last_heading: Optional[Tuple[str, SemanticRegion]],
        region: SemanticRegion,
    ) -> Optional[str]:
        """
        The section a region without a heading continues: the previous
        heading's section, when the region is on a later page and in the
        same column. None otherwise.
        """

        if last_heading is None:
            return None

        section_type, previous = last_heading

        if region.page_index <= previous.page_index:
            return None

        overlap = min(region.x1, previous.x1) - max(region.x0, previous.x0)

        narrower = min(
            region.x1 - region.x0,
            previous.x1 - previous.x0,
        )

        if narrower > 0 and overlap / narrower >= 0.5:
            return section_type

        return None

    def _detect_from_plain_text(
        self,
        text: str,
    ) -> Dict[str, List[str]]:

        if not text or not text.strip():
            return {}

        by_wording = self._detect_by_wording(
            text
        )

        if by_wording:
            return by_wording

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

    def _detect_by_wording(
        self,
        text: str,
    ) -> Dict[str, List[str]]:
        """
        Splits plain text at headings recognised by their wording. Returns
        an empty mapping when the text has no such heading, so the caller
        can fall back to the LLM.
        """

        segments = split_by_headings(
            text
        )

        if not any(
            heading is not None
            for heading, _ in segments
        ):
            return {}

        result: Dict[str, List[str]] = {}

        for heading, body in segments:

            section_type = heading

            if section_type is None:
                section_type, _ = (
                    self.semantic_classifier.classify(
                        body
                    )
                )

            if section_type == "other":
                continue

            result.setdefault(
                section_type,
                [],
            ).append(body)

        if "projects" in result:
            result["__projects_regions__"] = list(
                result["projects"]
            )

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