#!/usr/bin/env python3
"""Write Jeemoo AGENT conventions to <project>/.cursor/rules/jeemoo-agent.mdc."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

RULE_FILENAME = "jeemoo-agent.mdc"
MARKER_BEGIN = "<!-- jeemoo-agent-begin -->"
MARKER_END = "<!-- jeemoo-agent-end -->"


def default_source() -> Path:
    return Path(__file__).resolve().parent.parent / "agent.md"


def resolve_project_root(explicit: Path | None) -> Path:
    if explicit is not None:
        root = explicit.resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"project root not found: {root}")
        return root

    cwd = Path.cwd().resolve()
    for candidate in (cwd, *cwd.parents):
        if (candidate / ".git").exists() or (candidate / "AGENT.md").is_file():
            return candidate
    return cwd


def rules_dir(project_root: Path) -> Path:
    return project_root / ".cursor" / "rules"


def build_mdc(body: str) -> str:
    body = body.strip()
    return (
        "---\n"
        "description: Jeemoo project Agent conventions (doc layout, start scripts)\n"
        "alwaysApply: true\n"
        "---\n"
        "\n"
        f"{MARKER_BEGIN}\n"
        f"{body}\n"
        f"{MARKER_END}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install Jeemoo AGENT.md content into <project>/.cursor/rules/"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Target project root (default: cwd, or nearest .git / AGENT.md)",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Source Markdown (default: skill agent.md)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print target path and content length without writing",
    )
    args = parser.parse_args()

    try:
        project_root = resolve_project_root(args.project_root)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    source = (args.source or default_source()).resolve()
    if not source.is_file():
        print(f"error: source not found: {source}", file=sys.stderr)
        return 1

    body = source.read_text(encoding="utf-8")
    content = build_mdc(body)
    dest_dir = rules_dir(project_root)
    dest = dest_dir / RULE_FILENAME

    if args.dry_run:
        print(f"project: {project_root}")
        print(f"source:  {source}")
        print(f"target:  {dest}")
        print(f"bytes:   {len(content.encode('utf-8'))}")
        print("dry-run: no write")
        return 0

    dest_dir.mkdir(parents=True, exist_ok=True)

    if dest.is_file():
        existing = dest.read_text(encoding="utf-8")
        if existing == content:
            print(f"unchanged: {dest}")
            return 0
        bak = dest.with_suffix(dest.suffix + ".bak")
        shutil.copy2(dest, bak)
        print(f"backup:    {bak}")

    dest.write_text(content, encoding="utf-8", newline="\n")
    print(f"project:  {project_root}")
    print(f"written:  {dest}")
    print("next: open a new Cursor Agent chat in this project to load the rule")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
