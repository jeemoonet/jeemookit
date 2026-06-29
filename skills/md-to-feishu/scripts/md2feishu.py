#!/usr/bin/env python3
"""Upload Markdown to Feishu with format sync via md-to-word."""

from __future__ import annotations

import argparse
import json
import mimetypes
import sys
import time
from pathlib import Path
from typing import Any

import requests

from feishu_auth import (
    DEFAULT_REDIRECT_URI,
    OAUTH_SCOPES,
    TOKEN_STORE_PATH,
    feishu_error,
    load_secrets,
    oauth_login,
    resolve_access_token,
)
from md_sync import sync_md_to_docx

POLL_INTERVAL_SEC = 1.5
POLL_TIMEOUT_SEC = 120

IMPORT_PROFILES: dict[str, dict[str, Any]] = {
    "md": {
        "file_extension": None,  # resolved from path
        "target_type": "docx",
        "max_bytes": 20 * 1024 * 1024,
        "mime": "text/markdown",
    },
    "docx": {
        "file_extension": "docx",
        "target_type": "docx",
        "max_bytes": 600 * 1024 * 1024,
        "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    },
}

MD_EXTENSIONS = {"md", "markdown", "mark"}


def api_base(domain: str) -> str:
    return f"https://{domain}/open-apis"


def resolve_md_extension(file_path: Path) -> str:
    ext = file_path.suffix.lstrip(".").lower()
    if ext not in MD_EXTENSIONS:
        supported = ", ".join(sorted(MD_EXTENSIONS))
        raise ValueError(f"不支持的 Markdown 扩展名 .{ext}，仅支持: {supported}")
    return ext


def upload_import_media(
    domain: str,
    token: str,
    file_path: Path,
    *,
    file_extension: str,
    target_type: str,
) -> str:
    url = f"{api_base(domain)}/drive/v1/medias/upload_all"
    size = file_path.stat().st_size
    extra = json.dumps({"obj_type": target_type, "file_extension": file_extension}, ensure_ascii=False)
    mime = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"

    with file_path.open("rb") as fh:
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {token}"},
            data={
                "file_name": file_path.name,
                "parent_type": "ccm_import_open",
                "size": str(size),
                "extra": extra,
            },
            files={"file": (file_path.name, fh, mime)},
            timeout=300,
        )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"上传素材失败: {feishu_error(data)}")
    file_token = (data.get("data") or {}).get("file_token")
    if not file_token:
        raise RuntimeError(f"上传成功但未返回 file_token: {data}")
    return file_token


def create_import_task(
    domain: str,
    token: str,
    file_token: str,
    file_extension: str,
    file_name: str,
    target_type: str,
    folder_token: str | None,
) -> str:
    url = f"{api_base(domain)}/drive/v1/import_tasks"
    body: dict[str, Any] = {
        "file_extension": file_extension,
        "file_name": file_name,
        "file_token": file_token,
        "type": target_type,
        "point": {
            "mount_type": 1,
            "mount_key": folder_token or "",
        },
    }

    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        json=body,
        timeout=30,
    )
    data = resp.json()
    if data.get("code") != 0:
        msg = feishu_error(data)
        if data.get("code") == 99991672:
            raise RuntimeError(
                f"创建导入任务失败（应用缺少 API 权限）: {msg}\n"
                "请在飞书开放平台开通 docs:document:import 或 drive:drive 并发布应用。"
            )
        raise RuntimeError(f"创建导入任务失败: {msg}")
    ticket = (data.get("data") or {}).get("ticket")
    if not ticket:
        raise RuntimeError(f"创建任务成功但未返回 ticket: {data}")
    return ticket


def poll_import_result(domain: str, token: str, ticket: str) -> dict[str, Any]:
    url = f"{api_base(domain)}/drive/v1/import_tasks/{ticket}"
    headers = {"Authorization": f"Bearer {token}"}
    deadline = time.time() + POLL_TIMEOUT_SEC

    while time.time() < deadline:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"查询导入结果失败: {feishu_error(data)}")

        result = (data.get("data") or {}).get("result") or {}
        status = result.get("job_status")
        if status == 0:
            return result
        if status not in (1, 2):
            msg = result.get("job_error_msg") or feishu_error(data)
            raise RuntimeError(f"导入失败 (job_status={status}): {msg}")

        time.sleep(POLL_INTERVAL_SEC)

    raise RuntimeError(f"导入超时（>{POLL_TIMEOUT_SEC}s），ticket={ticket}")


def prepare_upload_file(md_path: Path, *, sync: bool) -> tuple[Path, str, str]:
    """Return (upload_path, import_extension, kind) where kind is md|docx."""
    md_path = md_path.resolve()
    if md_path.suffix.lower() == ".docx":
        return md_path, "docx", "docx"

    if not sync:
        ext = resolve_md_extension(md_path)
        return md_path, ext, "md"

    docx_path = sync_md_to_docx(md_path)
    return docx_path, "docx", "docx"


def upload_to_feishu(
    file_path: Path,
    *,
    title: str | None = None,
    folder_token: str | None = None,
    mode: str = "user",
    sync: bool = True,
    source_md: Path | None = None,
) -> dict[str, Any]:
    source_md = (source_md or file_path).resolve()
    if source_md.suffix.lower() != ".docx" and not source_md.is_file():
        raise FileNotFoundError(f"文件不存在: {source_md}")

    upload_path, import_ext, kind = prepare_upload_file(source_md, sync=sync)
    profile = IMPORT_PROFILES[kind]
    max_bytes = profile["max_bytes"]
    size = upload_path.stat().st_size
    if size > max_bytes:
        raise ValueError(f"文件超过导入上限 ({size} bytes): {upload_path}")

    secrets = load_secrets()
    domain = secrets.get("FEISHU_DOMAIN") or "open.feishu.cn"
    if folder_token is None:
        folder_token = secrets.get("FEISHU_FOLDER_TOKEN") or None

    doc_title = title or source_md.stem
    target_type = profile["target_type"]
    access_token = resolve_access_token(secrets, mode)

    file_token = upload_import_media(
        domain,
        access_token,
        upload_path,
        file_extension=import_ext,
        target_type=target_type,
    )
    ticket = create_import_task(
        domain,
        access_token,
        file_token,
        import_ext,
        doc_title,
        target_type,
        folder_token,
    )
    result = poll_import_result(domain, access_token, ticket)
    return {
        "title": doc_title,
        "url": result.get("url"),
        "token": result.get("token"),
        "ticket": ticket,
        "extra": result.get("extra") or [],
        "mode": mode,
        "sync": sync and kind == "docx" and source_md.suffix.lower() != ".docx",
        "uploaded_file": str(upload_path),
        "import_format": import_ext,
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
    print("下次上传默认使用你的飞书账号（无需机器人）。")
    print("\n请确保应用后台「安全设置 → 重定向 URL」已添加：")
    print(f"  {secrets.get('FEISHU_REDIRECT_URI') or DEFAULT_REDIRECT_URI}")
    return 0


def cmd_upload(args: argparse.Namespace) -> int:
    try:
        result = upload_to_feishu(
            args.markdown,
            title=args.title,
            folder_token=args.folder_token,
            mode=args.mode,
            sync=not args.no_sync,
            source_md=args.markdown,
        )
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        mode_label = "用户账号" if result["mode"] == "user" else "应用身份"
        sync_label = "已同步格式（Mermaid/SVG/图片→DOCX）" if result["sync"] else "原始 Markdown"
        print(f"已上传 ({mode_label}, {sync_label}): {result['title']}")
        if result.get("url"):
            print(f"链接: {result['url']}")
        if result.get("uploaded_file") and result["sync"]:
            print(f"中间文件: {result['uploaded_file']}")
        if result.get("extra"):
            filtered = [x for x in result["extra"] if not str(x).startswith("_")]
            if filtered:
                print(f"提示: extra={filtered}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Upload Markdown to Feishu with format sync (md-to-word pipeline)"
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("login", help="浏览器 OAuth 授权（用户账号，推荐）")

    upload_parser = subparsers.add_parser("upload", help="上传 Markdown 到飞书")
    upload_parser.add_argument("markdown", type=Path, help="Markdown 文件路径")
    upload_parser.add_argument("-t", "--title", help="导入后的文档标题")
    upload_parser.add_argument("-f", "--folder-token", help="目标云空间文件夹 token")
    upload_parser.add_argument(
        "--mode",
        choices=("user", "app"),
        default="user",
        help="user=用户 OAuth（默认）；app=应用 tenant token",
    )
    upload_parser.add_argument(
        "--no-sync",
        action="store_true",
        help="跳过格式同步，直接上传原始 .md（不含 Mermaid/SVG 渲染）",
    )
    upload_parser.add_argument("--json", action="store_true", help="以 JSON 输出结果")

    if len(sys.argv) > 1 and not sys.argv[1].startswith("-") and sys.argv[1] not in ("login", "upload"):
        sys.argv.insert(1, "upload")

    args = parser.parse_args()
    if args.command == "login":
        return cmd_login()
    if args.command == "upload":
        return cmd_upload(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
