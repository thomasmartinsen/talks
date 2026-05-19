"""Reassemble an edited Office Open XML directory into a distributable file.

Takes an unpacked directory tree (as produced by ``unpack.py`` /
``extract_office_file``), optionally validates and auto-repairs the XML,
minifies whitespace, and writes a conformant ``.docx``, ``.pptx``, or
``.xlsx`` ZIP archive.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Sequence

from lxml import etree

from validators import DocumentValidator, PresentationValidator, TrackedChangesValidator

_SUPPORTED_SUFFIXES = frozenset((".docx", ".pptx", ".xlsx"))


# ---------------------------------------------------------------------------
# XML minification
# ---------------------------------------------------------------------------

def compact_xml(path: Path) -> None:
    """Remove insignificant whitespace from *path* in place.

    Uses lxml's iterparse to strip whitespace-only text/tail segments
    while preserving content inside ``<*:t>`` elements (the text-run
    containers in OOXML).
    """
    try:
        tree = etree.parse(str(path))  # noqa: S320 – trusted local files
    except etree.XMLSyntaxError as exc:
        print(f"XML parse error in {path.name}: {exc}", file=sys.stderr)
        raise

    root = tree.getroot()
    _strip_whitespace(root)

    # Remove XML comments
    for comment in root.iter(etree.Comment):
        parent = comment.getparent()
        if parent is not None:
            parent.remove(comment)

    tree.write(str(path), xml_declaration=True, encoding="UTF-8")


def _is_text_run_tag(tag: str) -> bool:
    """True for local-name ``t`` (e.g. ``{…}t`` or ``w:t``)."""
    if "}" in tag:
        return tag.rsplit("}", 1)[1] == "t"
    return tag.endswith(":t") or tag == "t"


def _strip_whitespace(node: etree._Element) -> None:
    """Recursively remove whitespace-only text and tail nodes."""
    if not _is_text_run_tag(node.tag):
        if node.text is not None and not node.text.strip():
            node.text = None

    for child in node:
        _strip_whitespace(child)

    if node.tail is not None and not node.tail.strip():
        node.tail = None


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def run_validators(
    content_dir: Path,
    reference_file: Path,
    suffix: str,
    author_resolver=None,
) -> tuple[bool, list[str]]:
    """Instantiate the appropriate validators and run repair + check.

    Returns ``(all_passed, log_lines)``.
    """
    log: list[str] = []
    checkers = []

    if suffix == ".docx":
        author = "Claude"
        if author_resolver is not None:
            try:
                author = author_resolver(content_dir, reference_file)
            except (ValueError, TypeError) as err:
                log.append(f"Author detection fell back to default: {err}")
        checkers.append(DocumentValidator(content_dir, reference_file))
        checkers.append(TrackedChangesValidator(content_dir, reference_file, author=author))
    elif suffix == ".pptx":
        checkers.append(PresentationValidator(content_dir, reference_file))

    if not checkers:
        return True, log

    repairs = 0
    for chk in checkers:
        repairs += chk.repair()
    if repairs:
        log.append(f"Auto-repaired {repairs} issue(s)")

    passed = all(chk.validate() for chk in checkers)
    if passed:
        log.append("Validation passed")
    return passed, log


# ---------------------------------------------------------------------------
# Core packing logic
# ---------------------------------------------------------------------------

def build_office_file(
    src_dir: str,
    dst_file: str,
    *,
    reference: str | None = None,
    validate: bool = True,
    infer_author_func=None,
) -> tuple[bool, str]:
    """Create an Office file from an unpacked directory.

    Parameters
    ----------
    src_dir:
        Path to the directory containing the unpacked Office content.
    dst_file:
        Destination path for the resulting ``.docx`` / ``.pptx`` / ``.xlsx``.
    reference:
        Optional path to the original Office file used for validation.
    validate:
        Whether to run schema and tracked-change validation.
    infer_author_func:
        Optional callable ``(content_dir, ref_path) -> str`` returning the
        author name.

    Returns
    -------
    tuple[bool, str]
        ``(success, message)``
    """
    src = Path(src_dir)
    dst = Path(dst_file)

    if not src.is_dir():
        return False, f"Not a directory: {src_dir}"

    suffix = dst.suffix.lower()
    if suffix not in _SUPPORTED_SUFFIXES:
        return False, f"Unsupported extension '{suffix}'; expected one of {sorted(_SUPPORTED_SUFFIXES)}"

    # --- optional validation against the original file ---
    if validate and reference:
        ref = Path(reference)
        if not ref.is_file():
            return False, f"Reference file missing: {reference}"
        passed, log = run_validators(src, ref, suffix, infer_author_func)
        for line in log:
            print(line)
        if not passed:
            return False, f"Validation failed for {src_dir}"

    # --- minify XML in a temporary copy, then zip ---
    staging = Path(tempfile.mkdtemp())
    try:
        work = staging / "pkg"
        shutil.copytree(src, work)

        for markup in work.rglob("*"):
            if markup.is_file() and markup.suffix.lower() in (".xml", ".rels"):
                compact_xml(markup)

        dst.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zf:
            for entry in sorted(work.rglob("*")):
                if entry.is_file():
                    zf.write(entry, entry.relative_to(work))
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    return True, f"Built {dst_file} from {src_dir}"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _bool_flag(raw: str) -> bool:
    return raw.strip().lower() in ("true", "1", "yes")


def cli(argv: Sequence[str] | None = None) -> None:
    ap = argparse.ArgumentParser(
        description="Reassemble an unpacked Office directory into a .docx/.pptx/.xlsx file.",
    )
    ap.add_argument("src_dir", help="Unpacked Office document directory")
    ap.add_argument("dst_file", help="Output file path (.docx/.pptx/.xlsx)")
    ap.add_argument(
        "--reference",
        default=None,
        help="Original Office file used for validation comparison",
    )
    ap.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip schema and tracked-change validation",
    )
    opts = ap.parse_args(argv)

    ok, msg = build_office_file(
        opts.src_dir,
        opts.dst_file,
        reference=opts.reference,
        validate=not opts.skip_validation,
    )
    print(msg)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    cli()
