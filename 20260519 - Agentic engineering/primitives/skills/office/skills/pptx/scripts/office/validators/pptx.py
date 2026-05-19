"""PowerPoint (.pptx) document validator.

Uses a pipeline of grouped checks rather than sequential method calls.
XML is parsed once through the base-class cache and reused across checks.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

import lxml.etree

from .base import (
    NS_OFFICE_RELS,
    NS_PKG_RELS,
    OfficeDocValidator,
    _local_tag,
)

_NS_PML = "http://schemas.openxmlformats.org/presentationml/2006/main"

_UUID_RE = re.compile(
    r"^[\{\(]?[0-9A-Fa-f]{8}-?[0-9A-Fa-f]{4}-?[0-9A-Fa-f]{4}"
    r"-?[0-9A-Fa-f]{4}-?[0-9A-Fa-f]{12}[\}\)]?$"
)

_PPTX_REL_KINDS: dict[str, str] = {
    "sldid": "slide",
    "sldmasterid": "slidemaster",
    "notesmasterid": "notesmaster",
    "sldlayoutid": "slidelayout",
    "themeid": "theme",
    "tablestyleid": "tablestyles",
}


class PresentationValidator(OfficeDocValidator):
    """Validator tailored for ``.pptx`` files.

    Overrides the base pipeline with PPTX-specific checks grouped into
    three phases:

    1. **Structural** – XML syntax, namespaces, content types, XSD.
    2. **Identity** – UUID format and ID uniqueness (combined).
    3. **Referential** – file references, relationship IDs, slide-layout
       linkage, notes-slide uniqueness, duplicate layout references.
    """

    ELEMENT_RELATIONSHIP_TYPES = _PPTX_REL_KINDS

    # ── pipeline assembly ────────────────────────────────────────

    def _build_check_pipeline(self) -> list[tuple[str, Callable[[], list[str]]]]:
        return [
            # Phase 1: structural integrity
            ("xml-syntax", self.check_xml_syntax),
            ("namespace-decls", self.check_ns_declarations),
            ("content-types", self.check_content_types),
            ("xsd-conformance", self.check_xsd_conformance),
            # Phase 2: identifiers (uuid + uniqueness combined)
            ("identifiers", self._check_identifiers),
            # Phase 3: referential integrity
            ("file-references", self.check_references),
            ("relationship-ids", self.check_relationship_ids),
            ("layout-linkage", self._check_layout_references),
            ("notes-slide-refs", self._check_notes_uniqueness),
            ("single-layout-per-slide", self._check_no_duplicate_layouts),
        ]

    def validate(self) -> bool:
        """Gate on XML syntax first; if that fails skip everything else."""
        syntax_issues = self.check_xml_syntax()
        if syntax_issues:
            print(f"  FAIL [xml-syntax] – {len(syntax_issues)} issue(s):")
            for line in syntax_issues:
                print(f"       {line}")
            return False
        return self.run_pipeline()

    # ── Phase 2: combined identifier checks ──────────────────────

    def _check_identifiers(self) -> list[str]:
        """Merge UUID-format and uniqueness checks into one pass."""
        issues = self._scan_uuid_format()
        issues.extend(self.check_id_uniqueness())
        return issues

    def _scan_uuid_format(self) -> list[str]:
        """Flag ID-like attributes that look like UUIDs but have bad hex."""
        issues: list[str] = []
        for xf in self.xml_files:
            try:
                root = self._root_of(xf)
                for node in root.iter():
                    for attr, val in node.attrib.items():
                        name_lc = _local_tag(attr).lower()
                        if name_lc != "id" and not name_lc.endswith("id"):
                            continue
                        if not self._resembles_uuid(val):
                            continue
                        if not _UUID_RE.match(val):
                            issues.append(
                                f"{xf.relative_to(self.unpacked_dir)}:{node.sourceline} "
                                f"– id '{val}' looks like a UUID but has invalid hex"
                            )
            except Exception as exc:
                issues.append(f"{xf.relative_to(self.unpacked_dir)} – {exc}")
        return issues

    @staticmethod
    def _resembles_uuid(value: str) -> bool:
        stripped = value.strip("{}()").replace("-", "")
        return len(stripped) == 32 and stripped.isalnum()

    # ── Phase 3: PPTX-specific referential checks ────────────────

    def _check_layout_references(self) -> list[str]:
        """Verify every sldLayoutId in slide masters points to a real layout."""
        issues: list[str] = []
        masters = list(self.unpacked_dir.glob("ppt/slideMasters/*.xml"))
        for master_path in masters:
            try:
                master_root = lxml.etree.parse(str(master_path)).getroot()
                rels_path = master_path.parent / "_rels" / f"{master_path.name}.rels"
                if not rels_path.exists():
                    issues.append(
                        f"{master_path.relative_to(self.unpacked_dir)} – "
                        f"missing .rels file {rels_path.relative_to(self.unpacked_dir)}"
                    )
                    continue

                known_rids = self._layout_rids_from_rels(rels_path)

                for layout_node in master_root.findall(f".//{{{_NS_PML}}}sldLayoutId"):
                    rid = layout_node.get(f"{{{NS_OFFICE_RELS}}}id")
                    lid = layout_node.get("id", "?")
                    if rid and rid not in known_rids:
                        issues.append(
                            f"{master_path.relative_to(self.unpacked_dir)}:{layout_node.sourceline} "
                            f"– sldLayoutId id='{lid}' references r:id='{rid}' with no matching layout relationship"
                        )
            except Exception as exc:
                issues.append(f"{master_path.relative_to(self.unpacked_dir)} – {exc}")

        if issues:
            issues.append("Fix invalid references or add missing layouts to the .rels file.")
        return issues

    def _check_notes_uniqueness(self) -> list[str]:
        """Each notes slide should be referenced by at most one slide."""
        issues: list[str] = []
        rels_files = list(self.unpacked_dir.glob("ppt/slides/_rels/*.xml.rels"))
        if not rels_files:
            return issues

        target_to_sources: dict[str, list[tuple[str, Path]]] = {}
        for rf in rels_files:
            try:
                rroot = lxml.etree.parse(str(rf)).getroot()
                for rel in rroot.findall(f".//{{{NS_PKG_RELS}}}Relationship"):
                    if "notesSlide" not in rel.get("Type", ""):
                        continue
                    target = rel.get("Target", "")
                    if not target:
                        continue
                    normalised = target.replace("../", "")
                    slide_name = rf.stem.replace(".xml", "")
                    target_to_sources.setdefault(normalised, []).append((slide_name, rf))
            except Exception as exc:
                issues.append(f"{rf.relative_to(self.unpacked_dir)} – {exc}")

        for target, sources in target_to_sources.items():
            if len(sources) > 1:
                names = ", ".join(s[0] for s in sources)
                issues.append(f"notes slide '{target}' shared by multiple slides: {names}")
                for _, rf in sources:
                    issues.append(f"  → {rf.relative_to(self.unpacked_dir)}")

        if issues:
            issues.append("Each slide should have its own notes slide (or none).")
        return issues

    def _check_no_duplicate_layouts(self) -> list[str]:
        """Each slide .rels should reference exactly one slideLayout."""
        issues: list[str] = []
        for rf in self.unpacked_dir.glob("ppt/slides/_rels/*.xml.rels"):
            try:
                rroot = lxml.etree.parse(str(rf)).getroot()
                layout_count = sum(
                    1
                    for rel in rroot.findall(f".//{{{NS_PKG_RELS}}}Relationship")
                    if "slideLayout" in rel.get("Type", "")
                )
                if layout_count > 1:
                    issues.append(
                        f"{rf.relative_to(self.unpacked_dir)} – {layout_count} slideLayout references (expected 1)"
                    )
            except Exception as exc:
                issues.append(f"{rf.relative_to(self.unpacked_dir)} – {exc}")
        return issues

    # ── helpers ───────────────────────────────────────────────────

    @staticmethod
    def _layout_rids_from_rels(rels_path: Path) -> set[str]:
        """Extract rIds that point to slideLayout from a .rels file."""
        rids: set[str] = set()
        root = lxml.etree.parse(str(rels_path)).getroot()
        for rel in root.findall(f".//{{{NS_PKG_RELS}}}Relationship"):
            if "slideLayout" in rel.get("Type", ""):
                rid = rel.get("Id")
                if rid:
                    rids.add(rid)
        return rids


if __name__ == "__main__":
    raise RuntimeError("This module should not be run directly.")
