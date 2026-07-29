---
name: txt-to-image
description: >-
  为 Markdown 文档配图：结构图用 Mermaid、宣传场景图用 GenerateImage。
  宣传图存放 assets/。在用户编写设计文档、产品介绍时使用；导出 Word 配合 md-to-word。
---

# txt-to-image · 文档配图规范

导出 Word 见 `md-to-word` Skill。

## 两类图例

| 类型 | 适用 | 格式 | 工具 | 存放 |
|------|------|------|------|------|
| **结构图** | 架构、流程、时序、组件关系 | Mermaid 代码块 | Agent 编写 | 内嵌 Markdown |
| **宣传图** | 用户场景、主视觉、氛围插画 | PNG | **GenerateImage** | `assets/主题-简述.png` |

**选型**：可维护的结构 → Mermaid；视觉场景 → GenerateImage。

| 文档 | 识别 | 用图 |
|------|------|------|
| 功能/架构设计 | 「功能设计」「技术方案」「架构设计」 | 结构图 |
| 产品介绍/宣传 | 「产品介绍」「说明书」「宣传」 | 结构图 + 宣传图 |

**assets/ 约定**：宣传图放在文档同级 `assets/`。

> **不再生成专利 SVG 附图。** 交底书等若需结构示意，用 Mermaid 结构图。

---

## 1. 结构图（Mermaid）

- 用 ` ```mermaid `；优先 `flowchart TB/LR`、`sequenceDiagram`；标签中文。
- 单图 ≤ 15 节点；架构/流程不放 `assets/` PNG。
- 导出 Word 时 md2docx 自动渲染。

    ### 2.1 整体架构

    ```mermaid
    flowchart TB
        A[数据采集] --> B[AI 分析]
        B --> C[方案生成]
    ```

---

## 2. 宣传图（GenerateImage → assets/）

- 文档同目录建 `assets/`；生成后落盘再引用。
- 一图一场景；`![中文场景说明](assets/xxx.png)` 必填 alt；可与同节 Mermaid 互补，不重复同一信息。

```markdown
![用户场景：开发者用 Cursor 写 Markdown 并导出 Word](assets/jeemookit-user-scenario.png)
```

**Prompt 要素**：主体 + 动作 + 风格 + 约束（如 16:9、少文字、无商标 UI）。

| 用 GenerateImage | 改用 Mermaid |
|------------------|--------------|
| 用户场景、主视觉 | 架构、流程、数据流 |
| 协作氛围 | 带标号的结构示意 |

---

## 检查清单

- [ ] 结构图 = Mermaid；宣传图在 `assets/*.png`
- [ ] 引用路径存在
- [ ] 交付 Word → 调用 `md-to-word`
