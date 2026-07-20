#!/usr/bin/env python3
"""Convert Word (.docx) to Markdown: headings, lists, tables, basic inline formatting."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Optional

try:
    from docx import Document
    from docx.document import Document as DocumentObject
    from docx.oxml.ns import qn
    from docx.table import Table
    from docx.text.paragraph import Paragraph
except ImportError:
    sys.exit("Missing python-docx. Run: pip install python-docx")


HEADING_STYLE_RE = re.compile(
    r"^(Heading|标题|标题\s*)\s*([1-6])$",
    re.IGNORECASE,
)
HEADING_STYLE_CN = {
    "标题 1": 1,
    "标题1": 1,
    "标题 2": 2,
    "标题2": 2,
    "标题 3": 3,
    "标题3": 3,
    "标题 4": 4,
    "标题4": 4,
    "标题 5": 5,
    "标题5": 5,
    "标题 6": 6,
    "标题6": 6,
}
LIST_STYLE_HINTS = (
    "list",
    "bullet",
    "number",
    "列表",
    "项目符号",
    "编号",
)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class HeadingBlock:
    level: int
    text: str


@dataclass
class ParagraphBlock:
    text: str  # may contain **bold** / *italic* / [link](url)


@dataclass
class ListItemBlock:
    text: str
    ordered: bool
    level: int = 0


@dataclass
class TableBlock:
    rows: list[list[str]]


@dataclass
class ImageBlock:
    alt: str
    rel_path: str


@dataclass
class HrBlock:
    pass


Block = HeadingBlock | ParagraphBlock | ListItemBlock | TableBlock | ImageBlock | HrBlock


@dataclass
class ConvertResult:
    blocks: list[Block] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    image_count: int = 0


# ---------------------------------------------------------------------------
# Inline formatting
# ---------------------------------------------------------------------------

def escape_md_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def escape_md_text(text: str) -> str:
    # Keep light escaping so Chinese docs stay readable
    return text.replace("\\", "\\\\")


def runs_to_markdown(paragraph: Paragraph) -> str:
    """Convert paragraph runs to Markdown with bold/italic/links."""
    parts: list[str] = []
    for run in paragraph.runs:
        text = run.text or ""
        if not text:
            continue
        text = escape_md_text(text)

        # Detect hyperlink parent
        hyperlink = run._element.getparent()
        href = None
        if hyperlink is not None and hyperlink.tag == qn("w:hyperlink"):
            r_id = hyperlink.get(qn("r:id"))
            if r_id:
                try:
                    rel = paragraph.part.rels[r_id]
                    href = rel.target_ref
                except (KeyError, AttributeError):
                    href = None

        bold = bool(run.bold)
        italic = bool(run.italic)

        if bold and italic:
            text = f"***{text}***"
        elif bold:
            text = f"**{text}**"
        elif italic:
            text = f"*{text}*"

        if href:
            text = f"[{text}]({href})"

        parts.append(text)

    # Fallback: if runs empty but paragraph has text
    joined = "".join(parts).strip()
    if not joined:
        joined = (paragraph.text or "").strip()
    return joined


# ---------------------------------------------------------------------------
# Style / list / heading detection
# ---------------------------------------------------------------------------

def style_name(paragraph: Paragraph) -> str:
    try:
        name = paragraph.style.name if paragraph.style else ""
    except Exception:
        name = ""
    return (name or "").strip()


def heading_level_from_style(name: str) -> int:
    if not name:
        return 0
    if name in HEADING_STYLE_CN:
        return HEADING_STYLE_CN[name]
    m = HEADING_STYLE_RE.match(name)
    if m:
        return int(m.group(2))
    # Title / 标题 alone → H1
    if name.lower() in ("title", "标题"):
        return 1
    return 0


def outline_level(paragraph: Paragraph) -> Optional[int]:
    """Return outlineLvl (0-based) if present on paragraph or style."""
    pPr = paragraph._element.pPr
    if pPr is not None:
        ol = pPr.find(qn("w:outlineLvl"))
        if ol is not None:
            val = ol.get(qn("w:val"))
            if val is not None:
                return int(val)

    # Style-based outlineLvl
    try:
        style_el = paragraph.style._element
        spPr = style_el.find(qn("w:pPr"))
        if spPr is not None:
            ol = spPr.find(qn("w:outlineLvl"))
            if ol is not None:
                val = ol.get(qn("w:val"))
                if val is not None:
                    return int(val)
    except Exception:
        pass
    return None


def num_pr(paragraph: Paragraph) -> tuple[Optional[str], Optional[int]]:
    """Return (numId, ilvl) from paragraph properties."""
    pPr = paragraph._element.pPr
    if pPr is None:
        return None, None
    numPr = pPr.find(qn("w:numPr"))
    if numPr is None:
        return None, None
    num_id_el = numPr.find(qn("w:numId"))
    ilvl_el = numPr.find(qn("w:ilvl"))
    num_id = num_id_el.get(qn("w:val")) if num_id_el is not None else None
    ilvl = int(ilvl_el.get(qn("w:val"))) if ilvl_el is not None else 0
    return num_id, ilvl


def is_list_style(name: str) -> bool:
    lower = name.lower()
    return any(h in lower or h in name for h in LIST_STYLE_HINTS)


def detect_list(
    paragraph: Paragraph,
    num_formats: dict[str, str],
) -> Optional[tuple[bool, int]]:
    """Return (ordered, level) if paragraph is a list item."""
    num_id, ilvl = num_pr(paragraph)
    if num_id is not None:
        fmt = num_formats.get(num_id, "bullet")
        ordered = fmt not in ("bullet", "none")
        return ordered, ilvl or 0

    name = style_name(paragraph)
    if is_list_style(name):
        ordered = any(x in name.lower() or x in name for x in ("number", "编号", "有序"))
        # Nested list styles like List Bullet 2 / List Number 3
        m = re.search(r"(\d+)\s*$", name)
        level = max(0, int(m.group(1)) - 1) if m else 0
        return ordered, level

    return None


def load_numbering_formats(document: DocumentObject) -> dict[str, str]:
    """Map numId -> numFmt (bullet/decimal/...)."""
    formats: dict[str, str] = {}
    try:
        numbering_part = document.part.numbering_part
    except Exception:
        return formats
    if numbering_part is None:
        return formats

    root = numbering_part._element
    # abstractNumId -> fmt of level 0 (and store per-level if needed)
    abstract_fmt: dict[str, str] = {}
    for abstract in root.findall(qn("w:abstractNum")):
        aid = abstract.get(qn("w:abstractNumId"))
        if aid is None:
            continue
        # Prefer level 0 format; fall back to first lvl
        fmt = "bullet"
        for lvl in abstract.findall(qn("w:lvl")):
            ilvl = lvl.get(qn("w:ilvl")) or "0"
            num_fmt_el = lvl.find(qn("w:numFmt"))
            if num_fmt_el is not None:
                val = num_fmt_el.get(qn("w:val")) or "bullet"
                if ilvl == "0":
                    fmt = val
                    break
                if fmt == "bullet":
                    fmt = val
        abstract_fmt[aid] = fmt

    for num in root.findall(qn("w:num")):
        num_id = num.get(qn("w:numId"))
        abs_ref = num.find(qn("w:abstractNumId"))
        if num_id is None or abs_ref is None:
            continue
        aid = abs_ref.get(qn("w:val"))
        if aid is not None:
            formats[num_id] = abstract_fmt.get(aid, "bullet")

    return formats


# ---------------------------------------------------------------------------
# Tables & images
# ---------------------------------------------------------------------------

def table_to_rows(table: Table) -> list[list[str]]:
    rows: list[list[str]] = []
    for row in table.rows:
        cells: list[str] = []
        for cell in row.cells:
            # Merge multi-paragraph cell text
            texts = []
            for p in cell.paragraphs:
                t = runs_to_markdown(p)
                if t:
                    texts.append(t)
            cells.append(escape_md_cell(" ".join(texts)))
        rows.append(cells)
    # Normalize column count
    if rows:
        width = max(len(r) for r in rows)
        rows = [r + [""] * (width - len(r)) for r in rows]
    return rows


def extract_images_from_paragraph(
    paragraph: Paragraph,
    assets_dir: Optional[Path],
    counter: list[int],
) -> list[ImageBlock]:
    if assets_dir is None:
        return []

    images: list[ImageBlock] = []
    for drawing in paragraph._element.findall(".//" + qn("w:drawing")):
        blip = drawing.find(".//" + qn("a:blip"))
        if blip is None:
            # EMU namespace for drawings may use r:embed on a:blip
            for el in drawing.iter():
                if el.tag.endswith("}blip"):
                    blip = el
                    break
        if blip is None:
            continue
        r_id = blip.get(qn("r:embed"))
        if not r_id:
            continue
        try:
            rel = paragraph.part.rels[r_id]
            image_bytes = rel.target_part.blob
            content_type = getattr(rel.target_part, "content_type", "") or ""
        except Exception:
            continue

        ext = ".png"
        if "jpeg" in content_type or "jpg" in content_type:
            ext = ".jpg"
        elif "gif" in content_type:
            ext = ".gif"
        elif "webp" in content_type:
            ext = ".webp"
        elif "emf" in content_type:
            ext = ".emf"
        elif "wmf" in content_type:
            ext = ".wmf"

        counter[0] += 1
        assets_dir.mkdir(parents=True, exist_ok=True)
        filename = f"image-{counter[0]:03d}{ext}"
        out_path = assets_dir / filename
        out_path.write_bytes(image_bytes)
        images.append(ImageBlock(alt=f"image-{counter[0]:03d}", rel_path=f"{assets_dir.name}/{filename}"))

    return images


# ---------------------------------------------------------------------------
# Document walk (preserve paragraph/table order)
# ---------------------------------------------------------------------------

def iter_block_items(document: DocumentObject) -> Iterator[Paragraph | Table]:
    body = document.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, document)
        elif child.tag == qn("w:tbl"):
            yield Table(child, document)


def convert_docx(
    docx_path: Path,
    assets_dir: Optional[Path] = None,
) -> ConvertResult:
    document = Document(str(docx_path))
    num_formats = load_numbering_formats(document)
    result = ConvertResult()
    image_counter = [0]

    for item in iter_block_items(document):
        if isinstance(item, Table):
            rows = table_to_rows(item)
            if rows and any(any(c.strip() for c in row) for row in rows):
                result.blocks.append(TableBlock(rows=rows))
            continue

        paragraph = item
        text = runs_to_markdown(paragraph)

        # Images even if text empty
        if assets_dir is not None:
            for img in extract_images_from_paragraph(paragraph, assets_dir, image_counter):
                result.blocks.append(img)
                result.image_count += 1

        if not text:
            continue

        # Heading
        level = heading_level_from_style(style_name(paragraph))
        if level == 0:
            ol = outline_level(paragraph)
            if ol is not None and 0 <= ol <= 5:
                level = ol + 1
        if level > 0:
            result.blocks.append(HeadingBlock(level=level, text=text))
            continue

        # List
        list_info = detect_list(paragraph, num_formats)
        if list_info is not None:
            ordered, lvl = list_info
            result.blocks.append(ListItemBlock(text=text, ordered=ordered, level=max(0, lvl)))
            continue

        # Page break → hr (optional cue)
        if paragraph._element.find(qn("w:r")) is not None:
            for br in paragraph._element.findall(".//" + qn("w:br")):
                if br.get(qn("w:type")) == "page":
                    result.blocks.append(HrBlock())
                    break

        result.blocks.append(ParagraphBlock(text=text))

    return result


# ---------------------------------------------------------------------------
# Markdown render
# ---------------------------------------------------------------------------

def render_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    norm = [r + [""] * (width - len(r)) for r in rows]
    header = norm[0]
    body = norm[1:] if len(norm) > 1 else []
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    if not body:
        # Single-row table: treat as header-only with empty body row omitted
        pass
    else:
        for row in body:
            lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def blocks_to_markdown(blocks: list[Block]) -> str:
    lines: list[str] = []
    prev_list = False

    for block in blocks:
        if isinstance(block, HeadingBlock):
            if lines and lines[-1] != "":
                lines.append("")
            level = min(max(block.level, 1), 6)
            lines.append("#" * level + " " + block.text)
            lines.append("")
            prev_list = False
        elif isinstance(block, ListItemBlock):
            indent = "  " * block.level
            marker = "1." if block.ordered else "-"
            lines.append(f"{indent}{marker} {block.text}")
            prev_list = True
        elif isinstance(block, TableBlock):
            if prev_list and lines and lines[-1] != "":
                lines.append("")
            if lines and lines[-1] != "":
                lines.append("")
            lines.append(render_table(block.rows))
            lines.append("")
            prev_list = False
        elif isinstance(block, ImageBlock):
            if prev_list and lines and lines[-1] != "":
                lines.append("")
            lines.append(f"![{block.alt}]({block.rel_path})")
            lines.append("")
            prev_list = False
        elif isinstance(block, HrBlock):
            if lines and lines[-1] != "":
                lines.append("")
            lines.append("---")
            lines.append("")
            prev_list = False
        elif isinstance(block, ParagraphBlock):
            if prev_list and lines and lines[-1] != "":
                lines.append("")
            lines.append(block.text)
            lines.append("")
            prev_list = False

    # Trim trailing blank lines
    while lines and lines[-1] == "":
        lines.pop()
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Word (.docx) to Markdown (headings, lists, tables)."
    )
    parser.add_argument("docx", type=Path, help="Input .docx path")
    parser.add_argument("-o", "--output", type=Path, help="Output .md path")
    parser.add_argument(
        "--assets-dir",
        type=Path,
        help="Directory for extracted images (default: <stem>_assets)",
    )
    parser.add_argument(
        "--no-images",
        action="store_true",
        help="Do not extract embedded images",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    docx_path: Path = args.docx.resolve()
    if not docx_path.is_file():
        print(f"File not found: {docx_path}", file=sys.stderr)
        return 1
    if docx_path.suffix.lower() != ".docx":
        print("Only .docx is supported (not .doc).", file=sys.stderr)
        return 1

    out_path: Path = (
        args.output.resolve()
        if args.output
        else docx_path.with_suffix(".md")
    )
    assets_dir: Optional[Path] = None
    if not args.no_images:
        assets_dir = (
            args.assets_dir.resolve()
            if args.assets_dir
            else out_path.parent / f"{out_path.stem}_assets"
        )

    result = convert_docx(docx_path, assets_dir=assets_dir)
    md = blocks_to_markdown(result.blocks)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")

    print(f"Wrote: {out_path}")
    if result.image_count:
        print(f"Images: {result.image_count} → {assets_dir}")
    for w in result.warnings:
        print(f"Warning: {w}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
