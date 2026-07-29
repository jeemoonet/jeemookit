---
name: jeemoo-init
description: >-
  将 Jeemoo AGENT 协作约定写入当前项目 .cursor/rules/jeemoo-agent.mdc（alwaysApply）。
  在用户说「jeemoo-init」「初始化 jeemoo 规则」「安装项目 cursor rules」时使用。
---

# jeemoo-init · 写入本项目 Cursor Rules

把 Jeemoo 项目协作约定安装到**当前项目**规则目录（仅本仓库生效，可进 Git）：

```
<project>/
└── .cursor/
    └── rules/
        └── jeemoo-agent.mdc
```

## 何时使用

- 用户说「jeemoo-init」「初始化 jeemoo 规则」「给本项目加 cursor rules」
- 新项目已用 kit 初始化，需要把 AGENT 约定落到 `.cursor/rules/`
- 更新了 Agent 模板后，要同步到本项目 rules

## 执行步骤

1. **工作目录必须是目标项目根**（或传 `--project-root`）。
2. 运行：

**Windows：**

```powershell
python "$env:USERPROFILE\.cursor\skills\jeemoo-init\scripts\apply_rules.py" --project-root .
```

**macOS / Linux：**

```bash
python3 ~/.cursor/skills/jeemoo-init/scripts/apply_rules.py --project-root .
```

在 jeemookit 仓库内、Skill 尚未拷到全局时：

```bash
python skills/jeemoo-init/scripts/apply_rules.py --project-root .
```

3. 确认 stdout 为 `written` / `unchanged`，路径在 `<project>/.cursor/rules/`。
4. 告知用户：**在本项目新开 Agent 对话**后再验证。

## 选项

```bash
# 指定项目根与源文件
python apply_rules.py --project-root /path/to/my-app --source /path/to/AGENT.md

# 仅预览，不落盘
python apply_rules.py --project-root . --dry-run
```

未传 `--project-root` 时：从当前目录向上查找含 `.git` 或 `AGENT.md` 的目录，找不到则用 cwd。

## 行为说明

- **只写项目规则**，不写 `~/.cursor/rules/`，不改 Settings → User Rules。
- 幂等：覆盖同一文件 `jeemoo-agent.mdc`（先备份为 `jeemoo-agent.mdc.bak`）。
- 源内容：默认本 Skill 的 `agent.md`（与 kit `templates/AGENT.md` 保持同步）。
- 格式：Cursor `.mdc`，`alwaysApply: true`。

## 与 install / AGENT.md 的关系

- `install` 仍可复制项目根 `AGENT.md`；本 Skill 额外生成 `.cursor/rules/jeemoo-agent.mdc`，便于 Cursor 按官方规则机制加载。
- 建议将 `.cursor/rules/jeemoo-agent.mdc` 提交进项目 Git，团队共享。
