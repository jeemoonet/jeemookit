---
name: feishu-to-md
description: >-
  将飞书云文档拉取为本地 Markdown，默认保留飞书文档标题作为文件名，并尽量保留标题层级、表格和图片引用。
  在用户说「飞书文档转 md」「从飞书下载为 markdown」「同步飞书到本地」时使用。
---

# 飞书文档下载为 Markdown

Skill 安装位置（全局）：

- macOS/Linux: `~/.cursor/skills/feishu-to-md/`
- Windows: `%USERPROFILE%\.cursor\skills\feishu-to-md\`

## 快速使用

首次授权（浏览器 OAuth）：

```bash
python ~/.cursor/skills/feishu-to-md/scripts/feishu2md.py login
```

拉取文档（支持 docx URL、wiki URL、文档 token）：

```bash
python ~/.cursor/skills/feishu-to-md/scripts/feishu2md.py "https://xxx.feishu.cn/docx/XXXXXXXXXXXX"
python ~/.cursor/skills/feishu-to-md/scripts/feishu2md.py "doxcnXXXXXXXXXXXX" -o ./doc
```

JSON 输出：

```bash
python ~/.cursor/skills/feishu-to-md/scripts/feishu2md.py "doxcnXXXXXXXXXXXX" --json
```

## Agent 工作流

1. 默认使用 `--mode user`（用户 OAuth）。
2. 无 token 或 token 过期时先执行 `login`。
3. 调用 `feishu2md.py` 拉取文档，默认开启图片本地化。
4. 返回本地 Markdown 路径与 assets 目录路径。

## 保真策略

- **标题**：默认使用飞书文档标题作为 `.md` 文件名。
- **结构**：优先使用飞书 `raw_content`，保留标题层级、列表、代码块、表格。
- **图片**：尝试下载飞书图片到输出目录下的 `assets/`，并替换为相对路径（如 `assets/xxx.png`）。

## 限制

| 项 | 说明 |
|----|------|
| 接口能力 | 基于飞书 `raw_content`，极复杂布局可能与飞书页面有差异 |
| 图片权限 | 个别图片链接可能受权限/时效限制，失败时保留原始 URL |
| 文档类型 | 优先支持云文档（docx / wiki 指向 docx） |

## 配置

凭证与 `md-to-feishu` 一致：`~/.jeemoo/secrets.env`。详见 [reference.md](reference.md)。
