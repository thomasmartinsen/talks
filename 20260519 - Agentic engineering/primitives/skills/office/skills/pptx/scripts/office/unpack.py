"""Extract and prepare Office Open XML archives for human-readable editing.

Handles DOCX, PPTX, and XLSX files by unzipping the archive, indenting
the raw XML for readability, and converting typographic (curly) quote
characters to their XML entity equivalents so round-tripping is safe.

For DOCX inputs the extraction can optionally consolidate adjacent runs
that share formatting and collapse consecutive tracked-change spans by
the same author.
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

import defusedxml.minidom

# Unicode curly/smart quotes mapped to XML numeric character references.
CURLY_QUOTE_MAP: dict[str, str] = {
    "\u201c": "&#x201C;",  # left double
    "\u201d": "&#x201D;",  # right double
    "\u2018": "&#x2018;",  # left single
    "\u2019": "&#x2019;",  # right single
}

_SUPPORTED_SUFFIXES = frozenset((".docx", ".pptx", ".xlsx"))


@dataclass
class ExtractionResult:
    """Outcome of an Office file extraction."""

    ok: bool
    message: str
    xml_count: int = 0
    merged_runs: int = 0
    simplified_changes: int = 0
    warnings: list[str] = field(default_factory=list)


def format_xml(path: Path) -> bool:
    """Re-indent *path* in place using minidom pretty-printing.

    Returns True on success, False if the file could not be parsed.
    """
    try:
        raw = path.read_text(encoding="utf-8")
        doc = defusedxml.minidom.parseString(raw)
        path.write_bytes(doc.toprettyxml(indent="  ", encoding="utf-8"))
        return True
    except Exception:
        return False


def encode_smart_quotes(path: Path) -> None:
    """Replace typographic quote codepoints with XML entity references."""
    content = path.read_text(encoding="utf-8")
    for codepoint, entity in CURLY_QUOTE_MAP.items():
        content = content.replace(codepoint, entity)
    path.write_text(content, encoding="utf-8")


def _collect_markup_files(root: Path) -> list[Path]:
    """Return all XML and .rels files under *root*."""
    return sorted(
        p for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in (".xml", ".rels")
    )


def extract_office_file(
    src: str,
    dest: str,
    *,
    merge_runs: bool = True,
    simplify_redlines: bool = True,
) -> ExtractionResult:
    """Unzip an Office document and prepare the XML for editing.

    Parameters
    ----------
    src:
        Path to the ``.docx``, ``.pptx``, or ``.xlsx`` file.
    dest:
        Target directory (created if missing).
    merge_runs:
        Consolidate adjacent DOCX runs with identical formatting.
    simplify_redlines:
        Collapse adjacent tracked changes by the same author (DOCX).

    Returns
    -------
    ExtractionResult
        A dataclass describing what happened.
    """
    src_path = Path(src)
    if not src_path.is_file():
        return ExtractionResult(ok=False, message=f"Source file not found: {src}")

    suffix = src_path.suffix.lower()
    if suffix not in _SUPPORTED_SUFFIXES:
        return ExtractionResult(
            ok=False,
            message=f"Unsupported format '{suffix}'; expected one of {sorted(_SUPPORTED_SUFFIXES)}",
        )

    dest_path = Path(dest)
    try:
        dest_path.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(src_path) as archive:
            archive.extractall(dest_path)
    except zipfile.BadZipFile:
        return ExtractionResult(ok=False, message=f"Not a valid ZIP/Office file: {src}")

    markup_files = _collect_markup_files(dest_path)
    for mf in markup_files:
        format_xml(mf)

    result = ExtractionResult(ok=True, message="", xml_count=len(markup_files))

    if suffix == ".docx":
        if simplify_redlines:
            try:
                from helpers.simplify_redlines import compact_tracked_changes
                compact_tracked_changes(str(dest_path))
            except ImportError:
                result.warnings.append("simplify_redlines helper not available")

        if merge_runs:
            try:
                from helpers.merge_runs import consolidate_runs
                consolidate_runs(str(dest_path))
            except ImportError:
                result.warnings.append("merge_runs helper not available")

    for mf in markup_files:
        encode_smart_quotes(mf)

    parts = [f"Extracted {src} -> {dest} ({result.xml_count} XML files)"]
    if result.warnings:
        parts.extend(f"  warning: {w}" for w in result.warnings)
    result.message = "\n".join(parts)
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _bool_flag(raw: str) -> bool:
    return raw.strip().lower() in ("true", "1", "yes")


def cli(argv: Sequence[str] | None = None) -> None:
    ap = argparse.ArgumentParser(
        description="Extract an Office Open XML file for editing.",
    )
    ap.add_argument("source", help="Office file to extract (.docx/.pptx/.xlsx)")
    ap.add_argument("destination", help="Directory to write extracted content to")
    ap.add_argument(
        "--merge-runs",
        type=_bool_flag,
        default=True,
        metavar="BOOL",
        help="Consolidate adjacent DOCX runs (default: true)",
    )
    ap.add_argument(
        "--simplify-redlines",
        type=_bool_flag,
        default=True,
        metavar="BOOL",
        help="Collapse consecutive tracked changes by the same author (default: true)",
    )
    opts = ap.parse_args(argv)

    outcome = extract_office_file(
        opts.source,
        opts.destination,
        merge_runs=opts.merge_runs,
        simplify_redlines=opts.simplify_redlines,
    )
    print(outcome.message)
    if not outcome.ok:
        sys.exit(1)


if __name__ == "__main__":
    cli()
