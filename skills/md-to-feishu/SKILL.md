---
name: md-to-feishu
description: >-
  将 Markdown 上传并导入为飞书云文档，默认复用 md-to-word 管线同步格式（Mermaid/SVG/图片渲染后导入）。
  默认浏览器 OAuth 用户账号上传，无需机器人。在用户说「上传到飞书」「同步到飞书」时使用。
---

# Markdown 上传飞书（格式同步）

Skill 安装位置（全局）：

- macOS/Linux: `~/.cursor/skills/md-to-feishu/`
- Windows: `%USERPROFILE%\.cursor\skills\md-to-feishu\`

依赖 **md-to-word** Skill（Mermaid / SVG / 图片渲染），由 jeemookit 一并安装。

## 快速使用

**首次授权**（浏览器，用你的飞书账号）：

```bash
python ~/.cursor/skills/md-to-feishu/scripts/md2feishu.py login
```

**上传（默认同步格式）**：

```bash
python ~/.cursor/skills/md-to-feishu/scripts/md2feishu.py "路径/文档.md"
python ~/.cursor/skills/md-to-feishu/scripts/md2feishu.py "文档.md" -t "自定义标题"
```

跳过格式同步、上传原始 Markdown：

```bash
python ~/.cursor/skills/md-to-feishu/scripts/md2feishu.py "文档.md" --no-sync
```

## 格式同步流程（默认）

与 `md-to-word` 相同处理能力，再导入飞书：

```
.md → md2docx（Mermaid→PNG、SVG→PNG、图片嵌入）→ .docx → 飞书云文档
```

| Markdown 类型 | 同步行为 |
|--------------|----------|
| ` ```mermaid ` | 渲染为 PNG 嵌入 |
| `**图N**（`assets/xxx.svg`）` | SVG 渲染为 PNG 嵌入 |
| `![](相对路径.png)` | 嵌入文档 |
| 标题、列表、表格、代码块 | 转为 Word 样式后导入飞书（标题 1–6、嵌套列表、表格自动列宽） |

中间 DOCX 缓存：项目根目录 `.cache/md2feishu/`（源文件未变时复用）。

## Agent 工作流

1. 默认 `--mode user`；无 token 时先 `login`。
2. 上传 `.md` 时**默认开启格式同步**，不要加 `--no-sync`，除非用户明确要求原始 MD。
3. 确认 `md-to-word` 已安装（`~/.cursor/skills/md-to-word/`）。
4. 运行 `md2feishu.py`，返回飞书文档链接。
5. Mermaid/SVG 渲染失败时，stderr 会有 md2docx 警告，仍会继续上传。

## 环境要求

- Python 3.10+、Node.js（Mermaid / SVG 渲染）
- `requests`
- 飞书凭证：`~/.jeemoo/secrets.env`，见 [reference.md](reference.md)

## 限制

| 项 | 说明 |
|----|------|
| 同步模式 | 经 DOCX 导入，上限 **600MB** |
| `--no-sync` | 原始 MD，上限 **20MB**，Mermaid/本地图不渲染 |
| 飞书导入 | 极复杂排版可能与 Word 略有差异 |

## 配置

详见 [reference.md](reference.md)。
