"""
PDF text extraction using PyMuPDF.
Requirements: 5.1, 5.3, 5.4
"""
from __future__ import annotations
import re
import fitz  # PyMuPDF


class ImageOnlyPDFError(ValueError):
    """Raised when a PDF contains no extractable text layer."""


def _normalize(text: str) -> str:
    text = re.sub(r"[^\x20-\x7E\n]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract all readable text from a PDF file.
    Raises ImageOnlyPDFError if the PDF has no text layer.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages_text: list[str] = []
    for page in doc:
        blocks = page.get_text("blocks")  # type: ignore[attr-defined]
        page_lines = [b[4] for b in blocks if isinstance(b[4], str)]
        pages_text.append("\n".join(page_lines))
    doc.close()

    full_text = "\n\n".join(pages_text)
    if len(full_text.strip()) < 50:
        raise ImageOnlyPDFError(
            "This PDF appears to be image-only and contains no extractable text. "
            "Please upload a text-based PDF."
        )
    return _normalize(full_text)
