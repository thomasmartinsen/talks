"""Render PowerPoint slides as labelled grid thumbnails.

Converts a .pptx file into one or more JPEG contact-sheet images.
Each cell shows the slide image with its XML filename printed below.
Hidden slides are replaced by a hatched placeholder.

Usage:
    python thumbnail.py <pptx_file> [--output PREFIX] [--columns N]

Examples:
    python thumbnail.py deck.pptx
    python thumbnail.py deck.pptx --output overview --columns 4
"""

import argparse
import sys
import tempfile
import zipfile
from pathlib import Path

import defusedxml.minidom
from office.render_slides import render_slides_to_images as render_presentation_to_images
from PIL import Image, ImageDraw, ImageFont

CELL_WIDTH = 320
RENDER_DPI = 96
COLUMN_LIMIT = 8
COLUMN_DEFAULT = 3
OUTPUT_QUALITY = 92
PADDING = 16
STROKE_WIDTH = 1
LABEL_FONT_RATIO = 0.085
LABEL_GAP = 4


def read_slide_metadata(pptx_path: Path) -> list[dict]:
    """Return ordered list of ``{filename, hidden}`` dicts from the PPTX."""
    with zipfile.ZipFile(pptx_path, "r") as archive:
        rels_xml = archive.read("ppt/_rels/presentation.xml.rels").decode("utf-8")
        pres_xml = archive.read("ppt/presentation.xml").decode("utf-8")

    rels_dom = defusedxml.minidom.parseString(rels_xml)
    slide_by_rid: dict[str, str] = {}
    for node in rels_dom.getElementsByTagName("Relationship"):
        target = node.getAttribute("Target")
        if target.startswith("slides/") and "slide" in node.getAttribute("Type"):
            slide_by_rid[node.getAttribute("Id")] = target.rsplit("/", 1)[-1]

    pres_dom = defusedxml.minidom.parseString(pres_xml)
    entries: list[dict] = []
    for sld_node in pres_dom.getElementsByTagName("p:sldId"):
        rid = sld_node.getAttribute("r:id")
        filename = slide_by_rid.get(rid)
        if filename is not None:
            entries.append(
                {"filename": filename, "hidden": sld_node.getAttribute("show") == "0"}
            )
    return entries


def make_placeholder(dimensions: tuple[int, int]) -> Image.Image:
    """Create a hatched grey rectangle indicating a hidden slide."""
    img = Image.new("RGB", dimensions, color="#E8E8E8")
    draw = ImageDraw.Draw(img)
    w, h = dimensions
    step = max(20, min(dimensions) // 8)
    for offset in range(-h, w, step):
        draw.line([(offset, 0), (offset + h, h)], fill="#D0D0D0", width=2)
    return img


def map_slides_to_images(
    metadata: list[dict],
    page_images: list[Path],
    work_dir: Path,
) -> list[tuple[Path, str]]:
    """Pair each slide entry with a JPEG path and caption string."""
    if page_images:
        with Image.open(page_images[0]) as sample:
            dims = sample.size
    else:
        dims = (1280, 720)

    result: list[tuple[Path, str]] = []
    visible_pos = 0
    for entry in metadata:
        if entry["hidden"]:
            ph = make_placeholder(dims)
            ph_path = work_dir / f"ph_{entry['filename']}.jpg"
            ph.save(ph_path, "JPEG")
            result.append((ph_path, f"{entry['filename']} (hidden)"))
        elif visible_pos < len(page_images):
            result.append((page_images[visible_pos], entry["filename"]))
            visible_pos += 1
    return result


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Best-effort font loader: tries system fonts, then falls back."""
    for candidate in (
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "arial.ttf",
    ):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def assemble_grid(
    slides: list[tuple[Path, str]],
    cols: int,
    cell_w: int,
) -> Image.Image:
    """Compose one grid image with labels *below* each thumbnail."""
    if not slides:
        return Image.new("RGB", (1, 1), "white")

    with Image.open(slides[0][0]) as ref:
        aspect_ratio = ref.height / ref.width
    cell_h = int(cell_w * aspect_ratio)

    font_px = max(10, int(cell_w * LABEL_FONT_RATIO))
    font = _load_font(font_px)

    row_count = -(-len(slides) // cols)  # ceiling division
    total_w = PADDING + cols * (cell_w + PADDING)
    total_h = PADDING + row_count * (cell_h + font_px + LABEL_GAP + PADDING)

    canvas = Image.new("RGB", (total_w, total_h), "white")
    draw = ImageDraw.Draw(canvas)

    for idx, (img_path, caption) in enumerate(slides):
        r, c = divmod(idx, cols)
        origin_x = PADDING + c * (cell_w + PADDING)
        origin_y = PADDING + r * (cell_h + font_px + LABEL_GAP + PADDING)

        with Image.open(img_path) as thumb:
            thumb = thumb.resize((cell_w, cell_h), Image.Resampling.LANCZOS)
            canvas.paste(thumb, (origin_x, origin_y))

        if STROKE_WIDTH:
            draw.rectangle(
                [origin_x - 1, origin_y - 1,
                 origin_x + cell_w, origin_y + cell_h],
                outline="#999999", width=STROKE_WIDTH,
            )

        # Label centred below the thumbnail
        bbox = draw.textbbox((0, 0), caption, font=font)
        tw = bbox[2] - bbox[0]
        label_x = origin_x + (cell_w - tw) // 2
        label_y = origin_y + cell_h + LABEL_GAP
        draw.text((label_x, label_y), caption, fill="#333333", font=font)

    return canvas


def generate_thumbnails(
    slides: list[tuple[Path, str]],
    cols: int,
    cell_w: int,
    dest: Path,
) -> list[Path]:
    """Split slides across pages and write grid JPEGs.  Returns paths."""
    per_page = cols * max(cols, 4)
    pages: list[Path] = []

    chunks = [slides[i:i + per_page] for i in range(0, len(slides), per_page)]
    multi = len(chunks) > 1

    for page_num, chunk in enumerate(chunks, start=1):
        grid = assemble_grid(chunk, cols, cell_w)
        if multi:
            out = dest.with_stem(f"{dest.stem}-{page_num}")
        else:
            out = dest
        out.parent.mkdir(parents=True, exist_ok=True)
        grid.save(str(out), "JPEG", quality=OUTPUT_QUALITY)
        pages.append(out)

    return pages


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Render PowerPoint slides as labelled grid thumbnails.",
    )
    ap.add_argument("pptx_file", help="Path to the .pptx file")
    ap.add_argument("--output", default="thumbnails",
                     help="Output file prefix (default: thumbnails)")
    ap.add_argument("--columns", type=int, default=COLUMN_DEFAULT,
                     help=f"Grid columns (default {COLUMN_DEFAULT}, max {COLUMN_LIMIT})")
    args = ap.parse_args()

    src = Path(args.pptx_file)
    if not src.is_file() or src.suffix.lower() != ".pptx":
        print(f"Error: not a valid .pptx file: {src}", file=sys.stderr)
        sys.exit(1)

    cols = max(1, min(args.columns, COLUMN_LIMIT))
    out_path = Path(args.output if args.output.endswith(".jpg")
                    else f"{args.output}.jpg")

    try:
        metadata = read_slide_metadata(src)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            page_imgs = render_presentation_to_images(src, tmp_dir / "page")
            paired = map_slides_to_images(metadata, page_imgs, tmp_dir)

            if not paired:
                print("Error: presentation contains no slides", file=sys.stderr)
                sys.exit(1)

            written = generate_thumbnails(paired, cols, CELL_WIDTH, out_path)

        for p in written:
            print(p)

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
