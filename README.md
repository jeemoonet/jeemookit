# jeemookit

Jeemoo 新项目**初始化模板**：全局 **Skills**、项目 **AGENT.md** 与启动脚本。

新项目初始化时调用本目录下的 `install.ps1` / `install.sh`。

## 设计原则


| 内容           | 存放位置                | 进 Git  |
| ------------ | ------------------- | ------ |
| Skills       | `~/.cursor/skills/` | kit 仓库 |
| AGENT.md     | 项目根目录               | ✅ 项目仓库 |
| SSH / API 密钥 | `~/.jeemoo/`（本机）    | ❌ 永不   |


## 包含内容


| 组件                      | 安装位置                | 说明                                        |
| ----------------------- | ------------------- | ----------------------------------------- |
| `pdf-to-md`             | `~/.cursor/skills/` | PDF → Markdown，含表格、图片与 OCR                |
| `word-to-md`            | `~/.cursor/skills/` | Word (.docx) → Markdown，含标题、列表、表格         |
| `md-to-word`            | `~/.cursor/skills/` | MD → Word，Mermaid/SVG 自动嵌入                |
| `txt-to-image`          | `~/.cursor/skills/` | Markdown 配图：Mermaid / SVG / GenerateImage |
| `md-to-feishu`          | `~/.cursor/skills/` | MD → 飞书云文档（格式同步，依赖 md-to-word）            |
| `feishu-to-md`          | `~/.cursor/skills/` | 飞书云文档 → 本地 Markdown（保留标题、结构、表格并尽量本地化图片）   |
| `AGENT.md` 模板           | 目标项目根目录             | 项目级 Agent 约定                              |
| `scripts/start.*`       | 目标项目 `scripts/`     | 一键启动前后端                                   |
| `incoa` PPT 模板         | PPT Master `templates/decks/` | 咨询提案 deck 模板，自动部署并注册到已安装的 PPT Master |




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


| 参数                                | 说明                   |
| --------------------------------- | -------------------- |
| `-ProjectRoot` / `--project-root` | 目标项目路径（默认当前目录）       |
| `-ForceAgent` / `--force-agent`   | 覆盖已有 `AGENT.md`      |
| `-SkipDeps` / `--skip-deps`       | 只复制 Skill，不跑 pip/npm |
| `-SkillsOnly` / `--skills-only`   | 仅安装全局 Skills         |
| `-AgentOnly` / `--agent-only`     | 仅复制 AGENT.md 与启动脚本   |
| `-SkipPptMaster` / `--skip-ppt-master` | 跳过 `incoa` PPT 模板部署 |




## PPT Master 模板自动部署

安装时（非 `--agent-only`、未加 `--skip-ppt-master`）会自动部署 `incoa` deck 模板：

1. **探测** PPT Master skill，依次查找 `~/.agents/skills/ppt-master`、`~/.cursor/skills/ppt-master`、`~/.claude/skills/ppt-master`。
2. **已安装** → 把 `assets/ppt-templates/decks/incoa/` 复制到其 `templates/decks/incoa/`，并运行 `scripts/register_template.py incoa --kind deck` 注册到 `decks_index.json`。
3. **未安装** → 不静默安装，改为**提示从 GitHub 页面下载安装** [`hugohe3/ppt-master`](https://github.com/hugohe3/ppt-master)（`npx -y skills add hugohe3/ppt-master` 或 `git clone`），安装完成后重跑 `install` 即自动完成部署。

> 仅注册模板（依赖标准库 Python），不会触发 PPT Master 的 `pip install`。

## 初始化后目录

**全局 Skills**


| 平台            | 路径                             |
| ------------- | ------------------------------ |
| Windows       | `C:\Users\<你>\.cursor\skills\` |
| macOS / Linux | `~/.cursor/skills/`            |


**目标项目**

```
my-app/
├── AGENT.md              ← 项目 Agent 规则
└── scripts/
    ├── start.sh          ← macOS / Linux
    └── start.ps1         ← Windows
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
│   ├── secrets.env.example
│   └── scripts/
│       ├── start.sh
│       └── start.ps1
├── assets/
│   └── ppt-templates/
│       └── decks/
│           └── incoa/        ← 随包分发的 PPT Master deck 模板
└── skills/
    ├── pdf-to-md/
    ├── word-to-md/
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