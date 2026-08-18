from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict

from loguru import logger

from app.resume_processing.parsers.pdf_parser import PDFParser
from app.resume_processing.cleaners.text_cleaner import TextCleaner
from app.resume_processing.layout.layout_representation import LayoutDocument
from app.resume_processing.layout.layout_analyzer import LayoutAnalyzer
from app.resume_processing.layout.semantic_region_analyzer import (
    SemanticRegionAnalyzer,
)
from app.extraction.section.section_detector import SectionDetector
from app.extraction.extraction_engine import ExtractionEngine


class ResumePipeline:

    def __init__(
        self,
        section_detector: SectionDetector,
        extraction_engine: ExtractionEngine,
    ) -> None:

        self.parser = PDFParser()
        self.cleaner = TextCleaner()
        self.section_detector = section_detector
        self.extraction_engine = extraction_engine
        self.layout_analyzer = LayoutAnalyzer()
        self.region_analyzer = SemanticRegionAnalyzer()

    def process_pdf(
        self,
        file_path: str | Path,
    ) -> Dict[str, Any]:

        logger.info(
            "=================================================="
        )
        logger.info(
            "START RESUME PIPELINE"
        )
        logger.info(
            "File: {}",
            file_path,
        )
        logger.info(
            "=================================================="
        )

        pipeline_start = time.perf_counter()

        stage_times: Dict[str, float] = {}

        try:

            # ==================================================
            # 1. PDF PARSING
            # ==================================================

            start = time.perf_counter()

            parsed = self.parser.parse(
                file_path
            )

            raw_text = parsed["text"]

            elapsed = time.perf_counter() - start

            stage_times["pdf_parsing"] = elapsed

            logger.info(
                "[TIMING] PDF parsing: {:.3f}s",
                elapsed,
            )

            # ==================================================
            # 2. TEXT CLEANING
            # ==================================================

            start = time.perf_counter()

            cleaned_text = self.cleaner.clean(
                raw_text
            )

            elapsed = time.perf_counter() - start

            stage_times["text_cleaning"] = elapsed

            logger.info(
                "[TIMING] Text cleaning: {:.3f}s",
                elapsed,
            )

            # ==================================================
            # 3. LAYOUT + REGION ANALYSIS
            # ==================================================

            start = time.perf_counter()

            layout_document = (
                LayoutDocument.from_parser_result(
                    parsed
                )
            )

            layout_analysis = (
                self.layout_analyzer.analyze(
                    layout_document
                )
            )

            region_analysis = (
                self.region_analyzer.analyze(
                    layout_analysis
                )
            )

            elapsed = time.perf_counter() - start

            stage_times[
                "layout_region_analysis"
            ] = elapsed

            logger.info(
                "[TIMING] Layout + region analysis: {:.3f}s "
                "({} regions)",
                elapsed,
                len(
                    region_analysis.regions
                ),
            )

            # ==================================================
            # 4. SECTION DETECTION
            # ==================================================

            start = time.perf_counter()

            sections = (
                self.section_detector.detect(
                    layout_analysis=layout_analysis,
                    region_analysis=region_analysis,
                    cleaned_text=cleaned_text,
                )
            )

            elapsed = time.perf_counter() - start

            stage_times[
                "section_detection"
            ] = elapsed

            logger.info(
                "[TIMING] Section detection: {:.3f}s",
                elapsed,
            )

            logger.info(
                "Detected sections: {}",
                [
                    key
                    for key in sections.keys()
                    if not key.startswith("__")
                ],
            )

            # ==================================================
            # 5. EXTRACTION ENGINE
            # ==================================================

            start = time.perf_counter()

            extracted_data = (
                self.extraction_engine.extract_resume(
                    sections
                )
            )

            elapsed = time.perf_counter() - start

            stage_times[
                "extraction_engine"
            ] = elapsed

            logger.info(
                "[TIMING] Extraction engine: {:.3f}s",
                elapsed,
            )

            # ==================================================
            # 6. BUILD RESULT
            # ==================================================

            resume_data = {
                "raw_text": raw_text,
                "cleaned_text": cleaned_text,
                **extracted_data,
            }

            # ==================================================
            # 7. TOTAL TIME
            # ==================================================

            total_time = (
                time.perf_counter()
                - pipeline_start
            )

            stage_times["total"] = total_time

            self._log_timing_summary(
                stage_times
            )

            logger.success(
                "Resume pipeline completed successfully "
                "in {:.3f}s",
                total_time,
            )

            return resume_data

        except Exception as exc:

            total_time = (
                time.perf_counter()
                - pipeline_start
            )

            logger.exception(
                "Resume pipeline failed after {:.3f}s: {}",
                total_time,
                exc,
            )

            raise

    @staticmethod
    def _log_timing_summary(
        stage_times: Dict[str, float],
    ) -> None:

        total = stage_times.get(
            "total",
            0.0,
        )

        logger.info(
            "=================================================="
        )
        logger.info(
            "RESUME PIPELINE TIMING SUMMARY"
        )
        logger.info(
            "=================================================="
        )

        ordered_stages = [
            "pdf_parsing",
            "text_cleaning",
            "layout_region_analysis",
            "section_detection",
            "extraction_engine",
        ]

        for stage in ordered_stages:

            elapsed = stage_times.get(
                stage,
                0.0,
            )

            percentage = (
                elapsed / total * 100.0
                if total > 0
                else 0.0
            )

            logger.info(
                "{:<28} {:>10.3f}s  ({:>6.2f}%)",
                stage,
                elapsed,
                percentage,
            )

        logger.info(
            "{:<28} {:>10.3f}s",
            "TOTAL",
            total,
        )

        logger.info(
            "=================================================="
        )