from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from app.resume_processing.layout.layout_analyzer import (
    LayoutAnalysis,
    LayoutBlockFeatures,
)


@dataclass
class SemanticRegion:
    region_id: str
    page_index: int

    block_ids: List[str] = field(
        default_factory=list
    )

    x0: float = 0.0
    y0: float = 0.0
    x1: float = 0.0
    y1: float = 0.0


@dataclass
class SemanticRegionAnalysis:
    regions: List[SemanticRegion] = field(
        default_factory=list
    )


class SemanticRegionAnalyzer:

    def analyze(
        self,
        layout: LayoutAnalysis,
    ) -> SemanticRegionAnalysis:

        regions: List[SemanticRegion] = []

        for page in layout.pages:

            page_regions = self._analyze_page(
                page.page_index,
                page.width,
                page.height,
                page.blocks,
            )

            regions.extend(page_regions)

        return SemanticRegionAnalysis(
            regions=regions
        )

    # ---------------------------------------------------------
    # PAGE
    # ---------------------------------------------------------

    def _analyze_page(
        self,
        page_index: int,
        page_width: float,
        page_height: float,
        blocks: List[LayoutBlockFeatures],
    ) -> List[SemanticRegion]:

        if not blocks:
            return []

        columns = self._detect_columns(
            blocks,
            page_width,
        )

        if len(columns) <= 1:
            return self._build_vertical_regions(
                page_index,
                columns[0] if columns else [],
            )

        return self._build_column_regions(
            page_index,
            columns,
        )

    # ---------------------------------------------------------
    # COLUMN DETECTION
    # ---------------------------------------------------------

    def _detect_columns(
        self,
        blocks: List[LayoutBlockFeatures],
        page_width: float,
    ) -> List[List[LayoutBlockFeatures]]:

        if not blocks:
            return []

        ordered = sorted(
            blocks,
            key=lambda block: (
                self._bbox_x0(block),
                self._bbox_x1(block),
            ),
        )

        groups: List[List[LayoutBlockFeatures]] = []

        for block in ordered:

            placed = False

            for group in groups:

                if self._belongs_to_column(
                    block,
                    group,
                    page_width,
                ):
                    group.append(block)
                    placed = True
                    break

            if not placed:
                groups.append([block])

        candidate_groups = [
            group
            for group in groups
            if len(group) >= 2
        ]

        if not candidate_groups:
            return [blocks]

        assigned_ids = {
            block.block_id
            for group in candidate_groups
            for block in group
        }

        unassigned = [
            block
            for block in blocks
            if block.block_id not in assigned_ids
        ]

        if unassigned:
            candidate_groups = self._assign_unassigned_blocks(
                candidate_groups,
                unassigned,
            )

        candidate_groups.sort(
            key=lambda group: min(
                self._bbox_x0(block)
                for block in group
            )
        )

        return candidate_groups

    def _assign_unassigned_blocks(
        self,
        groups: List[List[LayoutBlockFeatures]],
        blocks: List[LayoutBlockFeatures],
    ) -> List[List[LayoutBlockFeatures]]:

        for block in blocks:
            best_group = None
            best_score = float("-inf")

            block_x0 = self._bbox_x0(block)
            block_x1 = self._bbox_x1(block)
            block_center = (
                block_x0 + block_x1
            ) / 2.0

            for group in groups:
                group_x0 = min(
                    self._bbox_x0(item)
                    for item in group
                )

                group_x1 = max(
                    self._bbox_x1(item)
                    for item in group
                )

                group_center = (
                    group_x0 + group_x1
                ) / 2.0

                overlap = max(
                    0.0,
                    min(block_x1, group_x1)
                    - max(block_x0, group_x0),
                )

                block_width = max(
                    block_x1 - block_x0,
                    1.0,
                )

                overlap_ratio = (
                    overlap / block_width
                )

                center_distance = abs(
                    block_center - group_center
                )

                score = (
                    overlap_ratio * 100.0
                    - center_distance
                )

                if score > best_score:
                    best_score = score
                    best_group = group

            if best_group is not None:
                best_group.append(block)

        return groups

    def _belongs_to_column(
        self,
        block: LayoutBlockFeatures,
        group: List[LayoutBlockFeatures],
        page_width: float,
    ) -> bool:

        block_x0 = self._bbox_x0(block)
        block_x1 = self._bbox_x1(block)

        group_x0 = min(
            self._bbox_x0(item)
            for item in group
        )

        group_x1 = max(
            self._bbox_x1(item)
            for item in group
        )

        overlap = max(
            0.0,
            min(block_x1, group_x1)
            - max(block_x0, group_x0),
        )

        block_width = max(
            block_x1 - block_x0,
            1.0,
        )

        overlap_ratio = (
            overlap / block_width
        )

        if overlap_ratio >= 0.30:
            return True

        block_center = (
            block_x0 + block_x1
        ) / 2.0

        group_center = (
            group_x0 + group_x1
        ) / 2.0

        distance = abs(
            block_center - group_center
        )

        return distance <= max(
            35.0,
            page_width * 0.06,
        )

    # ---------------------------------------------------------
    # COLUMN REGION BUILDING
    # ---------------------------------------------------------

    def _build_column_regions(
        self,
        page_index: int,
        columns: List[
            List[LayoutBlockFeatures]
        ],
    ) -> List[SemanticRegion]:

        regions: List[SemanticRegion] = []

        for column_index, column in enumerate(
            columns
        ):

            ordered = sorted(
                column,
                key=lambda block: (
                    block.y_center,
                    block.x_center,
                ),
            )

            if not ordered:
                continue

            # Split vertically when there is
            # a substantial whitespace gap.
            groups = self._split_vertical_groups(
                ordered
            )

            for group_index, group in enumerate(
                groups
            ):

                regions.append(
                    self._create_region(
                        page_index=page_index,
                        region_index=(
                            column_index,
                            group_index,
                        ),
                        blocks=group,
                    )
                )

        return regions

    # ---------------------------------------------------------
    # SINGLE COLUMN
    # ---------------------------------------------------------

    def _build_vertical_regions(
        self,
        page_index: int,
        blocks: List[LayoutBlockFeatures],
    ) -> List[SemanticRegion]:

        if not blocks:
            return []

        ordered = sorted(
            blocks,
            key=lambda block: (
                block.y_center,
                block.x_center,
            ),
        )

        groups = self._split_vertical_groups(
            ordered
        )

        return [
            self._create_region(
                page_index=page_index,
                region_index=(0, index),
                blocks=group,
            )
            for index, group in enumerate(groups)
        ]

    # ---------------------------------------------------------
    # VERTICAL SPLITTING
    # ---------------------------------------------------------

    def _split_vertical_groups(
        self,
        blocks: List[LayoutBlockFeatures],
    ) -> List[List[LayoutBlockFeatures]]:

        if not blocks:
            return []

        ordered = sorted(
            blocks,
            key=lambda block: (
                block.y_center,
                block.x_center,
            ),
        )

        groups: List[
            List[LayoutBlockFeatures]
        ] = []

        current: List[
            LayoutBlockFeatures
        ] = []

        for index, block in enumerate(ordered):

            if not current:
                current = [block]
                continue

            previous = current[-1]

            gap = self._vertical_gap(
                previous,
                block,
            )

            gap_threshold = (
                self._vertical_gap_threshold(
                    previous,
                    block,
                )
            )

            is_heading = self._is_section_heading(
                block,
                ordered,
                index,
            )

            if (
                gap > gap_threshold
                or (
                    is_heading
                    and self._has_meaningful_previous_content(
                        current
                    )
                )
            ):
                groups.append(current)
                current = [block]

            else:
                current.append(block)

        if current:
            groups.append(current)

        return groups

    def _vertical_gap(
        self,
        first: LayoutBlockFeatures,
        second: LayoutBlockFeatures,
    ) -> float:

        first_y1 = self._bbox_y1(first)
        second_y0 = self._bbox_y0(second)

        return max(
            0.0,
            second_y0 - first_y1,
        )

    def _vertical_gap_threshold(
        self,
        first: LayoutBlockFeatures,
        second: LayoutBlockFeatures,
    ) -> float:

        average_height = (
            max(first.height, 1.0)
            + max(second.height, 1.0)
        ) / 2.0

        return max(
            18.0,
            average_height * 2.5,
        )

    # ---------------------------------------------------------
    # REGION
    # ---------------------------------------------------------

    def _create_region(
        self,
        page_index: int,
        region_index: Tuple[int, int],
        blocks: List[LayoutBlockFeatures],
    ) -> SemanticRegion:

        x0 = min(
            self._bbox_x0(block)
            for block in blocks
        )

        y0 = min(
            self._bbox_y0(block)
            for block in blocks
        )

        x1 = max(
            self._bbox_x1(block)
            for block in blocks
        )

        y1 = max(
            self._bbox_y1(block)
            for block in blocks
        )

        column_index, group_index = region_index

        return SemanticRegion(
            region_id=(
                f"page_{page_index}"
                f"_region_{column_index}"
                f"_{group_index}"
            ),
            page_index=page_index,
            block_ids=[
                block.block_id
                for block in blocks
            ],
            x0=x0,
            y0=y0,
            x1=x1,
            y1=y1,
        )

    # ---------------------------------------------------------
    # BBOX HELPERS
    # ---------------------------------------------------------

    @staticmethod
    def _bbox_x0(
        block: LayoutBlockFeatures,
    ) -> float:

        return float(
            block.bbox.get(
                "x0",
                0.0,
            )
        )

    @staticmethod
    def _bbox_x1(
        block: LayoutBlockFeatures,
    ) -> float:

        return float(
            block.bbox.get(
                "x1",
                0.0,
            )
        )

    @staticmethod
    def _bbox_y0(
        block: LayoutBlockFeatures,
    ) -> float:

        return float(
            block.bbox.get(
                "y0",
                0.0,
            )
        )

    @staticmethod
    def _bbox_y1(
        block: LayoutBlockFeatures,
    ) -> float:

        return float(
            block.bbox.get(
                "y1",
                0.0,
            )
        )
        
    def _is_section_heading(
        self,
        block: LayoutBlockFeatures,
        blocks: List[LayoutBlockFeatures],
        index: int,
    ) -> bool:

        text = " ".join(
            block.text.split()
        ).strip()

        if not text:
            return False

        # Section headings are normally short.
        if len(text) > 80:
            return False

        # A heading is usually one line.
        if block.line_count > 2:
            return False

        # Heading should have meaningful font information.
        if block.font_size_mean <= 0:
            return False

        # Look at neighboring blocks in the same
        # vertical flow.
        previous = None

        if index > 0:
            previous = blocks[index - 1]

        # Large font is a strong heading signal.
        if previous is not None:
            if (
                block.font_size_mean
                >= previous.font_size_mean * 1.25
            ):
                return True

        # Otherwise compare against the local
        # neighborhood rather than the whole page.
        neighborhood = blocks[
            max(0, index - 3):
            min(len(blocks), index + 4)
        ]

        neighboring_sizes = [
            item.font_size_mean
            for item in neighborhood
            if item is not block
            and item.font_size_mean > 0
        ]

        if neighboring_sizes:
            local_average = (
                sum(neighboring_sizes)
                / len(neighboring_sizes)
            )

            if (
                block.font_size_mean
                >= local_average * 1.20
            ):
                return True

        # Short uppercase text is a useful generic
        # heading signal.
        letters = [
            char
            for char in text
            if char.isalpha()
        ]

        if letters:

            uppercase_ratio = (
                sum(
                    char.isupper()
                    for char in letters
                )
                / len(letters)
            )

            if (
                uppercase_ratio >= 0.80
                and len(text) <= 40
            ):
                return True

        return False


    def _has_meaningful_previous_content(
        self,
        current: List[LayoutBlockFeatures],
    ) -> bool:

        if not current:
            return False

        # Do not split a heading from another
        # heading-like block immediately above it.
        if len(current) == 1:
            if self._is_heading_like(
                current[0]
            ):
                return False

        return True


    def _is_heading_like(
        self,
        block: LayoutBlockFeatures,
    ) -> bool:

        text = " ".join(
            block.text.split()
        ).strip()

        if not text:
            return False

        if block.line_count > 2:
            return False

        if len(text) > 80:
            return False

        if block.font_size_mean >= 12:
            return True

        letters = [
            char
            for char in text
            if char.isalpha()
        ]

        if not letters:
            return False

        uppercase_ratio = (
            sum(
                char.isupper()
                for char in letters
            )
            / len(letters)
        )

        return (
            uppercase_ratio >= 0.80
            and len(text) <= 40
        )