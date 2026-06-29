#!/usr/bin/env python3
"""Extract PDF content (headings, tables, images) to Markdown."""

from __future__ import annotations

import argparse
import re
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

try:
    import fitz  # PyMuPDF
except ImportError as exc:
    sys.exit("Missing pymupdf. Run: pip install pymupdf")

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class TextLine:
    text: str
    page: int
    y0: float
    y1: float
    x0: float
    x1: float
    font_size: float = 0.0
    is_bold: bool = False
    level: int = 0  # 0=body, 1-6=heading


@dataclass
class TableBlock:
    page: int
    rows: list[list[str]]
    y0: float = 0.0


@dataclass
class ImageBlock:
    page: int
    path: Path
    caption: str = ""
    y0: float = 0.0


@dataclass
class PageContent:
    page: int
    lines: list[TextLine] = field(default_factory=list)
    tables: list[TableBlock] = field(default_factory=list)
    images: list[ImageBlock] = field(default_factory=list)
    is_scanned: bool = False


# ---------------------------------------------------------------------------
# Heading heuristics
# ---------------------------------------------------------------------------

SECTION_RE = re.compile(
    r"^([一二三四五六七八九十]+[、．.]|[（(][一二三四五六七八九十]+[)）]|"
    r"第[一二三四五六七八九十百]+[章节条部分]|附件\s*\d+)"
)
NUMBERED_RE = re.compile(r"^\d+[.、．]\s*")
DOC_TITLE_HINTS = ("通知", "办法", "规定", "意见", "方案", "报告", "申报表", "填表说明")
HEADING_STOP_PREFIX = ("为", "经", "在", "将", "按", "请", "各", "据", "对", "以", "把", "从")


def classify_heading(line: TextLine, body_size: float, page_width: float) -> int:
    text = line.text.strip()
    if not text or len(text) > 80:
        return 0

    # Mid-sentence continuations are never headings
    if text.startswith(HEADING_STOP_PREFIX) and len(text) > 15:
        return 0
    if text.endswith(("，", "、", "：", "；")) and len(text) > 20:
        return 0

    size_ratio = line.font_size / body_size if body_size > 0 else 1.0
    height = line.y1 - line.y0
    centered = page_width > 0 and abs((line.x0 + line.x1) / 2 - page_width / 2) < page_width * 0.15
    width_ratio = (line.x1 - line.x0) / page_width if page_width > 0 else 1.0

    # Section: 一、二、 / 附件N (strong signal)
    if SECTION_RE.match(text):
        if len(text) <= 25:
            return 2
        return 3

    # Sub-section numbering at line start — keep as list item, not heading
    if NUMBERED_RE.match(text) and len(text) <= 60:
        return 0

    # Document title (large, centered)
    if size_ratio >= 1.35 and centered and len(text) <= 40:
        if any(h in text for h in DOC_TITLE_HINTS) or size_ratio >= 1.55:
            return 1

    if size_ratio >= 1.8 and centered:
        return 1

    # Font-size based (conservative)
    if size_ratio >= 1.45 and len(text) <= 30:
        return 2
    if size_ratio >= 1.28 and len(text) <= 25:
        return 3

    return 0


def apply_heading_levels(lines: list[TextLine], page_width: float) -> None:
    sizes = [ln.font_size for ln in lines if ln.font_size > 0]
    if not sizes:
        sizes = [ln.y1 - ln.y0 for ln in lines]
    body_size = statistics.median(sizes) if sizes else 12.0

    for ln in lines:
        ln.level = classify_heading(ln, body_size, page_width)

    _apply_first_page_layout(lines, body_size, page_width)


DOC_NO_RE = re.compile(r"^[\u4e00-\u9fff]{1,6}〔\d{4}〕\d+号")


def _apply_first_page_layout(lines: list[TextLine], body_size: float, page_width: float) -> None:
    """Heuristics for Chinese gov-doc cover pages (OCR)."""
    page1 = [ln for ln in lines if ln.page == 1]
    if not page1:
        return

    for ln in page1:
        if DOC_NO_RE.match(ln.text.strip()):
            ln.level = 0
            continue

    # Largest centered line → org name (plain, not heading)
    candidates = [
        ln for ln in page1
        if page_width > 0 and abs((ln.x0 + ln.x1) / 2 - page_width / 2) < page_width * 0.12
    ]
    if candidates:
        org = max(candidates, key=lambda ln: ln.font_size)
        if org.font_size >= body_size * 1.5:
            org.level = 0

    # Title block: centered lines after doc-no / org, before salutation (各...)
    doc_no_idx = next(
        (i for i, ln in enumerate(page1) if DOC_NO_RE.match(ln.text.strip())), -1
    )
    title_start = doc_no_idx + 1 if doc_no_idx >= 0 else 1
    title_block: list[TextLine] = []
    for ln in page1[title_start:]:
        t = ln.text.strip()
        if t.startswith("各") and t.endswith("："):
            break
        if page_width > 0 and abs((ln.x0 + ln.x1) / 2 - page_width / 2) < page_width * 0.18:
            if ln.font_size >= body_size * 1.05 and len(t) <= 35:
                title_block.append(ln)
                continue
        if title_block:
            break

    for ln in title_block:
        ln.level = 1


# ---------------------------------------------------------------------------
# Text-based PDF extraction
# ---------------------------------------------------------------------------

def page_has_text(page: fitz.Page, min_chars: int = 30) -> bool:
    return len(page.get_text().strip()) >= min_chars


def extract_text_lines(page: fitz.Page, page_num: int) -> list[TextLine]:
    lines: list[TextLine] = []
    data = page.get_text("dict")
    page_width = page.rect.width

    for block in data.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            if not spans:
                continue
            text = "".join(s["text"] for s in spans).strip()
            if not text:
                continue
            sizes = [s.get("size", 0) for s in spans if s.get("text", "").strip()]
            flags = [s.get("flags", 0) for s in spans]
            font_size = statistics.mean(sizes) if sizes else 0.0
            is_bold = any(f & 2**4 for f in flags)
            bbox = line["bbox"]
            lines.append(
                TextLine(
                    text=text,
                    page=page_num,
                    y0=bbox[1],
                    y1=bbox[3],
                    x0=bbox[0],
                    x1=bbox[2],
                    font_size=font_size,
                    is_bold=is_bold,
                )
            )

    apply_heading_levels(lines, page_width)
    return lines


def extract_tables_pdfplumber(pdf_path: Path, page_num: int) -> list[TableBlock]:
    if pdfplumber is None:
        return []
    tables: list[TableBlock] = []
    with pdfplumber.open(pdf_path) as pdf:
        if page_num > len(pdf.pages):
            return []
        page = pdf.pages[page_num - 1]
        for table in page.extract_tables() or []:
            if not table or not any(any(cell for cell in row) for row in table):
                continue
            cleaned = [
                [str(cell or "").replace("\n", " ").strip() for cell in row]
                for row in table
            ]
            tables.append(TableBlock(page=page_num, rows=cleaned))
    return tables


def extract_embedded_images(
    doc: fitz.Document,
    page: fitz.Page,
    page_num: int,
    assets_dir: Path,
    img_counter: list[int],
    skip_fullpage: bool = True,
) -> list[ImageBlock]:
    images: list[ImageBlock] = []
    page_area = page.rect.width * page.rect.height

    for img_info in page.get_images(full=True):
        xref = img_info[0]
        try:
            extracted = doc.extract_image(xref)
        except Exception:
            continue
        w, h = extracted["width"], extracted["height"]
        if skip_fullpage and page_area > 0:
            img_area = w * h
            if img_area >= page_area * 0.85:
                continue

        img_counter[0] += 1
        ext = extracted.get("ext", "png")
        filename = f"image-{img_counter[0]:03d}.{ext}"
        out_path = assets_dir / filename
        out_path.write_bytes(extracted["image"])

        rects = page.get_image_rects(xref)
        y0 = rects[0].y0 if rects else 0.0
        images.append(ImageBlock(page=page_num, path=out_path, y0=y0))

    return images


# ---------------------------------------------------------------------------
# OCR extraction (scanned PDF)
# ---------------------------------------------------------------------------

def ocr_page(page: fitz.Page, dpi: int = 200):
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError as exc:
        raise SystemExit(
            "Scanned PDF detected but rapidocr-onnxruntime is not installed.\n"
            "Run: pip install rapidocr-onnxruntime"
        ) from exc

    pix = page.get_pixmap(dpi=dpi)
    engine = RapidOCR()
    result, _ = engine(pix.tobytes("png"))
    return result or [], pix


def ocr_to_lines(result: list, page_num: int, page_width: float) -> list[TextLine]:
    if not result:
        return []

    # Group OCR boxes into lines by y-center
    items = []
    for box, text, _score in result:
        text = text.strip()
        if not text:
            continue
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        items.append(
            {
                "text": text,
                "x0": min(xs),
                "x1": max(xs),
                "y0": min(ys),
                "y1": max(ys),
                "cy": (min(ys) + max(ys)) / 2,
                "h": max(ys) - min(ys),
            }
        )

    items.sort(key=lambda it: (it["cy"], it["x0"]))
    lines_raw: list[list[dict]] = []
    for item in items:
        placed = False
        for group in lines_raw:
            ref = group[0]
            if abs(item["cy"] - ref["cy"]) <= max(ref["h"], item["h"]) * 0.5:
                group.append(item)
                placed = True
                break
        if not placed:
            lines_raw.append([item])

    text_lines: list[TextLine] = []
    for group in lines_raw:
        group.sort(key=lambda it: it["x0"])
        text = "".join(it["text"] for it in group) if len(group) == 1 else " ".join(
            it["text"] for it in group
        )
        x0 = min(it["x0"] for it in group)
        x1 = max(it["x1"] for it in group)
        y0 = min(it["y0"] for it in group)
        y1 = max(it["y1"] for it in group)
        h = y1 - y0
        text_lines.append(
            TextLine(
                text=text,
                page=page_num,
                y0=y0,
                y1=y1,
                x0=x0,
                x1=x1,
                font_size=h,
            )
        )

    apply_heading_levels(text_lines, page_width)
    return text_lines


FORM_PAGE_STRONG = ("填表说明",)
FORM_SECTION_MARKERS = ("一、基本信息", "二、基本情况", "二、建设理念")


def is_form_page(lines: list[TextLine], page_num: int) -> bool:
    joined = " ".join(ln.text for ln in lines)
    if "填表说明" in joined:
        return True
    # Form cover: 申报表 + 制表, short page
    if "申报表" in joined and "制表" in joined and len(lines) <= 10:
        return True
    # Form body: section markers typical of templates
    markers = sum(1 for m in FORM_SECTION_MARKERS if m in joined)
    if markers >= 2:
        return True
    return False


def save_page_image(pix: fitz.Pixmap, assets_dir: Path, page_num: int) -> Path:
    out = assets_dir / f"page-{page_num:03d}.png"
    pix.save(str(out))
    return out


# ---------------------------------------------------------------------------
# OCR table detection (simple column alignment)
# ---------------------------------------------------------------------------

def detect_ocr_tables(lines: list[TextLine], page_num: int) -> list[TableBlock]:
    """Detect simple multi-column rows from OCR line x-positions."""
    if len(lines) < 3:
        return []

    # Split lines that look like multi-column (large x-gap)
    rows: list[list[str]] = []
    for ln in lines:
        if ln.level > 0:
            continue
        # Already merged; try tab-like splits
        parts = re.split(r"\s{2,}|\t", ln.text.strip())
        if len(parts) >= 2:
            rows.append(parts)

    if len(rows) < 2:
        return []

    col_counts = [len(r) for r in rows]
    if max(set(col_counts), key=col_counts.count) < 2:
        return []

    mode_cols = max(set(col_counts), key=col_counts.count)
    normalized = [r + [""] * (mode_cols - len(r)) for r in rows if len(r) <= mode_cols + 1]
    if len(normalized) < 2:
        return []

    return [TableBlock(page=page_num, rows=normalized[:])]


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def line_to_md(line: TextLine) -> str:
    text = line.text.strip()
    if line.level == 1:
        return f"# {text}"
    if line.level == 2:
        return f"## {text}"
    if line.level == 3:
        return f"### {text}"
    if line.level == 4:
        return f"#### {text}"
    if line.level == 5:
        return f"##### {text}"
    if line.level == 6:
        return f"###### {text}"
    return text


def table_to_md(table: TableBlock) -> str:
    if not table.rows:
        return ""
    rows = table.rows
    ncol = max(len(r) for r in rows)
    norm = [r + [""] * (ncol - len(r)) for r in rows]

    def esc(cell: str) -> str:
        return cell.replace("|", "\\|").replace("\n", " ")

    header = norm[0]
    body = norm[1:] if len(norm) > 1 else []
    lines = [
        "| " + " | ".join(esc(c) for c in header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    for row in body:
        lines.append("| " + " | ".join(esc(c) for c in row) + " |")
    return "\n".join(lines)


def merge_title_lines(lines: list[TextLine]) -> list[TextLine]:
    """Merge consecutive level-1 OCR title lines on the first page."""
    if not lines:
        return lines
    merged: list[TextLine] = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.level == 1 and ln.page == 1:
            parts = [ln.text.strip()]
            j = i + 1
            while j < len(lines) and lines[j].level == 1 and lines[j].page == 1:
                parts.append(lines[j].text.strip())
                j += 1
            if len(parts) > 1:
                combined = TextLine(
                    text="".join(parts),
                    page=ln.page,
                    y0=ln.y0,
                    y1=lines[j - 1].y1,
                    x0=ln.x0,
                    x1=ln.x1,
                    font_size=ln.font_size,
                    level=1,
                )
                merged.append(combined)
                i = j
                continue
        merged.append(ln)
        i += 1
    return merged


def merge_paragraphs(lines: list[TextLine]) -> list[str]:
    """Merge consecutive body lines into paragraphs."""
    lines = merge_title_lines(lines)
    output: list[str] = []
    buf: list[str] = []

    def flush():
        if buf:
            output.append("".join(buf))
            buf.clear()

    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.level > 0:
            flush()
            output.append(line_to_md(ln))
            i += 1
            continue

        text = ln.text.strip()
        if not text:
            flush()
            i += 1
            continue

        if NUMBERED_RE.match(text):
            flush()
            item_parts = [text]
            j = i + 1
            while j < len(lines):
                nxt_ln = lines[j]
                nxt = nxt_ln.text.strip()
                if not nxt or nxt_ln.level > 0 or NUMBERED_RE.match(nxt):
                    break
                if nxt.startswith(("联系人", "附件", "各")):
                    break
                item_parts.append(nxt)
                j += 1
                if nxt.endswith("。"):
                    break
            output.append("".join(item_parts))
            i = j
            continue

        if DOC_NO_RE.match(text):
            flush()
            output.append(text)
            i += 1
            continue

        # Salutation line (各xxx：) starts its own paragraph
        if text.startswith("各") and text.endswith("："):
            flush()
            output.append(text)
            i += 1
            continue

        if buf:
            prev = buf[-1]
            if prev[-1:] in "。；！？":
                flush()
            elif text.startswith(("联系人", "附件", "电话")):
                flush()

        buf.append(text)
        i += 1

    flush()
    return output


def render_markdown(pages: list[PageContent], assets_dir: Path) -> str:
    parts: list[str] = []
    seen_title = False

    for pc in pages:
        page_parts: list[tuple[float, str]] = []

        md_lines = merge_paragraphs(pc.lines)
        if md_lines:
            # Promote first H1; demote org-name style duplicates
            filtered = []
            for ln in md_lines:
                if ln.startswith("# ") and seen_title:
                    filtered.append("## " + ln[2:])
                elif ln.startswith("# "):
                    seen_title = True
                    filtered.append(ln)
                elif ln.startswith("## ") and not seen_title and "办公室" in ln[:20]:
                    filtered.append(ln[3:])  # org name as plain text
                else:
                    filtered.append(ln)
            y = pc.lines[0].y0 if pc.lines else 0
            page_parts.append((y, "\n\n".join(filtered)))

        for tbl in pc.tables:
            md = table_to_md(tbl)
            if md:
                page_parts.append((tbl.y0, md))

        # Form/table page images go after text (large y to sort last)
        for img in pc.images:
            rel = img.path.name
            cap = img.caption or f"第{img.page}页"
            sort_y = img.y0 if img.y0 > 0 else 1e9
            page_parts.append((sort_y, f"![{cap}]({assets_dir.name}/{rel})"))

        page_parts.sort(key=lambda x: x[0])
        if page_parts:
            parts.append("\n\n".join(p for _, p in page_parts))

    return "\n\n".join(parts).strip() + "\n"


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def process_pdf(
    pdf_path: Path,
    output_md: Path,
    assets_dir: Path,
    dpi: int = 200,
    force_ocr: bool = False,
    include_form_pages: bool = True,
) -> dict:
    pdf_path = pdf_path.resolve()
    output_md = output_md.resolve()
    assets_dir = assets_dir.resolve()
    assets_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf_path)
    pages: list[PageContent] = []
    img_counter = [0]
    stats = {"pages": len(doc), "scanned_pages": 0, "text_pages": 0, "tables": 0, "images": 0}

    for i in range(len(doc)):
        page_num = i + 1
        page = doc[i]
        scanned = force_ocr or not page_has_text(page)
        pc = PageContent(page=page_num, is_scanned=scanned)

        if scanned:
            stats["scanned_pages"] += 1
            ocr_result, pix = ocr_page(page, dpi=dpi)
            ocr_width = float(pix.width)
            pc.lines = ocr_to_lines(ocr_result, page_num, ocr_width)

            if include_form_pages and is_form_page(pc.lines, page_num):
                page_img = save_page_image(pix, assets_dir, page_num)
                pc.images.append(
                    ImageBlock(
                        page=page_num,
                        path=page_img,
                        caption=f"第{page_num}页表格/表单",
                        y0=1e9,
                    )
                )
                stats["images"] += 1
        else:
            stats["text_pages"] += 1
            pc.lines = extract_text_lines(page, page_num)
            pc.tables.extend(extract_tables_pdfplumber(pdf_path, page_num))
            stats["tables"] += len(pc.tables)
            pc.images.extend(
                extract_embedded_images(doc, page, page_num, assets_dir, img_counter)
            )
            stats["images"] += len(pc.images)

            ocr_tables = detect_ocr_tables(pc.lines, page_num)
            if ocr_tables:
                pc.tables.extend(ocr_tables)
                stats["tables"] += len(ocr_tables)

        pages.append(pc)

    doc.close()

    md_content = render_markdown(pages, assets_dir)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(md_content, encoding="utf-8")

    return stats


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Extract PDF headings, tables, and images to Markdown."
    )
    p.add_argument("pdf", type=Path, help="Input PDF file")
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output .md path (default: same name as PDF)",
    )
    p.add_argument(
        "--assets-dir",
        type=Path,
        help="Directory for extracted images (default: <output_stem>_assets)",
    )
    p.add_argument("--dpi", type=int, default=200, help="OCR render DPI (default: 200)")
    p.add_argument(
        "--ocr",
        action="store_true",
        help="Force OCR even if PDF has selectable text",
    )
    p.add_argument(
        "--no-form-images",
        action="store_true",
        help="Do not embed form/table page images for scanned PDFs",
    )
    return p.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    pdf_path = args.pdf
    if not pdf_path.is_file():
        print(f"Error: PDF not found: {pdf_path}", file=sys.stderr)
        return 1

    output_md = args.output or pdf_path.with_suffix(".md")
    assets_dir = args.assets_dir or output_md.parent / f"{output_md.stem}_assets"

    try:
        stats = process_pdf(
            pdf_path,
            output_md,
            assets_dir,
            dpi=args.dpi,
            force_ocr=args.ocr,
            include_form_pages=not args.no_form_images,
        )
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    mode = "OCR" if stats["scanned_pages"] else "text"
    if stats["scanned_pages"] and stats["text_pages"]:
        mode = "mixed"

    print(f"Done [{mode}]: {output_md}")
    print(
        f"  pages={stats['pages']} text={stats['text_pages']} "
        f"scanned={stats['scanned_pages']} tables={stats['tables']} images={stats['images']}"
    )
    print(f"  assets: {assets_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
