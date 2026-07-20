# Agent 协作说明

本文件供 **Cursor Agent / 开发者** 快速理解仓库结构与文档归档规则。人类可读索引见 [doc/README.md](doc/README.md)。

## 1. 仓库目录结构

```text
/
├── AGENT.md                        # 本文件
├── .jeemoo/project.json            # 部署目标（serverId、remotePath，无密钥）
├── src/                            # 开发代码，根据开发框架可以细分web/admin/api等子目录
├── doc/                            # 项目文档（按阶段分子目录，见 §2）
└── scripts/                        # 启动/部署脚本（start.sh、start.ps1、deploy.ps1）
```

## 2. 文档目录（`doc/`）

按**项目阶段**编号子目录（与 DOC 编号前缀对应）：


| 子目录             | 阶段    | 放置内容                                                                          |
| --------------- | ----- | ----------------------------------------------------------------------------- |
| `doc/0.项目管理/`   | 项目管理  | `DOC-PLAN-`*、`DOC-MVP-*`                                                      |
| `doc/1.需求调研/`   | 需求    | `DOC-REQ-*`                                                                   |
| `doc/2.产品设计/`   | 产品与设计 | `DOC-PROD-*`、`DOC-USER-*`、`DOC-ADMIN-*` ；子目录 `sop/`、`knowledge-base/`、`demo/` |
| `doc/3.开发/`     | 开发    | `DOC-DEV-*、DOC-DB-*`（技术方案、开发规范）                                               |
| `doc/4.部署发布/`   | 部署发布  | `DOC-SRV-*`、`DOC-DEP-*`、启动/部署操作手册                                             |
| `doc/9.参考资料/`   | 参考    | 外部技术分析（无正式 DOC 编号）                                                            |
| `doc/README.md` | —     | 文档总索引                                                                         |


## 3. 服务器部署

配置与密钥分离：**项目内只存服务器 ID 与远程路径，密钥在用户目录**。

服务器部署：
Server: OpenClaw1Y
IP: 43.128.98.192
User: ubuntu
SSH KEY: openclaw.pem

Server: JeemooApps
IP: 81.70.187.19
User: ubuntu
SSH KEY: JeemooApps.pem

## 4. 本地启动脚本（`scripts/`）

提供跨平台启动脚本，用于一键拉起前后端并打开浏览器：

- macOS / Linux：`bash scripts/start.sh`
- Windows PowerShell：`powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1`

启动脚本强制约定（Agent 必须遵守）：

- 必须生成并维护 `scripts/start.*`（至少包含 `start.sh` 与 `start.ps1`）。
- 启动应用时必须优先使用 `scripts/start.*`，禁止直接要求用户分别手动启动前后端。
- 若项目目录结构变化，必须同步更新 `scripts/start.*` 的默认目录与命令，确保新成员一键可启动。
- 新增前后端启动相关文档时，命令示例必须使用 `scripts/start.*`。

可选环境变量（默认值）：

- `FRONTEND_DIR`（`src/web`）
- `BACKEND_DIR`（`src/api`）
- `FRONTEND_CMD`（`npm run dev`）
- `BACKEND_CMD`（`npm run dev`）
- `FRONTEND_URL`（`http://localhost:3000`）

示例：

```bash
FRONTEND_DIR=frontend BACKEND_DIR=backend FRONTEND_URL=http://localhost:5173 bash scripts/start.sh
```

## 5. 前端落地页 / 营销页

做落地页、作品集、营销站或 UI 改版时，优先加载全局 Skill **`design-taste-frontend`**（taste-skill v2）：先 Brief 推断与三档 Dial，再实现，交付前跑 Pre-Flight。

