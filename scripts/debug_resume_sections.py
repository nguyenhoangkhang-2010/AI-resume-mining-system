from pathlib import Path
import sys

from app.resume_processing.parsers.pdf_parser import PDFParser
from app.resume_processing.cleaners.text_cleaner import TextCleaner
from app.extraction.section.section_detector import SectionDetector
from app.extraction.extraction_engine import ExtractionEngine
from app.core.config.settings import settings


def main() -> None:
    if len(sys.argv) != 2:
        print(
            "Usage: python scripts/debug_resume_sections.py <resume.pdf>"
        )
        raise SystemExit(1)

    pdf_path = Path(sys.argv[1])

    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}")
        raise SystemExit(1)

    print("=" * 80)
    print("CONFIGURATION")
    print("=" * 80)
    print(f"LLM_MODEL_NAME: {settings.LLM_MODEL_NAME}")
    print(f"MAX_NEW_TOKENS: {settings.MAX_NEW_TOKENS}")

    print("\n" + "=" * 80)
    print("1. PDF PARSING")
    print("=" * 80)

    parser = PDFParser()
    raw_text = parser.extract_text(pdf_path)

    print(raw_text)

    print("\n" + "=" * 80)
    print("2. CLEANED TEXT")
    print("=" * 80)

    cleaner = TextCleaner()
    cleaned_text = cleaner.clean(raw_text)

    print(cleaned_text)

    print("\n" + "=" * 80)
    print("3. SECTION DETECTION")
    print("=" * 80)

    detector = SectionDetector()
    sections = detector.detect(cleaned_text)

    print("\nDetected sections:")
    print("-" * 80)

    for section_name, section_lines in sections.items():
        print(f"\n[{section_name}]")
        for line in section_lines:
            print(f"  {line}")

    print("\n" + "=" * 80)
    print("4. EXTRACTION ENGINE INPUT")
    print("=" * 80)

    section_texts = {
        key: "\n".join(value)
        for key, value in sections.items()
    }

    full_text = "\n".join(section_texts.values())

    print("\nSection texts passed to extractors:")

    for section_name, text in section_texts.items():
        print("\n" + "-" * 80)
        print(f"EXTRACTOR INPUT: {section_name}")
        print("-" * 80)
        print(text)

    print("\n" + "=" * 80)
    print("5. ACTUAL EXTRACTION ENGINE")
    print("=" * 80)

    extraction_engine = ExtractionEngine()
    extracted_data = extraction_engine.extract_resume(sections)

    print("\nExtracted data:")

    for key, value in extracted_data.items():
        print("\n" + "-" * 80)
        print(key)
        print("-" * 80)
        print(value)


if __name__ == "__main__":
    main()