# PptxGenJS — Practical Reference

> Generate `.pptx` files from JavaScript. Every coordinate is in **inches**; every color is a **6-character hex string without `#`**.

---

## Your First Slide

Start every presentation by creating a *fresh* `pptxgen` instance, adding at least one slide, and writing the file.

```js
const PptxGenJS = require("pptxgenjs");

const deck = new PptxGenJS();
deck.author = "DevOps Team";
deck.title  = "Infrastructure Report";
deck.layout = "LAYOUT_16x9";

const intro = deck.addSlide();
intro.background = { color: "FAFAFA" };

intro.addText("Infrastructure Health — May 2025", {
  x: 1, y: 2, w: 8, h: 1.5,
  fontSize: 28, fontFace: "Segoe UI", color: "0F172A",
  bold: true, align: "center", valign: "middle",
});

deck.writeFile({ fileName: "infra-report.pptx" });
```

> ⚠️ **One instance = one file.** The object accumulates slides and metadata. Instantiate a new `PptxGenJS()` for every output file to avoid merged or corrupt results.

---

## Backgrounds

Set `slide.background` to a color or image before adding content.

```js
// Flat color
intro.background = { color: "1E293B" };

// Semi-transparent color
intro.background = { color: "7C3AED", transparency: 70 };

// Full-bleed image
intro.background = { path: "https://cdn.example.com/dark-gradient.jpg" };

// Base64 image (no network call)
intro.background = { data: "data:image/png;base64,iVBORw0KGgo..." };
```

---

## Text & Rich Formatting

### Placing a heading

```js
intro.addText("Cluster Overview", {
  x: 0.5, y: 0.4, w: 9, h: 0.7,
  fontSize: 22, fontFace: "Calibri", color: "1E293B",
  bold: true, align: "left", valign: "middle",
});
```

### Inline mixed styles

Pass an array of `{ text, options }` objects to combine different formatting in a single text box:

```js
intro.addText([
  { text: "Uptime: ",  options: { fontSize: 14, color: "475569" } },
  { text: "99.97 %",   options: { fontSize: 14, color: "16A34A", bold: true } },
  { text: " (target ≥ 99.9 %)", options: { fontSize: 12, color: "94A3B8", italic: true } },
], { x: 0.5, y: 1.4, w: 9, h: 0.4 });
```

### Separate lines with `breakLine`

Without `breakLine: true` on every item except the last, all segments render on the same line.

```js
intro.addText([
  { text: "Region: us-east-1", options: { fontSize: 12, breakLine: true } },
  { text: "Nodes: 24",         options: { fontSize: 12, breakLine: true } },
  { text: "Pods running: 187", options: { fontSize: 12 } },
], { x: 0.5, y: 2.2, w: 5, h: 1.2 });
```

### Character spacing

Spread letters apart with `charSpacing` (points). The CSS-like property `letterSpacing` does **not** exist in PptxGenJS and is silently ignored.

```js
intro.addText("SYSTEM STATUS", {
  x: 0.5, y: 0.2, w: 4, h: 0.4,
  fontSize: 11, charSpacing: 5, color: "64748B",
});
```

### Internal margin

Text boxes carry default internal padding. Set `margin: 0` when you need the text edge to align precisely with adjacent shapes.

`margin` also accepts a four-element array `[top, right, bottom, left]` in points.

---

## Lists & Bullets

Each list item needs `bullet: true` plus `breakLine: true` (except the last item).

```js
const statusSlide = deck.addSlide();

statusSlide.addText([
  { text: "All nodes healthy",        options: { bullet: true, breakLine: true } },
  { text: "TLS certificates renewed", options: { bullet: true, breakLine: true } },
  { text: "Backup verified at 03:00", options: { bullet: true } },
], { x: 0.8, y: 1.0, w: 8, h: 2, fontSize: 13, color: "334155" });
```

> ❌ Never prepend `"• "` yourself — PptxGenJS already renders a bullet glyph, so you get **double bullets**.

**Nested items** — increase `indentLevel`:

```js
{ text: "Certificate details", options: { bullet: true, indentLevel: 1, breakLine: true } }
```

**Numbered lists** — swap in `{ type: "number" }`:

```js
{ text: "Stop old pods",  options: { bullet: { type: "number" }, breakLine: true } }
{ text: "Apply manifest",  options: { bullet: { type: "number" }, breakLine: true } }
{ text: "Verify rollout",  options: { bullet: { type: "number" } } }
```

> Use `paraSpaceAfter` (e.g., `8`) to control vertical spacing between bullets. Avoid `lineSpacing` — it inflates gaps unpredictably with bulleted text.

---

## Shapes

Shapes are accessed via `pres.ShapeType`. The most common members:

| Enum value    | Constant equivalent     | Typical use            |
|---------------|-------------------------|------------------------|
| `.rect`       | `RECTANGLE`             | Panels, cards, bars    |
| `.ellipse`    | `OVAL`                  | Badges, decorations    |
| `.line`       | `LINE`                  | Separators, connectors |
| `.roundRect`  | `ROUNDED_RECTANGLE`     | Soft-corner cards      |

### Rectangles, ovals, and lines

```js
// Solid panel
statusSlide.addShape(deck.ShapeType.rect, {
  x: 0.4, y: 0.4, w: 4.5, h: 2.5,
  fill: { color: "EEF2FF" },
  line: { color: "6366F1", width: 1 },
});

// Circle badge
statusSlide.addShape(deck.ShapeType.ellipse, {
  x: 7, y: 1, w: 1.2, h: 1.2,
  fill: { color: "DCFCE7" },
});

// Dashed separator
statusSlide.addShape(deck.ShapeType.line, {
  x: 0.4, y: 3.4, w: 9.2, h: 0,
  line: { color: "CBD5E1", width: 0.75, dashType: "lgDash" },
});
```

Available `dashType` values: `"solid"`, `"dash"`, `"dot"`, `"dashDot"`, `"lgDash"`, `"lgDashDot"`, `"sysDash"`, `"sysDot"`.

### Transparency and rounded corners

```js
// 40% transparent overlay
statusSlide.addShape(deck.ShapeType.rect, {
  x: 0, y: 0, w: 10, h: 5.625,
  fill: { color: "0F172A", transparency: 40 },
});

// Rounded card
statusSlide.addShape(deck.ShapeType.roundRect, {
  x: 1, y: 1, w: 3.5, h: 2,
  fill: { color: "FFFFFF" }, rectRadius: 0.15,
});
```

> ⚠️ If you overlay a straight-edged accent bar on a `roundRect`, the bar won't cover the rounded corners — use `rect` instead when you need flush accent overlays.

### Shadows

```js
statusSlide.addShape(deck.ShapeType.rect, {
  x: 2, y: 1.5, w: 6, h: 3,
  fill: { color: "FFFFFF" },
  shadow: {
    type: "outer", color: "000000",
    blur: 8, offset: 4, angle: 225, opacity: 0.2,
  },
});
```

**Shadow property reference:**

| Property  | Type / range          | Gotchas                                                        |
|-----------|-----------------------|----------------------------------------------------------------|
| `type`    | `"outer"` or `"inner"` |                                                               |
| `color`   | 6-char hex            | No `#`. No 8-char hex (corrupts file — use `opacity` instead) |
| `blur`    | 0–100 pt              |                                                                |
| `offset`  | 0–200 pt              | **Negative values corrupt the file.** Use `angle: 270` for upward shadows |
| `angle`   | 0–359°                | 225 = bottom-left, 270 = upward, 315 = bottom-right           |
| `opacity` | 0.0–1.0               | The *only* way to make a shadow translucent                    |

### Gradient fills

PptxGenJS has no native gradient fill API. Workaround: use a pre-rendered gradient PNG as a slide or shape background image.

---

## Images

Three source types — local path, URL, or base64 data URI:

```js
// Local file
statusSlide.addImage({ path: "assets/diagram.png", x: 0.5, y: 0.5, w: 4, h: 2.5 });

// Remote URL
statusSlide.addImage({ path: "https://cdn.example.com/arch.png", x: 5, y: 0.5, w: 4, h: 2.5 });

// Base64 (no I/O, fastest)
statusSlide.addImage({ data: "data:image/png;base64,iVBORw0KGgo...", x: 0.5, y: 3.5, w: 3, h: 1.5 });
```

### Optional properties

| Property       | Type      | Description                              |
|----------------|-----------|------------------------------------------|
| `rotate`       | 0–359     | Clockwise rotation in degrees            |
| `rounding`     | boolean   | Circular crop                            |
| `transparency` | 0–100     | Image opacity                            |
| `flipH`        | boolean   | Mirror horizontally                      |
| `flipV`        | boolean   | Mirror vertically                        |
| `altText`      | string    | Accessibility description                |
| `hyperlink`    | object    | `{ url: "..." }` or `{ slide: N }`      |

### Sizing modes

| Mode        | Behaviour                                    | Example                                                           |
|-------------|----------------------------------------------|-------------------------------------------------------------------|
| `contain`   | Fit inside bounds, keep ratio (may letterbox) | `sizing: { type: "contain", w: 5, h: 3 }`                       |
| `cover`     | Fill bounds, keep ratio (may crop)            | `sizing: { type: "cover", w: 5, h: 3 }`                         |
| `crop`      | Extract a sub-region of the source            | `sizing: { type: "crop", x: 0.5, y: 0.5, w: 2, h: 2 }`        |

### Keeping aspect ratio manually

```js
const srcW = 2560, srcH = 1440, targetH = 3.5;
const targetW = targetH * (srcW / srcH);
const xOffset = (10 - targetW) / 2; // centre on 10″-wide slide

statusSlide.addImage({ path: "screenshot.png", x: xOffset, y: 1, w: targetW, h: targetH });
```

### Supported formats

PNG, JPG, GIF (animated GIFs play in Microsoft 365), SVG (modern PowerPoint / Microsoft 365).

---

## Icons via react-icons

Render any react-icons component to SVG, rasterise with **sharp**, and embed as a PNG data URI for maximum compatibility.

```bash
npm install react-icons react react-dom sharp
```

```js
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const { MdCloudDone } = require("react-icons/md");

function toSvgString(Icon, hexColor = "000000", px = 512) {
  return ReactDOMServer.renderToStaticMarkup(
    React.createElement(Icon, { size: px, color: `#${hexColor}` })
  );
}

async function svgToPngDataUri(svgStr, px = 512) {
  const buf = await sharp(Buffer.from(svgStr)).resize(px, px).png().toBuffer();
  return `data:image/png;base64,${buf.toString("base64")}`;
}

// Usage
const cloudIcon = await svgToPngDataUri(toSvgString(MdCloudDone, "2563EB", 512));
statusSlide.addImage({ data: cloudIcon, x: 8.5, y: 0.3, w: 0.4, h: 0.4 });
```

The `px` parameter controls rasterisation resolution (use ≥ 256 for sharpness). Display size is set by `w`/`h` in inches.

**Popular icon sets:** `react-icons/fa` (Font Awesome), `react-icons/md` (Material Design), `react-icons/hi` (Heroicons), `react-icons/bi` (Bootstrap Icons).

---

## Tables

### Simple table

```js
const metricSlide = deck.addSlide();

const header = [
  { text: "Service",   options: { bold: true, fill: "3B82F6", color: "FFFFFF" } },
  { text: "Latency",   options: { bold: true, fill: "3B82F6", color: "FFFFFF", align: "right" } },
  { text: "Error Rate", options: { bold: true, fill: "3B82F6", color: "FFFFFF", align: "right" } },
];

const rows = [
  ["auth-api",   "42 ms",  "0.03 %"],
  ["payments",   "118 ms", "0.12 %"],
  ["search",     "67 ms",  "0.01 %"],
];

metricSlide.addTable([header, ...rows], {
  x: 0.5, y: 1.2, w: 9,
  fontSize: 11,
  border: { color: "E2E8F0", pt: 0.5 },
  colW: [3.5, 2.75, 2.75],
});
```

### Merged cells (colspan)

```js
const merged = [
  [{ text: "Monthly Incident Summary", options: { colspan: 3, bold: true, fill: "EFF6FF", align: "center", fontSize: 13 } }],
  [
    { text: "Severity",  options: { bold: true, fill: "F1F5F9" } },
    { text: "Count",     options: { bold: true, fill: "F1F5F9", align: "right" } },
    { text: "MTTR",      options: { bold: true, fill: "F1F5F9", align: "right" } },
  ],
  ["SEV-1", { text: "2",     options: { align: "right" } }, { text: "23 min",  options: { align: "right" } }],
  ["SEV-2", { text: "7",     options: { align: "right" } }, { text: "48 min",  options: { align: "right" } }],
  ["SEV-3", { text: "15",    options: { align: "right" } }, { text: "4.2 hrs", options: { align: "right" } }],
];

metricSlide.addTable(merged, {
  x: 0.5, y: 3.0, w: 9,
  fontSize: 11,
  border: { color: "CBD5E1", pt: 0.5 },
  colW: [3.5, 2.75, 2.75],
});
```

---

## Charts

### Column chart

```js
const chartSlide = deck.addSlide();

const deployData = [{
  name: "Deployments",
  labels: ["Mon", "Tue", "Wed", "Thu", "Fri"],
  values: [12, 18, 9, 22, 15],
}];

chartSlide.addChart(deck.ChartType.bar, deployData, {
  x: 0.5, y: 0.8, w: 9, h: 4.2,
  barDir: "col",
  showTitle: true, title: "Daily Deployments", titleFontSize: 13,
});
```

### Line chart

```js
const latencyData = [{
  name: "p99 Latency (ms)",
  labels: ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6"],
  values: [210, 195, 230, 180, 160, 145],
}];

chartSlide.addChart(deck.ChartType.line, latencyData, {
  x: 0.5, y: 0.8, w: 9, h: 4.2,
  lineSize: 2.5, lineSmooth: true,
  showTitle: true, title: "p99 Latency Trend",
});
```

### Pie / doughnut chart

```js
const budgetData = [{
  name: "Cloud Spend",
  labels: ["Compute", "Storage", "Network", "Other"],
  values: [52, 23, 14, 11],
}];

chartSlide.addChart(deck.ChartType.doughnut, budgetData, {
  x: 2, y: 0.6, w: 6, h: 4.5,
  showPercent: true,
  showTitle: true, title: "Cloud Cost Breakdown",
});
```

### Polished chart styling

Default charts look plain. Apply these options for a cleaner result:

```js
chartSlide.addChart(deck.ChartType.bar, deployData, {
  x: 0.5, y: 0.8, w: 9, h: 4.2,
  barDir: "col",

  chartColors: ["6366F1", "818CF8", "A5B4FC"],
  chartArea: { fill: { color: "FFFFFF" }, roundedCorners: true },

  catAxisLabelColor: "94A3B8", catAxisLabelFontSize: 9,
  valAxisLabelColor: "94A3B8", valAxisLabelFontSize: 9,

  valGridLine: { color: "F1F5F9", size: 0.5 },
  catGridLine: { style: "none" },

  showValue: true, dataLabelPosition: "outEnd", dataLabelColor: "334155",
  showLegend: false,
});
```

**Styling properties worth knowing:**

- `chartColors` — array of hex strings applied to each series or segment.
- `chartArea` — `{ fill, border, roundedCorners }` for the plot background.
- `valGridLine` / `catGridLine` — control gridline color, size, or hide with `style: "none"`.
- `lineSmooth: true` — curved interpolation for line charts.
- `showValue`, `dataLabelPosition` (`"outEnd"`, `"inEnd"`, `"center"`), `dataLabelColor` — data labels.
- `showLegend`, `legendPos` (`"b"`, `"t"`, `"l"`, `"r"`, `"tr"`) — legend visibility and placement.

---

## Slide Masters (Reusable Templates)

Define a master once; every slide that references it inherits its background, shapes, and placeholders.

```js
deck.defineSlideMaster({
  title: "REPORT_PAGE",
  background: { color: "F8FAFC" },
  objects: [
    { rect: { x: 0, y: 5.2, w: 10, h: 0.425, fill: { color: "6366F1" } } },
    {
      placeholder: {
        options: { name: "heading", type: "title", x: 0.5, y: 0.3, w: 9, h: 0.6, fontSize: 18, color: "1E293B", bold: true },
        text: "",
      },
    },
    {
      text: {
        text: "Confidential — DevOps Team",
        options: { x: 0.5, y: 5.25, w: 9, h: 0.35, fontSize: 7, color: "E0E7FF", align: "right" },
      },
    },
  ],
});
```

Apply it to a slide:

```js
const pg = deck.addSlide({ masterName: "REPORT_PAGE" });
pg.addText("Deployment Pipeline", { placeholder: "heading" });
pg.addText("All stages green for the past 14 days.", {
  x: 0.5, y: 1.2, w: 9, h: 0.5, fontSize: 13, color: "475569",
});
```

---

## Slide Dimensions

| Layout constant | Width  | Height | Aspect ratio |
|-----------------|--------|--------|--------------|
| `LAYOUT_16x9`   | 10″    | 5.625″ | 16 : 9       |
| `LAYOUT_16x10`  | 10″    | 6.25″  | 16 : 10      |
| `LAYOUT_4x3`    | 10″    | 7.5″   | 4 : 3        |
| `LAYOUT_WIDE`   | 13.3″  | 7.5″   | ~16 : 9      |

For non-standard sizes:

```js
deck.defineLayout({ name: "A4_LANDSCAPE", width: 13.33, height: 7.5 });
deck.layout = "A4_LANDSCAPE";
```

---

## Troubleshooting

Bugs in PptxGenJS output typically fall into three buckets. Recognising which category a problem belongs to speeds up debugging.

### File-corruption errors

These produce a `.pptx` that PowerPoint refuses to open or "repairs" with data loss.

| Mistake | Why it breaks | Fix |
|---------|---------------|-----|
| `color: "#3B82F6"` | The `#` prefix is not stripped and generates invalid XML | Always use bare hex: `color: "3B82F6"` |
| `shadow: { color: "00000030" }` | 8-char hex is not valid OOXML; the file becomes unreadable | Use 6-char hex + `opacity`: `{ color: "000000", opacity: 0.19 }` |
| `shadow: { offset: -4 }` | Negative offset produces an illegal attribute in the XML | Keep offset ≥ 0. For upward shadows use `angle: 270` with a positive offset |
| Reusing a `pptxgen()` instance for a second file | Slides, masters, and metadata accumulate | Instantiate `new PptxGenJS()` per output file |

### Visual bugs (file opens but looks wrong)

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Shared mutable option object | Second shape gets already-converted values (e.g., shadow offset in EMU instead of pt) | Use a factory function that returns a fresh object each call |
| `roundRect` with a flush rectangular accent bar | Straight-edged overlay exposes rounded corners | Switch to `rect` when accent bars are needed |
| `letterSpacing: 10` instead of `charSpacing: 10` | Property is silently ignored; text looks unchanged | Always use `charSpacing` |

### Silent failures (no error, unexpected output)

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Unicode `"• "` in text + `bullet: true` | Double bullet glyphs on every item | Remove the `"• "` — `bullet: true` renders its own glyph |
| Missing `breakLine: true` on array text items | All segments concatenate onto one line | Add `breakLine: true` to every item except the last |
| `lineSpacing` on bulleted text | Excessive vertical gaps between items | Use `paraSpaceAfter` (e.g., `6`) for predictable spacing |

---

## API Cheat Sheet

### Enum quick-look

**Shapes** (`deck.ShapeType.*`)

| Property   | Maps to               |
|------------|-----------------------|
| `.rect`    | `RECTANGLE`           |
| `.ellipse` | `OVAL`                |
| `.line`    | `LINE`                |
| `.roundRect` | `ROUNDED_RECTANGLE` |

**Charts** (`deck.ChartType.*`)

`.bar` · `.line` · `.pie` · `.doughnut` · `.scatter` · `.bubble` · `.radar`

### Text alignment values

| Direction  | Options                           |
|------------|-----------------------------------|
| Horizontal | `"left"` · `"center"` · `"right"` |
| Vertical   | `"top"` · `"middle"` · `"bottom"` |

### Data-label positions

`"outEnd"` · `"inEnd"` · `"center"`

### Line dash types

`"solid"` · `"dash"` · `"dot"` · `"dashDot"` · `"lgDash"` · `"lgDashDot"` · `"sysDash"` · `"sysDot"`
