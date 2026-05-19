# Editing Presentations

## PPTX Internals

A `.pptx` file is a ZIP archive of XML files and binary media. The files you will interact with most:

- **`ppt/presentation.xml`** — The deck manifest. Its `<p:sldIdLst>` element holds an ordered list of `<p:sldId>` entries that determines which slides exist and in what sequence.
- **`ppt/slides/slide{N}.xml`** — One file per slide. Text content lives in `<a:t>` elements, character formatting in `<a:rPr>` attributes, and paragraph structure in `<a:p>` / `<a:pPr>` elements.
- **`ppt/slides/_rels/slide{N}.xml.rels`** — Per-slide relationships linking to images, layouts, and other resources.
- **`ppt/slideLayouts/`** — Layout definitions from which slides inherit fonts, bullet styles, and spacing (unless overridden at the slide level).
- **`[Content_Types].xml`** — Package-wide registry. Every slide file must have an entry here.

This matters because structural edits (adding, removing, reordering slides) modify the manifest and registries, while content edits only touch individual slide files. The two categories of work must happen in separate, sequential phases.

---

## Structural Changes

Everything in this section modifies which slides exist or their order. **Finish all structural work before touching any slide content.** Mixing the two leads to dangling references and corrupt output.

### Inspect the Template

Render a visual inventory of the template deck:

```bash
python scripts/thumbnail.py template.pptx
```

Produces a `thumbnails.jpg` grid with each slide labeled by filename (e.g., `slide1.xml`). Defaults to 3 columns and 12 slides per image; decks with more slides generate multiple grids.

> `thumbnail.py` is for template analysis — choosing which layouts to reuse. For final visual QA after editing, render full-resolution images via `render_slides.py` (see SKILL.md). On Windows that path can use PowerPoint COM directly.

Then extract the text layer:

```bash
python -m markitdown template.pptx
```

Compare the grid against the markitdown output to build a map of slide number → layout type → placeholder text.

**Deliberately vary layouts.** Relying on a single layout throughout the deck is the most frequent quality failure. Scan the template for:

- Section dividers that mark topic transitions
- Stat or number callout slides for headline metrics
- Image-and-text pairings for narrative or explanatory content
- Quote or testimonial layouts for standout statements
- Multi-column grids (2- or 3-column) for comparisons or parallel items
- Icon rows or icon grids for listing capabilities or categories
- Full-bleed visuals with overlaid text for openers or emphasis

Assign each content section to the layout that serves it best. A conversion rate belongs on a stat callout, not in a bullet list. A client testimonial warrants a quote slide, not a body-text paragraph.

### Unpack

```bash
python scripts/office/unpack.py template.pptx unpacked/
```

Extracts the ZIP contents, pretty-prints every XML file for readability, and converts smart quotes to ASCII-safe escape sequences so the Edit tool can modify files without introducing encoding corruption.

### Modify the Slide List

> ⚠️ **Do this yourself — do not delegate to subagents.** These operations touch shared manifest files and must be performed sequentially to avoid conflicts.

Open `ppt/presentation.xml` and find `<p:sldIdLst>`. Each child `<p:sldId>` element corresponds to one slide.

**Removing slides:** Delete the target `<p:sldId>` element. The orphaned slide files are cleaned up later by `clean.py`.

**Duplicating slides:** Use `add_slide.py` for every copy:

```bash
python scripts/add_slide.py unpacked/ slide5.xml       # copy an existing slide
python scripts/add_slide.py unpacked/ slideLayout3.xml  # blank slide from a layout
```

The script outputs a `<p:sldId>` element — paste it into `<p:sldIdLst>` at the position where the new slide should appear. It also registers the slide in `[Content_Types].xml`, creates the necessary `.rels` entries, and links any notes slides. Never copy slide XML files manually; missing any of these registrations produces a file PowerPoint cannot open.

**Reordering slides:** Rearrange the `<p:sldId>` elements within `<p:sldIdLst>`. Their document order defines the presentation sequence.

---

## Content Editing

With the slide roster locked in, edit individual slide XML files under `ppt/slides/`. Each slide is an independent file, so **subagents can work on separate slides concurrently** without conflict.

When dispatching subagents, give them:

- The exact file path(s) for the slides they should modify
- The directive: **"Use the Edit tool for all changes"**
- The formatting guidance and warnings from this section

### Replacement Process

For every slide:

1. Read the complete XML.
2. Inventory every placeholder — titles, body copy, image alt text, chart data, icon captions, footer strings. Leave nothing unaccounted for.
3. Swap each placeholder for the final content, keeping the surrounding XML tags and their formatting attributes intact.

**Always use the Edit tool.** Avoid `sed`, `awk`, regex replacements, or Python XML-manipulation scripts for content changes — they routinely drop attributes or break element nesting.

### Handling Surplus Template Elements

Templates frequently contain more slots than your source material fills. A slide laid out for 5 service offerings when you only need 3 requires more than emptying the extra text boxes.

Delete the surplus elements in their entirety: the shape (`<p:sp>`), its parent group (`<p:grpSp>`) if one exists, any associated images, and decorative elements like connector lines or background shapes that accompanied the removed items. A text box with cleared content still occupies layout space and produces a visible gap.

Verify with visual QA that the remaining elements are visually balanced after removal.

### Text Length Mismatches

Shorter replacement text is generally harmless — the text box retains extra whitespace but renders correctly. Longer text risks overflowing the box, wrapping in unexpected places, or pushing elements off the slide edge.

When content exceeds the available space, split it across additional slides or condense it. Do not force verbose text into a compact template slot. Run visual QA after every round of text changes to catch overflow early.

### Multi-Item Content

Source material that contains a list — agenda topics, feature descriptions, quarterly results — must be encoded as separate `<a:p>` elements, one per entry. Concatenating all items into a single paragraph destroys readability and defeats PowerPoint's line-spacing calculations.

**Wrong** — everything in one paragraph:

```xml
<a:p>
  <a:r>
    <a:rPr lang="en-US" dirty="0"/>
    <a:t>Overview: Current market conditions Key Findings: Revenue grew 18% YoY Next Steps: Expand into APAC region</a:t>
  </a:r>
</a:p>
```

**Right** — individual paragraphs with bold labels:

```xml
<a:p>
  <a:pPr marL="0" indent="0">
    <a:lnSpc><a:spcPts val="2400"/></a:lnSpc>
    <a:buNone/>
  </a:pPr>
  <a:r>
    <a:rPr lang="en-US" b="1" dirty="0"/>
    <a:t>Overview</a:t>
  </a:r>
</a:p>
<a:p>
  <a:pPr marL="0" indent="0">
    <a:lnSpc><a:spcPts val="2400"/></a:lnSpc>
    <a:buNone/>
  </a:pPr>
  <a:r>
    <a:rPr lang="en-US" dirty="0"/>
    <a:t>Current market conditions and competitive landscape</a:t>
  </a:r>
</a:p>
<a:p>
  <a:pPr marL="0" indent="0">
    <a:lnSpc><a:spcPts val="2400"/></a:lnSpc>
    <a:buNone/>
  </a:pPr>
  <a:r>
    <a:rPr lang="en-US" b="1" dirty="0"/>
    <a:t>Key Findings</a:t>
  </a:r>
</a:p>
<a:p>
  <a:pPr marL="0" indent="0">
    <a:lnSpc><a:spcPts val="2400"/></a:lnSpc>
    <a:buNone/>
  </a:pPr>
  <a:r>
    <a:rPr lang="en-US" dirty="0"/>
    <a:t>Revenue grew 18% year over year across all segments</a:t>
  </a:r>
</a:p>
<a:p>
  <a:pPr marL="0" indent="0">
    <a:lnSpc><a:spcPts val="2400"/></a:lnSpc>
    <a:buNone/>
  </a:pPr>
  <a:r>
    <a:rPr lang="en-US" b="1" dirty="0"/>
    <a:t>Next Steps</a:t>
  </a:r>
</a:p>
<a:p>
  <a:pPr marL="0" indent="0">
    <a:lnSpc><a:spcPts val="2400"/></a:lnSpc>
    <a:buNone/>
  </a:pPr>
  <a:r>
    <a:rPr lang="en-US" dirty="0"/>
    <a:t>Expand operations into the APAC region</a:t>
  </a:r>
</a:p>
```

Copy the `<a:pPr>` from the original template paragraph to retain line spacing and indentation. Apply `b="1"` on `<a:rPr>` for entry labels.

### Formatting Rules

**Bold usage:** Set `b="1"` on the `<a:rPr>` element for all slide titles, in-slide section headers, and inline labels that open a line (e.g., "Timeline:", "Owner:", "Risk:").

**Bullet characters:** Never insert Unicode bullet symbols (•, ●, ▪) directly into text. They bypass PowerPoint's layout engine and create uneven alignment. Use `<a:buChar>` for custom bullets or `<a:buAutoNum>` for numbered lists.

**Bullet inheritance:** Let bullet style, color, size, and indentation cascade from the slide layout or master. Only override with `<a:buChar>` (to swap the character) or `<a:buNone>` (to suppress bullets entirely). Building bullet formatting from scratch creates visual inconsistency with the rest of the template.

### Smart Quote Encoding

The unpack/pack pipeline manages smart quotes transparently: `unpack.py` escapes them to ASCII-safe form and `pack.py` restores them. The Edit tool, however, writes plain ASCII quotes.

When inserting new text that should render as curly quotes, use XML character entities:

```xml
<a:t>the &#x201C;Proposal&#x201D; document</a:t>
```

| Character | Unicode | Entity |
|-----------|---------|--------|
| \u201c (left double quote) | U+201C | `&#x201C;` |
| \u201d (right double quote) | U+201D | `&#x201D;` |
| \u2018 (left single quote) | U+2018 | `&#x2018;` |
| \u2019 (right single quote) | U+2019 | `&#x2019;` |

### Whitespace in Text Elements

When an `<a:t>` element needs leading or trailing spaces — padding around a label, for instance — add `xml:space="preserve"`:

```xml
<a:t xml:space="preserve"> Revenue: </a:t>
```

Without this attribute, XML parsers may silently strip the surrounding spaces.

### XML Library Choice

For any custom XML manipulation, use `defusedxml.minidom`. Avoid `xml.etree.ElementTree` — it silently rewrites or drops namespace prefixes, corrupting the OpenXML structure and producing files PowerPoint cannot open.

---

## Packaging

Once all content edits are complete, finalize the deck:

```bash
python scripts/clean.py unpacked/
```

Scans `<p:sldIdLst>` and removes slide files not listed there, deletes media that no remaining slide references, and purges orphaned `.rels` entries.

```bash
python scripts/office/pack.py unpacked/ output.pptx --original template.pptx
```

Validates XML structure, repairs minor issues, collapses pretty-printed XML back to compact form, restores smart quotes from their ASCII escapes, and assembles the final `.pptx`. The `--original` flag copies binary resources (embedded fonts, OLE objects) from the source file that the unpacked directory does not contain.
