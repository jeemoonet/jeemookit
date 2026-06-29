---
name: txt-to-image
description: >-
  为 Markdown 文档配图：结构图用 Mermaid、专利附图用 SVG、宣传场景图用 GenerateImage。
  专利图与宣传图统一存放 assets/。在用户编写设计文档、专利交底书、产品介绍时使用；导出 Word 配合 md-to-word。
---

# txt-to-image · 文档配图规范

导出 Word 见 `md-to-word` Skill。

## 三类图例

| 类型 | 适用 | 格式 | 工具 | 存放 |
|------|------|------|------|------|
| **结构图** | 架构、流程、时序、组件关系 | Mermaid 代码块 | Agent 编写 | 内嵌 Markdown |
| **专利图** | 交底书附图（黑白线稿、图号） | SVG | Agent 编写 | `assets/图N-描述.svg` |
| **宣传图** | 用户场景、主视觉、氛围插画 | PNG | **GenerateImage** | `assets/主题-简述.png` |

**选型**：可维护的结构 → Mermaid；审查级线稿 → SVG；视觉场景 → GenerateImage。**专利图禁用 GenerateImage。**

| 文档 | 识别 | 用图 |
|------|------|------|
| 功能/架构设计 | 「功能设计」「技术方案」「架构设计」 | 结构图 |
| 专利交底书 | 「专利交底书」 | 专利图 |
| 产品介绍/宣传 | 「产品介绍」「说明书」「宣传」 | 结构图 + 宣传图 |

**assets/ 约定**：文档同级建 `assets/`；专利 SVG 与宣传 PNG 同目录，靠文件名区分（专利以 `图N-` 开头）。

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

## 2. 专利图（SVG → assets/）

- 文档同目录建 `assets/`；可选 `图例说明.md` 登记（图号 | 文件名 | 说明）。
- 命名 `assets/图N-简短描述.svg`；白底黑线、`viewBox` 明确；字体 SimHei / Microsoft YaHei。
- 「## 5. 附图说明」引用，图号与文件名一致：

```markdown
- **图1**（`assets/图1-整体流程.svg`）：方法整体流程示意图
```

---

## 3. 宣传图（GenerateImage → assets/）

- 与专利图共用 `assets/`；生成后落盘再引用。
- 一图一场景；`![中文场景说明](assets/xxx.png)` 必填 alt；可与同节 Mermaid 互补，不重复同一信息。

```markdown
![用户场景：开发者用 Cursor 写 Markdown 并导出 Word](assets/jeemookit-user-scenario.png)
```

**Prompt 要素**：主体 + 动作 + 风格 + 约束（如 16:9、少文字、无商标 UI）。

| 用 GenerateImage | 改用 Mermaid / SVG |
|------------------|-------------------|
| 用户场景、主视觉 | 架构、流程、数据流 |
| 协作氛围 | 专利附图、带标号线稿 |

---

## 检查清单

- [ ] 结构图 = Mermaid；外部图均在 `assets/`（专利 `*.svg`、宣传 `*.png`）
- [ ] 专利图号与文件名一致；引用路径存在
- [ ] 交付 Word → 调用 `md-to-word`
