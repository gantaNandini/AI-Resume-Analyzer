"""Plain-text parser for JD .txt files. Requirements: 4.2, 5.4"""
from __future__ import annotations
import re


def _normalize(text: str) -> str:
    text = re.sub(r"[^\x20-\x7E\n]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def extract_text_from_txt(file_bytes: bytes) -> str:
    text = file_bytes.decode("utf-8", errors="replace")
    return _normalize(text)
