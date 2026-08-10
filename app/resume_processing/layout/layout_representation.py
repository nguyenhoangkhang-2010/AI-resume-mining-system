from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class LayoutSpan:

    text: str
    bbox: Dict[str, float]

    font: Optional[str] = None
    size: Optional[float] = None
    flags: Optional[int] = None
    color: Optional[int] = None
    origin: Optional[Any] = None

    page_index: int = 0
    block_index: int = 0
    line_index: int = 0
    span_index: int = 0


@dataclass
class LayoutLine:

    text: str
    bbox: Dict[str, float]

    spans: List[LayoutSpan] = field(default_factory=list)

    page_index: int = 0
    block_index: int = 0
    line_index: int = 0


@dataclass
class LayoutBlock:

    type: str
    bbox: Dict[str, float]

    text: str = ""

    lines: List[LayoutLine] = field(default_factory=list)

    page_index: int = 0
    block_index: int = 0

    width: Optional[float] = None
    height: Optional[float] = None


@dataclass
class LayoutImage:

    bbox: Dict[str, float]

    page_index: int = 0
    block_index: int = 0

    width: Optional[float] = None
    height: Optional[float] = None
    ext: Optional[str] = None


@dataclass
class LayoutPage:

    page_index: int
    width: float
    height: float

    blocks: List[LayoutBlock] = field(default_factory=list)
    images: List[LayoutImage] = field(default_factory=list)

    text: str = ""


@dataclass
class LayoutDocument:

    pages: List[LayoutPage] = field(default_factory=list)

    text: str = ""

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def blocks(self) -> List[LayoutBlock]:

        result: List[LayoutBlock] = []

        for page in self.pages:
            result.extend(page.blocks)

        return result

    @property
    def text_blocks(self) -> List[LayoutBlock]:

        return [
            block
            for block in self.blocks
            if block.type == "text"
        ]

    @property
    def image_blocks(self) -> List[LayoutBlock]:

        return [
            block
            for block in self.blocks
            if block.type == "image"
        ]

    @classmethod
    def from_parser_result(
        cls,
        parsed: Dict[str, Any],
    ) -> "LayoutDocument":

        pages: List[LayoutPage] = []

        for raw_page in parsed.get(
            "pages",
            [],
        ):

            page_index = int(
                raw_page.get(
                    "page_index",
                    len(pages),
                )
            )

            page = LayoutPage(
                page_index=page_index,
                width=float(
                    raw_page.get(
                        "width",
                        0.0,
                    )
                ),
                height=float(
                    raw_page.get(
                        "height",
                        0.0,
                    )
                ),
                text=str(
                    raw_page.get(
                        "text",
                        "",
                    )
                ),
            )

            for raw_block in raw_page.get(
                "blocks",
                [],
            ):

                block_type = str(
                    raw_block.get(
                        "type",
                        "unknown",
                    )
                )

                bbox = dict(
                    raw_block.get(
                        "bbox",
                        {},
                    )
                )

                block = LayoutBlock(
                    type=block_type,
                    bbox=bbox,
                    text=str(
                        raw_block.get(
                            "text",
                            "",
                        )
                    ),
                    page_index=page_index,
                    block_index=int(
                        raw_block.get(
                            "block_index",
                            len(page.blocks),
                        )
                    ),
                    width=LayoutDocument._optional_float(
                        bbox.get("width")
                    ),
                    height=LayoutDocument._optional_float(
                        bbox.get("height")
                    ),
                )

                for raw_line in raw_block.get(
                    "lines",
                    [],
                ):

                    line_index = int(
                        raw_line.get(
                            "line_index",
                            len(block.lines),
                        )
                    )

                    line = LayoutLine(
                        text=str(
                            raw_line.get(
                                "text",
                                "",
                            )
                        ),
                        bbox=dict(
                            raw_line.get(
                                "bbox",
                                {},
                            )
                        ),
                        page_index=page_index,
                        block_index=block.block_index,
                        line_index=line_index,
                    )

                    for span_index, raw_span in enumerate(
                        raw_line.get(
                            "spans",
                            [],
                        )
                    ):

                        span = LayoutSpan(
                            text=str(
                                raw_span.get(
                                    "text",
                                    "",
                                )
                            ),
                            bbox=dict(
                                raw_span.get(
                                    "bbox",
                                    {},
                                )
                            ),
                            font=raw_span.get(
                                "font"
                            ),
                            size=LayoutDocument._optional_float(
                                raw_span.get(
                                    "size"
                                )
                            ),
                            flags=raw_span.get(
                                "flags"
                            ),
                            color=raw_span.get(
                                "color"
                            ),
                            origin=raw_span.get(
                                "origin"
                            ),
                            page_index=page_index,
                            block_index=block.block_index,
                            line_index=line_index,
                            span_index=span_index,
                        )

                        line.spans.append(
                            span
                        )

                    block.lines.append(
                        line
                    )

                page.blocks.append(
                    block
                )

            for raw_image in raw_page.get(
                "images",
                [],
            ):

                image_bbox = dict(
                    raw_image.get(
                        "bbox",
                        {},
                    )
                )

                image = LayoutImage(
                    bbox=image_bbox,
                    page_index=page_index,
                    block_index=int(
                        raw_image.get(
                            "block_index",
                            len(page.images),
                        )
                    ),
                    width=LayoutDocument._optional_float(
                        raw_image.get(
                            "width"
                        )
                    ),
                    height=LayoutDocument._optional_float(
                        raw_image.get(
                            "height"
                        )
                    ),
                    ext=raw_image.get(
                        "ext"
                    ),
                )

                page.images.append(
                    image
                )

            pages.append(
                page
            )

        return cls(
            pages=pages,
            text=str(
                parsed.get(
                    "text",
                    "",
                )
            ),
            metadata=dict(
                parsed.get(
                    "metadata",
                    {},
                )
            ),
        )

    @staticmethod
    def _optional_float(
        value: Any,
    ) -> Optional[float]:

        if value is None:
            return None

        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return None