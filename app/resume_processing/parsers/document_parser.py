"""Chooses the parser for a CV file by its type."""

from pathlib import Path
from typing import Any, Dict

from app.resume_processing.parsers.docx_parser import DocxParser, UnreadableFileError
from app.resume_processing.parsers.pdf_parser import PDFParser


class DocumentParser:
    """Same interface as PDFParser.parse; the result has the same shape for every type."""

    def parse(self, file_path: str | Path, password: str | None = None) -> Dict[str, Any]:
        suffix = Path(file_path).suffix.lower()

        if suffix == ".docx":
            return DocxParser.parse(file_path)

        if suffix == ".pdf":
            return PDFParser.parse(file_path, password=password)

        raise UnreadableFileError(f"Unsupported file type '{suffix}'.")
