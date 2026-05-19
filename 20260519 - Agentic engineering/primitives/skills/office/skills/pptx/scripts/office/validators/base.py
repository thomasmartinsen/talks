"""Office Open XML document validator foundation.

Provides :class:`OfficeDocValidator`, the shared base for format-specific
validators (DOCX, PPTX, XLSX).  Each concrete subclass overrides
:meth:`_build_check_pipeline` to return format-specific checks and then
calls :meth:`run_pipeline` from its :meth:`validate` implementation.

The key design differences from earlier iterations are:

* **Pipeline architecture** – every individual check is a callable
  ``() -> list[str]`` that returns a (possibly empty) list of diagnostic
  strings.  :meth:`run_pipeline` drives them all and collects results.
* **Parsed-tree cache** – XML files are parsed *once* during init and
  reused by every check, avoiding redundant I/O and parsing.
* **Structured diagnostics** – each problem is returned as a plain string
  with a ``[CATEGORY]`` prefix instead of ``PASSED``/``FAILED`` print
  statements, making results easier to filter programmatically.
"""

from __future__ import annotations

import random
import re
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Sequence

import defusedxml.minidom
import lxml.etree


# ── Diagnostic result ────────────────────────────────────────────────

@dataclass
class CheckResult:
    """Container returned by every pipeline check."""

    name: str
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.problems) == 0


# ── Namespace / schema constants ─────────────────────────────────────

NS_MARKUP_COMPAT = "http://schemas.openxmlformats.org/markup-compatibility/2006"
NS_XML = "http://www.w3.org/XML/1998/namespace"
NS_PKG_RELS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS_OFFICE_RELS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_CONTENT_TYPES = "http://schemas.openxmlformats.org/package/2006/content-types"

KNOWN_NAMESPACES: set[str] = {
    "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "http://schemas.openxmlformats.org/schemaLibrary/2006/main",
    "http://schemas.openxmlformats.org/drawingml/2006/main",
    "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "http://schemas.openxmlformats.org/drawingml/2006/chartDrawing",
    "http://schemas.openxmlformats.org/drawingml/2006/diagram",
    "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing",
    "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "http://schemas.openxmlformats.org/presentationml/2006/main",
    "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "http://schemas.openxmlformats.org/officeDocument/2006/sharedTypes",
    NS_XML,
}

FILE_SCHEMA_MAP: dict[str, str] = {
    "word": "ISO-IEC29500-4_2016/wml.xsd",
    "ppt": "ISO-IEC29500-4_2016/pml.xsd",
    "xl": "ISO-IEC29500-4_2016/sml.xsd",
    "[Content_Types].xml": "ecma/fouth-edition/opc-contentTypes.xsd",
    "app.xml": "ISO-IEC29500-4_2016/shared-documentPropertiesExtended.xsd",
    "core.xml": "ecma/fouth-edition/opc-coreProperties.xsd",
    "custom.xml": "ISO-IEC29500-4_2016/shared-documentPropertiesCustom.xsd",
    ".rels": "ecma/fouth-edition/opc-relationships.xsd",
    "people.xml": "microsoft/wml-2012.xsd",
    "commentsIds.xml": "microsoft/wml-cid-2016.xsd",
    "commentsExtensible.xml": "microsoft/wml-cex-2018.xsd",
    "commentsExtended.xml": "microsoft/wml-2012.xsd",
    "chart": "ISO-IEC29500-4_2016/dml-chart.xsd",
    "theme": "ISO-IEC29500-4_2016/dml-main.xsd",
    "drawing": "ISO-IEC29500-4_2016/dml-main.xsd",
}

ID_UNIQUENESS_RULES: dict[str, tuple[str, str]] = {
    "comment": ("id", "file"),
    "commentrangestart": ("id", "file"),
    "commentrangeend": ("id", "file"),
    "bookmarkstart": ("id", "file"),
    "bookmarkend": ("id", "file"),
    "sldid": ("id", "file"),
    "sldmasterid": ("id", "global"),
    "sldlayoutid": ("id", "global"),
    "cm": ("authorid", "file"),
    "sheet": ("sheetid", "file"),
    "definedname": ("id", "file"),
    "cxnsp": ("id", "file"),
    "sp": ("id", "file"),
    "pic": ("id", "file"),
    "grpsp": ("id", "file"),
}

_SKIP_ID_PARENTS: set[str] = {"sectionlst"}
_DOCUMENT_FOLDERS: frozenset[str] = frozenset({"word", "ppt", "xl"})
_XSD_ERROR_NOISE: Sequence[str] = ("hyphenationZone", "purl.org/dc/terms")

_DECLARABLE_ROOT_TAGS: set[str] = {
    "sld", "sldLayout", "sldMaster", "presentation",
    "document", "workbook", "worksheet", "theme",
}
_MEDIA_CONTENT_TYPES: dict[str, str] = {
    "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
    "gif": "image/gif", "bmp": "image/bmp", "tiff": "image/tiff",
    "wmf": "image/x-wmf", "emf": "image/x-emf",
}

# For subclasses: maps element-local-name → expected relationship kind.
_DEFAULT_REL_TYPES: dict[str, str] = {}


# ── Helper: extract local tag name ──────────────────────────────────

def _local_tag(tag: str) -> str:
    """``'{http://…}foo'`` → ``'foo'``; ``'foo'`` → ``'foo'``."""
    return tag.rsplit("}", 1)[-1]


# ── Base validator ───────────────────────────────────────────────────

class OfficeDocValidator:
    """Shared validation logic for OOXML packages.

    Subclasses **must** override :meth:`_build_check_pipeline` and call
    :meth:`run_pipeline` from their own :meth:`validate`.
    """

    ELEMENT_RELATIONSHIP_TYPES: dict[str, str] = _DEFAULT_REL_TYPES

    def __init__(
        self,
        unpacked_dir: str | Path,
        original_file: str | Path | None = None,
        verbose: bool = False,
    ) -> None:
        self.unpacked_dir = Path(unpacked_dir).resolve()
        self.original_file = Path(original_file) if original_file else None
        self.verbose = verbose
        self._schemas_dir = Path(__file__).parent.parent / "schemas"

        # Discover and cache XML file paths
        self.xml_files: list[Path] = sorted(
            f
            for pat in ("*.xml", "*.rels")
            for f in self.unpacked_dir.rglob(pat)
        )
        if not self.xml_files:
            print(f"Warning: No XML files found in {self.unpacked_dir}")

        # Lazy-populated parsed-tree cache (path → etree root)
        self._parsed_roots: dict[Path, lxml.etree._Element] = {}

    # ── Tree cache ───────────────────────────────────────────────

    def _root_of(self, path: Path) -> lxml.etree._Element:
        """Return the cached parsed root for *path* (parse on first call)."""
        if path not in self._parsed_roots:
            self._parsed_roots[path] = lxml.etree.parse(str(path)).getroot()
        return self._parsed_roots[path]

    def _drop_cache(self) -> None:
        self._parsed_roots.clear()

    # ── Pipeline driver ──────────────────────────────────────────

    def _build_check_pipeline(self) -> list[tuple[str, Callable[[], list[str]]]]:
        """Return ``[(check_name, callable), …]``.  Override in subclass."""
        raise NotImplementedError

    def run_pipeline(self) -> bool:
        """Execute every check returned by :meth:`_build_check_pipeline`.

        Prints diagnostics and returns ``True`` only when every check passes.
        """
        pipeline = self._build_check_pipeline()
        results: list[CheckResult] = []
        for name, fn in pipeline:
            problems = fn()
            results.append(CheckResult(name=name, problems=problems))

        all_ok = True
        for res in results:
            if res.ok:
                if self.verbose:
                    print(f"  OK  [{res.name}]")
            else:
                all_ok = False
                print(f"  FAIL [{res.name}] – {len(res.problems)} issue(s):")
                for line in res.problems:
                    print(f"       {line}")
        return all_ok

    def validate(self) -> bool:
        raise NotImplementedError

    # ── Repair helpers ───────────────────────────────────────────

    def repair(self) -> int:
        self._drop_cache()
        count = self._fix_hex_ids() + self._fix_whitespace_preserve()
        self._drop_cache()
        return count

    def _fix_hex_ids(self) -> int:
        """Replace overlong or non-hex paraId / durableId values."""
        repaired = 0
        valid_hex = re.compile(r"^[0-9A-Fa-f]{1,8}$")
        target_attrs = ("w14:paraId", "w16cid:durableId")

        for xml_path in self.xml_files:
            try:
                raw = xml_path.read_text(encoding="utf-8")
                dom = defusedxml.minidom.parseString(raw)
                changed = False
                for node in dom.getElementsByTagName("*"):
                    for attr in target_attrs:
                        if not node.hasAttribute(attr):
                            continue
                        val = node.getAttribute(attr)
                        if len(val) > 8 or not valid_hex.match(val):
                            replacement = f"{random.randint(0, 0x7FFFFFFE):08X}"
                            node.setAttribute(attr, replacement)
                            print(f"  Repaired: {xml_path.name}: {attr} {val} → {replacement}")
                            repaired += 1
                            changed = True
                if changed:
                    xml_path.write_bytes(dom.toxml(encoding="UTF-8"))
            except Exception:
                pass
        return repaired

    def _fix_whitespace_preserve(self) -> int:
        """Add ``xml:space='preserve'`` to text elements with edge whitespace."""
        repaired = 0
        for xml_path in self.xml_files:
            try:
                raw = xml_path.read_text(encoding="utf-8")
                dom = defusedxml.minidom.parseString(raw)
                changed = False
                for node in dom.getElementsByTagName("*"):
                    if not node.tagName.endswith(":t") or not node.firstChild:
                        continue
                    text = node.firstChild.nodeValue
                    if not text:
                        continue
                    if text[0] in (" ", "\t") or text[-1] in (" ", "\t"):
                        if node.getAttribute("xml:space") != "preserve":
                            node.setAttribute("xml:space", "preserve")
                            snippet = repr(text[:30]) + ("..." if len(text) > 30 else "")
                            print(f"  Repaired: {xml_path.name}: Added xml:space='preserve' to {node.tagName}: {snippet}")
                            repaired += 1
                            changed = True
                if changed:
                    xml_path.write_bytes(dom.toxml(encoding="UTF-8"))
            except Exception:
                pass
        return repaired

    # ── Individual checks (each returns a list of problem strings) ───

    def check_xml_syntax(self) -> list[str]:
        """Verify every XML file is well-formed."""
        issues: list[str] = []
        for xf in self.xml_files:
            try:
                lxml.etree.parse(str(xf))
            except lxml.etree.XMLSyntaxError as exc:
                issues.append(f"{xf.relative_to(self.unpacked_dir)}:{exc.lineno} – {exc.msg}")
            except Exception as exc:
                issues.append(f"{xf.relative_to(self.unpacked_dir)} – {exc}")
        return issues

    def check_ns_declarations(self) -> list[str]:
        """Ensure every mc:Ignorable prefix is actually declared."""
        issues: list[str] = []
        for xf in self.xml_files:
            try:
                root = self._root_of(xf)
                declared = set(root.nsmap.keys()) - {None}
                for val in (v for k, v in root.attrib.items() if k.endswith("Ignorable")):
                    for prefix in set(val.split()) - declared:
                        issues.append(f"{xf.relative_to(self.unpacked_dir)}: prefix '{prefix}' in Ignorable but undeclared")
            except lxml.etree.XMLSyntaxError:
                continue
        return issues

    def check_id_uniqueness(self) -> list[str]:
        """Detect duplicate IDs governed by :data:`ID_UNIQUENESS_RULES`."""
        issues: list[str] = []
        global_ids: dict[str, tuple] = {}
        inherited_dups = self._inherited_duplicate_ids()

        for xf in self.xml_files:
            try:
                root = lxml.etree.parse(str(xf)).getroot()
                per_file: dict[tuple, dict[str, int]] = {}

                # Strip mc:AlternateContent to avoid false-positive dups
                for ac in root.xpath(".//mc:AlternateContent", namespaces={"mc": NS_MARKUP_COMPAT}):
                    ac.getparent().remove(ac)

                for node in root.iter():
                    tag_lc = _local_tag(node.tag).lower()
                    if tag_lc not in ID_UNIQUENESS_RULES:
                        continue
                    if any(_local_tag(a.tag).lower() in _SKIP_ID_PARENTS for a in node.iterancestors()):
                        continue

                    attr_name, scope = ID_UNIQUENESS_RULES[tag_lc]
                    id_val = None
                    for a, v in node.attrib.items():
                        if _local_tag(a).lower() == attr_name:
                            id_val = v
                            break
                    if id_val is None:
                        continue

                    rel = xf.relative_to(self.unpacked_dir)
                    if scope == "global":
                        if id_val in global_ids:
                            pf, pl, pt = global_ids[id_val]
                            if (tag_lc, id_val) not in inherited_dups:
                                issues.append(
                                    f"{rel}:{node.sourceline} – global id '{id_val}' in <{tag_lc}> "
                                    f"conflicts with {pf}:{pl} <{pt}>"
                                )
                        else:
                            global_ids[id_val] = (rel, node.sourceline, tag_lc)
                    else:
                        bucket_key = (tag_lc, attr_name)
                        bucket = per_file.setdefault(bucket_key, {})
                        if id_val in bucket:
                            if (tag_lc, id_val, str(rel)) not in inherited_dups:
                                issues.append(
                                    f"{rel}:{node.sourceline} – duplicate {attr_name}='{id_val}' in <{tag_lc}> "
                                    f"(first at line {bucket[id_val]})"
                                )
                        else:
                            bucket[id_val] = node.sourceline
            except Exception as exc:
                issues.append(f"{xf.relative_to(self.unpacked_dir)} – {exc}")
        return issues

    def check_references(self) -> list[str]:
        """Verify .rels targets resolve and all content files are referenced."""
        issues: list[str] = []
        rels_files = list(self.unpacked_dir.rglob("*.rels"))
        if not rels_files:
            return issues

        content_files = {
            fp.resolve()
            for fp in self.unpacked_dir.rglob("*")
            if fp.is_file() and fp.name != "[Content_Types].xml" and not fp.name.endswith(".rels")
        }
        referenced: set[Path] = set()

        for rf in rels_files:
            try:
                rroot = lxml.etree.parse(str(rf)).getroot()
                base = rf.parent.parent if rf.name != ".rels" else self.unpacked_dir
                for rel in rroot.findall(f".//{{{NS_PKG_RELS}}}Relationship"):
                    target = rel.get("Target", "")
                    if not target or target.startswith(("http", "mailto:")):
                        continue
                    if target.startswith("/"):
                        resolved = self.unpacked_dir / target.lstrip("/")
                    elif rf.name == ".rels":
                        resolved = self.unpacked_dir / target
                    else:
                        resolved = base / target
                    try:
                        resolved = resolved.resolve()
                        if resolved.exists() and resolved.is_file():
                            referenced.add(resolved)
                        else:
                            issues.append(f"{rf.relative_to(self.unpacked_dir)}:{rel.sourceline} – broken target '{target}'")
                    except (OSError, ValueError):
                        issues.append(f"{rf.relative_to(self.unpacked_dir)}:{rel.sourceline} – broken target '{target}'")
            except Exception as exc:
                issues.append(f"{rf.relative_to(self.unpacked_dir)} – parse error: {exc}")

        for orphan in sorted(content_files - referenced):
            issues.append(f"unreferenced: {orphan.relative_to(self.unpacked_dir)}")

        if issues:
            issues.append(
                "CRITICAL: Broken references / orphaned files will corrupt the document."
            )
        return issues

    def check_content_types(self) -> list[str]:
        """Validate [Content_Types].xml coverage."""
        issues: list[str] = []
        ct_path = self.unpacked_dir / "[Content_Types].xml"
        if not ct_path.exists():
            return ["[Content_Types].xml not found"]

        try:
            ct_root = lxml.etree.parse(str(ct_path)).getroot()
            declared_parts: set[str] = set()
            declared_exts: set[str] = set()

            for ovr in ct_root.findall(f".//{{{NS_CONTENT_TYPES}}}Override"):
                pn = ovr.get("PartName")
                if pn:
                    declared_parts.add(pn.lstrip("/"))
            for dflt in ct_root.findall(f".//{{{NS_CONTENT_TYPES}}}Default"):
                ext = dflt.get("Extension")
                if ext:
                    declared_exts.add(ext.lower())

            for xf in self.xml_files:
                rel_str = str(xf.relative_to(self.unpacked_dir)).replace("\\", "/")
                if any(s in rel_str for s in (".rels", "[Content_Types]", "docProps/", "_rels/")):
                    continue
                try:
                    root_name = _local_tag(lxml.etree.parse(str(xf)).getroot().tag)
                    if root_name in _DECLARABLE_ROOT_TAGS and rel_str not in declared_parts:
                        issues.append(f"{rel_str}: <{root_name}> not in [Content_Types].xml")
                except Exception:
                    continue

            for fp in self.unpacked_dir.rglob("*"):
                if not fp.is_file():
                    continue
                if fp.suffix.lower() in (".xml", ".rels") or fp.name == "[Content_Types].xml":
                    continue
                if "_rels" in fp.parts or "docProps" in fp.parts:
                    continue
                ext = fp.suffix.lstrip(".").lower()
                if ext and ext not in declared_exts and ext in _MEDIA_CONTENT_TYPES:
                    issues.append(
                        f"{fp.relative_to(self.unpacked_dir)}: extension '.{ext}' undeclared "
                        f'(add <Default Extension="{ext}" ContentType="{_MEDIA_CONTENT_TYPES[ext]}"/>)'
                    )
        except Exception as exc:
            issues.append(f"[Content_Types].xml parse error: {exc}")
        return issues

    def check_xsd_conformance(self) -> list[str]:
        """Run XSD validation; only report *new* errors vs the original file."""
        issues: list[str] = []
        for xf in self.xml_files:
            ok, new_errs = self._xsd_check_single(xf)
            if ok is None or ok:
                continue
            rel = str(xf.relative_to(self.unpacked_dir))
            issues.append(f"{rel}: {len(new_errs)} new XSD error(s)")
            for msg in list(new_errs)[:3]:
                issues.append(f"  ↳ {msg[:250]}{'…' if len(msg) > 250 else ''}")
        return issues

    def check_relationship_ids(self) -> list[str]:
        """Cross-check r:id / r:embed / r:link against .rels entries."""
        issues: list[str] = []
        for xf in self.xml_files:
            if xf.suffix == ".rels":
                continue
            rf = xf.parent / "_rels" / f"{xf.name}.rels"
            if not rf.exists():
                continue

            try:
                rroot = lxml.etree.parse(str(rf)).getroot()
                rid_map: dict[str, str] = {}
                for rel in rroot.findall(f".//{{{NS_PKG_RELS}}}Relationship"):
                    rid = rel.get("Id")
                    rtype = rel.get("Type", "")
                    if not rid:
                        continue
                    if rid in rid_map:
                        issues.append(f"{rf.relative_to(self.unpacked_dir)}:{rel.sourceline} – duplicate rId '{rid}'")
                    rid_map[rid] = rtype.rsplit("/", 1)[-1] if "/" in rtype else rtype

                xroot = lxml.etree.parse(str(xf)).getroot()
                for node in xroot.iter():
                    for attr_suffix in ("id", "embed", "link"):
                        ref = node.get(f"{{{NS_OFFICE_RELS}}}{attr_suffix}")
                        if not ref:
                            continue
                        el_name = _local_tag(node.tag)
                        rel_path = xf.relative_to(self.unpacked_dir)
                        if ref not in rid_map:
                            sample = ", ".join(sorted(rid_map)[:5]) + ("…" if len(rid_map) > 5 else "")
                            issues.append(
                                f"{rel_path}:{node.sourceline} – <{el_name}> r:{attr_suffix}='{ref}' "
                                f"not in .rels (known: {sample})"
                            )
                        elif attr_suffix == "id" and self.ELEMENT_RELATIONSHIP_TYPES:
                            expected = self._expected_rel_kind(el_name)
                            if expected and expected not in rid_map[ref].lower():
                                issues.append(
                                    f"{rel_path}:{node.sourceline} – <{el_name}> '{ref}' → "
                                    f"'{rid_map[ref]}' but expected '{expected}'"
                                )
            except Exception as exc:
                issues.append(f"{xf.relative_to(self.unpacked_dir)} – {exc}")

        if issues:
            issues.append("Relationship ID mismatches will corrupt the document!")
        return issues

    # ── Internal helpers ─────────────────────────────────────────

    def _expected_rel_kind(self, element_name: str) -> str | None:
        low = element_name.lower()
        if low in self.ELEMENT_RELATIONSHIP_TYPES:
            return self.ELEMENT_RELATIONSHIP_TYPES[low]
        if low.endswith("id") and len(low) > 2:
            stem = low[:-2]
            return "slide" if stem == "sld" else stem
        if low.endswith("reference") and len(low) > 9:
            return low[:-9]
        return None

    def _resolve_schema(self, xml_path: Path) -> Path | None:
        name = xml_path.name
        if name in FILE_SCHEMA_MAP:
            return self._schemas_dir / FILE_SCHEMA_MAP[name]
        if xml_path.suffix == ".rels":
            return self._schemas_dir / FILE_SCHEMA_MAP[".rels"]
        s = str(xml_path)
        if "charts/" in s and name.startswith("chart"):
            return self._schemas_dir / FILE_SCHEMA_MAP["chart"]
        if "theme/" in s and name.startswith("theme"):
            return self._schemas_dir / FILE_SCHEMA_MAP["theme"]
        if xml_path.parent.name in _DOCUMENT_FOLDERS:
            return self._schemas_dir / FILE_SCHEMA_MAP[xml_path.parent.name]
        return None

    def _xsd_check_single(self, xml_path: Path) -> tuple[bool | None, set[str]]:
        xml_path = xml_path.resolve()
        ok, cur_errs = self._raw_xsd_validate(xml_path, self.unpacked_dir.resolve())
        if ok is None:
            return None, set()
        if ok:
            return True, set()
        baseline = self._original_xsd_errors(xml_path)
        assert cur_errs is not None
        novel = {e for e in cur_errs - baseline if not any(p in e for p in _XSD_ERROR_NOISE)}
        return (True, set()) if not novel else (False, novel)

    def _raw_xsd_validate(self, xml_path: Path, base: Path) -> tuple[bool | None, set[str] | None]:
        schema_path = self._resolve_schema(xml_path)
        if not schema_path:
            return None, None
        try:
            xsd_doc = lxml.etree.parse(str(schema_path), parser=lxml.etree.XMLParser(), base_url=str(schema_path))
            schema = lxml.etree.XMLSchema(xsd_doc)
            with open(xml_path, "r") as fh:
                doc = lxml.etree.parse(fh)
            doc, _ = self._strip_template_tags(doc)
            doc = self._drop_mc_ignorable_attr(doc)
            rp = xml_path.relative_to(base)
            if rp.parts and rp.parts[0] in _DOCUMENT_FOLDERS:
                doc = self._scrub_extension_namespaces(doc)
            if schema.validate(doc):
                return True, set()
            return False, {e.message for e in schema.error_log}
        except Exception as exc:
            return False, {str(exc)}

    def _original_xsd_errors(self, xml_path: Path) -> set[str]:
        if self.original_file is None:
            return set()
        rel = xml_path.relative_to(self.unpacked_dir.resolve())
        with tempfile.TemporaryDirectory() as td:
            tp = Path(td)
            with zipfile.ZipFile(self.original_file, "r") as zf:
                zf.extractall(tp)
            orig = tp / rel
            if not orig.exists():
                return set()
            _, errs = self._raw_xsd_validate(orig, tp)
            return errs or set()

    def _inherited_duplicate_ids(self) -> set[tuple]:
        """IDs already duplicated in the original file (baseline noise)."""
        dups: set[tuple] = set()
        if not self.original_file or not self.original_file.exists():
            return dups
        try:
            with tempfile.TemporaryDirectory() as td:
                tp = Path(td)
                with zipfile.ZipFile(self.original_file, "r") as zf:
                    zf.extractall(tp)
                global_seen: dict[str, bool] = {}
                for xf in tp.rglob("*.xml"):
                    try:
                        root = lxml.etree.parse(str(xf)).getroot()
                        file_seen: dict[tuple, dict] = {}
                        for node in root.iter():
                            tag_lc = _local_tag(node.tag).lower()
                            if tag_lc not in ID_UNIQUENESS_RULES:
                                continue
                            attr_name, scope = ID_UNIQUENESS_RULES[tag_lc]
                            id_val = None
                            for a, v in node.attrib.items():
                                if _local_tag(a).lower() == attr_name:
                                    id_val = v
                                    break
                            if id_val is None:
                                continue
                            if scope == "global":
                                if id_val in global_seen:
                                    dups.add((tag_lc, id_val))
                                else:
                                    global_seen[id_val] = True
                            else:
                                bk = (tag_lc, attr_name)
                                bucket = file_seen.setdefault(bk, {})
                                if id_val in bucket:
                                    dups.add((tag_lc, id_val, str(xf.relative_to(tp))))
                                else:
                                    bucket[id_val] = True
                    except Exception:
                        continue
        except Exception:
            pass
        return dups

    # ── XML preprocessing ────────────────────────────────────────

    def _strip_mc_elements(self, root):
        mc = NS_MARKUP_COMPAT
        ignorable = f"{{{mc}}}Ignorable"
        if ignorable in root.attrib:
            del root.attrib[ignorable]
        for node in root.iter():
            for a in [a for a in node.attrib if a.startswith(f"{{{mc}}}")]:
                del node.attrib[a]
        ac_tag = f"{{{mc}}}AlternateContent"
        fb_tag = f"{{{mc}}}Fallback"
        while True:
            hits = root.findall(f".//{ac_tag}")
            if not hits:
                break
            for ac in hits:
                parent = ac.getparent()
                if parent is None:
                    continue
                pos = list(parent).index(ac)
                for fb in ac.findall(fb_tag):
                    for ch in list(fb):
                        parent.insert(pos, ch)
                        pos += 1
                parent.remove(ac)
        return root

    def _scrub_extension_namespaces(self, doc):
        raw = lxml.etree.tostring(doc, encoding="unicode")
        copy = lxml.etree.fromstring(raw)
        for node in copy.iter():
            for a in [a for a in node.attrib if "{" in a and a.split("}")[0][1:] not in KNOWN_NAMESPACES]:
                del node.attrib[a]
        self._prune_unknown_ns_elements(copy)
        return lxml.etree.ElementTree(copy)

    def _prune_unknown_ns_elements(self, root):
        doomed = []
        for child in list(root):
            if not hasattr(child, "tag") or callable(child.tag):
                continue
            ts = str(child.tag)
            if ts.startswith("{") and ts.split("}")[0][1:] not in KNOWN_NAMESPACES:
                doomed.append(child)
            else:
                self._prune_unknown_ns_elements(child)
        for d in doomed:
            root.remove(d)

    def _drop_mc_ignorable_attr(self, doc):
        root = doc.getroot()
        key = f"{{{NS_MARKUP_COMPAT}}}Ignorable"
        if key in root.attrib:
            del root.attrib[key]
        return doc

    def _strip_template_tags(self, doc):
        warnings: list[str] = []
        pat = re.compile(r"\{\{[^}]*\}\}")
        raw = lxml.etree.tostring(doc, encoding="unicode")
        copy = lxml.etree.fromstring(raw)

        def _clean(text, label):
            if not text:
                return text
            hits = list(pat.finditer(text))
            if hits:
                for m in hits:
                    warnings.append(f"Template tag in {label}: {m.group()}")
                return pat.sub("", text)
            return text

        for node in copy.iter():
            if not hasattr(node, "tag") or callable(node.tag):
                continue
            ts = str(node.tag)
            if ts.endswith("}t") or ts == "t":
                continue
            node.text = _clean(node.text, "text")
            node.tail = _clean(node.tail, "tail")
        return lxml.etree.ElementTree(copy), warnings


if __name__ == "__main__":
    raise RuntimeError("This module should not be run directly.")
