from pathlib import Path
from typing import Any, Dict, List

import fitz
from loguru import logger


class PDFParser:

    @staticmethod
    def extract_text(
        file_path: str | Path,
        password: str | None = None,
    ) -> str:
        parsed = PDFParser.parse(
            file_path=file_path,
            password=password,
        )

        return parsed["text"]

    @staticmethod
    def parse(
        file_path: str | Path,
        password: str | None = None,
    ) -> Dict[str, Any]:

        path_obj = Path(file_path)

        if not path_obj.exists() or not path_obj.is_file():
            logger.error(
                f"PDF file not found at path: {file_path}"
            )
            raise FileNotFoundError(
                f"File not found: {file_path}"
            )

        logger.info(
            f"Parsing PDF with layout preservation: "
            f"{path_obj.name}"
        )

        try:
            with fitz.open(path_obj) as doc:

                if doc.is_encrypted:
                    logger.warning(
                        f"PDF '{path_obj.name}' is encrypted. "
                        "Attempting authentication."
                    )

                    authenticated = doc.authenticate(
                        password or ""
                    )

                    if not authenticated:
                        raise ValueError(
                            f"Failed to decrypt PDF "
                            f"'{path_obj.name}'. "
                            "Password may be incorrect."
                        )

                pages: List[Dict[str, Any]] = []

                all_text_parts: List[str] = []

                for page_index, page in enumerate(doc):

                    page_data = PDFParser._parse_page(
                        page=page,
                        page_index=page_index,
                    )

                    pages.append(page_data)

                    page_text = page_data["text"]

                    if page_text:
                        all_text_parts.append(
                            page_text
                        )

                full_text = "\n".join(
                    all_text_parts
                ).strip()

                result = {
                    "text": full_text,
                    "pages": pages,
                    "metadata": PDFParser._extract_metadata(
                        doc
                    ),
                }

                logger.info(
                    f"PDF parsed successfully: "
                    f"{len(pages)} pages, "
                    f"{len(full_text)} characters"
                )

                return result

        except ValueError:
            raise

        except Exception as exc:
            logger.exception(
                f"Error while parsing PDF "
                f"'{path_obj.name}': {exc}"
            )
            raise

    @staticmethod
    def _parse_page(
        page: fitz.Page,
        page_index: int,
    ) -> Dict[str, Any]:

        page_rect = page.rect

        raw_dict = page.get_text(
            "dict"
        )

        blocks: List[Dict[str, Any]] = []

        text_parts: List[str] = []

        images: List[Dict[str, Any]] = []

        for block_index, block in enumerate(
            raw_dict.get("blocks", [])
        ):

            block_type = block.get(
                "type"
            )

            bbox = PDFParser._normalize_bbox(
                block.get("bbox"),
                page_rect,
            )

            if block_type == 0:

                lines: List[Dict[str, Any]] = []

                block_text_parts: List[str] = []

                for line_index, line in enumerate(
                    block.get("lines", [])
                ):

                    spans: List[Dict[str, Any]] = []

                    line_text_parts: List[str] = []

                    line_bbox = PDFParser._normalize_bbox(
                        line.get("bbox"),
                        page_rect,
                    )

                    for span_index, span in enumerate(
                        line.get("spans", [])
                    ):

                        span_text = str(
                            span.get("text", "")
                        )

                        if not span_text:
                            continue

                        span_bbox = PDFParser._normalize_bbox(
                            span.get("bbox"),
                            page_rect,
                        )

                        span_data = {
                            "text": span_text,
                            "bbox": span_bbox,
                            "font": span.get(
                                "font"
                            ),
                            "size": span.get(
                                "size"
                            ),
                            "flags": span.get(
                                "flags"
                            ),
                            "color": span.get(
                                "color"
                            ),
                            "origin": span.get(
                                "origin"
                            ),
                        }

                        spans.append(
                            span_data
                        )

                        line_text_parts.append(
                            span_text
                        )

                    line_text = "".join(
                        line_text_parts
                    ).strip()

                    if not line_text:
                        continue

                    line_data = {
                        "text": line_text,
                        "bbox": line_bbox,
                        "spans": spans,
                        "line_index": line_index,
                    }

                    lines.append(
                        line_data
                    )

                    block_text_parts.append(
                        line_text
                    )

                    text_parts.append(
                        line_text
                    )

                if not lines:
                    continue

                block_text = "\n".join(
                    block_text_parts
                )

                blocks.append(
                    {
                        "type": "text",
                        "block_index": block_index,
                        "bbox": bbox,
                        "text": block_text,
                        "lines": lines,
                    }
                )

            elif block_type == 1:

                image_data = {
                    "type": "image",
                    "block_index": block_index,
                    "bbox": bbox,
                    "width": block.get(
                        "width"
                    ),
                    "height": block.get(
                        "height"
                    ),
                    "image": block.get(
                        "image"
                    ),
                    "ext": block.get(
                        "ext"
                    ),
                }

                images.append(
                    image_data
                )

                blocks.append(
                    {
                        "type": "image",
                        "block_index": block_index,
                        "bbox": bbox,
                    }
                )

        return {
            "page_index": page_index,
            "width": float(
                page_rect.width
            ),
            "height": float(
                page_rect.height
            ),
            "text": "\n".join(
                text_parts
            ),
            "blocks": blocks,
            "images": images,
        }

    @staticmethod
    def _normalize_bbox(
        bbox,
        page_rect,
    ) -> Dict[str, float]:

        if not bbox or len(bbox) != 4:
            return {
                "x0": 0.0,
                "y0": 0.0,
                "x1": 0.0,
                "y1": 0.0,
            }

        x0, y0, x1, y1 = bbox

        width = max(
            float(page_rect.width),
            1.0,
        )

        height = max(
            float(page_rect.height),
            1.0,
        )

        return {
            "x0": float(x0),
            "y0": float(y0),
            "x1": float(x1),
            "y1": float(y1),
            "width": max(
                0.0,
                float(x1 - x0),
            ),
            "height": max(
                0.0,
                float(y1 - y0),
            ),
            "x_center": float(
                (x0 + x1) / 2
            ),
            "y_center": float(
                (y0 + y1) / 2
            ),
            "x_ratio": float(
                x0 / width
            ),
            "y_ratio": float(
                y0 / height
            ),
            "x_center_ratio": float(
                ((x0 + x1) / 2) / width
            ),
            "y_center_ratio": float(
                ((y0 + y1) / 2) / height
            ),
        }

    @staticmethod
    def _extract_metadata(
        doc: fitz.Document,
    ) -> Dict[str, Any]:

        metadata = doc.metadata or {}

        return {
            "title": metadata.get(
                "title"
            ),
            "author": metadata.get(
                "author"
            ),
            "subject": metadata.get(
                "subject"
            ),
            "keywords": metadata.get(
                "keywords"
            ),
            "creator": metadata.get(
                "creator"
            ),
            "producer": metadata.get(
                "producer"
            ),
            "page_count": len(doc),
        }