---
name: design-doc-figures
description: >-
  编写功能设计、技术方案、专利交底书类 Markdown 时，自动生成 Mermaid 流程图或
  专利 SVG 附图，并与 markdown-to-word Skill 配合导出 Word。在用户编写设计文档、
  专利交底书、架构说明、附图说明时使用。
---

# 设计文档与图例规范

与全局 Skill `markdown-to-word` 配合使用。导出命令见该 Skill 或项目根 `AGENT.md`。

## 文档类型判断

| 类型 | 识别 | 图例方式 |
|------|------|----------|
| 功能/架构设计 | 路径或标题含「功能设计」「技术方案」「架构设计」 | Mermaid 内嵌 |
| 专利交底书 | 路径含「专利交底书」 | `图例/*.svg` 外部文件 |

## 设计文档路线（Mermaid）

1. 架构、流程、时序用 ` ```mermaid ` 代码块。
2. 优先 `flowchart TB/LR`、`sequenceDiagram`；节点标签用中文。
3. 控制节点数量，避免 Mermaid 渲染失败。
4. 不写外部 PNG（除非已有素材）；导出 Word 时由 md2docx 自动渲染。

示例（在 MD 正文中插入 mermaid  fenced block）：

    ### 2.1 整体架构

    ```mermaid
    flowchart TB
        A[数据采集] --> B[AI 分析]
        B --> C[方案生成]
    ```

## 专利交底书路线（SVG）

1. 在同目录创建 `图例/` 与 `图例说明.md`。
2. 每张附图：`图例/图N-简短描述.svg`（黑白线条、SimHei/Microsoft YaHei）。
3. 在「## 5. 附图说明」引用：

```markdown
- **图1**（`图例/图1-整体流程.svg`）：方法整体流程示意图
```

4. `图例说明.md` 表格：图号 | 文件名 | 说明。

SVG 要求：

- `viewBox` 明确，白底黑线
- 标题：`图N  xxx示意图`
- 与交底书第 5 节图号一一对应

## 完成检查清单

- [ ] 正文图号与 `图例/` 文件名一致
- [ ] Mermaid 块可解析（设计文档）
- [ ] 所有 SVG 文件已落盘（专利文档）
- [ ] 需要交付 Word 时调用 `markdown-to-word` Skill 导出
