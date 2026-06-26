# 组件清单（Component Catalog）· headset 品类

> **性质**:这是一份**活清单(living catalog)**,记录当前系统里所有可复用 UI 组件、它们的用途、
> 通用性,以及 Agent 在生成期/编写期如何调用它们。**每次新增/改名/删除组件都要更新这里。**
> 设计推理与决策记录见 [`function-card-architecture.md`](function-card-architecture.md)(思考日志,不是清单)。
>
> **最后更新**:2026-06-26 · **维护规则见文末第 6 节。**

## 0. 速览

| 类别 | 数量 | 位置 |
|---|---|---|
| 原子片段(sub-control) | 6 | `.agents/skills/headset-shared/subcontrols/` |
| 通用 Frame(卡壳) | 1 | `.agents/skills/headset-function/templates/` |
| 功能卡快照(function snapshot) | 6 | `.agents/skills/headset-gen-subpage/templates/functions/` |
| 槽机制(slot mechanism) | 4 | 嵌在上述文件 + `headset.css` |

**调用模型一句话**:`gen-subpage` 读 manifest 的 `functions[]` → **按 `id` 复制整张功能卡**(D8,纯 id,
不认名字)→ 无快照才转 `headset-function`(复制卡壳 Frame + 按 archetype 复制原子拼装)。"用哪个控件"
是**编写期**按 §7 三表决定、冻进 manifest;**生成期只照抄,不推断**。

---

## 1. 原子片段(subcontrols/)—— 卡片 body 里堆叠的最小积木

| 片段 | 何时用 | 通用性 | Agent 如何调用 |
|---|---|---|---|
| **control-row.html** | 布尔开关的标准行"左标题+右控件"。**最高频** | ✅ 通用 | `headset-function`/快照作者 copy 进 `.function-content`,每个开关类子控件一份,填 `{label}`/`{id}-state` |
| **slider.html** | 一个值落在**有序**区间/档位(音量、强度、Sidetone 等级) | ✅ 通用 | copy 进 body;填 `{min}/{max}/{val}`;唯一一行 `oninput` 驱动数值气泡 |
| **segmented.html** | 从 **2–4 个无序项选 1**、要全部可见/带图标(**模式切换**:ANC/Transparency) | ✅ 通用 | copy 进 body;加/删 `.segment` 配选项数;可选 `.segment-panels` 条件面板。**选项+面板上限 6** |
| **preset-grid.html** | **4–6 个预设**平铺选择(EQ 预设、音效 profile) | ✅ 通用 | copy 进 body;2 列网格;末项可 `.segment--span` 整行。**上限 6** |
| **info-tooltip.html** | 某控件**有说明文字**时(可选 ⓘ + hover) | ✅ 通用(可选件) | 有 info 才 copy 进该行 `.function-icons`;无则删该 div |
| **dropdown.html** | 单选枚举但**选项多/位置紧**,不适合平铺(详见第 4 节) | ✅ 通用 | copy 进 body 作下拉;**或 swap 进 header 槽**(见第 5 节) |

**segmented vs preset-grid vs dropdown 的判据**(详见 `subcontrols/README.md` + AGENTS 控件选型表):
2–3 项→segmented;5–6 项→preset-grid;4 项看语义(模式切换→segmented,预设→grid);选项多/位置紧→dropdown。

---

## 2. 通用 Frame —— 万能卡壳兜底

| 文件 | 何时用 | 通用性 | Agent 如何调用 |
|---|---|---|---|
| **function-frame.html** | 某功能**没有专属快照**时的兜底卡壳(标题 + 可选 ⓘ 槽 + 子控件 body 槽) | ✅ 通用 | `headset-function`(Layer-2) copy 它,填 `function-title`,再按 manifest 往 `data-slot="subcontrols"` copy 原子 |

---

## 3. 功能卡快照(functions/)—— 按 `id` 整卡复制

| 卡 | 内含交互件 | 何时用 | 通用性 | Agent 如何调用 |
|---|---|---|---|---|
| **single-control.html** | 1 switch | 整卡=header 里一个布尔开关、下方无内容区 | ✅ 通用 | 按 id copy;header 控件是 swap 槽(规则见 control-row) |
| **auto-power-off.html** | 1 dropdown | header 一行、值从下拉选(关机超时);**swappable 槽的 worked example** | ✅ 通用 | 按 id copy;dropdown 已换入 header 槽,填 `auto-power-off-value`/`-option` |
| **collaboration.html** | 2 switch + 1 slider + ⓘ | 协作/通话降噪(**参考装配范例**) | ✅ 通用(数据驱动拼装,可删/改/增子控件) | 按 id copy + 填 `data-property` |
| **noise-control.html** | 1 switch + 1 slider | 降噪 | ⚠️ **半通用**:结构通用,但当前是**简化测试版**,≠ Figma 真三段(ANC/Transparency/Off);docs §6.8 标"保留中" | 按 id copy;真三段版出现时再换 |
| **promotion-download.html** | 2 按钮(关闭+CTA) | App 下载推广卡 | ⚠️ **半通用**:卡结构通用,默认内容 **Dell 品牌特定**,靠槽覆盖 | 按 id copy + 填 `promo-icon-src`/`promo-title`/`promo-description`/`promo-cta-label` |
| **eq-audio.html** | 5 拖拽点 | 音频均衡器曲线 | ❌ **固定特殊**:5-band 写死、**单实例**(固定 SVG id)、唯一可变是 cy 档位值 | 按 id copy;几乎不填值(除非 manifest 给 6 档之一的初始 cy) |

> **通用性总评**:除 **eq-audio**(固定)外其余基本通用;唯二要留意 **noise-control**(测试版待换真版)
> 和 **promotion-download**(默认内容品牌化、靠槽覆盖才通用)。

---

## 4. Dropdown 下拉菜单(= 第 1 节的 dropdown.html)

| 维度 | 说明 |
|---|---|
| 何时用 | 单选枚举但**选项多/空间紧**,不适合 segmented 平铺(如关机超时 15min…8h) |
| 通用性 | ✅ 通用 |
| 实现 | 有意的**自定义件**(`<details>/<summary>` + 自定义列表 + 定位脚本),非原生 `<select>`——为保 Figma 外观,架构 §8.3/D12 登记为例外。`position:fixed` 浮层逃出滚动容器裁剪 |
| Agent 如何调用 | (a) 作 body 内子控件 copy;(b) **swap 进** control-row / single-control 的 header CONTROL 槽(带 `margin-left:auto`)。实证卡见 `auto-power-off.html` |

---

## 5. 槽机制(Slot)—— 嵌在上述文件 + headset.css 里

| 机制 | 何时用 | 通用性 | Agent 如何调用 |
|---|---|---|---|
| **可替换 header 槽**(`control-row` / `single-control` 的 `CONTROL START/END`) | header 右侧控件要从默认 switch 换成别的 | ✅ 通用,但**仅限紧凑控件**:switch ↔ dropdown(slider/segmented/preset 整宽,禁入 header) | 把 CONTROL 块整段替换为 switch 或 dropdown。**swap 规则单一权威在 `control-row.html`**;single-control 引用它 |
| **Frame 的两个 data-slot**(`function-info` ⓘ槽 / `subcontrols` 子控件槽) | 用 function-frame 兜底拼卡时 | ✅ 通用 | headset-function 往 `subcontrols` 槽按序 copy 原子;有 info 才往 `function-info` 槽放 tooltip |
| **segment-panels 条件面板**(segmented/preset 内) | 选某分段后**冒出**一组子控件(选 ANC 露出 XYZ) | ✅ 通用(上限 6) | 数据结构表达:第 N 段选中→第 N 面板显示,纯 CSS `:has()`,0 JS |
| **subfn-group 依赖**(`.subfn-toggle`/`.subfn-child`) | 父开关 OFF 时**置灰**旗下子控件(Sidetone 关→灰 slider) | ✅ 通用 | 把父 toggle + 依赖件包进 `.subfn-group`,纯 CSS `:has()` 置灰 |

---

## 6. 维护规则(怎么更新这份清单)

每次发生以下情况,**同一个 PR 内**更新本文件:

1. **新增原子/卡/Frame** → 在对应表加一行(何时用 / 通用性 / 调用方式),并更新第 0 节速览数量。
2. **改名/删除** → 改/删对应行;若旧名可能被人查找,在 [`function-card-architecture.md`](function-card-architecture.md) 旧名处留"(现名 …)"括注。
3. **通用性变化**(如 noise-control 换成 Figma 真版、promotion 去品牌化)→ 更新该行的通用性标记。
4. **调用规则变化**(路由、swap 范围、控件选型表)→ 同步 `headset/AGENTS.md` + 本表"调用方式"列。
5. 改完顶部"最后更新"日期。

> 约束提醒(对所有组件都成立):片段内**无内联 `<style>`**,样式只进 `headset.css` 用 `shared/tokens.css` 的
> token;markup 一律 **copy 不 generate**;生成期剥掉 `data-slot`/`data-instruction`/`data-property` 标记。
> 本系统**不做 a11y**(无 aria/role/键盘导航/focus-ring,用户偏好)。
