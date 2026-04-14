#!/usr/bin/env python3
"""
imageToMarkdownFiles — convert images and PDFs to Markdown.

Usage:
    python convert.py <file_or_directory>

Supported input types: PDF, PNG, JPG, JPEG, TIFF, BMP, WEBP
Output: Markdown files written to ./output/
"""

import sys
import os
from pathlib import Path

# ── Dependency check (runs immediately so errors are clear) ───────────────────
_missing = []
try:
    import pdfplumber
except ImportError:
    _missing.append("pdfplumber")

try:
    from PIL import Image, ImageOps, ImageFilter
except ImportError:
    _missing.append("Pillow")

try:
    import pytesseract
except ImportError:
    _missing.append("pytesseract")

if _missing:
    print(f"\n❌  Missing dependencies: {', '.join(_missing)}")
    print(f"\n   This Python interpreter: {sys.executable}")
    print(f"   Fix: {sys.executable} -m pip install {' '.join(_missing)}\n")
    sys.exit(1)

# ── Output directory (always relative to this script) ────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = SCRIPT_DIR / "output"

# ── Supported extensions ──────────────────────────────────────────────────────
PDF_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}
ALL_SUPPORTED = PDF_EXTENSIONS | IMAGE_EXTENSIONS


# ── Helpers ───────────────────────────────────────────────────────────────────

def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def output_path(source: Path) -> Path:
    """Return the destination .md path for a given source file."""
    return OUTPUT_DIR / (source.stem + ".md")


def deduplicate_name(dest: Path) -> Path:
    """If dest already exists, append _1, _2, … until unique."""
    if not dest.exists():
        return dest
    stem = dest.stem
    suffix = dest.suffix
    parent = dest.parent
    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


# ── PDF conversion ─────────────────────────────────────────────────────────────

def pdf_to_markdown(source: Path) -> str:
    """Extract text from a PDF and return it as a Markdown string."""

    lines = [f"# {source.stem}", ""]

    with pdfplumber.open(source) as pdf:
        total_pages = len(pdf.pages)
        for i, page in enumerate(pdf.pages, start=1):
            lines.append(f"## Page {i} of {total_pages}")
            lines.append("")

            # ── Tables first ──────────────────────────────────────────────────
            tables = page.extract_tables()
            table_bboxes = [t.bbox for t in page.find_tables()] if tables else []

            for table in tables:
                if not table:
                    continue
                # Header row
                header = table[0]
                lines.append("| " + " | ".join(cell or "" for cell in header) + " |")
                lines.append("| " + " | ".join("---" for _ in header) + " |")
                for row in table[1:]:
                    lines.append("| " + " | ".join(cell or "" for cell in row) + " |")
                lines.append("")

            # ── Body text (outside table bboxes) ─────────────────────────────
            words = page.extract_words()
            if words:
                # Group words into lines by their top-coordinate
                from itertools import groupby
                words_sorted = sorted(words, key=lambda w: (round(w["top"] / 5) * 5, w["x0"]))
                paragraph_lines = []
                for _, group in groupby(words_sorted, key=lambda w: round(w["top"] / 5) * 5):
                    row_words = list(group)
                    row_text = " ".join(w["text"] for w in row_words).strip()
                    if row_text:
                        paragraph_lines.append(row_text)

                if paragraph_lines:
                    lines.append("\n".join(paragraph_lines))
                    lines.append("")

    return "\n".join(lines)


# ── Image conversion ──────────────────────────────────────────────────────────

def preprocess_image(img):
    """Convert to grayscale and increase contrast to improve OCR accuracy."""
    try:
        img = img.convert("L")                         # grayscale
        img = ImageOps.autocontrast(img)               # stretch contrast
        img = img.filter(ImageFilter.SHARPEN)          # sharpen
    except Exception:
        pass  # fall back to original image if preprocessing fails
    return img


def image_to_markdown(source: Path) -> str:
    """OCR an image file and return the text as a Markdown string."""
    img = Image.open(source)
    img = preprocess_image(img)

    # PSM 6 = assume a single uniform block of text (good for docs/screenshots)
    config = "--psm 6"
    raw_text = pytesseract.image_to_string(img, config=config)

    lines = [f"# {source.stem}", ""]
    for line in raw_text.splitlines():
        stripped = line.rstrip()
        lines.append(stripped)

    # Trim trailing blank lines, then add one final newline
    content = "\n".join(lines).rstrip() + "\n"
    return content


# ── Core dispatcher ───────────────────────────────────────────────────────────

def convert_file(source: Path) -> tuple[bool, str]:
    """
    Convert a single file.  Returns (success, message).
    """
    ext = source.suffix.lower()

    if ext not in ALL_SUPPORTED:
        return False, f"Skipped (unsupported type): {source.name}"

    try:
        if ext in PDF_EXTENSIONS:
            markdown = pdf_to_markdown(source)
        else:
            markdown = image_to_markdown(source)
    except Exception as exc:
        return False, f"Failed: {source.name} — {exc}"

    dest = deduplicate_name(output_path(source))
    dest.write_text(markdown, encoding="utf-8")
    return True, f"✓  {source.name}  →  output/{dest.name}"


def collect_files(path: Path) -> list[Path]:
    """Return all supported files under `path` (file or directory)."""
    if path.is_file():
        return [path]
    if path.is_dir():
        return sorted(
            f for f in path.rglob("*")
            if f.is_file() and f.suffix.lower() in ALL_SUPPORTED
        )
    return []


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python convert.py <file_or_directory>")
        sys.exit(1)

    target = Path(sys.argv[1]).resolve()

    if not target.exists():
        print(f"Error: path does not exist — {target}")
        sys.exit(1)

    files = collect_files(target)

    if not files:
        print("No supported files found.")
        print(f"Supported types: {', '.join(sorted(ALL_SUPPORTED))}")
        sys.exit(0)

    ensure_output_dir()

    print(f"\nConverting {len(files)} file(s)  →  {OUTPUT_DIR}\n")

    converted = skipped = failed = 0

    for f in files:
        success, msg = convert_file(f)
        print(f"  {msg}")
        if success:
            converted += 1
        elif "Skipped" in msg:
            skipped += 1
        else:
            failed += 1

    print(f"\nDone — {converted} converted, {skipped} skipped, {failed} failed.\n")


if __name__ == "__main__":
    main()
