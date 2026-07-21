---
deck_id: incoa
kind: deck
category: brand
summary: 积木网(JEEMOO) 企业AI应用/FDE咨询交付方案 —— 深藏青+点缀金的高端咨询提案风格，适合方法论分享、爆品打法拆解、AI落地路线图、阶段门禁与工作坊。
keywords: [咨询提案, 企业AI, FDE, 深色高端, 金色点缀, 方法论]
primary_color: "#152238"
canvas_format: ppt169
replication_mode: fidelity
placeholders:
  01_cover: ["{{BRAND_LOGO}}", "{{TITLE}}", "{{SUBTITLE}}", "{{TAGLINE}}", "{{AUTHOR}}", "{{DATE}}", "{{STATEMENT}}"]
  02_chapter: ["{{EYEBROW}}", "{{CHAPTER_NUM}}", "{{CHAPTER_TITLE}}", "{{CHAPTER_DESC}}"]
  02_toc: ["{{EYEBROW}}", "{{PAGE_TITLE}}", "{{TOC_ITEM_1_TITLE}}", "{{TOC_ITEM_1_DESC}}", "{{TOC_ITEM_2_TITLE}}", "{{TOC_ITEM_2_DESC}}", "{{TOC_ITEM_3_TITLE}}", "{{TOC_ITEM_3_DESC}}", "{{TOC_ITEM_4_TITLE}}", "{{TOC_ITEM_4_DESC}}"]
  03_content: ["{{EYEBROW}}", "{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{CONTENT_AREA}}", "{{PAGE_NUM}}"]
  03a_content_statement: ["{{EYEBROW}}", "{{STATEMENT}}", "{{STATEMENT_SUB}}", "{{PILL_1}}", "{{PILL_2}}", "{{PILL_3}}", "{{PAGE_NUM}}"]
  03b_content_three_col: ["{{EYEBROW}}", "{{PAGE_TITLE}}", "{{COL_1_TITLE}}", "{{COL_2_TITLE}}", "{{COL_3_TITLE}}", "{{PAGE_NUM}}"]
  03c_content_dual_panel: ["{{EYEBROW}}", "{{PAGE_TITLE}}", "{{LEFT_TITLE}}", "{{RIGHT_TITLE}}", "{{PAGE_NUM}}"]
  03d_content_card_grid: ["{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{PAGE_NUM}}"]
  03e_content_flow: ["{{EYEBROW}}", "{{PAGE_TITLE}}", "{{CALLOUT}}", "{{PAGE_NUM}}"]
  03f_content_matrix: ["{{TAG}}", "{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{PAGE_NUM}}"]
  03g_content_timeline: ["{{TAG}}", "{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{SIDEBAR_TITLE}}", "{{PAGE_NUM}}"]
  03h_content_gates: ["{{TAG}}", "{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{SIDE_TITLE}}", "{{PAGE_NUM}}"]
  04_ending: ["{{THANK_YOU}}", "{{ENDING_SUBTITLE}}", "{{CONTACT_INFO}}", "{{BRAND_LOGO}}"]
---

# INCOA — 积木网企业AI/FDE咨询提案 Design Specification

## I. Template Overview

- **Use cases**: 企业AI落地方法论分享、爆品/内容打法拆解、FDE（Forward Deployed Engineer）咨询交付方案、三阶段战略路线图、阶段门禁（gate）评审、现场工作坊（workshop）流程。
- **Design tone**: 高端咨询、克制稳重、结构化、数据驱动；深色主导 + 金色点缀营造"专业 + 可信 + 有质感"的观感。
- **Theme mode**: 混合（Mixed）—— 内容页以浅灰白背景为主体，封面/章节/侧边强调卡与 callout 条使用深藏青，形成明暗对比节奏。
- **一眼识别**：左上角金色胶囊小标签 + 字母间距英文眉标 + 深藏青粗体大标题（局部用金色斜体或红色强调）+ 右下角超大浅灰"幽灵水印"数字/字母 + 底部 `积木网(JEEMOO.COM)` 页脚线。

## II. Color Scheme

| Role | HEX | 用法 |
|------|-----|------|
| Primary 深藏青 | `#152238` | 封面主面板、章节页背景、深色强调卡、callout 条、图标章内容 |
| Navy-2 次深藏青 | `#1E2D48` | 深色卡片的层次变化、渐变收尾 |
| Charcoal 炭黑 | `#1A1D24` | 封面左侧品牌面板 |
| Accent 点缀金 | `#C79A3E` | 小标签胶囊、标题下划线、强调斜体字、图标高亮、CTA 按钮 |
| Gold-soft 浅金 | `#E6CE93` | 金色渐变高光、深色底上的金色文字 |
| Secondary 蓝 | `#2E6DA4` | "核心洞察"竖条、FDE/门禁类蓝色表头、业务侧箭头 |
| Blue-deep 深蓝 | `#24567F` | 蓝色表头渐变收尾 |
| Emphasis 红 | `#C4382A` | 强烈观点标题强调（如"七步闭环""可复制的内容判断系统"）、门禁不达标提示 |
| Background 浅底 | `#F4F5F7` | 内容页画布背景 |
| Card 白卡 | `#FFFFFF` | 浅色卡片，配 `#E4E7EC` 描边 |
| Card-soft 浅灰卡 | `#F7F8FA` | 次级浅卡 / 象限底 |
| Cream 奶油 | `#F1ECDF` | 圆形图标章底色 |
| Ink 标题墨 | `#1F2A3C` | 深色标题文字 |
| Body 正文 | `#3C4757` | 正文 |
| Muted 次要 | `#8A94A3` | 眉标、页脚、说明文字 |
| Watermark 水印 | `#EAECEF` | 浅底上的超大幽灵数字/字母 |

**应用规则**：门禁卡表头在蓝（业务/工程门）与金（质量/治理门）之间交替；三阶段/多卡布局中"本方案落地阶段"用深藏青卡从浅卡中被高亮出来；红色仅用于观点性强调标题，不做大面积铺色。

## III. Typography

- 中文：`'Microsoft YaHei', 'PingFang SC', 'Source Han Sans SC', sans-serif`，标题 bold。
- 英文眉标 / 页脚 / 编号：`Arial, 'Helvetica Neue', sans-serif`，大写 + `letter-spacing` 2–3。
- 标题强调采用 `font-style="italic"` 的金色字，或 `#C4382A` 红色字，与黑色标题混排。
- Body 基线约 15px（`spec_lock.md` 按项目最终锁定）。

## IV. Signature Design Elements

1. **金色胶囊小标签**：左上角 `#C79A3E` 圆角矩形（约 110×26，rx13）+ 大写白字（`WORKSHOP` / `SELECTION` / `WHY FDE` / `S2 / S3`），是场景/章节的身份标识。
2. **英文眉标 + 大标题**：字母间距灰色小眉标（中英混排，如"我们的终极目标 OUR MISSION"）压在粗体大标题之上；部分标题下方带一段约 180×3 的金色下划线。
3. **"核心洞察"副标题条**：标题下方 4px 蓝色竖条 + 灰色说明文字，承载该页一句话洞察。
4. **超大幽灵水印**：右下角超大浅灰（`#EAECEF`）数字或字母（页码、章节号、`FDE`），作为页面锚点，深色页上用低亮度藏青实现。
5. **页脚系统**：底部一条 `#E4E7EC` 细分隔线，左下 `积木网(JEEMOO.COM)`，右下页码，均为 12px 灰字。
6. **卡片三态**：浅白卡（白底 + `#E4E7EC` 描边 + rx12）/ 深藏青卡（`#152238` + 白字 + 金/图标点缀）/ 高亮卡（深卡置于浅卡群中）。
7. **圆形图标章**：奶油色圆（`#F1ECDF`）内嵌深藏青线性/实心小图标，用于流程节点与协同机制卡。
8. **深色 callout 金标条**：页面底部整宽深藏青圆角条，左侧金色图标 + 关键结论文字，用于沉淀"一句话要点"。
9. **矩形箭头连接**：横向卡片之间用金色小箭头（`›`/三角）连接，表达流程推进。

## V. Page Roster

| File | Role | Description |
|------|------|-------------|
| `01_cover.svg` | cover | 左炭黑品牌面板（金标 + 大标题 + 金色副标 + 署名日期 + `FDE` 水印）/ 右满幅封面图（内置 `cover_illustration.png`，`slice` 铺满并叠深色渐变），图上叠半透明白色圆角声明卡。适合方案封面；替换 `cover_illustration.png` 即可换图。 |
| `02_chapter.svg` | chapter | 深藏青满幅章节分隔页：右下超大金色章节号水印 + 眉标 + 大标题 + 金色下划线 + 描述。适合阶段/篇章切换。 |
| `02_toc.svg` | toc | 浅底目录页：左标题区 + 右四项带序号的目录条（序号 + 标题 + 描述），金色序号。 |
| `03_content.svg` | content | 通用内容页：眉标 + 标题 + 蓝竖条"核心洞察"副标 + 自由内容区 `{{CONTENT_AREA}}` + 页脚 + 右下水印。内容区留白由 AI 自由排布。 |
| `03a_content_statement.svg` | content | 大幅使命宣言页：居中/左对齐超大双行陈述（局部金色斜体强调）+ 一行说明 + 底部三枚深藏青药丸能力标（金色图标）。适合价值主张/终极目标。 |
| `03b_content_three_col.svg` | content | 三阶段并列卡：三张等宽卡（中间或指定一张为深藏青高亮），圆形图标章 + 阶段名 + 副题 + 要点列表 + 金色"重点阶段"角标。适合三阶段蓝图/路线图。 |
| `03c_content_dual_panel.svg` | content | 双栏大面板对比：左浅卡 + 右深藏青卡（或按需互换），各带勾选要点列表与角标；适合"现状 vs 要务""轨道A vs 轨道B"。 |
| `03d_content_card_grid.svg` | content | 2×4 编号流程卡网格（01–08），末卡深藏青高亮；红色标题强调 + 一句话核心洞察。适合"N 步闭环/流程全景"。 |
| `03e_content_flow.svg` | content | 横向流程：4 个圆形图标章卡用金色箭头连接 + 底部整宽深藏青 callout 金标条承载关键结论。适合协同机制/价值链条。 |
| `03f_content_matrix.svg` | content | 2×2 价值-可行性矩阵（右上象限金色高亮 + 星标）+ 右侧两张评分维度卡；坐标轴中文标注。适合优先级筛选。 |
| `03g_content_timeline.svg` | content | 左侧 4 段"时间盒"轮次条（深号码块 + 标题 + 说明）+ 右侧深藏青侧栏卡（进度条 + 规则列表 + 金色产出按钮）。适合工作坊/议程节奏。 |
| `03h_content_gates.svg` | content | 左深藏青总结卡 + 右 2×2 门禁卡（蓝/金交替表头 + 要点 + 红色底线提示）。适合阶段门禁/上线评审。 |
| `04_ending.svg` | ending | 深藏青满幅结束页：居中金线分隔的致谢主句 + 副标语 + 联系方式 + 底部品牌名，右下 `FDE` 幽灵水印。 |

## VI. Bundled Assets

模板目录内附带以下图片资源，可被 SVG 直接引用（同目录相对路径）：

| 资源 | 用途 |
|------|------|
| `cover_illustration.png` | `01_cover.svg` 右侧满幅封面图；替换此文件即可整体换封面配图。 |
| `brand_icon_dark.png` | 深色背景上的品牌/装饰图标（备用）。 |
| `brand_icon_light.png` | 浅色背景上的品牌/装饰图标（备用）。 |
| `checkmark.png` | 勾选要点图标（备用，双栏/列表可复用）。 |

> 换肤指引：主色 `#152238`（藏青）、强调色 `#C79A3E`（金）、警示红 `#E23A2E`，如需整体改色，可在各 SVG 中统一替换这三个色值。
