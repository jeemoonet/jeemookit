---
name: design-taste-frontend
description: >-
  Anti-slop frontend skill for landing pages, portfolios, and UI redesigns.
  Infers design direction from the brief, tunes variance/motion/density dials,
  and ships non-generic interfaces with a strict pre-flight check. Use when
  building marketing sites, portfolios, landing pages, frontend UI, redesigning
  existing pages, or when the user mentions taste-skill, anti-slop, or premium
  frontend design.
---

# design-taste-frontend · Anti-Slop Frontend

基于 [taste-skill](https://github.com/Leonxlnx/taste-skill) v2（MIT）。适用：**落地页、作品集、营销站、现有页面改版**；不适用仪表盘、数据表、多步表单（见 [reference.md](reference.md) §13）。

## 工作流（必须按序）

1. **Brief Inference** — 读需求信号（页面类型、氛围词、参考、受众、品牌资产、约束），输出一行 Design Read：
   `Reading this as: [page kind] for [audience], with a [language], leaning toward [stack].`
   歧义时只问 **一个** 澄清问题；能推断则直接声明并继续。
2. **Three Dials** — 从 Design Read 设定（默认 `8 / 6 / 4`）：
   - `DESIGN_VARIANCE` — 布局实验度（1 对称 · 10 实验）
   - `MOTION_INTENSITY` — 动效深度（1 静态 · 10 电影感）
   - `VISUAL_DENSITY` — 信息密度（1 留白 · 10 密集）
3. **Design System** — 企业/政务 brief 用官方 DS（Fluent、Carbon、GOV.UK 等）；美学 brief 用 Tailwind v4 + Motion，诚实标注灵感来源。见 reference §2。
4. **实现** — 按 dial 与 §4 规则写代码；改版先审计（reference §11）。
5. **Pre-Flight** — 交付前跑完 reference §14 清单；任一项失败则继续改。

## 写代码前必读

打开并按需引用 **[reference.md](reference.md)**：

| 章节 | 内容 |
|------|------|
| §0–1 | Brief 推断、Dial 预设表 |
| §2–3 | 设计系统选型、React/Next + Tailwind v4 + Motion 约定 |
| §4 | 排版、配色、布局、图片、文案密度（核心反 slop 规则） |
| §5–8 | 主动性、性能/a11y、Dial 技术细节、暗色模式 |
| §9 | AI tells 禁用模式（含 em-dash 全站禁止） |
| §10–12 | 模式词汇、改版协议、Block 库 |
| §14 | **Pre-Flight 完整清单** |
| 附录 | 各 DS 安装命令、官方文档、Liquid Glass 近似 |

## 硬规则摘要（易漏）

- **零 em-dash（`—`）** — 全页禁止（§9.G）
- **Hero** — 首屏可见 CTA；标题 ≤2 行；副文 ≤20 词；`min-h-[100dvh]` 非 `h-screen`
- **Eyebrow** — 每 3 个 section 最多 1 个 `uppercase tracking` 小标签
- **配色** — 一页一 accent；premium-consumer 禁用 beige+brass 默认套色
- **图片** — 有 GenerateImage 则优先生成；禁止 div 假截图
- **依赖** — 引入库前先查 `package.json`，缺失则先输出安装命令

## 变体技能

需要更专精方向时，见 [variants.md](variants.md)（可从上游单独安装或复制 SKILL.md）。

## 与 jeemookit 配图技能

营销页需场景图时，配合 `txt-to-image`（宣传图 → `assets/`）；结构图用 Mermaid，不用 taste-skill 替代文档配图规范。
