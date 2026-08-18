from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from app.resume_processing.layout.layout_representation import (
    LayoutBlock,
    LayoutDocument,
)


@dataclass
class LayoutBlockFeatures:
    block_id: str

    page_index: int
    block_index: int

    block_type: str
    text: str

    bbox: Dict[str, float]

    width: float
    height: float

    x0: float
    y0: float
    x1: float
    y1: float

    x_center: float
    y_center: float

    x_center_ratio: float
    y_center_ratio: float

    width_ratio: float
    height_ratio: float

    area_ratio: float

    line_count: int
    span_count: int

    font_sizes: List[float] = field(default_factory=list)
    font_names: List[str] = field(default_factory=list)

    font_size_min: float = 0.0
    font_size_max: float = 0.0
    font_size_mean: float = 0.0
    font_size_std: float = 0.0

    left_alignment: float = 0.0
    center_alignment: float = 0.0
    right_alignment: float = 0.0

    is_single_line: bool = False
    is_short_text: bool = False
    is_long_text: bool = False

    lines: List[Dict[str, Any]] = field(default_factory=list)

    nearby_block_ids: List[str] = field(
        default_factory=list
    )

    previous_block_id: Optional[str] = None
    next_block_id: Optional[str] = None

    above_block_ids: List[str] = field(
        default_factory=list
    )

    below_block_ids: List[str] = field(
        default_factory=list
    )

    left_block_ids: List[str] = field(
        default_factory=list
    )

    right_block_ids: List[str] = field(
        default_factory=list
    )


@dataclass
class LayoutImageFeatures:
    image_id: str

    page_index: int
    block_index: int

    bbox: Dict[str, float]

    width: float
    height: float

    x0: float
    y0: float
    x1: float
    y1: float

    x_center: float
    y_center: float

    x_center_ratio: float
    y_center_ratio: float

    width_ratio: float
    height_ratio: float

    area_ratio: float

    aspect_ratio: float

    nearby_block_ids: List[str] = field(
        default_factory=list
    )


@dataclass
class LayoutPageFeatures:
    page_index: int

    width: float
    height: float

    blocks: List[LayoutBlockFeatures] = field(
        default_factory=list
    )

    images: List[LayoutImageFeatures] = field(
        default_factory=list
    )

    image_count: int = 0


@dataclass
class LayoutAnalysis:
    pages: List[LayoutPageFeatures] = field(
        default_factory=list
    )

    block_count: int = 0

    image_count: int = 0

    page_count: int = 0

    document_text: str = ""

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


class LayoutAnalyzer:

    MAX_NEIGHBORS = 8

    def analyze(
        self,
        document: LayoutDocument,
    ) -> LayoutAnalysis:

        pages: List[LayoutPageFeatures] = []

        total_images = 0
        total_blocks = 0

        for page in document.pages:

            page_blocks = [
                self._build_block_features(
                    block=block,
                    page_width=page.width,
                    page_height=page.height,
                )
                for block in page.blocks
                if block.type == "text"
            ]

            page_images = [
                self._build_image_features(
                    image=image,
                    page_width=page.width,
                    page_height=page.height,
                )
                for image in page.images
            ]

            self._attach_spatial_relationships(
                page_blocks
            )

            self._attach_image_relationships(
                page_blocks=page_blocks,
                page_images=page_images,
            )

            page_features = LayoutPageFeatures(
                page_index=page.page_index,
                width=page.width,
                height=page.height,
                blocks=page_blocks,
                images=page_images,
                image_count=len(page_images),
            )

            pages.append(page_features)

            total_blocks += len(page_blocks)
            total_images += len(page_images)

        return LayoutAnalysis(
            pages=pages,
            block_count=total_blocks,
            image_count=total_images,
            page_count=len(pages),
            document_text=document.text,
            metadata=document.metadata,
        )

    def _build_block_features(
        self,
        block: LayoutBlock,
        page_width: float,
        page_height: float,
    ) -> LayoutBlockFeatures:

        font_sizes: List[float] = []
        font_names: List[str] = []

        lines: List[Dict[str, Any]] = []

        span_count = 0

        for line in block.lines:

            line_data = {
                "text": line.text,
                "bbox": dict(line.bbox),
                "line_index": line.line_index,
                "spans": [],
            }

            for span in line.spans:

                span_count += 1

                if span.size is not None:
                    font_sizes.append(
                        float(span.size)
                    )

                if span.font:
                    font_names.append(
                        str(span.font)
                    )

                line_data["spans"].append(
                    {
                        "text": span.text,
                        "bbox": dict(span.bbox),
                        "font": span.font,
                        "size": span.size,
                        "flags": span.flags,
                        "color": span.color,
                    }
                )

            lines.append(line_data)

        bbox = dict(block.bbox)

        x0 = self._float(
            bbox.get("x0")
        )

        y0 = self._float(
            bbox.get("y0")
        )

        x1 = self._float(
            bbox.get("x1")
        )

        y1 = self._float(
            bbox.get("y1")
        )

        width = self._float(
            bbox.get("width")
        )

        height = self._float(
            bbox.get("height")
        )

        if width <= 0:
            width = max(
                0.0,
                x1 - x0,
            )

        if height <= 0:
            height = max(
                0.0,
                y1 - y0,
            )

        x_center = self._float(
            bbox.get("x_center")
        )

        y_center = self._float(
            bbox.get("y_center")
        )

        if x_center == 0.0 and (
            x0 != 0.0 or x1 != 0.0
        ):
            x_center = (
                x0 + x1
            ) / 2.0

        if y_center == 0.0 and (
            y0 != 0.0 or y1 != 0.0
        ):
            y_center = (
                y0 + y1
            ) / 2.0

        x_center_ratio = self._ratio(
            x_center,
            page_width,
        )

        y_center_ratio = self._ratio(
            y_center,
            page_height,
        )

        width_ratio = self._ratio(
            width,
            page_width,
        )

        height_ratio = self._ratio(
            height,
            page_height,
        )

        area_ratio = self._ratio(
            width * height,
            page_width * page_height,
        )

        (
            font_size_min,
            font_size_max,
            font_size_mean,
            font_size_std,
        ) = self._font_statistics(
            font_sizes
        )

        (
            left_alignment,
            center_alignment,
            right_alignment,
        ) = self._alignment_features(
            x0=x0,
            x1=x1,
            x_center=x_center,
            page_width=page_width,
        )

        text = block.text.strip()

        return LayoutBlockFeatures(
            block_id=(
                f"page_{block.page_index}"
                f"_block_{block.block_index}"
            ),
            page_index=block.page_index,
            block_index=block.block_index,
            block_type=block.type,
            text=block.text,
            bbox=bbox,
            width=width,
            height=height,
            x0=x0,
            y0=y0,
            x1=x1,
            y1=y1,
            x_center=x_center,
            y_center=y_center,
            x_center_ratio=x_center_ratio,
            y_center_ratio=y_center_ratio,
            width_ratio=width_ratio,
            height_ratio=height_ratio,
            area_ratio=area_ratio,
            line_count=len(block.lines),
            span_count=span_count,
            font_sizes=font_sizes,
            font_names=font_names,
            font_size_min=font_size_min,
            font_size_max=font_size_max,
            font_size_mean=font_size_mean,
            font_size_std=font_size_std,
            left_alignment=left_alignment,
            center_alignment=center_alignment,
            right_alignment=right_alignment,
            is_single_line=len(block.lines) == 1,
            is_short_text=len(text) <= 40,
            is_long_text=len(text) >= 250,
            lines=lines,
        )

    def _build_image_features(
        self,
        image: Any,
        page_width: float,
        page_height: float,
    ) -> LayoutImageFeatures:

        bbox = dict(image.bbox)

        x0 = self._float(
            bbox.get("x0")
        )

        y0 = self._float(
            bbox.get("y0")
        )

        x1 = self._float(
            bbox.get("x1")
        )

        y1 = self._float(
            bbox.get("y1")
        )

        width = self._float(
            image.width
        )

        height = self._float(
            image.height
        )

        if width <= 0:
            width = max(
                0.0,
                x1 - x0,
            )

        if height <= 0:
            height = max(
                0.0,
                y1 - y0,
            )

        x_center = (
            x0 + x1
        ) / 2.0

        y_center = (
            y0 + y1
        ) / 2.0

        aspect_ratio = (
            width / height
            if height > 0
            else 0.0
        )

        return LayoutImageFeatures(
            image_id=(
                f"page_{image.page_index}"
                f"_image_{image.block_index}"
            ),
            page_index=image.page_index,
            block_index=image.block_index,
            bbox=bbox,
            width=width,
            height=height,
            x0=x0,
            y0=y0,
            x1=x1,
            y1=y1,
            x_center=x_center,
            y_center=y_center,
            x_center_ratio=self._ratio(
                x_center,
                page_width,
            ),
            y_center_ratio=self._ratio(
                y_center,
                page_height,
            ),
            width_ratio=self._ratio(
                width,
                page_width,
            ),
            height_ratio=self._ratio(
                height,
                page_height,
            ),
            area_ratio=self._ratio(
                width * height,
                page_width * page_height,
            ),
            aspect_ratio=aspect_ratio,
        )

    def _attach_spatial_relationships(
        self,
        blocks: List[LayoutBlockFeatures],
    ) -> None:

        ordered = sorted(
            blocks,
            key=lambda block: (
                block.y0,
                block.x0,
            ),
        )

        for index, block in enumerate(ordered):

            if index > 0:
                block.previous_block_id = (
                    ordered[index - 1].block_id
                )

            if index + 1 < len(ordered):
                block.next_block_id = (
                    ordered[index + 1].block_id
                )

        for block in blocks:

            candidates: List[
                Tuple[float, str]
            ] = []

            above: List[
                Tuple[float, str]
            ] = []

            below: List[
                Tuple[float, str]
            ] = []

            left: List[
                Tuple[float, str]
            ] = []

            right: List[
                Tuple[float, str]
            ] = []

            for other in blocks:

                if block is other:
                    continue

                distance = (
                    self._spatial_distance(
                        block,
                        other,
                    )
                )

                candidates.append(
                    (
                        distance,
                        other.block_id,
                    )
                )

                vertical_gap = (
                    other.y0 - block.y1
                )

                reverse_vertical_gap = (
                    block.y0 - other.y1
                )

                horizontal_gap = (
                    other.x0 - block.x1
                )

                reverse_horizontal_gap = (
                    block.x0 - other.x1
                )

                overlap_x = (
                    min(
                        block.x1,
                        other.x1,
                    )
                    - max(
                        block.x0,
                        other.x0,
                    )
                )

                overlap_y = (
                    min(
                        block.y1,
                        other.y1,
                    )
                    - max(
                        block.y0,
                        other.y0,
                    )
                )

                if (
                    vertical_gap >= 0
                    and overlap_x > 0
                ):
                    above.append(
                        (
                            vertical_gap,
                            other.block_id,
                        )
                    )

                if (
                    reverse_vertical_gap >= 0
                    and overlap_x > 0
                ):
                    below.append(
                        (
                            reverse_vertical_gap,
                            other.block_id,
                        )
                    )

                if (
                    horizontal_gap >= 0
                    and overlap_y > 0
                ):
                    right.append(
                        (
                            horizontal_gap,
                            other.block_id,
                        )
                    )

                if (
                    reverse_horizontal_gap >= 0
                    and overlap_y > 0
                ):
                    left.append(
                        (
                            reverse_horizontal_gap,
                            other.block_id,
                        )
                    )

            candidates.sort(
                key=lambda item: item[0]
            )

            above.sort(
                key=lambda item: item[0]
            )

            below.sort(
                key=lambda item: item[0]
            )

            left.sort(
                key=lambda item: item[0]
            )

            right.sort(
                key=lambda item: item[0]
            )

            block.nearby_block_ids = [
                block_id
                for _, block_id
                in candidates[
                    : self.MAX_NEIGHBORS
                ]
            ]

            block.above_block_ids = [
                block_id
                for _, block_id
                in above[
                    : self.MAX_NEIGHBORS
                ]
            ]

            block.below_block_ids = [
                block_id
                for _, block_id
                in below[
                    : self.MAX_NEIGHBORS
                ]
            ]

            block.left_block_ids = [
                block_id
                for _, block_id
                in left[
                    : self.MAX_NEIGHBORS
                ]
            ]

            block.right_block_ids = [
                block_id
                for _, block_id
                in right[
                    : self.MAX_NEIGHBORS
                ]
            ]

    def _attach_image_relationships(
        self,
        page_blocks: List[LayoutBlockFeatures],
        page_images: List[LayoutImageFeatures],
    ) -> None:

        for image in page_images:

            candidates: List[
                Tuple[float, str]
            ] = []

            for block in page_blocks:

                distance = self._point_to_box_distance(
                    image.x_center,
                    image.y_center,
                    block,
                )

                candidates.append(
                    (
                        distance,
                        block.block_id,
                    )
                )

            candidates.sort(
                key=lambda item: item[0]
            )

            image.nearby_block_ids = [
                block_id
                for _, block_id
                in candidates[
                    : self.MAX_NEIGHBORS
                ]
            ]

    @staticmethod
    def _point_to_box_distance(
        x: float,
        y: float,
        block: LayoutBlockFeatures,
    ) -> float:

        dx = max(
            block.x0 - x,
            0.0,
            x - block.x1,
        )

        dy = max(
            block.y0 - y,
            0.0,
            y - block.y1,
        )

        return (
            dx * dx
            + dy * dy
        ) ** 0.5

    @staticmethod
    def _spatial_distance(
        first: LayoutBlockFeatures,
        second: LayoutBlockFeatures,
    ) -> float:

        dx = (
            first.x_center
            - second.x_center
        )

        dy = (
            first.y_center
            - second.y_center
        )

        return (
            dx * dx
            + dy * dy
        ) ** 0.5

    @staticmethod
    def _alignment_features(
        x0: float,
        x1: float,
        x_center: float,
        page_width: float,
    ) -> Tuple[float, float, float]:

        if page_width <= 0:
            return 0.0, 0.0, 0.0

        left_alignment = 1.0 - min(
            abs(x0) / page_width,
            1.0,
        )

        center_alignment = 1.0 - min(
            abs(
                x_center
                - page_width / 2.0
            )
            / (page_width / 2.0),
            1.0,
        )

        right_alignment = 1.0 - min(
            abs(
                page_width - x1
            )
            / page_width,
            1.0,
        )

        return (
            left_alignment,
            center_alignment,
            right_alignment,
        )

    @staticmethod
    def _font_statistics(
        values: List[float],
    ) -> Tuple[
        float,
        float,
        float,
        float,
    ]:

        if not values:
            return 0.0, 0.0, 0.0, 0.0

        minimum = min(values)
        maximum = max(values)

        mean = sum(values) / len(values)

        variance = (
            sum(
                (value - mean) ** 2
                for value in values
            )
            / len(values)
        )

        return (
            minimum,
            maximum,
            mean,
            variance ** 0.5,
        )

    @staticmethod
    def _ratio(
        numerator: float,
        denominator: float,
    ) -> float:

        if denominator <= 0:
            return 0.0

        return numerator / denominator

    @staticmethod
    def _float(
        value: Optional[Any],
    ) -> float:

        if value is None:
            return 0.0

        try:
            return float(value)

        except (
            TypeError,
            ValueError,
        ):
            return 0.0