"""Compact adjacent tracked-change wrappers in DOCX XML.

Scans for consecutive <w:ins> or <w:del> elements authored by the same
person and collapses them into a single wrapper, reducing visual noise
in heavily-redlined documents.

Merging rules:
- Only same-type elements are combined (ins+ins, del+del)
- Author must match (timestamp differences are ignored)
- Elements must be truly adjacent (only whitespace between them)
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import defusedxml.minidom

WORDPROCESSING_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


# ---------------------------------------------------------------------------
# DOM helpers
# ---------------------------------------------------------------------------


def _walk_elements(node, tag: str) -> list:
    """Collect every descendant element whose localName equals *tag*."""
    found: list = []
    stack = list(node.childNodes)
    while stack:
        current = stack.pop()
        if current.nodeType == current.ELEMENT_NODE:
            local = current.localName or current.tagName
            if local == tag or local.endswith(f":{tag}"):
                found.append(current)
            stack.extend(current.childNodes)
    return found


def _matches_tag(node, tag: str) -> bool:
    """True when *node* is an element whose localName equals *tag*."""
    if node.nodeType != node.ELEMENT_NODE:
        return False
    local = node.localName or node.tagName
    return local == tag or local.endswith(f":{tag}")


def _extract_author(elem) -> str:
    """Return the ``w:author`` attribute value, or the empty string."""
    author = elem.getAttribute("w:author")
    if not author:
        for attr in elem.attributes.values():
            if attr.localName == "author" or attr.name.endswith(":author"):
                return attr.value
    return author


# ---------------------------------------------------------------------------
# Merge-pair detection
# ---------------------------------------------------------------------------


def _only_whitespace_between(a, b) -> bool:
    """True when only whitespace text/comment nodes sit between *a* and *b*."""
    cursor = a.nextSibling
    while cursor is not None and cursor is not b:
        if cursor.nodeType == cursor.ELEMENT_NODE:
            return False
        if cursor.nodeType == cursor.TEXT_NODE and cursor.data.strip():
            return False
        cursor = cursor.nextSibling
    return cursor is b


def _are_mergeable(first, second) -> bool:
    """True when two tracked-change elements can be folded together."""
    author_a = _extract_author(first)
    author_b = _extract_author(second)
    if not author_a or author_a != author_b:
        return False
    return _only_whitespace_between(first, second)


def _transfer_children(target, source) -> None:
    """Move every child node from *source* into *target*."""
    while source.firstChild:
        target.appendChild(source.removeChild(source.firstChild))


# ---------------------------------------------------------------------------
# Core: collect-then-apply strategy
# ---------------------------------------------------------------------------


def _collect_merge_pairs(container, tag: str) -> list[tuple]:
    """Scan direct children for adjacent, mergeable pairs of *tag* elements.

    Returns a list of ``(keep, discard)`` tuples in document order.
    """
    elements = [ch for ch in container.childNodes if _matches_tag(ch, tag)]
    if len(elements) < 2:
        return []

    pairs: list[tuple] = []
    anchor = elements[0]
    for elem in elements[1:]:
        if _are_mergeable(anchor, elem):
            pairs.append((anchor, elem))
        else:
            anchor = elem
    return pairs


def _coalesce_changes_in(container, tag: str) -> int:
    """Merge adjacent tracked-change wrappers of *tag* inside *container*.

    First collects every mergeable pair, then applies transfers in
    document order.  Returns the number of merges applied.
    """
    pairs = _collect_merge_pairs(container, tag)
    if not pairs:
        return 0

    for keeper, discard in pairs:
        _transfer_children(keeper, discard)
        container.removeChild(discard)

    return len(pairs)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def compact_tracked_changes(input_dir: str) -> tuple[int, str]:
    """Merge adjacent tracked-change wrappers in ``word/document.xml``.

    Parameters
    ----------
    input_dir:
        Path to the unpacked DOCX directory.

    Returns
    -------
    tuple[int, str]
        ``(merge_count, status_message)``
    """
    doc_path = Path(input_dir) / "word" / "document.xml"
    if not doc_path.exists():
        return 0, f"Error: {doc_path} not found"

    try:
        dom = defusedxml.minidom.parseString(doc_path.read_text(encoding="utf-8"))
        root = dom.documentElement

        containers = _walk_elements(root, "p") + _walk_elements(root, "tc")

        total = 0
        for container in containers:
            total += _coalesce_changes_in(container, "ins")
            total += _coalesce_changes_in(container, "del")

        doc_path.write_bytes(dom.toxml(encoding="UTF-8"))
        return total, f"Simplified {total} tracked changes"

    except Exception as exc:
        return 0, f"Error: {exc}"


# ---------------------------------------------------------------------------
# Author-inference utilities
# ---------------------------------------------------------------------------


def _tally_authors(xml_root) -> dict[str, int]:
    """Count tracked-change elements per author in an ElementTree root."""
    ns_author = f"{{{WORDPROCESSING_NS}}}author"
    counts: dict[str, int] = {}
    for tag_name in ("ins", "del"):
        for elem in xml_root.iter(f"{{{WORDPROCESSING_NS}}}{tag_name}"):
            author = elem.get(ns_author)
            if author:
                counts[author] = counts.get(author, 0) + 1
    return counts


def count_change_authors(doc_xml_path: Path) -> dict[str, int]:
    """Parse ``document.xml`` and return a mapping of author → change count.

    Parameters
    ----------
    doc_xml_path:
        Path to a ``word/document.xml`` file on disk.

    Returns
    -------
    dict[str, int]
    """
    if not doc_xml_path.exists():
        return {}
    try:
        tree = ET.parse(doc_xml_path)  # noqa: S314
    except ET.ParseError:
        return {}
    return _tally_authors(tree.getroot())


def _count_authors_in_docx(docx_path: Path) -> dict[str, int]:
    """Count tracked-change authors inside a packed ``.docx`` ZIP file."""
    try:
        with zipfile.ZipFile(docx_path, "r") as zf:
            if "word/document.xml" not in zf.namelist():
                return {}
            with zf.open("word/document.xml") as fh:
                tree = ET.parse(fh)  # noqa: S314
    except (zipfile.BadZipFile, ET.ParseError):
        return {}
    return _tally_authors(tree.getroot())


def detect_editing_author(
    modified_dir: Path,
    original_docx: Path,
    default: str = "Claude",
) -> str:
    """Identify which author introduced new tracked changes.

    Compares change counts between the modified (unpacked) directory and
    the original ``.docx`` file.  Authors whose count grew — or who
    appear for the first time — are treated as the editing author.

    Parameters
    ----------
    modified_dir:
        Path to the unpacked DOCX directory after modifications.
    original_docx:
        Path to the original ``.docx`` before modifications.
    default:
        Fallback name when no new changes are detected.

    Returns
    -------
    str

    Raises
    ------
    ValueError
        If more than one author added new tracked changes.
    """
    current = count_change_authors(modified_dir / "word" / "document.xml")
    if not current:
        return default

    baseline = _count_authors_in_docx(original_docx)

    new_authors = [
        author
        for author, n in current.items()
        if n > baseline.get(author, 0)
    ]

    if not new_authors:
        return default
    if len(new_authors) == 1:
        return new_authors[0]

    raise ValueError(
        f"Multiple authors added new changes: {sorted(new_authors)}. "
        "Cannot infer which author to validate."
    )
