---
name: markdown-to-word
description: >-
  将 Markdown 文档（含 Mermaid 代码块、图例 SVG/PNG、标准图片引用）导出为 Word
  (.docx)，图片自动渲染并嵌入。在用户说「导出 Word」「转成 docx」「生成 Word
  文档」，或完成设计文档/专利交底书后需要交付 Word 时使用。
---

# Markdown 转 Word

Skill 安装位置（全局，所有项目共用）：

- Windows: `%USERPROFILE%\.cursor\skills\markdown-to-word\`
- macOS/Linux: `~/.cursor/skills/markdown-to-word/`

## 快速使用

Windows PowerShell：

```powershell
python "$env:USERPROFILE\.cursor\skills\markdown-to-word\scripts\md2docx.py" "路径/文档.md"
```

macOS / Linux：

```bash
python ~/.cursor/skills/markdown-to-word/scripts/md2docx.py "路径/文档.md"
```

可选指定输出路径：

```powershell
python "$env:USERPROFILE\.cursor\skills\markdown-to-word\scripts\md2docx.py" "路径/文档.md" -o "路径/输出.docx"
```

## 环境要求

- Python 3.10+
- Node.js（Mermaid 与 SVG 渲染）
- 依赖由 `cursor-dev-kit` 的 `install.ps1` 一次性安装；手动安装见 kit README

## Agent 工作流

1. 编写或修改 Markdown 后，在用户要求时导出 Word（或询问是否导出）。
2. 使用上方**全局路径**运行 `md2docx.py`；路径相对于**当前项目根目录**。
3. 确认 `.docx` 已生成（默认与 `.md` 同目录、同名）。
4. 若 stderr 报错，排查依赖、Mermaid 语法、图片路径后重试。

## 支持的 Markdown 特性

| 类型 | 处理方式 |
|------|----------|
| ` ```mermaid ` 代码块 | mermaid-cli 渲染 PNG 并居中嵌入 |
| `**图N**（`图例/xxx.svg`）：说明` | Chromium 渲染 SVG（支持中文）后嵌入 |
| `![](相对路径.png)` | 直接嵌入 |
| 标题、列表、引用、表格、分隔线 | 转为 Word 样式 |

## 图片路径规则

- 相对路径以 **Markdown 文件所在目录** 为基准。
- 专利附图：`图例/图N-描述.svg`，正文在「附图说明」引用。

## 缓存

渲染缓存位于**当前项目**根目录 `.cache/md2docx/`。

## 注意事项

- Mermaid 语法错误时保留代码块文本并继续导出。
- 导出完成后告知用户 `.docx` 的完整路径。
