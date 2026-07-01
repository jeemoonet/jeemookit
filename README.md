# jeemookit

Jeemoo 新项目**初始化模板**：全局 **Skills**、项目 **AGENT.md** 与 **`.jeemoo/project.json`**。

新项目初始化时调用本目录下的 `install.ps1` / `install.sh`。

## 设计原则

| 内容 | 存放位置 | 进 Git |
|------|---------|--------|
| Skills | `~/.cursor/skills/` | kit 仓库 |
| AGENT.md | 项目根目录 | ✅ 项目仓库 |
| 项目部署元数据 | `.jeemoo/project.json` | ✅ 项目仓库 |
| SSH 密钥 (*.pem) | 本地保管 | ❌ 永不 |

## 包含内容

| 组件 | 安装位置 | 说明 |
|------|---------|------|
| `pdf-to-md` | `~/.cursor/skills/` | PDF → Markdown，含表格、图片与 OCR |
| `md-to-word` | `~/.cursor/skills/` | MD → Word，Mermaid/SVG 自动嵌入 |
| `txt-to-image` | `~/.cursor/skills/` | Markdown 配图：Mermaid / SVG / GenerateImage |
| `md-to-feishu` | `~/.cursor/skills/` | MD → 飞书云文档（格式同步，依赖 md-to-word） |
| `feishu-to-md` | `~/.cursor/skills/` | 飞书云文档 → 本地 Markdown（保留标题、结构、表格并尽量本地化图片） |
| `AGENT.md` 模板 | 目标项目根目录 | 项目级 Agent 约定 |
| `project.json` | 项目 `.jeemoo/` | 部署目标与 Agent 权限 |

## 前置要求

- **Windows**: PowerShell 5.1+
- **Python** 3.10+
- **Node.js** 18+（`md-to-word` 需要）
- **Cursor** IDE

## 一键初始化（新项目）

### Windows

```powershell
# 在目标项目根目录执行
D:\Dev\jeemookit\install.ps1

# 或指定项目路径（不存在则自动创建）
D:\Dev\jeemookit\install.ps1 -ProjectRoot D:\Dev\my-new-project
```

### macOS / Linux

```bash
chmod +x /path/to/jeemookit/install.sh
/path/to/jeemookit/install.sh --project-root /path/to/my-new-project
```

### 常用参数

| 参数 | 说明 |
|------|------|
| `-ProjectRoot` / `--project-root` | 目标项目路径（默认当前目录） |
| `-ForceAgent` / `--force-agent` | 覆盖已有 `AGENT.md` |
| `-ForceProject` / `--force-project` | 覆盖 `.jeemoo/project.json` |
| `-SkipDeps` / `--skip-deps` | 只复制 Skill，不跑 pip/npm |
| `-SkillsOnly` / `--skills-only` | 仅安装全局 Skills |
| `-AgentOnly` / `--agent-only` | 仅复制 AGENT.md 与项目配置 |

## 初始化后目录

```
C:\Users\<你>\.cursor\skills\          ← 全局 Skills

D:\Dev\my-app\
├── AGENT.md                           ← 项目 Agent 规则
└── .jeemoo\
    ├── project.json                   ← 部署元数据
    └── .gitignore
```

## 仓库结构

```
jeemookit/
├── install.ps1
├── install.sh
├── manifest.json
├── README.md
├── templates/
│   ├── AGENT.md
│   └── .jeemoo/
│       ├── project.json
│       └── .gitignore
└── skills/
    ├── pdf-to-md/
    ├── md-to-word/
    ├── txt-to-image/
    ├── md-to-feishu/
    └── feishu-to-md/
```

## 扩展 kit

1. 在 `skills/<name>/` 添加 Skill，并在 `manifest.json` 注册
2. 在 `templates/AGENT.md` 补充团队约定

## 许可

MIT
