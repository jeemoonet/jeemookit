"""Prepare Markdown for Feishu upload by reusing md-to-word rendering."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path


def find_python_for_md2docx() -> str:
    if sys.version_info >= (3, 10):
        return sys.executable
    for name in ("python3.12", "python3.11", "python3.10"):
        path = shutil.which(name)
        if path:
            return path
    raise RuntimeError(
        "格式同步需要 Python 3.10+ 运行 md-to-word。\n"
        "请安装 Python 3.10+，或使用 --no-sync 上传原始 Markdown。"
    )


def find_project_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".cursor").is_dir():
            return candidate
    return start.parent if start.is_file() else start


def cache_dir_for(md_path: Path) -> Path:
    root = find_project_root(md_path.resolve())
    cache = root / ".cache" / "md2feishu"
    cache.mkdir(parents=True, exist_ok=True)
    return cache


def find_md2docx_script() -> Path:
    script = Path.home() / ".cursor/skills/md-to-word/scripts/md2docx.py"
    if script.is_file():
        return script
    raise RuntimeError(
        "未找到 md-to-word Skill（md2docx.py）。\n"
        "请先运行 jeemookit 的 install.sh 安装全局 Skills。"
    )


def md2docx_venv_python() -> Path:
    return Path.home() / ".cursor/skills/md-to-word/.venv/bin/python"


def venv_is_ready(python: Path) -> bool:
    if not python.is_file():
        return False
    result = subprocess.run(
        [str(python), "-c", "import docx; from PIL import Image"],
        capture_output=True,
    )
    return result.returncode == 0


def ensure_md2docx_venv() -> str:
    venv_python = md2docx_venv_python()
    req = find_md2docx_script().parent / "requirements.txt"

    if venv_is_ready(venv_python):
        return str(venv_python)

    if not venv_python.is_file():
        base_python = find_python_for_md2docx()
        venv_dir = venv_python.parent.parent
        subprocess.check_call([base_python, "-m", "venv", str(venv_dir)])

    subprocess.check_call(
        [str(venv_python), "-m", "pip", "install", "-q", "-r", str(req)],
    )
    if not venv_is_ready(venv_python):
        raise RuntimeError("md-to-word 虚拟环境依赖安装失败，请手动运行 jeemookit install.sh")
    return str(venv_python)


def python_for_md2docx() -> str:
    return ensure_md2docx_venv()


def content_fingerprint(md_path: Path) -> str:
    stat = md_path.stat()
    payload = f"{md_path.resolve()}:{stat.st_mtime_ns}:{stat.st_size}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def sync_md_to_docx(md_path: Path, *, output: Path | None = None) -> Path:
    """Render MD (Mermaid/SVG/images) to DOCX via md-to-word."""
    md_path = md_path.resolve()
    if not md_path.is_file():
        raise FileNotFoundError(f"Markdown 文件不存在: {md_path}")

    if output is None:
        output = cache_dir_for(md_path) / f"{md_path.stem}-{content_fingerprint(md_path)}.docx"
    else:
        output = output.resolve()

    md2docx = find_md2docx_script()
    python_exe = python_for_md2docx()
    cmd = [python_exe, str(md2docx), str(md_path), "-o", str(output)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "未知错误").strip()
        raise RuntimeError(f"Markdown 格式同步失败（md2docx）:\n{detail}")

    if not output.is_file():
        raise RuntimeError(f"md2docx 未生成文件: {output}")

    return output
