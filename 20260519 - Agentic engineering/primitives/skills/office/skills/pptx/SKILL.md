---
name: pptx
description: "Activate this skill whenever a .pptx file is part of the workflow — whether the task is building a new deck, extracting or reviewing content from an existing one, modifying slides, or merging presentations. Covers pitch decks, reports, templates, speaker notes, and any scenario where the user refers to \"slides,\" \"deck,\" \"presentation,\" or a .pptx filename. If the task touches a PowerPoint file in any capacity, this is the right skill."
---

# Working with PowerPoint Files

This guide walks you through every stage of a .pptx workflow — from inspecting what's already in a deck, to building new slides, to verifying the final output looks right. Companion references cover the mechanical details: [editing.md](editing.md) for template-based work and [pptxgenjs.md](pptxgenjs.md) for blank-canvas creation.

---

## How to Choose Your Workflow

**Starting from an existing file or template?** Follow the template-based editing path: generate thumbnails, unpack the XML, make your changes, repack. Full walkthrough in [editing.md](editing.md).

**Building a brand-new deck with no reference file?** Use pptxgenjs to generate slides programmatically. See [pptxgenjs.md](pptxgenjs.md) for the complete API guide. Define helper functions for repeated elements (e.g., `addFooter(slide)`, `addTopAccent(slide, color)`) to enforce visual consistency across every slide and avoid copy-paste drift.

**Just need to read or extract content?** Jump to [Inspecting & Extracting Content](#inspecting--extracting-content) below.

---

## Inspecting & Extracting Content

Three tools cover different levels of inspection:

**Pull out all text** (slide content, speaker notes, tables) as Markdown:

```bash
python -m markitdown deck.pptx
```

**Generate a visual thumbnail grid** to see every slide at a glance:

```bash
python scripts/thumbnail.py deck.pptx
```

**Drill into the raw Open XML** when you need to understand shape positions, relationships, or layout internals:

```bash
python scripts/office/unpack.py deck.pptx deck_unpacked/
```

These same commands are also the first step in QA — see [Verifying Your Output](#verifying-your-output).

---

## Rendering Slides as Images

You'll need slide images for visual QA. Prefer the bundled renderer instead of chaining platform-specific commands by hand:

```bash
python scripts/office/render_slides.py result.pptx page
```

The output will be `page-01.jpg`, `page-02.jpg`, etc. — written directly into the current folder, alongside your `.pptx`. **Keep the rendered images and the PDF in your outputs folder as delivery evidence.**

On Windows, `render_slides.py` first tries PowerPoint COM export because it is the most reliable way to get slide images from a local Office install. If PowerPoint is unavailable, it falls back to LibreOffice + `pdftoppm` when those tools are installed. If neither is available, surface that blocker explicitly rather than claiming visual QA happened.

To re-render only slide 3 after a targeted fix:

```bash
python scripts/office/render_slides.py result.pptx page --first-slide 3 --last-slide 3
```

---

## Slide Design Playbook

Slides that are just bullet points on white backgrounds communicate nothing about craft or effort. Every slide should feel intentionally designed. Use the guidance below to make that happen.

### Choosing a Color Palette

Your colors should feel like they belong to this specific presentation. A good test: if you could drop the same palette into an unrelated deck and it would still fit, your palette isn't specific enough.

**Structure your palette with hierarchy.** One dominant color carries 60–70% of the visual weight. One or two secondary tones provide contrast and variety. A single accent color draws the eye to key elements. Giving all colors equal presence makes the deck feel flat and uncommitted.

**Use dark and light strategically.** A common approach: dark backgrounds on the opening and closing slides, lighter tones for content-heavy middle slides. Alternatively, go dark throughout for a polished, high-end aesthetic.

**Anchor the deck with a recurring visual motif.** Choose one signature design element — circular image masks, tinted icon badges, bold left-edge borders — and use it consistently on every slide. This creates cohesion without monotony.

Here are ten curated palettes to start from. Adjust hex values freely to fit your content:

| Palette | Base | Support | Highlight |
|---------|------|---------|-----------|
| **Espresso Board** | `3E2723` (dark brown) | `D7CCC8` (warm gray) | `FF8F00` (amber) |
| **Arctic Horizon** | `0D47A1` (deep blue) | `BBDEFB` (sky) | `E3F2FD` (ice) |
| **Sandstone Dusk** | `8D6E63` (taupe) | `EFEBE9` (linen) | `C62828` (brick red) |
| **Electric Mint** | `00695C` (deep teal) | `B2DFDB` (mint) | `212121` (charcoal) |
| **Plum Noir** | `4A148C` (deep purple) | `CE93D8` (lavender) | `F3E5F5` (pale lilac) |
| **Burnt Sienna** | `BF360C` (rust) | `FBE9E7` (blush) | `33691E` (olive) |
| **Storm Cloud** | `455A64` (blue-gray) | `CFD8DC` (silver) | `FF6F00` (tangerine) |
| **Jade & Ivory** | `1B5E20` (hunter green) | `F1F8E9` (pale sage) | `827717` (dark lime) |
| **Copper Luxe** | `4E342E` (dark cocoa) | `BCAAA4` (mocha cream) | `E65100` (copper) |
| **Nordic Fjord** | `263238` (ink) | `90A4AE` (steel) | `80CBC4` (seafoam) |

### Layouts That Work

Variety keeps a deck engaging. Rotate through these patterns rather than repeating one layout:

- **Split composition** — content on one half, a large image or illustration bleeding to the edge on the other
- **Card grid** — a 2×2 or 2×3 arrangement of content blocks, each with an icon or image header
- **Icon roster** — a row or column of items where each has an icon badge, a bold label, and a short description
- **Hero stat** — one or two oversized numbers (60–72pt) with compact labels underneath, ideal for data callouts
- **Dashboard hybrid** — hero stat callouts in the upper half with a bar or line chart below; shows current values *and* historical trend on one slide; strongly recommended for traction and metrics slides
- **Comparison strip** — two or three parallel columns for before/after, options, or pros/cons
- **Process sequence** — numbered steps connected by arrows or a horizontal timeline

### Typography Guidelines

Default fonts like Arial signal zero design effort. Pair a heading font that has visual weight with a clean, readable body font:

| Heading | Body | Character |
|---------|------|-----------|
| Rockwell | Segoe UI | Sturdy, editorial |
| Constantia | Corbel | Classic, warm |
| Franklin Gothic Medium | Garamond | Bold contrast, elegant body |
| Lucida Sans | Book Antiqua | Modern heading, traditional body |
| Century Gothic | Calibri Light | Geometric, airy |
| Candara | Cambria | Friendly, scholarly |

**Sizing hierarchy matters.** The audience should instantly see what's a title, what's a section label, and what's body copy. Use a minimum 2:1 ratio between title and body size:

- Slide titles: **36–48pt**, always bold
- Section labels within a slide: **22–28pt**, bold or semi-bold
- Body copy: **15–18pt**
- Footnotes, captions, source lines: **10–12pt**, use a muted color

### Spacing & Margins

- Keep at least **0.5 inches** of clear space between content and slide edges
- Use **0.3–0.5 inches** of consistent gaps between content blocks — pick one value and stick with it throughout
- White space is a feature, not wasted space; resist the urge to fill every corner

### Design Checklist

Run through this list before finalizing any deck. These issues are ordered from hardest to notice (so you check them first) to most obvious:

1. **Text box padding misalignment** — Shapes or lines placed at the same x/y as a text box won't visually align because text boxes have internal margin. Set `margin: 0` on the text box or offset decorative elements to compensate.
2. **Low contrast on secondary elements** — Body text contrast is usually fine, but icons, captions, and border lines are often too subtle. Test every non-text element against its background.
3. **Inconsistent gap sizes** — If gaps between elements vary (0.2" here, 0.5" there) the slide feels haphazard. Commit to a single spacing unit (e.g., 0.4") and use multiples of it throughout the deck.
4. **All-centered paragraph text** — Center-aligning titles is fine; center-aligning body text, lists, or multi-line descriptions makes them harder to scan. Left-align all body content.
5. **Decorative underlines on titles** — Thin lines beneath headings are a strong signal of auto-generated content. Use background color shifts, generous whitespace, or subtle shape borders instead.
6. **Flat size hierarchy** — Titles, subtitles, and body text should be visually distinct at a glance. Aim for a 2:1+ ratio between heading and body font sizes.
7. **Monotonous slide structure** — Using the same layout for every slide is the fastest way to lose an audience. Alternate between split, grid, stat, and comparison patterns.
8. **Half-designed decks** — Starting strong with richly styled opening slides and then dropping to plain bullet slides in the middle is worse than being consistently simple. Match the effort level across every slide.
9. **No visual anchor on any slide** — Every slide benefits from at least one non-text element: an icon, shape, image, chart, or colored block. Pure text slides are skimmable and forgettable.
10. **Overcrowded slides** — Resist filling every inch. If content doesn't fit comfortably with 0.5" margins and breathing room between blocks, split it across two slides.
11. **Emoji icons** — Emoji rendering varies across PowerPoint versions and platforms. Use pptxgenjs shapes (`ShapeType.ellipse` as icon badges, colored `addShape` blocks) or plain Unicode symbols (`▶ ✓ •`) instead of emoji characters.

---

## Verifying Your Output

Every deck needs two rounds of verification before it's done: one for content accuracy, one for visual correctness. Skipping either one is how broken slides get delivered.

### Step 1: Content Check

Extract the text and scan for problems:

```bash
python -m markitdown result.pptx
```

Look for missing slides, incorrect ordering, typos, or duplicated content.

If the deck was built from a template, hunt for leftover placeholder text that didn't get replaced:

```powershell
python -m markitdown result.pptx | Select-String -Pattern "lorem|ipsum|xxxx|placeholder|sample.*(text|title)"
```

Any matches mean there's unfinished work.

### Step 2: Visual Inspection

**⚠️ Always delegate visual review to a subagent.** After writing the slide code, you are primed to see what you intended, not what actually rendered. A fresh pair of eyes catches problems you will miss, even on a two-slide deck.

First, render the slides as images (see [Rendering Slides as Images](#rendering-slides-as-images)). On Windows, prefer the bundled renderer because it can use PowerPoint COM directly. If slide rendering is blocked because neither PowerPoint nor LibreOffice is available, surface that blocker explicitly in `user_notes.md` instead of claiming visual QA happened. Then hand the images to a subagent with this prompt template:

```
Review these slide images critically. Your goal is to find every
visual defect — assume problems exist and look until you find them.

Check each slide for:
- Text clipping: content cut off by slide edges or container boundaries
- Overlap: text running through shapes, icons stacked on each other,
  footers colliding with body content
- Layout problems: columns misaligned, uneven spacing between cards,
  one section cramped while another has excessive empty space
- Margin violations: content closer than 0.5" from any slide edge
- Contrast issues: text hard to read against its background, icons
  that vanish into dark or light surfaces
- Wrapping artifacts: text boxes too narrow causing single words on
  their own line, or decorative elements sized for one line of text
  but the title wraps to two
- Stale content: any placeholder text, template labels, or "Lorem
  ipsum" fragments

Slide images to analyze:
- slides/page-01.jpg — [describe what this slide should show]
- slides/page-02.jpg — [describe what this slide should show]

List every issue you find per slide, even cosmetic ones.
```

### Step 3: Fix-and-Recheck Cycle

After identifying problems:

1. Fix the issues in your slide code
2. Re-render **all** slides (not just the ones you changed) — a fix on one slide frequently causes misalignment on another
3. Inspect the re-rendered slides with a fresh subagent pass. A re-check counts only when all slides are inspected in the same round; a partial pass (e.g. slide 3 only) does not count as a complete iteration
4. Repeat until a full inspection pass finds nothing new

**You must complete at least one full fix-and-verify iteration.** A deck that was only generated and never corrected is not finished.

### Deliverables Checklist

Before declaring the task done, confirm all of these exist in your outputs folder:

- `generate.js` (or equivalent script)
- `result.pptx`
- `result.pdf` (produced during the rendering step — keep it as evidence)
- `page-01.jpg` … `page-NN.jpg` (rendered slide images, in the outputs root — **not** in a subdirectory)

---

## Required Dependencies

| Package | Install | Purpose |
|---------|---------|---------|
| markitdown | `pip install "markitdown[pptx]"` | Text extraction from .pptx files |
| Pillow | `pip install Pillow` | Thumbnail grid generation |
| pptxgenjs | `npm install -g pptxgenjs` | Programmatic slide creation |
| Microsoft PowerPoint | (Windows desktop app, optional) | Preferred slide-image rendering on Windows via `scripts/office/render_slides.py` |
| LibreOffice | (system package) | Cross-platform fallback rendering, managed by `scripts/office/soffice.py` and `scripts/office/render_slides.py` |
| Poppler | (system package, provides `pdftoppm`) | Splitting fallback PDFs into per-slide images |
