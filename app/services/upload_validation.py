from pathlib import Path
from typing import BinaryIO, Mapping

from app.resume_processing.parsers.docx_parser import archive_problem
from app.core.exceptions import (
    FileTooLargeError,
    InvalidUploadError,
    UnsupportedFileTypeError,
)

CHUNK_BYTES = 1024 * 1024

# The PDF header may be preceded by a few bytes of junk, but must appear
# within the first kilobyte.
PDF_HEADER_WINDOW = 1024

SIGNATURES: Mapping[str, bytes] = {
    ".pdf": b"%PDF-",
    ".docx": b"PK\x03\x04",
}


def validate_signature(extension: str, header: bytes) -> None:
    """
    Checks that the first bytes of the file match its extension, so a renamed
    or truncated file is rejected at upload instead of failing later in the
    background.
    """

    if not header:
        raise InvalidUploadError("The uploaded file is empty.")

    signature = SIGNATURES.get(extension)

    if signature is None:
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{extension}'."
        )

    if extension == ".pdf":
        matches = signature in header[:PDF_HEADER_WINDOW]
    else:
        matches = header.startswith(signature)

    if not matches:
        raise InvalidUploadError(
            f"The file content is not a valid {extension[1:].upper()} document."
        )


def save_upload(
    source: BinaryIO,
    destination: Path,
    extension: str,
    max_bytes: int,
) -> int:
    """
    Copies an upload to disk, enforcing the size limit while reading and
    checking the file signature on the first chunk. A partly written file is
    removed on any failure. Returns the number of bytes written.
    """

    written = 0

    try:
        with destination.open("wb") as target:
            while True:
                chunk = source.read(CHUNK_BYTES)

                if not chunk:
                    break

                if written == 0:
                    validate_signature(extension, chunk)

                written += len(chunk)

                if written > max_bytes:
                    raise FileTooLargeError(
                        f"The file is larger than {max_bytes // (1024 * 1024)} MB."
                    )

                target.write(chunk)

        if written == 0:
            raise InvalidUploadError("The uploaded file is empty.")

        if extension == ".docx":
            problem = archive_problem(destination)

            if problem:
                raise InvalidUploadError(problem)

    except BaseException:
        destination.unlink(missing_ok=True)
        raise

    return written
