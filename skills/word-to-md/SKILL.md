---
name: word-to-md
description: >-
  将 Word (.docx) 文档的标题、列表、表格等内容转换为 Markdown。在用户说「Word 转
  MD」「docx 转 Markdown」「提取 Word 内容」或需要从 Word 文档生成可编辑
  Markdown 时使用。
---

# Word 转 Markdown

Skill 安装位置（全局，所有项目共用）：

- Windows: `%USERPROFILE%\.cursor\skills\word-to-md\`
- macOS/Linux: `~/.cursor/skills/word-to-md/`

## 快速使用

Windows PowerShell：

```powershell
python "$env:USERPROFILE\.cursor\skills\word-to-md\scripts\docx2md.py" "路径/文档.docx"
```

macOS / Linux：

```bash
python ~/.cursor/skills/word-to-md/scripts/docx2md.py "路径/文档.docx"
```

指定输出路径：

```powershell
python "$env:USERPROFILE\.cursor\skills\word-to-md\scripts\docx2md.py" "文档.docx" -o "输出/文档.md"
```

## 环境要求

- Python 3.10+
- 依赖：`python-docx`
- 由 `jeemookit` 的 `install.sh` / `install.ps1` 自动安装；手动安装：

```bash
pip install -r ~/.cursor/skills/word-to-md/scripts/requirements.txt
```

## Agent 工作流

1. 确认 `.docx` 路径有效（不支持旧版 `.doc`）。
2. 运行 `docx2md.py`；默认输出与 Word 同目录、同名的 `.md` 文件。
3. 嵌入图片默认保存到 `<md文件名>_assets/`。
4. 检查生成的 Markdown，必要时微调标题层级或表格。
5. 告知用户 `.md`（及 `_assets`）的完整路径。

## 转换能力

| 内容 | 处理方式 |
|------|----------|
| 标题 | Word「标题 1–6」/ Heading 1–6 / outlineLvl → `#` … `######` |
| 无序列表 | 项目符号 / bullet numbering → `-` |
| 有序列表 | 编号列表 → `1.`（保留嵌套缩进） |
| 表格 | 按文档顺序提取 → Markdown 管道表 |
| 加粗 / 斜体 | 转为 `**` / `*` |
| 超链接 | 转为 `[文本](url)` |
| 嵌入图片 | 提取到 `_assets/`，插入 `![](...)`（可用 `--no-images` 关闭） |

## 命令行选项

| 选项 | 说明 |
|------|------|
| `-o PATH` | 输出 Markdown 路径 |
| `--assets-dir DIR` | 图片输出目录（默认 `<stem>_assets`） |
| `--no-images` | 不提取嵌入图片 |

## 输出结构示例

```markdown
# 产品需求说明

## 一、背景

正文段落……

- 要点 A
- 要点 B
  - 子要点

1. 第一步
2. 第二步

| 列1 | 列2 |
| --- | --- |
| …   | …   |
```

## 注意事项

- 仅支持 `.docx`；`.doc` 请先用 Word / LibreOffice 另存为 `.docx`。
- 合并单元格、复杂嵌套表格会展平为普通管道表，可能需人工校对。
- 依赖「标题」样式与 Word 列表编号；纯手工加粗大字号不会自动识别为标题。
- 转换完成后可配合 **md-to-feishu** 或再次用 **md-to-word** 导出。

## 与其他 Skill 协作

```
Word → word-to-md → .md → md-to-feishu → 飞书云文档
                  └→ md-to-word → .docx（再编辑后回写）
PDF  → pdf-to-md  → .md
```
