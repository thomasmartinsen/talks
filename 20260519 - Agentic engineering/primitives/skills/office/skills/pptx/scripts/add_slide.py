"""Add a slide to an unpacked PPTX directory (clone or from layout).

Subcommands:
    clone   <unpacked_dir> <slide_file>
        Copy an existing slide (e.g. slide2.xml) and register the duplicate.

    layout  <unpacked_dir> <layout_file>
        Create a blank slide linked to a slideLayout (e.g. slideLayout3.xml).

Both modes print the ``<p:sldId …/>`` element that must be inserted into
the ``<p:sldIdLst>`` inside ``ppt/presentation.xml``.

Examples:
    python add_slide.py clone  unpacked/ slide2.xml
    python add_slide.py layout unpacked/ slideLayout4.xml
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

from defusedxml.minidom import getDOMImplementation


# ── helpers ──────────────────────────────────────────────────────────────

def find_available_number(slides_dir: Path) -> int:
    """Scan ``slide*.xml`` in *slides_dir* and return the first unused number."""
    taken = {
        int(m.group(1))
        for f in slides_dir.glob("slide*.xml")
        if (m := re.match(r"slide(\d+)\.xml$", f.name))
    }
    n = 1
    while n in taken:
        n += 1
    return n


def next_id(unpacked_dir: Path) -> int:
    """Return ``max(existing sldId/@id) + 1``, or 256 when none exist."""
    pres = (unpacked_dir / "ppt" / "presentation.xml").read_text(encoding="utf-8")
    ids = [int(v) for v in re.findall(r'<p:sldId[^>]+\bid="(\d+)"', pres)]
    return max(ids) + 1 if ids else 256


def register_in_content_types(unpacked_dir: Path, slide_name: str) -> None:
    """Ensure ``[Content_Types].xml`` has an Override for the new slide."""
    ct_path = unpacked_dir / "[Content_Types].xml"
    xml_text = ct_path.read_text(encoding="utf-8")
    part = f"/ppt/slides/{slide_name}"
    if part in xml_text:
        return
    entry = (
        f'<Override PartName="{part}" '
        f'ContentType="application/vnd.openxmlformats-officedocument'
        f'.presentationml.slide+xml"/>'
    )
    xml_text = xml_text.replace("</Types>", f"  {entry}\n</Types>")
    ct_path.write_text(xml_text, encoding="utf-8")


def register_in_rels(unpacked_dir: Path, slide_name: str) -> str:
    """Add a Relationship for the new slide and return the assigned rId."""
    rels_path = unpacked_dir / "ppt" / "_rels" / "presentation.xml.rels"
    xml_text = rels_path.read_text(encoding="utf-8")

    used = {int(x) for x in re.findall(r'Id="rId(\d+)"', xml_text)}
    rid_num = 1
    while rid_num in used:
        rid_num += 1
    rid = f"rId{rid_num}"

    rel = (
        f'<Relationship Id="{rid}" '
        f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" '
        f'Target="slides/{slide_name}"/>'
    )
    xml_text = xml_text.replace("</Relationships>", f"  {rel}\n</Relationships>")
    rels_path.write_text(xml_text, encoding="utf-8")
    return rid


def _build_blank_slide_xml() -> str:
    """Programmatically construct a minimal slide XML document."""
    NS_P = "http://schemas.openxmlformats.org/presentationml/2006/main"
    NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
    NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

    impl = getDOMImplementation()
    doc = impl.createDocument(NS_P, "p:sld", None)
    root = doc.documentElement
    root.setAttribute("xmlns:a", NS_A)
    root.setAttribute("xmlns:r", NS_R)
    root.setAttribute("xmlns:p", NS_P)

    cSld = doc.createElementNS(NS_P, "p:cSld")
    spTree = doc.createElementNS(NS_P, "p:spTree")

    nvGrpSpPr = doc.createElementNS(NS_P, "p:nvGrpSpPr")
    cNvPr = doc.createElementNS(NS_P, "p:cNvPr")
    cNvPr.setAttribute("id", "1")
    cNvPr.setAttribute("name", "")
    nvGrpSpPr.appendChild(cNvPr)
    nvGrpSpPr.appendChild(doc.createElementNS(NS_P, "p:cNvGrpSpPr"))
    nvGrpSpPr.appendChild(doc.createElementNS(NS_P, "p:nvPr"))
    spTree.appendChild(nvGrpSpPr)

    grpSpPr = doc.createElementNS(NS_P, "p:grpSpPr")
    xfrm = doc.createElementNS(NS_A, "a:xfrm")
    for tag, attrs in [
        ("a:off", {"x": "0", "y": "0"}),
        ("a:ext", {"cx": "0", "cy": "0"}),
        ("a:chOff", {"x": "0", "y": "0"}),
        ("a:chExt", {"cx": "0", "cy": "0"}),
    ]:
        el = doc.createElementNS(NS_A, tag)
        for k, v in attrs.items():
            el.setAttribute(k, v)
        xfrm.appendChild(el)
    grpSpPr.appendChild(xfrm)
    spTree.appendChild(grpSpPr)

    cSld.appendChild(spTree)
    root.appendChild(cSld)

    clrMapOvr = doc.createElementNS(NS_P, "p:clrMapOvr")
    clrMapOvr.appendChild(doc.createElementNS(NS_A, "a:masterClrMapping"))
    root.appendChild(clrMapOvr)

    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + root.toxml()


def _build_slide_rels_xml(layout_filename: str) -> str:
    """Build a minimal .rels file pointing at *layout_filename*."""
    NS_PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
    NS_SL = ("http://schemas.openxmlformats.org/officeDocument/"
             "2006/relationships/slideLayout")

    impl = getDOMImplementation()
    doc = impl.createDocument(NS_PKG, "Relationships", None)
    root = doc.documentElement
    root.setAttribute("xmlns", NS_PKG)

    rel = doc.createElement("Relationship")
    rel.setAttribute("Id", "rId1")
    rel.setAttribute("Type", NS_SL)
    rel.setAttribute("Target", f"../slideLayouts/{layout_filename}")
    root.appendChild(rel)

    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + root.toxml()


# ── subcommands ──────────────────────────────────────────────────────────

def new_slide_from_layout(unpacked_dir: Path, layout_file: str) -> None:
    """Create a blank slide that references the given layout."""
    layout_path = unpacked_dir / "ppt" / "slideLayouts" / layout_file
    if not layout_path.exists():
        print(f"Error: layout not found: {layout_path}", file=sys.stderr)
        sys.exit(1)

    slides_dir = unpacked_dir / "ppt" / "slides"
    slides_dir.mkdir(parents=True, exist_ok=True)
    num = find_available_number(slides_dir)
    dest = f"slide{num}.xml"

    (slides_dir / dest).write_text(_build_blank_slide_xml(), encoding="utf-8")

    rels_dir = slides_dir / "_rels"
    rels_dir.mkdir(parents=True, exist_ok=True)
    (rels_dir / f"{dest}.rels").write_text(
        _build_slide_rels_xml(layout_file), encoding="utf-8"
    )

    register_in_content_types(unpacked_dir, dest)
    rid = register_in_rels(unpacked_dir, dest)
    sid = next_id(unpacked_dir)

    print(f"Created {dest} from layout {layout_file}")
    print(f'<p:sldId id="{sid}" r:id="{rid}"/>')


def clone_slide(unpacked_dir: Path, source_file: str) -> None:
    """Duplicate *source_file* as a new slide, stripping notes references."""
    slides_dir = unpacked_dir / "ppt" / "slides"
    src = slides_dir / source_file
    if not src.exists():
        print(f"Error: slide not found: {src}", file=sys.stderr)
        sys.exit(1)

    num = find_available_number(slides_dir)
    dest = f"slide{num}.xml"
    shutil.copy2(src, slides_dir / dest)

    src_rels = slides_dir / "_rels" / f"{source_file}.rels"
    if src_rels.exists():
        rels_text = src_rels.read_text(encoding="utf-8")
        rels_text = re.sub(
            r'\s*<Relationship[^>]*Type="[^"]*notesSlide"[^>]*/>', "", rels_text
        )
        dst_rels = slides_dir / "_rels" / f"{dest}.rels"
        dst_rels.parent.mkdir(parents=True, exist_ok=True)
        dst_rels.write_text(rels_text, encoding="utf-8")

    register_in_content_types(unpacked_dir, dest)
    rid = register_in_rels(unpacked_dir, dest)
    sid = next_id(unpacked_dir)

    print(f"Created {dest} from {source_file}")
    print(f'<p:sldId id="{sid}" r:id="{rid}"/>')


# ── CLI ──────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add a slide to an unpacked PPTX directory.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_clone = sub.add_parser("clone", help="Duplicate an existing slide")
    p_clone.add_argument("unpacked_dir", type=Path, help="Unpacked PPTX directory")
    p_clone.add_argument("slide", help="Source slide file (e.g. slide2.xml)")

    p_layout = sub.add_parser("layout", help="Create a slide from a layout")
    p_layout.add_argument("unpacked_dir", type=Path, help="Unpacked PPTX directory")
    p_layout.add_argument("layout_file", help="Layout file (e.g. slideLayout3.xml)")

    args = parser.parse_args()

    if not args.unpacked_dir.is_dir():
        print(f"Error: '{args.unpacked_dir}' is not a directory", file=sys.stderr)
        sys.exit(1)

    if args.command == "clone":
        clone_slide(args.unpacked_dir, args.slide)
    else:
        new_slide_from_layout(args.unpacked_dir, args.layout_file)


if __name__ == "__main__":
    main()
