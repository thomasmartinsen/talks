"""Tracked-changes (redlining) validator for Word documents.

Verifies that all edits made by a given *author* are wrapped in proper
``<w:ins>`` / ``<w:del>`` markup so that the underlying document text is
unchanged when the author's tracked changes are backed out.
"""

from __future__ import annotations

import subprocess
import tempfile
import zipfile
from pathlib import Path


_NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


class TrackedChangesValidator:
    """Compare the document after removing a single author's tracked changes
    against the original to confirm nothing was silently modified."""

    def __init__(
        self,
        unpacked_dir: str | Path,
        original_docx: str | Path,
        verbose: bool = False,
        author: str = "Claude",
    ) -> None:
        self.unpacked_dir = Path(unpacked_dir)
        self.original_docx = Path(original_docx)
        self.verbose = verbose
        self.author = author

    # ── public API ───────────────────────────────────────────────

    def repair(self) -> int:
        return 0

    def validate(self) -> bool:
        doc_xml = self.unpacked_dir / "word" / "document.xml"
        if not doc_xml.exists():
            print(f"  FAIL [tracked-changes] – document.xml not found at {doc_xml}")
            return False

        if not self._has_author_changes(doc_xml):
            if self.verbose:
                print(f"  OK  [tracked-changes] – no changes by {self.author}")
            return True

        original_text = self._text_from_original()
        if original_text is None:
            return False

        modified_text = self._text_without_author_changes(doc_xml)
        if modified_text is None:
            return False

        if original_text == modified_text:
            if self.verbose:
                print(f"  OK  [tracked-changes] – all {self.author} changes properly tracked")
            return True

        self._report_mismatch(original_text, modified_text)
        return False

    # ── change detection ─────────────────────────────────────────

    def _has_author_changes(self, doc_xml: Path) -> bool:
        import xml.etree.ElementTree as ET

        try:
            root = ET.parse(doc_xml).getroot()
            ns = {"w": _NS_W}
            author_attr = f"{{{_NS_W}}}author"
            for tag in ("w:del", "w:ins"):
                if any(
                    el.get(author_attr) == self.author
                    for el in root.findall(f".//{tag}", ns)
                ):
                    return True
        except Exception:
            pass
        return False

    # ── text extraction ──────────────────────────────────────────

    def _text_without_author_changes(self, doc_xml: Path) -> str | None:
        import xml.etree.ElementTree as ET

        try:
            root = ET.parse(doc_xml).getroot()
            self._undo_author_edits(root)
            return self._collect_paragraphs(root)
        except ET.ParseError as exc:
            print(f"  FAIL [tracked-changes] – XML parse error: {exc}")
            return None

    def _text_from_original(self) -> str | None:
        import xml.etree.ElementTree as ET

        with tempfile.TemporaryDirectory() as td:
            tp = Path(td)
            try:
                with zipfile.ZipFile(self.original_docx, "r") as zf:
                    zf.extractall(tp)
            except Exception as exc:
                print(f"  FAIL [tracked-changes] – cannot unpack original: {exc}")
                return None

            orig_doc = tp / "word" / "document.xml"
            if not orig_doc.exists():
                print(f"  FAIL [tracked-changes] – original has no document.xml")
                return None
            try:
                root = ET.parse(orig_doc).getroot()
                self._undo_author_edits(root)
                return self._collect_paragraphs(root)
            except ET.ParseError as exc:
                print(f"  FAIL [tracked-changes] – original XML parse error: {exc}")
                return None

    # ── tracked-change removal ───────────────────────────────────

    def _undo_author_edits(self, root) -> None:
        """Remove the author's insertions and restore the author's deletions."""
        ins_tag = f"{{{_NS_W}}}ins"
        del_tag = f"{{{_NS_W}}}del"
        author_attr = f"{{{_NS_W}}}author"

        # Drop insertion elements entirely
        for parent in root.iter():
            for child in [
                c for c in parent
                if c.tag == ins_tag and c.get(author_attr) == self.author
            ]:
                parent.remove(child)

        # Promote deletion content back into the flow
        deltext = f"{{{_NS_W}}}delText"
        t_tag = f"{{{_NS_W}}}t"

        for parent in root.iter():
            targets = [
                (child, list(parent).index(child))
                for child in parent
                if child.tag == del_tag and child.get(author_attr) == self.author
            ]
            for del_elem, idx in reversed(targets):
                for node in del_elem.iter():
                    if node.tag == deltext:
                        node.tag = t_tag
                for child in reversed(list(del_elem)):
                    parent.insert(idx, child)
                parent.remove(del_elem)

    # ── paragraph text ───────────────────────────────────────────

    @staticmethod
    def _collect_paragraphs(root) -> str:
        p_tag = f"{{{_NS_W}}}p"
        t_tag = f"{{{_NS_W}}}t"
        paragraphs: list[str] = []
        for p in root.findall(f".//{p_tag}"):
            text = "".join(t.text for t in p.findall(f".//{t_tag}") if t.text)
            if text:
                paragraphs.append(text)
        return "\n".join(paragraphs)

    # ── diff reporting ───────────────────────────────────────────

    def _report_mismatch(self, original: str, modified: str) -> None:
        lines = [
            f"  FAIL [tracked-changes] – text mismatch after removing {self.author}'s changes",
            "",
            "  Possible causes:",
            "    • Edited text inside another author's <w:ins>/<w:del>",
            "    • Changed content without tracked-change markup",
            "    • Deleted another's insertion without nesting <w:del> inside <w:ins>",
            "",
            "  Redlining patterns for pre-redlined documents:",
            "    • Reject another's insertion → nest <w:del> inside their <w:ins>",
            "    • Restore another's deletion → add <w:ins> after their <w:del>",
        ]
        diff = self._word_diff(original, modified)
        if diff:
            lines += ["", "  Diff:", "  " + "=" * 40, diff]
        else:
            lines.append("  (git word-diff unavailable)")
        print("\n".join(lines))

    @staticmethod
    def _word_diff(before: str, after: str) -> str | None:
        """Use ``git diff --word-diff`` to produce a readable delta."""
        try:
            with tempfile.TemporaryDirectory() as td:
                tp = Path(td)
                (tp / "a.txt").write_text(before, encoding="utf-8")
                (tp / "b.txt").write_text(after, encoding="utf-8")
                for extra_args in (["--word-diff-regex=."], []):
                    result = subprocess.run(
                        [
                            "git", "diff", "--word-diff=plain",
                            *extra_args, "-U0", "--no-index",
                            str(tp / "a.txt"), str(tp / "b.txt"),
                        ],
                        capture_output=True, text=True,
                    )
                    if result.stdout.strip():
                        content = []
                        started = False
                        for line in result.stdout.splitlines():
                            if line.startswith("@@"):
                                started = True
                                continue
                            if started and line.strip():
                                content.append(line)
                        if content:
                            return "\n".join(content)
        except Exception:
            pass
        return None


if __name__ == "__main__":
    raise RuntimeError("This module should not be run directly.")
