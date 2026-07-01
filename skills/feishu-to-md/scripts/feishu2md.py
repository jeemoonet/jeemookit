#!/usr/bin/env python3
"""Download Feishu docs to local Markdown."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

from feishu_auth import (
    DEFAULT_DOMAIN,
    DEFAULT_REDIRECT_URI,
    OAUTH_SCOPES,
    TOKEN_STORE_PATH,
    feishu_error,
    load_secrets,
    oauth_login,
    resolve_access_token,
)

DOCX_URL_RE = re.compile(r"/docx/([A-Za-z0-9]+)")
WIKI_URL_RE = re.compile(r"/wiki/([A-Za-z0-9]+)")
IMG_MD_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
TOKEN_ONLY_RE = re.compile(r"^[A-Za-z0-9_-]{8,}$")
HEADING_FIELD_TO_LEVEL = {
    "heading1": 1,
    "heading2": 2,
    "heading3": 3,
    "heading4": 4,
    "heading5": 5,
    "heading6": 6,
    "heading7": 6,
    "heading8": 6,
    "heading9": 6,
}


def api_base(domain: str) -> str:
    return f"https://{domain}/open-apis"


def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|\r\n\t]', " ", name).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or "feishu-doc"


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    idx = 1
    while True:
        candidate = parent / f"{stem}-{idx}{suffix}"
        if not candidate.exists():
            return candidate
        idx += 1


def request_json(
    method: str,
    url: str,
    token: str,
    *,
    params: dict[str, Any] | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    resp = requests.request(
        method,
        url,
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"飞书接口调用失败: {feishu_error(data)}")
    return data


def apply_text_style(text: str, style: dict[str, Any] | None) -> str:
    if not style:
        return text

    rendered = text
    if style.get("inline_code"):
        rendered = f"`{rendered}`"
    if style.get("bold"):
        rendered = f"**{rendered}**"
    if style.get("italic"):
        rendered = f"*{rendered}*"
    if style.get("strikethrough"):
        rendered = f"~~{rendered}~~"
    link = style.get("link") or {}
    href = link.get("url")
    if href:
        rendered = f"[{rendered}]({href})"
    return rendered


def render_elements(elements: list[dict[str, Any]] | None) -> str:
    if not elements:
        return ""

    parts: list[str] = []
    for element in elements:
        if element.get("text_run"):
            run = element["text_run"]
            content = run.get("content", "")
            style = run.get("text_element_style") or {}
            parts.append(apply_text_style(content, style))
            continue
        if element.get("mention_user"):
            user = element["mention_user"]
            name = user.get("name") or user.get("user_id") or "用户"
            parts.append(f"@{name}")
            continue
        if element.get("reminder"):
            parts.append("⏰提醒")
            continue
        if element.get("equation"):
            eq = (element["equation"] or {}).get("content", "")
            parts.append(f"${eq}$" if eq else "")
            continue
        if element.get("file"):
            file_token = (element["file"] or {}).get("file_token", "")
            parts.append(f"[附件](feishu://file/{file_token})")
            continue

    return "".join(parts).strip()


def markdown_escape_table(text: str) -> str:
    return text.replace("|", r"\|").replace("\n", "<br/>")


def extract_token_from_input(value: str) -> tuple[str, str]:
    if value.startswith("http://") or value.startswith("https://"):
        docx_match = DOCX_URL_RE.search(value)
        if docx_match:
            return "docx", docx_match.group(1)
        wiki_match = WIKI_URL_RE.search(value)
        if wiki_match:
            return "wiki", wiki_match.group(1)
        raise ValueError("无法从 URL 中识别 docx/wiki token，请检查链接。")

    if not TOKEN_ONLY_RE.match(value):
        raise ValueError("请输入合法的飞书文档 token 或 URL。")

    if value.startswith("wiki"):
        return "wiki", value
    return "docx", value


def resolve_docx_token(domain: str, token: str, token_type: str, access_token: str) -> str:
    if token_type == "docx":
        return token

    url = f"{api_base(domain)}/wiki/v2/spaces/get_node"
    data = request_json("GET", url, access_token, params={"token": token})
    node = (data.get("data") or {}).get("node") or {}
    obj_type = node.get("obj_type")
    obj_token = node.get("obj_token")
    if obj_type != "docx" or not obj_token:
        raise RuntimeError(f"当前 wiki 节点不是 docx 文档（obj_type={obj_type}）")
    return obj_token


def fetch_document(domain: str, access_token: str, docx_token: str) -> tuple[str, str]:
    meta_url = f"{api_base(domain)}/docx/v1/documents/{docx_token}"
    meta_data = request_json("GET", meta_url, access_token)
    document = (meta_data.get("data") or {}).get("document") or {}
    title = document.get("title") or docx_token

    content_url = f"{api_base(domain)}/docx/v1/documents/{docx_token}/raw_content"
    content_data = request_json("GET", content_url, access_token)
    raw_content = (content_data.get("data") or {}).get("content")
    if raw_content is None:
        raise RuntimeError("未获取到 raw_content，可能是文档权限不足或接口返回变更。")
    return title, raw_content


def fetch_document_blocks(domain: str, access_token: str, docx_token: str) -> dict[str, dict[str, Any]]:
    url = f"{api_base(domain)}/docx/v1/documents/{docx_token}/blocks"
    block_map: dict[str, dict[str, Any]] = {}
    page_token: str | None = None

    while True:
        params: dict[str, Any] = {
            "document_revision_id": -1,
            "page_size": 500,
        }
        if page_token:
            params["page_token"] = page_token

        data = request_json("GET", url, access_token, params=params, timeout=60)
        payload = data.get("data") or {}
        for item in payload.get("items") or []:
            block_id = item.get("block_id")
            if block_id:
                block_map[block_id] = item

        if not payload.get("has_more"):
            break
        page_token = payload.get("page_token")
        if not page_token:
            break

    if not block_map:
        raise RuntimeError("未获取到文档 blocks 数据，无法渲染结构化 Markdown。")
    return block_map


def block_to_text(block: dict[str, Any], block_map: dict[str, dict[str, Any]]) -> str:
    if block.get("text"):
        return render_elements((block["text"] or {}).get("elements"))

    for field in HEADING_FIELD_TO_LEVEL:
        if block.get(field):
            return render_elements((block[field] or {}).get("elements"))

    children = block.get("children") or []
    child_parts: list[str] = []
    for child_id in children:
        child = block_map.get(child_id)
        if not child:
            continue
        child_text = block_to_text(child, block_map)
        if child_text:
            child_parts.append(child_text)
    return " ".join(part for part in child_parts if part).strip()


def render_table(block: dict[str, Any], block_map: dict[str, dict[str, Any]]) -> str:
    table = block.get("table") or {}
    cells = table.get("cells") or []
    prop = table.get("property") or {}
    col_size = int(prop.get("column_size") or 0)
    if col_size <= 0:
        return ""

    rows: list[list[str]] = []
    row: list[str] = []
    for cell_id in cells:
        cell_block = block_map.get(cell_id) or {}
        cell_text = block_to_text(cell_block, block_map)
        row.append(markdown_escape_table(cell_text))
        if len(row) == col_size:
            rows.append(row)
            row = []
    if row:
        row.extend([""] * (col_size - len(row)))
        rows.append(row)

    if not rows:
        return ""

    header = rows[0]
    body = rows[1:] if len(rows) > 1 else []
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * col_size) + " |",
    ]
    lines.extend("| " + " | ".join(r) + " |" for r in body)
    return "\n".join(lines)


def render_blocks_to_markdown(
    title: str,
    docx_token: str,
    block_map: dict[str, dict[str, Any]],
) -> str:
    root = block_map.get(docx_token)
    if not root:
        return title

    lines: list[str] = [f"# {title}", ""]

    def append_line(text: str = "") -> None:
        if text == "" and lines and lines[-1] == "":
            return
        lines.append(text)

    def render_block(block_id: str, list_level: int = 0, list_kind: str | None = None) -> None:
        block = block_map.get(block_id)
        if not block:
            return

        if block.get("table"):
            table_md = render_table(block, block_map)
            if table_md:
                append_line(table_md)
                append_line("")
            return

        for field, level in HEADING_FIELD_TO_LEVEL.items():
            if block.get(field):
                text = render_elements((block[field] or {}).get("elements"))
                if text:
                    md_level = min(level + 1, 6)
                    append_line(f"{'#' * md_level} {text}")
                    append_line("")
                for child_id in block.get("children") or []:
                    render_block(child_id, list_level, list_kind)
                return

        if block.get("bullet"):
            text = render_elements((block["bullet"] or {}).get("elements"))
            indent = "  " * list_level
            append_line(f"{indent}- {text}".rstrip())
            for child_id in block.get("children") or []:
                render_block(child_id, list_level + 1, "bullet")
            return

        if block.get("ordered"):
            text = render_elements((block["ordered"] or {}).get("elements"))
            indent = "  " * list_level
            append_line(f"{indent}1. {text}".rstrip())
            for child_id in block.get("children") or []:
                render_block(child_id, list_level + 1, "ordered")
            return

        if block.get("quote"):
            text = render_elements((block["quote"] or {}).get("elements"))
            if text:
                append_line(f"> {text}")
                append_line("")
            for child_id in block.get("children") or []:
                render_block(child_id, list_level, list_kind)
            return

        if block.get("code"):
            code = block.get("code") or {}
            language = code.get("language") or ""
            code_text = render_elements(code.get("elements")) or ""
            append_line(f"```{language}")
            append_line(code_text)
            append_line("```")
            append_line("")
            for child_id in block.get("children") or []:
                render_block(child_id, list_level, list_kind)
            return

        if block.get("text"):
            text = render_elements((block["text"] or {}).get("elements"))
            if text:
                append_line(text)
                append_line("")
            for child_id in block.get("children") or []:
                render_block(child_id, list_level, list_kind)
            return

        for child_id in block.get("children") or []:
            render_block(child_id, list_level, list_kind)

    for child_id in root.get("children") or []:
        render_block(child_id)

    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def infer_extension(url: str, content_type: str | None) -> str:
    parsed = urlparse(url)
    base = os.path.basename(parsed.path)
    ext = Path(base).suffix
    if ext:
        return ext.lower()
    if content_type:
        lowered = content_type.lower()
        if "png" in lowered:
            return ".png"
        if "jpeg" in lowered or "jpg" in lowered:
            return ".jpg"
        if "gif" in lowered:
            return ".gif"
        if "webp" in lowered:
            return ".webp"
        if "svg" in lowered:
            return ".svg"
    return ".bin"


def download_feishu_images(
    markdown: str,
    *,
    domain: str,
    access_token: str,
    assets_dir: Path,
    file_prefix: str,
) -> tuple[str, list[str]]:
    assets_dir.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []
    image_index = 1
    replaced: dict[str, str] = {}

    def should_download(url: str) -> bool:
        if not url or url.startswith("data:"):
            return False
        parsed = urlparse(url)
        if not parsed.scheme and url.startswith("/"):
            return True
        if parsed.scheme in {"http", "https"}:
            host = parsed.netloc.lower()
            return any(k in host for k in ("feishu", "larksuite"))
        return False

    for match in IMG_MD_RE.finditer(markdown):
        raw_url = match.group(2).strip()
        if raw_url in replaced:
            continue
        if not should_download(raw_url):
            continue

        download_url = raw_url
        if raw_url.startswith("/"):
            download_url = f"https://{domain}{raw_url}"

        try:
            resp = requests.get(
                download_url,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=60,
            )
            resp.raise_for_status()
            ext = infer_extension(download_url, resp.headers.get("Content-Type"))
            local_name = f"{file_prefix}-image-{image_index:03d}{ext}"
            image_index += 1
            local_path = assets_dir / local_name
            local_path.write_bytes(resp.content)
            replaced[raw_url] = f"{assets_dir.name}/{local_name}"
        except requests.RequestException as exc:
            warnings.append(f"图片下载失败，已保留原链接: {raw_url} ({exc})")

    converted = markdown
    for old_url, new_url in replaced.items():
        converted = converted.replace(f"]({old_url})", f"]({new_url})")
    return converted, warnings


def pull_feishu_doc(
    source: str,
    *,
    output_dir: Path,
    mode: str,
    localize_images: bool,
    overwrite: bool,
) -> dict[str, Any]:
    secrets = load_secrets()
    domain = secrets.get("FEISHU_DOMAIN") or DEFAULT_DOMAIN
    access_token = resolve_access_token(secrets, mode)

    token_type, token = extract_token_from_input(source)
    docx_token = resolve_docx_token(domain, token, token_type, access_token)
    title, raw_markdown = fetch_document(domain, access_token, docx_token)
    blocks_markdown = raw_markdown
    try:
        block_map = fetch_document_blocks(domain, access_token, docx_token)
        blocks_markdown = render_blocks_to_markdown(title, docx_token, block_map)
    except RuntimeError:
        # blocks 接口不可用时回退 raw_content
        blocks_markdown = raw_markdown

    output_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{sanitize_filename(title)}.md"
    md_path = output_dir / file_name
    if not overwrite:
        md_path = unique_path(md_path)

    warnings: list[str] = []
    markdown = blocks_markdown
    assets_dir = output_dir / "assets"

    if localize_images:
        markdown, warnings = download_feishu_images(
            markdown,
            domain=domain,
            access_token=access_token,
            assets_dir=assets_dir,
            file_prefix=sanitize_filename(md_path.stem).replace(" ", "-"),
        )
        if assets_dir.exists() and not any(assets_dir.iterdir()):
            assets_dir.rmdir()

    md_path.write_text(markdown, encoding="utf-8")

    return {
        "title": title,
        "docx_token": docx_token,
        "source": source,
        "markdown_path": str(md_path),
        "assets_path": str(assets_dir) if assets_dir.exists() else None,
        "warnings": warnings,
        "mode": mode,
    }


def cmd_login() -> int:
    secrets = load_secrets()
    try:
        store = oauth_login(secrets)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print("用户授权成功。")
    print(f"Token 已保存: {TOKEN_STORE_PATH}")
    print(f"权限 scope: {store.get('scope', OAUTH_SCOPES)}")
    print("\n请确保应用后台「安全设置 → 重定向 URL」已添加：")
    print(f"  {secrets.get('FEISHU_REDIRECT_URI') or DEFAULT_REDIRECT_URI}")
    return 0


def cmd_pull(args: argparse.Namespace) -> int:
    try:
        result = pull_feishu_doc(
            args.source,
            output_dir=args.output.resolve(),
            mode=args.mode,
            localize_images=not args.keep_remote_images,
            overwrite=args.overwrite,
        )
    except (RuntimeError, ValueError, FileNotFoundError, requests.RequestException) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    mode_label = "用户账号" if result["mode"] == "user" else "应用身份"
    print(f"已下载 ({mode_label}): {result['title']}")
    print(f"Markdown: {result['markdown_path']}")
    if result.get("assets_path"):
        print(f"Assets: {result['assets_path']}")
    if result.get("warnings"):
        for warning in result["warnings"]:
            print(f"警告: {warning}", file=sys.stderr)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download Feishu docx document to local Markdown",
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("login", help="浏览器 OAuth 授权（用户账号）")

    pull_parser = subparsers.add_parser("pull", help="拉取飞书文档为 Markdown")
    pull_parser.add_argument("source", help="飞书 docx/wiki 链接或 token")
    pull_parser.add_argument("-o", "--output", type=Path, default=Path("."), help="输出目录")
    pull_parser.add_argument(
        "--mode",
        choices=("user", "app"),
        default="user",
        help="user=用户 OAuth（默认）；app=应用 tenant token",
    )
    pull_parser.add_argument(
        "--keep-remote-images",
        action="store_true",
        help="不下载图片到本地，保留远程链接",
    )
    pull_parser.add_argument("--overwrite", action="store_true", help="覆盖同名 Markdown 文件")
    pull_parser.add_argument("--json", action="store_true", help="JSON 输出")

    if len(sys.argv) > 1 and not sys.argv[1].startswith("-") and sys.argv[1] not in ("login", "pull"):
        sys.argv.insert(1, "pull")

    args = parser.parse_args()
    if args.command == "login":
        return cmd_login()
    if args.command == "pull":
        return cmd_pull(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
