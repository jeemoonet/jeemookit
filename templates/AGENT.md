
# Agent 协作说明

本文件供 **Cursor Agent / 开发者** 快速理解仓库结构与文档归档规则。人类可读索引见 [doc/README.md](doc/README.md)。


## 1. 仓库目录结构

```text
/
├── AGENT.md                        # 本文件
├── .jeemoo/project.json            # 部署目标（serverId、remotePath，无密钥）
├── src/                            # 开发代码，根据开发框架可以细分web/admin/api等子目录
├── doc/                            # 项目文档（按阶段分子目录，见 §2）
└── scripts/                        # 安装部署脚本（含 deploy.ps1）
```


## 2. 文档目录（`doc/`）

按**项目阶段**编号子目录（与 DOC 编号前缀对应）：

| 子目录 | 阶段 | 放置内容 |
|--------|------|----------|
| `doc/0.项目管理/` | 项目管理 | `DOC-PLAN-*`、`DOC-MVP-*` |
| `doc/1.需求调研/` | 需求 | `DOC-REQ-*` |
| `doc/2.产品设计/` | 产品与设计 | `DOC-PROD-*`、`DOC-USER-*`、`DOC-ADMIN-*`、`DOC-DES-*`、`DOC-KB-*`、`DOC-KG-*`、`DOC-CONN-*`；子目录 `sop/`、`knowledge-base/`、`demo/` |
| `doc/3.开发/` | 开发 | `DOC-DEV-*`（技术方案、开发规范） |
| `doc/4.部署发布/` | 部署发布 | `DOC-SRV-*`、`DOC-DEP-*`、启动/部署操作手册 |
| `doc/9.参考资料/` | 参考 | 外部技术分析（无正式 DOC 编号） |
| `doc/README.md` | — | 文档总索引 |

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
