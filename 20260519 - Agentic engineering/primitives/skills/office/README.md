# office

A pack of skills for working with Office files — building, editing, extracting, and verifying them from the command line.

---

## Contents

### Skills

#### `pptx`

Handles every stage of a `.pptx` workflow — from reading an existing deck, to building new slides from scratch, to visually verifying the result.

**What it helps you do:**

- Build a new deck programmatically using [pptxgenjs](https://gitbrent.github.io/PptxGenJS/)
- Edit an existing deck by unpacking the Open XML, making changes, and repacking
- Extract text, speaker notes, and tables from any `.pptx` file
- Render slides as images for visual QA
- Apply consistent slide design: color palettes, layout patterns, typography, and spacing

**How to choose your path:**

- **Editing an existing file or template** — uses the template-based editing path: unpack XML → modify → repack
- **Building a new deck with no reference file** — generates slides programmatically with pptxgenjs
- **Reading or extracting content** — pulls all text and notes as Markdown via `markitdown`

**Required dependencies:**

| Package | Install | Purpose |
|---------|---------|---------|
| markitdown | `pip install "markitdown[pptx]"` | Text extraction from `.pptx` files |
| Pillow | `pip install Pillow` | Thumbnail grid generation |
| pptxgenjs | `npm install -g pptxgenjs` | Programmatic slide creation |
| Microsoft PowerPoint | *(Windows desktop app, optional)* | Preferred slide-image rendering on Windows |
| LibreOffice | *(system package)* | Cross-platform fallback rendering |
| Poppler | *(system package)* | Splitting fallback PDFs into per-slide images |
