"""
generic_formatter.py
----------------------
Fallback formatter used when a document cannot be confidently
classified as a lab report, prescription, or pharmacy bill. Also
exposes `clean_text`, the shared text-cleaning step used by the
`formatter.py` router before document-type detection.

This module only improves *readability* — it never invents, drops, or
reorders real content. It:
    - Removes pure OCR noise lines (border/underline artifacts).
    - Collapses redundant blank lines.
    - Adds visual separation around heading-like lines.
    - Normalizes internal whitespace.
"""

import re
from typing import List

# Lines that consist entirely of border/decoration characters (common
# OCR artifacts from scanned table lines, underlines, etc.). These carry
# no information and are safe to drop.
_NOISE_LINE_RE = re.compile(r"^[\-_=|.\s]{1,}$")

# A short, all-caps line with no digits looks like a section heading
# (e.g. "LABORATORY REPORT", "DISCHARGE SUMMARY") — a shape check, not
# a keyword check.
_HEADING_RE = re.compile(r"^[A-Z][A-Z\s\-&/]{2,40}$")

_HEADING_SEPARATOR = "=" * 60


def _clean_line(line: str) -> str:
    """
    Normalize a single line WITHOUT collapsing multi-space runs.

    Runs of 2+ spaces are a meaningful column-boundary signal used by
    downstream formatters (e.g. pharmacy_formatter's column splitting),
    so this shared cleaning step only normalizes tabs and trims
    leading/trailing whitespace rather than collapsing all internal
    whitespace to single spaces.
    """
    return line.replace("\t", "  ").strip()


def _is_noise_line(line: str) -> bool:
    """Return True if a line contains only border/decoration characters."""
    return bool(line.strip()) and bool(_NOISE_LINE_RE.match(line))


def _is_heading_line(line: str) -> bool:
    """Return True if a line looks like a short, all-caps section heading."""
    return bool(_HEADING_RE.match(line)) and len(line.split()) <= 6


def _collapse_blank_lines(lines: List[str]) -> List[str]:
    """Collapse runs of 2+ consecutive blank lines into a single blank line."""
    result: List[str] = []
    previous_blank = False

    for line in lines:
        blank = not line.strip()
        if blank and previous_blank:
            continue
        result.append(line)
        previous_blank = blank

    while result and not result[0].strip():
        result.pop(0)
    while result and not result[-1].strip():
        result.pop()

    return result


def clean_text(raw_text: str) -> str:
    """
    Shared, content-preserving text-cleaning step used both by this
    formatter and by `formatter.py` before document-type detection.

    Steps:
        1. Normalize whitespace on every line.
        2. Drop pure-noise/border lines.
        3. Collapse multiple blank lines into single separators.

    Args:
        raw_text: Raw OCR text.

    Returns:
        Cleaned text with the same real content, better spacing.
    """
    if not raw_text:
        return ""

    lines = [_clean_line(line) for line in raw_text.splitlines()]
    lines = [line for line in lines if not _is_noise_line(line)]
    lines = _collapse_blank_lines(lines)

    return "\n".join(lines)


def format_generic(text: str) -> str:
    """
    Fallback formatter: improve readability of text that couldn't be
    classified into a known document type.

    In addition to the base cleaning in `clean_text`, this adds visual
    separators around heading-like lines so the document is easier to
    scan, without altering or reordering any real content.

    Args:
        text: Raw (or already cleaned) OCR text.

    Returns:
        A readability-improved version of the text.
    """
    cleaned = clean_text(text)
    if not cleaned:
        return "No text could be extracted from this document."

    output_lines: List[str] = []
    for line in cleaned.splitlines():
        if _is_heading_line(line):
            if output_lines and output_lines[-1] != "":
                output_lines.append("")
            output_lines.append(_HEADING_SEPARATOR)
            output_lines.append(line)
            output_lines.append(_HEADING_SEPARATOR)
            output_lines.append("")
        else:
            output_lines.append(line)

    return "\n".join(output_lines).strip()