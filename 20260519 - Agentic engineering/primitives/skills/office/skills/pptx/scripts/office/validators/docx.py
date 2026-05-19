"""Word (.docx) document validator.

Extends :class:`OfficeDocValidator` with Word-specific checks via the
pipeline pattern.
"""

from __future__ import annotations

from typing import Callable

from .base import OfficeDocValidator


class DocumentValidator(OfficeDocValidator):
    """Validates unpacked ``.docx`` content."""

    ELEMENT_RELATIONSHIP_TYPES: dict[str, str] = {}

    def _build_check_pipeline(self) -> list[tuple[str, Callable[[], list[str]]]]:
        return [
            ("xml-syntax", self.check_xml_syntax),
            ("namespace-decls", self.check_ns_declarations),
            ("id-uniqueness", self.check_id_uniqueness),
            ("file-references", self.check_references),
            ("content-types", self.check_content_types),
            ("xsd-conformance", self.check_xsd_conformance),
            ("relationship-ids", self.check_relationship_ids),
        ]

    def validate(self) -> bool:
        syntax_issues = self.check_xml_syntax()
        if syntax_issues:
            print(f"  FAIL [xml-syntax] – {len(syntax_issues)} issue(s):")
            for line in syntax_issues:
                print(f"       {line}")
            return False
        return self.run_pipeline()


if __name__ == "__main__":
    raise RuntimeError("This module should not be run directly.")
