---
name: pdf-to-md
description: >-
  将 PDF 文件的标题层级、表格、图片提取并转换为 Markdown。支持可选文本 PDF
  与扫描件 OCR（中文）。在用户说「PDF 转 MD」「提取 PDF 内容」「PDF 转
  Markdown」或需要从 PDF 文档生成可编辑 Markdown 时使用。
---

# PDF 转 Markdown

Skill 安装位置（全局，所有项目共用）：

- macOS/Linux: `~/.cursor/skills/pdf-to-md/`
- Windows: `%USERPROFILE%\.cursor\skills\pdf-to-md\`

## 快速使用

macOS / Linux：

```bash
python ~/.cursor/skills/pdf-to-md/scripts/pdf2md.py "路径/文档.pdf"
```

Windows PowerShell：

```powershell
python "$env:USERPROFILE\.cursor\skills\pdf-to-md\scripts\pdf2md.py" "路径/文档.pdf"
```

指定输出路径：

```bash
python ~/.cursor/skills/pdf-to-md/scripts/pdf2md.py "文档.pdf" -o "输出/文档.md"
```

## 环境要求

- Python 3.10+
- 依赖：`pymupdf`、`pdfplumber`、`rapidocr-onnxruntime`、`Pillow`
- 由 `jeemookit` 的 `install.sh` / `install.ps1` 自动安装；手动安装：

```bash
pip install -r ~/.cursor/skills/pdf-to-md/scripts/requirements.txt
```

## Agent 工作流

1. 确认 PDF 路径有效。
2. 运行 `pdf2md.py`；默认输出与 PDF 同目录、同名的 `.md` 文件。
3. 图片保存到 `<md文件名>_assets/` 目录。
4. 检查生成的 Markdown，必要时微调标题或表格。
5. 告知用户 `.md` 与 `_assets` 的完整路径。

## 提取能力

| 内容 | 文本 PDF | 扫描 PDF |
|------|----------|----------|
| 标题层级 | 字体大小 + 加粗 | OCR 行高 + 公文格式（一、二、） |
| 表格 | pdfplumber 提取 → MD 表格 | 简单列对齐；复杂表单保留页面图片 |
| 图片 | 提取嵌入图片 | 申报表/填表说明等表单页导出 PNG |
| 正文 | 段落合并 | OCR + 段落合并 |

## 命令行选项

| 选项 | 说明 |
|------|------|
| `-o PATH` | 输出 Markdown 路径 |
| `--assets-dir DIR` | 图片输出目录（默认 `<stem>_assets`） |
| `--dpi N` | OCR 渲染 DPI，默认 200 |
| `--ocr` | 强制 OCR（即使 PDF 含可选文本） |
| `--no-form-images` | 不导出表单/表格页整页图片 |

## 输出结构示例

```markdown
湖北省教育厅办公室

鄂教高办函〔2026〕11号

# 省教育厅办公室关于探索开展高校未来学习中心建设项目的通知

各普通本科高校：

……正文……

## 一、建设目标

……

| 列1 | 列2 |
| --- | --- |
| …   | …   |

![第3页表格/表单](文档_assets/page-003.png)
```

## 注意事项

- **扫描件**首次运行会下载 OCR 模型（约数十 MB），耗时略长。
- 复杂嵌套表格、合并单元格可能无法完美还原为 MD 表格，此时会保留整页图片。
- 转换完成后可配合 **md-to-word** 或 **md-to-feishu** 继续导出。
- OCR 结果建议人工校对关键数字、日期与专有名词。

## 与其他 Skill 协作

```
PDF → pdf-to-md → .md → md-to-word → .docx
                    └→ md-to-feishu → 飞书云文档
```
