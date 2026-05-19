"""Purge unreferenced artefacts from an unpacked PPTX directory.

Usage:
    python clean.py <unpacked_dir>

Removes orphaned slides, stale relationship files, unused media /
embeddings / charts / diagrams / drawings / ink / tags, unreferenced
themes and notes slides, the [trash] folder, and stale Content_Types
overrides.  Iterates until nothing more can be removed.
"""

import re
import shutil
import sys
from pathlib import Path

import defusedxml.minidom

PPTX_RESOURCE_FOLDERS = (
    "media", "embeddings", "charts", "diagrams", "drawings", "ink", "tags",
)

RELS_WITH_SUB_RELS = ("charts", "diagrams", "drawings")


# ── reference helpers ────────────────────────────────────────────────────

def _targets_from_rels(rels_path: Path, base_dir: Path, root: Path) -> set[str]:
    """Parse one ``.rels`` file; return target paths relative to *root*."""
    hits: set[str] = set()
    try:
        dom = defusedxml.minidom.parse(str(rels_path))
    except Exception:
        return hits
    for rel in dom.getElementsByTagName("Relationship"):
        mode = rel.getAttribute("TargetMode")
        if mode and mode.lower() == "external":
            continue
        target = rel.getAttribute("Target")
        if not target:
            continue
        resolved = (root / target.lstrip("/") if target.startswith("/")
                     else (base_dir / target)).resolve()
        try:
            hits.add(str(resolved.relative_to(root.resolve())))
        except ValueError:
            pass
    return hits


def collect_references(unpacked: Path, *, scope: Path | None = None) -> set[str]:
    """Gather every file mentioned in ``.rels`` files.

    When *scope* is given, only ``.rels`` files under that subtree are
    examined; otherwise the whole *unpacked* tree is walked.
    """
    search_root = scope if scope is not None else unpacked
    refs: set[str] = set()
    for rfile in search_root.rglob("*.rels"):
        refs |= _targets_from_rels(rfile, rfile.parent.parent, unpacked)
    return refs


# ── individual cleanup passes ────────────────────────────────────────────

def find_active_slides(unpacked: Path) -> set[str]:
    """Return slide filenames present in ``<p:sldIdLst>``."""
    pres_path = unpacked / "ppt" / "presentation.xml"
    rels_path = unpacked / "ppt" / "_rels" / "presentation.xml.rels"
    if not pres_path.exists() or not rels_path.exists():
        return set()

    rels_dom = defusedxml.minidom.parse(str(rels_path))
    rid_map: dict[str, str] = {}
    for rel in rels_dom.getElementsByTagName("Relationship"):
        t = rel.getAttribute("Target")
        if t.startswith("slides/") and "slide" in rel.getAttribute("Type"):
            rid_map[rel.getAttribute("Id")] = Path(t).name

    pres_dom = defusedxml.minidom.parse(str(pres_path))
    active: set[str] = set()
    for node in pres_dom.getElementsByTagName("p:sldId"):
        rid = node.getAttribute("r:id")
        if rid in rid_map:
            active.add(rid_map[rid])
    return active


def purge_orphan_slides(unpacked: Path) -> list[str]:
    """Delete slide files not listed in ``<p:sldIdLst>``."""
    slides_dir = unpacked / "ppt" / "slides"
    if not slides_dir.exists():
        return []

    active = find_active_slides(unpacked)
    deleted: list[str] = []

    for sfile in sorted(slides_dir.glob("slide*.xml")):
        if sfile.name in active:
            continue
        rel = str(sfile.relative_to(unpacked))
        sfile.unlink()
        deleted.append(rel)
        companion = slides_dir / "_rels" / f"{sfile.name}.rels"
        if companion.exists():
            deleted.append(str(companion.relative_to(unpacked)))
            companion.unlink()

    # Scrub orphan entries from presentation.xml.rels
    pres_rels = unpacked / "ppt" / "_rels" / "presentation.xml.rels"
    if deleted and pres_rels.exists():
        dom = defusedxml.minidom.parse(str(pres_rels))
        changed = False
        for rel in list(dom.getElementsByTagName("Relationship")):
            t = rel.getAttribute("Target")
            if t.startswith("slides/") and Path(t).name not in active:
                rel.parentNode.removeChild(rel)
                changed = True
        if changed:
            pres_rels.write_bytes(dom.toxml(encoding="utf-8"))

    return deleted


def _wipe_trash(unpacked: Path) -> list[str]:
    """Remove the ``[trash]`` directory if present."""
    trash = unpacked / "[trash]"
    if not trash.is_dir():
        return []
    removed = [
        str(f.relative_to(unpacked)) for f in trash.rglob("*") if f.is_file()
    ]
    shutil.rmtree(trash, ignore_errors=True)
    return removed


def _prune_stale_sub_rels(unpacked: Path) -> list[str]:
    """Drop ``.rels`` under chart/diagram/drawing dirs when their parent
    resource is gone or no longer slide-referenced."""
    slide_refs = collect_references(
        unpacked, scope=unpacked / "ppt" / "slides" / "_rels"
    )
    norm = {str(Path(r)) for r in slide_refs}
    removed: list[str] = []

    for folder in RELS_WITH_SUB_RELS:
        rd = unpacked / "ppt" / folder / "_rels"
        if not rd.is_dir():
            continue
        for rf in sorted(rd.glob("*.rels")):
            resource = rd.parent / rf.stem  # strip .rels → resource name
            rp = str(Path("ppt") / folder / resource.name)
            if not resource.exists() or rp not in norm:
                removed.append(str(rf.relative_to(unpacked)))
                rf.unlink()
    return removed


def sweep_unused_files(unpacked: Path, referenced: set[str]) -> list[str]:
    """Delete files in resource / theme / notes directories that nobody
    points to via a ``.rels`` entry."""
    norm = {str(Path(r)) for r in referenced}
    removed: list[str] = []

    for folder in PPTX_RESOURCE_FOLDERS:
        d = unpacked / "ppt" / folder
        if not d.is_dir():
            continue
        for f in sorted(d.iterdir()):
            if f.is_file() and str(f.relative_to(unpacked)) not in norm:
                removed.append(str(f.relative_to(unpacked)))
                f.unlink()

    # Themes
    theme_dir = unpacked / "ppt" / "theme"
    if theme_dir.is_dir():
        for tf in sorted(theme_dir.glob("theme*.xml")):
            rp = str(tf.relative_to(unpacked))
            if rp not in norm:
                removed.append(rp)
                tf.unlink()
                tr = theme_dir / "_rels" / f"{tf.name}.rels"
                if tr.exists():
                    removed.append(str(tr.relative_to(unpacked)))
                    tr.unlink()

    # Notes slides
    notes_dir = unpacked / "ppt" / "notesSlides"
    if notes_dir.is_dir():
        for nf in sorted(notes_dir.glob("*.xml")):
            rp = str(nf.relative_to(unpacked))
            if rp not in norm:
                removed.append(rp)
                nf.unlink()
        nr = notes_dir / "_rels"
        if nr.is_dir():
            for rf in sorted(nr.glob("*.rels")):
                parent_xml = notes_dir / rf.name.replace(".rels", "")
                if not parent_xml.exists():
                    removed.append(str(rf.relative_to(unpacked)))
                    rf.unlink()

    return removed


def _sync_content_types(unpacked: Path, removed: list[str]) -> None:
    """Strip ``<Override>`` entries whose files were deleted."""
    ct = unpacked / "[Content_Types].xml"
    if not ct.exists() or not removed:
        return

    parts_gone = set()
    for r in removed:
        try:
            parts_gone.add("/" + str(Path(r)).replace("\\", "/"))
        except ValueError:
            pass

    dom = defusedxml.minidom.parse(str(ct))
    dirty = False
    for ov in list(dom.getElementsByTagName("Override")):
        if ov.getAttribute("PartName") in parts_gone:
            ov.parentNode.removeChild(ov)
            dirty = True
    if dirty:
        ct.write_bytes(dom.toxml(encoding="utf-8"))


# ── orchestrator ─────────────────────────────────────────────────────────

def run_cleanup(unpacked: Path) -> list[str]:
    """Execute all cleanup passes, iterating until stable."""
    all_removed: list[str] = []

    all_removed.extend(purge_orphan_slides(unpacked))
    all_removed.extend(_wipe_trash(unpacked))

    for _ in range(50):  # safety bound
        batch: list[str] = []
        batch.extend(_prune_stale_sub_rels(unpacked))
        refs = collect_references(unpacked)
        batch.extend(sweep_unused_files(unpacked, refs))
        if not batch:
            break
        all_removed.extend(batch)

    _sync_content_types(unpacked, all_removed)
    return all_removed


# ── CLI ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python clean.py <unpacked_dir>", file=sys.stderr)
        sys.exit(1)

    target = Path(sys.argv[1])
    if not target.is_dir():
        print(f"Error: directory not found: {target}", file=sys.stderr)
        sys.exit(1)

    gone = run_cleanup(target)
    if gone:
        print(f"Purged {len(gone)} file(s):")
        for entry in gone:
            print(f"  {entry}")
    else:
        print("Nothing to remove.")
