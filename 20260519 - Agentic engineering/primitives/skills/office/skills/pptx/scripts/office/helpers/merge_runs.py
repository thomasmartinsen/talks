"""Consolidate adjacent runs sharing formatting in DOCX XML.

Scans <w:r> elements within paragraphs and tracked-change wrappers
(<w:ins>, <w:del>), merging neighbours that carry identical <w:rPr>
formatting properties into a single run.

Pre-processing steps:
- Strips rsid revision-tracking attributes from runs
- Deletes proofErr markers that would otherwise prevent merging
"""

from __future__ import annotations

from functools import reduce
from pathlib import Path

import defusedxml.minidom


# ---------------------------------------------------------------------------
# DOM query helpers
# ---------------------------------------------------------------------------


def _query_by_tag(node, tag: str) -> list:
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


def _first_child_of_type(parent, tag: str):
    """Return the first direct child element matching *tag*, or ``None``."""
    for child in parent.childNodes:
        if child.nodeType == child.ELEMENT_NODE:
            local = child.localName or child.tagName
            if local == tag or local.endswith(f":{tag}"):
                return child
    return None


def _children_of_type(parent, tag: str) -> list:
    """Return every direct child element matching *tag*."""
    return [
        ch
        for ch in parent.childNodes
        if ch.nodeType == ch.ELEMENT_NODE
        and (
            (ch.localName or ch.tagName) == tag
            or (ch.localName or ch.tagName).endswith(f":{tag}")
        )
    ]


def _are_neighbors(a, b) -> bool:
    """True when *a* and *b* are adjacent siblings (only whitespace between)."""
    cursor = a.nextSibling
    while cursor is not None:
        if cursor is b:
            return True
        if cursor.nodeType == cursor.ELEMENT_NODE:
            return False
        if cursor.nodeType == cursor.TEXT_NODE and cursor.data.strip():
            return False
        cursor = cursor.nextSibling
    return False


# ---------------------------------------------------------------------------
# Pre-processing: clean revision IDs and proof markers
# ---------------------------------------------------------------------------


def _delete_all_matching(root, tag: str) -> None:
    """Remove every descendant element whose localName equals *tag*."""
    for el in _query_by_tag(root, tag):
        if el.parentNode:
            el.parentNode.removeChild(el)


def _clear_revision_ids(root) -> None:
    """Strip all ``rsid``-prefixed attributes from <w:r> elements."""
    for run in _query_by_tag(root, "r"):
        to_remove = [
            attr.name
            for attr in run.attributes.values()
            if "rsid" in attr.name.lower()
        ]
        for name in to_remove:
            run.removeAttribute(name)


# ---------------------------------------------------------------------------
# Run identification and formatting comparison
# ---------------------------------------------------------------------------


def _is_run_element(node) -> bool:
    """True when *node* is a <w:r> element."""
    if node.nodeType != node.ELEMENT_NODE:
        return False
    local = node.localName or node.tagName
    return local == "r" or local.endswith(":r")


def _formatting_matches(run_a, run_b) -> bool:
    """True when both runs carry identical <w:rPr> properties."""
    props_a = _first_child_of_type(run_a, "rPr")
    props_b = _first_child_of_type(run_b, "rPr")
    if props_a is None and props_b is None:
        return True
    if props_a is None or props_b is None:
        return False
    return props_a.toxml() == props_b.toxml()


# ---------------------------------------------------------------------------
# Content transfer and text-node unification
# ---------------------------------------------------------------------------


def _absorb_content(target, source) -> None:
    """Append every non-rPr child of *source* into *target*."""
    for child in list(source.childNodes):
        if child.nodeType == child.ELEMENT_NODE:
            local = child.localName or child.tagName
            if local == "rPr" or local.endswith(":rPr"):
                continue
        target.appendChild(child)


def _unify_text_nodes(run) -> None:
    """Merge adjacent <w:t> elements inside a single run."""
    t_nodes = _children_of_type(run, "t")
    if len(t_nodes) < 2:
        return

    idx = 0
    while idx < len(t_nodes) - 1:
        first, second = t_nodes[idx], t_nodes[idx + 1]
        if not _are_neighbors(first, second):
            idx += 1
            continue

        text_a = first.firstChild.data if first.firstChild else ""
        text_b = second.firstChild.data if second.firstChild else ""
        combined = text_a + text_b

        if first.firstChild:
            first.firstChild.data = combined
        else:
            first.appendChild(run.ownerDocument.createTextNode(combined))

        if combined != combined.strip():
            first.setAttribute("xml:space", "preserve")
        elif first.hasAttribute("xml:space"):
            first.removeAttribute("xml:space")

        run.removeChild(second)
        t_nodes.pop(idx + 1)


# ---------------------------------------------------------------------------
# Core merging: list-collect-and-reduce approach
# ---------------------------------------------------------------------------


def _collect_direct_runs(container) -> list:
    """Return an ordered list of direct-child <w:r> elements."""
    return [ch for ch in container.childNodes if _is_run_element(ch)]


def _group_mergeable(runs: list) -> list[list]:
    """Partition *runs* into groups of adjacent, format-compatible runs.

    Each group is a list of runs that can all be collapsed into one.
    Uses ``functools.reduce`` to accumulate groups in a single pass.
    """
    if not runs:
        return []

    def _accumulate(groups: list[list], run) -> list[list]:
        if not groups:
            return [[run]]
        last_group = groups[-1]
        prev = last_group[-1]
        if _are_neighbors(prev, run) and _formatting_matches(prev, run):
            last_group.append(run)
        else:
            groups.append([run])
        return groups

    return reduce(_accumulate, runs, [])


def _fuse_runs_in_container(container) -> int:
    """Merge adjacent, identically-formatted runs inside *container*.

    Collects runs into a flat list, groups mergeable neighbours via
    ``reduce``, then folds each group into its first element.
    Returns the merge count.
    """
    runs = _collect_direct_runs(container)
    groups = _group_mergeable(runs)

    merges = 0
    for group in groups:
        if len(group) < 2:
            continue
        anchor = group[0]
        for donor in group[1:]:
            _absorb_content(anchor, donor)
            container.removeChild(donor)
            merges += 1
        _unify_text_nodes(anchor)

    return merges


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def consolidate_runs(input_dir: str) -> tuple[int, str]:
    """Merge adjacent, identically-formatted runs in ``word/document.xml``.

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

        _delete_all_matching(root, "proofErr")
        _clear_revision_ids(root)

        # Identify every container that may hold runs
        containers = {r.parentNode for r in _query_by_tag(root, "r")}

        total = sum(_fuse_runs_in_container(c) for c in containers)

        doc_path.write_bytes(dom.toxml(encoding="UTF-8"))
        return total, f"Merged {total} runs"

    except Exception as exc:
        return 0, f"Error: {exc}"
