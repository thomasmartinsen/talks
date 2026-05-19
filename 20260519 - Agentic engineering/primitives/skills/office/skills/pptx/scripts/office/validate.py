"""Validate Office Open XML content against XSD schemas and change-tracking rules.

Accepts either an unpacked directory or a packed ``.docx``/``.pptx``/``.xlsx``
file.  Packed files are transparently extracted to a temporary directory.

Supports optional auto-repair for common issues such as out-of-range hex IDs
and missing ``xml:space="preserve"`` attributes on ``<w:t>`` elements.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Sequence

from validators import DocumentValidator, PresentationValidator, TrackedChangesValidator

_OFFICE_SUFFIXES = frozenset((".docx", ".pptx", ".xlsx"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _suffix_from_content_types(directory: Path) -> str | None:
    """Infer the Office format by inspecting ``[Content_Types].xml``."""
    ct = directory / "[Content_Types].xml"
    if not ct.is_file():
        return None
    blob = ct.read_text(encoding="utf-8", errors="replace").lower()
    if "word/" in blob:
        return ".docx"
    if "ppt/" in blob:
        return ".pptx"
    if "xl/" in blob:
        return ".xlsx"
    return None


def _extract_archive(archive: Path) -> Path:
    """Unzip *archive* into a fresh temp directory and return its path."""
    dest = Path(tempfile.mkdtemp(prefix="validate_"))
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(dest)
    return dest


# ---------------------------------------------------------------------------
# Core validation logic
# ---------------------------------------------------------------------------

def run_validation(
    target: str,
    *,
    reference: str | None = None,
    auto_repair: bool = False,
    author: str = "Claude",
    verbose: bool = False,
) -> bool:
    """Validate the Office content at *target*.

    Parameters
    ----------
    target:
        Path to an unpacked directory **or** a packed Office file.
    reference:
        Optional path to the original Office file for delta comparison.
    auto_repair:
        If ``True``, attempt automatic fixes before checking.
    author:
        Author name passed to tracked-changes validation.
    verbose:
        Print per-validator PASS/FAIL details.

    Returns
    -------
    bool
        ``True`` when every validator passes.
    """
    path = Path(target)
    if not path.exists():
        print(f"Path not found: {target}", file=sys.stderr)
        return False

    staging: Path | None = None

    # Determine working directory and file extension.
    if path.is_file() and path.suffix.lower() in _OFFICE_SUFFIXES:
        ext = path.suffix.lower()
        staging = _extract_archive(path)
        work_dir = staging
    elif path.is_dir():
        work_dir = path
        ext = _suffix_from_content_types(work_dir)
        if ext is None and reference:
            ext = Path(reference).suffix.lower()
        if ext is None or ext not in _OFFICE_SUFFIXES:
            print(
                "Cannot determine Office format from directory contents.",
                file=sys.stderr,
            )
            return False
    else:
        print(f"Unsupported path: {target}", file=sys.stderr)
        return False

    ref = Path(reference) if reference else None

    try:
        checkers = _build_validators(work_dir, ref, ext, author, verbose)
        if not checkers:
            print(f"No validators available for '{ext}' files.", file=sys.stderr)
            return False

        if auto_repair:
            total_fixes = sum(v.repair() for v in checkers)
            if total_fixes:
                print(f"Repaired {total_fixes} issue(s)")

        ok = True
        for v in checkers:
            name = type(v).__name__
            if v.validate():
                if verbose:
                    print(f"  PASS  {name}")
            else:
                ok = False
                print(f"  FAIL  {name}", file=sys.stderr)

        if ok:
            print("All checks passed")
        return ok
    finally:
        if staging is not None:
            shutil.rmtree(staging, ignore_errors=True)


def _build_validators(work_dir, ref, ext, author, verbose):
    checkers = []
    if ext == ".docx":
        checkers.append(DocumentValidator(work_dir, ref, verbose=verbose))
        if ref is not None:
            checkers.append(
                TrackedChangesValidator(work_dir, ref, verbose=verbose, author=author),
            )
    elif ext == ".pptx":
        checkers.append(PresentationValidator(work_dir, ref, verbose=verbose))
    return checkers


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cli(argv: Sequence[str] | None = None) -> None:
    ap = argparse.ArgumentParser(
        description="Validate Office XML against schemas and tracked-change rules.",
    )
    ap.add_argument(
        "target",
        help="Unpacked directory or packed .docx/.pptx/.xlsx file",
    )
    ap.add_argument(
        "-r", "--reference",
        default=None,
        help="Original Office file for comparison-based checks",
    )
    ap.add_argument(
        "--repair",
        action="store_true",
        help="Auto-fix repairable issues before validating",
    )
    ap.add_argument(
        "--author",
        default="Claude",
        help="Author name for tracked-change checks (default: Claude)",
    )
    ap.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show per-validator pass/fail details",
    )
    opts = ap.parse_args(argv)

    passed = run_validation(
        opts.target,
        reference=opts.reference,
        auto_repair=opts.repair,
        author=opts.author,
        verbose=opts.verbose,
    )
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    cli()
