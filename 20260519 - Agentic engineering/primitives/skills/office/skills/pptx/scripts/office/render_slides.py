"""Render PPTX slides to JPEG images with a Windows-friendly fallback.

On Windows, this helper prefers PowerPoint COM automation because it
produces reliable slide renders when desktop PowerPoint is installed.
Otherwise it falls back to the LibreOffice -> PDF -> pdftoppm pipeline
used elsewhere in the skill.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from office.soffice import run_libreoffice

RENDER_DPI = 150
DEFAULT_WIDTH = 1600
DEFAULT_HEIGHT = 900

_POWERPOINT_EXPORT_PS = r"""
param(
    [Parameter(Mandatory = $true)][string]$InputPath,
    [Parameter(Mandatory = $true)][string]$OutputDir,
    [Parameter(Mandatory = $true)][string]$Prefix,
    [int]$Width = 1600,
    [int]$Height = 900,
    [int]$FirstSlide = 1,
    [int]$LastSlide = 0
)

$resolvedInput = (Resolve-Path -LiteralPath $InputPath).Path
$resolvedOutputDir = [System.IO.Path]::GetFullPath($OutputDir)
New-Item -ItemType Directory -Force -Path $resolvedOutputDir | Out-Null

$powerPoint = $null
$presentation = $null

try {
    $powerPoint = New-Object -ComObject PowerPoint.Application
    $powerPoint.Visible = -1
    $presentation = $powerPoint.Presentations.Open($resolvedInput, $false, $false, $false)

    $startIndex = [Math]::Max(1, $FirstSlide)
    $endIndex = if ($LastSlide -gt 0) {
        [Math]::Min($LastSlide, $presentation.Slides.Count)
    } else {
        $presentation.Slides.Count
    }

    for ($index = $startIndex; $index -le $endIndex; $index++) {
        $target = Join-Path $resolvedOutputDir ('{0}-{1:D2}.jpg' -f $Prefix, $index)
        $presentation.Slides.Item($index).Export($target, 'JPG', $Width, $Height)
    }
}
finally {
    if ($presentation -ne $null) {
        $presentation.Close()
    }
    if ($powerPoint -ne $null) {
        $powerPoint.Quit()
    }

    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}
"""


def _powershell_binary() -> str:
    for candidate in ("powershell", "pwsh"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise FileNotFoundError("PowerShell executable not found on PATH.")


def _pdftoppm_binary() -> str:
    resolved = shutil.which("pdftoppm")
    if resolved:
        return resolved
    raise FileNotFoundError("`pdftoppm` not found on PATH.")


def _cleanup_existing_outputs(output_prefix: Path) -> None:
    for existing in output_prefix.parent.glob(f"{output_prefix.name}-*.jpg"):
        existing.unlink()


def _normalize_range(first_slide: int | None, last_slide: int | None) -> tuple[int, int]:
    start = first_slide or 1
    end = last_slide or 0
    if start < 1:
        raise ValueError("--first-slide must be >= 1")
    if end and end < start:
        raise ValueError("--last-slide must be >= --first-slide")
    return start, end


def _render_with_powerpoint(
    pptx_path: Path,
    output_prefix: Path,
    first_slide: int,
    last_slide: int,
    width: int,
    height: int,
) -> list[Path]:
    with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False, encoding="utf-8") as handle:
        handle.write(_POWERPOINT_EXPORT_PS)
        script_path = Path(handle.name)

    try:
        subprocess.run(
            [
                _powershell_binary(),
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script_path),
                "-InputPath",
                str(pptx_path),
                "-OutputDir",
                str(output_prefix.parent),
                "-Prefix",
                output_prefix.name,
                "-Width",
                str(width),
                "-Height",
                str(height),
                "-FirstSlide",
                str(first_slide),
                "-LastSlide",
                str(last_slide),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        script_path.unlink(missing_ok=True)

    return sorted(output_prefix.parent.glob(f"{output_prefix.name}-*.jpg"))


def _render_with_libreoffice(
    pptx_path: Path,
    output_prefix: Path,
    first_slide: int,
    last_slide: int,
) -> list[Path]:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        run_libreoffice(
            [
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(tmp_dir),
                str(pptx_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        pdf_path = tmp_dir / f"{pptx_path.stem}.pdf"
        if not pdf_path.exists():
            raise RuntimeError("LibreOffice produced no PDF output.")

        command = [
            _pdftoppm_binary(),
            "-jpeg",
            "-r",
            str(RENDER_DPI),
            "-f",
            str(first_slide),
        ]
        if last_slide:
            command.extend(["-l", str(last_slide)])
        command.extend([str(pdf_path), str(output_prefix)])

        subprocess.run(command, check=True, capture_output=True, text=True)

    return sorted(output_prefix.parent.glob(f"{output_prefix.name}-*.jpg"))


def render_slides_to_images(
    pptx_path: Path,
    output_prefix: Path,
    first_slide: int | None = None,
    last_slide: int | None = None,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
) -> list[Path]:
    """Render slides and return the written image paths."""
    start, end = _normalize_range(first_slide, last_slide)
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    _cleanup_existing_outputs(output_prefix)

    errors: list[str] = []

    if os.name == "nt":
        try:
            images = _render_with_powerpoint(
                pptx_path, output_prefix, start, end, width, height
            )
            if images:
                return images
            errors.append("PowerPoint COM export produced no slide images.")
        except Exception as exc:  # surface concrete fallback reasons to the caller
            errors.append(f"PowerPoint COM export failed: {exc}")

    try:
        images = _render_with_libreoffice(pptx_path, output_prefix, start, end)
        if images:
            return images
        errors.append("LibreOffice rendering produced no slide images.")
    except Exception as exc:
        errors.append(f"LibreOffice rendering failed: {exc}")

    raise RuntimeError(" ; ".join(errors))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render PPTX slides to JPEG images.",
    )
    parser.add_argument("pptx_file", help="Path to the .pptx file")
    parser.add_argument(
        "output_prefix",
        nargs="?",
        default="slides/page",
        help="Output prefix, e.g. slides/page (default: slides/page)",
    )
    parser.add_argument("--first-slide", type=int, default=1, help="First slide to render")
    parser.add_argument("--last-slide", type=int, default=0, help="Last slide to render")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH, help="Output image width in pixels")
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT, help="Output image height in pixels")
    args = parser.parse_args()

    source = Path(args.pptx_file)
    if not source.is_file() or source.suffix.lower() != ".pptx":
        raise SystemExit(f"Error: not a valid .pptx file: {source}")

    output_prefix = Path(args.output_prefix)
    written = render_slides_to_images(
        source,
        output_prefix,
        first_slide=args.first_slide,
        last_slide=args.last_slide or None,
        width=args.width,
        height=args.height,
    )
    for image_path in written:
        print(image_path)


if __name__ == "__main__":
    main()
