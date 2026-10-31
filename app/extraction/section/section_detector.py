from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from loguru import logger

from app.extraction.section.heading_cache import HeadingCache
from app.extraction.section.heading_classifier import HeadingClassifier
from app.extraction.section.heading_lexicon import (
    looks_like_contact,
    split_by_headings,
    split_contact_header,
)
from app.extraction.section.heading_style import (
    StyledLine,
    header_zone_end,
    learn_heading_style,
    split_styled,
    styled_lines_from_block,
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


# Answer for catch-all headings; the text under the heading decides.
MIXED_HEADING = SectionClassifier.MIXED

# Confidence given to a region placed by its position under a heading.
COLUMN_CONFIDENCE = 0.6


class SectionDetector:

    def __init__(
        self,
        semantic_classifier: SectionSemanticClassifier,
        llm_classifier: Optional[SectionClassifier] = None,
        min_confidence: float = 0.55,
        heading_classifier: Optional[HeadingClassifier] = None,
        heading_cache: Optional[HeadingCache] = None,
        use_heading_style: bool = True,
        use_column_continuation: bool = True,
    ) -> None:
        self.semantic_classifier = semantic_classifier
        self.heading_classifier = heading_classifier
        self.heading_cache = heading_cache
        self.use_heading_style = use_heading_style
        self.use_column_continuation = use_column_continuation

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
        styled_used = 0
        continued = 0

        # Headings whose words are unknown are found by their look: the
        # style of the known headings is learned from this document.
        region_lines = self._index_region_lines(
            layout_analysis,
            region_analysis,
        )

        document_lines = [
            line
            for region in region_analysis.regions
            for line in region_lines.get(region.region_id, [])
        ]

        heading_style = (
            learn_heading_style(
                document_lines,
                protected=header_zone_end(document_lines),
            )
            if self.use_heading_style
            else None
        )

        header_checked = False

        # "section:how:confidence" for every segment, so a later stage can
        # tell a section found by its heading from one guessed by a model.
        provenance: List[str] = []

        # Section and region of the most recent heading found by wording.
        last_heading: Optional[Tuple[str, SemanticRegion]] = None

        # Every heading seen so far, to place regions that have none.
        anchors: List[Tuple[str, SemanticRegion]] = []

        for region in region_analysis.regions:

            region_text = self._region_text(
                region,
                block_text_by_id,
            )

            if not region_text:
                continue

            # Headings are recognised by their wording, whatever their style,
            # and by their look when the wording is unknown. They split the
            # region wherever they appear.
            styled = region_lines.get(region.region_id)

            if styled:
                protected = 0 if header_checked else header_zone_end(styled)
                header_checked = True

                segments = [
                    (
                        part.section,
                        part.text,
                        part.heading if part.unknown_heading else None,
                    )
                    for part in split_styled(
                        styled,
                        heading_style,
                        protected,
                    )
                ]

                if self.heading_classifier is not None:
                    self.heading_classifier.prefetch(
                        [
                            heading
                            for _, _, heading in segments
                            if heading
                        ]
                    )
            else:
                segments = [
                    (heading, text, None)
                    for heading, text in split_by_headings(
                        region_text
                    )
                ]

            # Text before the first heading that carries an email, phone
            # number or profile link starts with the CV header (name and
            # contact lines); what follows it is classified separately.
            if (
                last_heading is None
                and segments
                and segments[0][0] is None
                and segments[0][2] is None
                and looks_like_contact(segments[0][1])
            ):
                header, rest = split_contact_header(
                    segments[0][1]
                )

                segments = [
                    ("personal_info", header, None),
                    *(
                        [(None, rest, None)]
                        if rest.strip()
                        else []
                    ),
                    *segments[1:],
                ]

                header_forced = True
            else:
                header_forced = False

            for position, (heading, segment_text, unknown) in enumerate(
                segments
            ):

                if unknown is not None:
                    if not segment_text.strip():
                        continue

                    section_type, confidence = self._resolve_heading(
                        unknown,
                        segment_text,
                    )
                    styled_used += 1
                    last_heading = (section_type, region)
                    anchors.append(last_heading)
                    how = "heading_style"

                elif header_forced and position == 0:
                    section_type, confidence = "personal_info", 1.0
                    how = "contact_header"

                elif heading is not None:
                    section_type, confidence = heading, 1.0
                    heading_used += 1
                    last_heading = (heading, region)
                    anchors.append(last_heading)
                    how = "heading_words"

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
                    how = "continued"

                else:
                    section_type, confidence = (
                        self.semantic_classifier.classify(
                            segment_text
                        )
                    )
                    how = "semantic"

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
                        how = "model_guess"

                        # Neither the text nor the model could tell: a region
                        # that sits under a heading in the same column is
                        # part of that heading's section (the pieces of a
                        # designed template are separate regions).
                        if (
                            confidence < self.min_confidence
                            and self.use_column_continuation
                            and (
                                below := self._below_heading(
                                    anchors,
                                    region,
                                )
                            )
                            is not None
                        ):
                            section_type = below
                            confidence = COLUMN_CONFIDENCE
                            how = "column"

                logger.info(
                    "Region {} -> '{}' (confidence={:.2f})",
                    region.region_id,
                    section_type,
                    confidence,
                )

                provenance.append(f"{section_type}:{how}:{confidence:.2f}")

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

        sections["__provenance__"] = provenance

        logger.info(
            "Section detection complete: {} sections, {} by heading "
            "wording, {} by heading style, {} continued across pages, "
            "{} region(s) used LLM fallback.",
            len(
                [
                    key
                    for key in sections.keys()
                    if not key.startswith("__")
                ]
            ),
            heading_used,
            styled_used,
            continued,
            fallback_used,
        )

        return sections

    def _resolve_heading(
        self,
        heading: str,
        body: str,
    ) -> Tuple[str, float]:
        """
        The section started by a heading whose words are not in the lexicon.

        A remembered answer is used first, then the language model is asked
        about the heading alone (cheap, and remembered for next time). If
        the model is unavailable, the heading's wording and the text under
        it are compared with the sections; when they disagree the text under
        the heading is trusted, since that is what ends up in the section.
        """

        mixed = False

        if self.heading_cache is not None:
            remembered = self.heading_cache.get(heading)

            if remembered == MIXED_HEADING:
                mixed = True
            elif remembered is not None:
                return remembered, 1.0

        ask_heading = getattr(self.llm_classifier, "classify_heading", None)

        if ask_heading is not None and not mixed:
            answered = ask_heading(heading)

            if answered is not None:
                if self.heading_cache is not None:
                    self.heading_cache.put(heading, answered)

                if answered == MIXED_HEADING:
                    mixed = True
                else:
                    return answered, 1.0

        # A catch-all heading ("Additional Information") says nothing about
        # what it holds: only the text under it can tell.
        by_wording = (
            self.heading_classifier.classify(heading)
            if self.heading_classifier is not None and not mixed
            else None
        )

        by_body, confidence = self.semantic_classifier.classify(body)

        if by_wording is not None and (
            confidence < self.min_confidence or by_body == by_wording
        ):
            return by_wording, 1.0

        if confidence >= self.min_confidence:
            return by_body, confidence

        fallback_type, fallback_confidence = (
            self.llm_classifier.classify_single(body)
        )

        return fallback_type, fallback_confidence

    @staticmethod
    def _index_region_lines(
        layout_analysis: LayoutAnalysis,
        region_analysis: SemanticRegionAnalysis,
    ) -> Dict[str, List[StyledLine]]:
        """The lines of each region with their typography, in region order."""

        blocks = {
            block.block_id: block
            for page in layout_analysis.pages
            for block in page.blocks
        }

        result: Dict[str, List[StyledLine]] = {}

        for region in region_analysis.regions:
            lines: List[StyledLine] = []
            bottom = None

            for block_id in region.block_ids:
                block = blocks.get(block_id)

                if block is None:
                    continue

                block_lines, bottom = styled_lines_from_block(
                    getattr(block, "lines", None) or [],
                    bottom,
                )
                lines.extend(block_lines)

            if lines:
                result[region.region_id] = lines

        return result

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

    @staticmethod
    def _below_heading(
        anchors: List[Tuple[str, SemanticRegion]],
        region: SemanticRegion,
    ) -> Optional[str]:
        """
        The section of the closest heading above a region: same page, same
        column, starting at or below the heading. None if there is none.
        """

        best: Optional[Tuple[str, SemanticRegion]] = None

        for section_type, previous in anchors:
            if section_type == "personal_info":
                continue

            if (
                region.page_index != previous.page_index
                or region.y0 < previous.y0
            ):
                continue

            overlap = min(region.x1, previous.x1) - max(region.x0, previous.x0)

            narrower = min(
                region.x1 - region.x0,
                previous.x1 - previous.x0,
            )

            if narrower <= 0 or overlap / narrower < 0.5:
                continue

            if best is None or previous.y0 >= best[1].y0:
                best = (section_type, previous)

        return best[0] if best else None

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
            return self._with_provenance(
                by_wording,
                "heading_words",
                1.0,
            )

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

        return self._with_provenance(
            result,
            "model_guess",
            0.5,
        )

    @staticmethod
    def _with_provenance(
        sections: Dict[str, List[str]],
        how: str,
        confidence: float,
    ) -> Dict[str, List[str]]:
        """Marks sections found without page layout, one entry each."""

        sections["__provenance__"] = [
            f"{name}:{how}:{confidence:.2f}"
            for name in sections
            if not name.startswith("__")
        ]

        return sections

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