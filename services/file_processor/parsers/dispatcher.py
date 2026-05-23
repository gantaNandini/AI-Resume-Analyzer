"""
Unified document parser dispatcher.
Requirements: 5.1, 5.2, 5.3, 5.4
"""
from __future__ import annotations
from services.file_processor.parsers.pdf_parser import ImageOnlyPDFError, extract_text_from_pdf
from services.file_processor.parsers.docx_parser import extract_text_from_docx
from services.file_processor.parsers.txt_parser import extract_text_from_txt

MIME_PDF = "application/pdf"
MIME_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
MIME_TXT = "text/plain"


class UnsupportedFormatError(ValueError):
    """Raised when the MIME type is not supported."""


def parse_document(file_bytes: bytes, mime_type: str) -> str:
    """
    Route file bytes to the correct parser based on MIME type.
    Raises UnsupportedFormatError for unknown types.
    Raises ImageOnlyPDFError for scanned PDFs (caller should convert to HTTP 422).
    """
    if mime_type == MIME_PDF:
        return extract_text_from_pdf(file_bytes)
    elif mime_type == MIME_DOCX:
        return extract_text_from_docx(file_bytes)
    elif mime_type == MIME_TXT:
        return extract_text_from_txt(file_bytes)
    else:
        raise UnsupportedFormatError(f"Unsupported file format: {mime_type}")
