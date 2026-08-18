from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from app.resume_processing.layout.layout_analyzer import (
    LayoutAnalysis,
    LayoutBlockFeatures,
)
from app.resume_processing.layout.semantic_region_analyzer import (
    SemanticRegion,
    SemanticRegionAnalysis,
    SemanticRegionAnalyzer,
)


@dataclass
class ReadingOrderPage:
    page_index: int

    ordered_block_ids: List[str] = field(
        default_factory=list
    )


@dataclass
class ReadingOrderAnalysis:
    pages: List[ReadingOrderPage] = field(
        default_factory=list
    )

    ordered_block_ids: List[str] = field(
        default_factory=list
    )


class ReadingOrderAnalyzer:

    def __init__(
        self,
        semantic_region_analyzer: SemanticRegionAnalyzer | None = None,
    ) -> None:

        self.semantic_region_analyzer = (
            semantic_region_analyzer
            or SemanticRegionAnalyzer()
        )

    def analyze(
        self,
        layout: LayoutAnalysis,
    ) -> ReadingOrderAnalysis:

        semantic_analysis = (
            self.semantic_region_analyzer.analyze(
                layout
            )
        )

        pages: List[ReadingOrderPage] = []
        global_order: List[str] = []

        for page in layout.pages:

            page_regions = [
                region
                for region in semantic_analysis.regions
                if region.page_index == page.page_index
            ]

            block_lookup = {
                block.block_id: block
                for block in page.blocks
            }

            ordered_regions = self._order_regions(
                page_regions
            )

            page_block_ids: List[str] = []

            for region in ordered_regions:

                ordered_blocks = self._order_region_blocks(
                    region,
                    block_lookup,
                )

                for block in ordered_blocks:

                    if block.block_id not in page_block_ids:
                        page_block_ids.append(
                            block.block_id
                        )

            remaining_blocks = [
                block
                for block in page.blocks
                if block.block_id
                not in page_block_ids
            ]

            remaining_blocks.sort(
                key=lambda block: (
                    block.y_center,
                    block.x_center,
                )
            )

            page_block_ids.extend(
                block.block_id
                for block in remaining_blocks
            )

            page_order = ReadingOrderPage(
                page_index=page.page_index,
                ordered_block_ids=page_block_ids,
            )

            pages.append(page_order)
            global_order.extend(page_block_ids)

        return ReadingOrderAnalysis(
            pages=pages,
            ordered_block_ids=global_order,
        )

    def _order_regions(
        self,
        regions: List[SemanticRegion],
    ) -> List[SemanticRegion]:

        if not regions:
            return []

        top_regions: List[SemanticRegion] = []
        body_regions: List[SemanticRegion] = []

        for region in regions:

            if self._is_top_region(region):
                top_regions.append(region)
            else:
                body_regions.append(region)

        top_regions.sort(
            key=lambda region: (
                region.y0,
                region.x0,
            )
        )

        if not body_regions:
            return top_regions

        body_regions = self._order_body_regions(
            body_regions
        )

        return [
            *top_regions,
            *body_regions,
        ]

    def _is_top_region(
        self,
        region: SemanticRegion,
    ) -> bool:

        return region.y0 <= 220.0

    def _order_body_regions(
        self,
        regions: List[SemanticRegion],
    ) -> List[SemanticRegion]:

        if len(regions) <= 1:
            return regions

        columns = self._group_regions_into_columns(
            regions
        )

        if len(columns) <= 1:

            return sorted(
                regions,
                key=lambda region: (
                    region.y0,
                    region.x0,
                ),
            )

        ordered: List[SemanticRegion] = []

        for column in columns:

            column.sort(
                key=lambda region: (
                    region.y0,
                    region.x0,
                )
            )

            ordered.extend(column)

        return ordered

    def _group_regions_into_columns(
        self,
        regions: List[SemanticRegion],
    ) -> List[List[SemanticRegion]]:

        if not regions:
            return []

        sorted_regions = sorted(
            regions,
            key=lambda region: region.x0,
        )

        columns: List[
            List[SemanticRegion]
        ] = []

        for region in sorted_regions:

            placed = False

            for column in columns:

                if self._region_belongs_to_column(
                    region,
                    column,
                ):
                    column.append(region)
                    placed = True
                    break

            if not placed:
                columns.append([region])

        columns.sort(
            key=lambda column: min(
                region.x0
                for region in column
            )
        )

        return columns

    def _region_belongs_to_column(
        self,
        region: SemanticRegion,
        column: List[SemanticRegion],
    ) -> bool:

        region_width = max(
            region.x1 - region.x0,
            1.0,
        )

        column_x0 = min(
            item.x0
            for item in column
        )

        column_x1 = max(
            item.x1
            for item in column
        )

        overlap = max(
            0.0,
            min(region.x1, column_x1)
            - max(region.x0, column_x0),
        )

        overlap_ratio = (
            overlap / region_width
        )

        if overlap_ratio >= 0.30:
            return True

        region_center = (
            region.x0 + region.x1
        ) / 2.0

        column_center = (
            column_x0 + column_x1
        ) / 2.0

        distance = abs(
            region_center - column_center
        )

        return distance <= 45.0

    def _order_region_blocks(
        self,
        region: SemanticRegion,
        block_lookup: Dict[
            str,
            LayoutBlockFeatures,
        ],
    ) -> List[LayoutBlockFeatures]:

        blocks = [
            block_lookup[block_id]
            for block_id in region.block_ids
            if block_id in block_lookup
        ]

        return sorted(
            blocks,
            key=lambda block: (
                block.y_center,
                block.x_center,
            ),
        )