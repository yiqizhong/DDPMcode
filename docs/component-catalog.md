# 组件清单（Component Catalog）· headset 品类

> **性质**:一份**活清单**,记录当前所有可复用 UI 组件:它是什么、何时用、通用不通用、Agent 怎么调用。
> **每次新增/改名/删除组件都要更新这里。** 类名用大白话,括号里是代码里的真实文件/术语(映射不丢)。
> 设计决策的"为什么"见 [`function-card-architecture.md`](function-card-architecture.md);去哪读/改见 [`navigation.md`](navigation.md)。
> **最后更新**:2026-06-26 · 维护规则见文末。

## 0. 速览(可复用的"件"有哪三类)

| 类别 | 一句话是什么 | 数量 | 位置 |
|---|---|---|---|
| **① 卡内控件积木**(子控件 / `subcontrols/`) | 拼进功能卡里的小控件:开关、下拉、滑杆、分段… | 6 文件(+ 开关无独立文件) | `.agents/skills/headset-shared/subcontrols/` |
| **② 通用功能卡骨架**(空白卡壳 / `function-frame.html`) | 没现成卡时用的**空模板**:一个标题 + 空 body,往里塞积木拼出卡 | 1 | `.agents/skills/headset-function/templates/` |
| **③ 可换内容的槽位 + 联动机制**(slot / CSS) | 模板里"能换内容 / 会联动"的位置 | 4 | 嵌在上面文件 + `headset.css` |

> 上面 **①积木 / ②骨架 / ③槽机制** 是跨产品复用的"件"。`functions/` 目录里那些**整张的功能卡**另算,且分两类:
> 一类是**现成可套用的卡**(`single-control`/`eq-audio`/`promotion-download`),另一类是开发时建的**演示样例**
> (`collaboration`/`auto-power-off`/`noise-control`)——清点与区分见文末附录。

**调用模型一句话**:`gen-subpage` 读 manifest 的 `functions[]` → 若某功能 `id` **正好命中 `functions/` 里已有的卡**就
整张复制(D8,纯 id 不认名字),**否则**用 `headset-function` 复制②空白卡壳 + copy ①积木**现拼**。"用哪个控件"是
**编写期**按选型表决定、冻进 manifest;生成期只照抄。

---

## ① 卡内控件积木(子控件 · `subcontrols/`)

> 这些是拼进功能卡里的小控件。按"长什么样、放哪"分成四组——**A 是装控件的行,B/C 是控件本体,D 是辅助。**

### A. 行容器(装一个控件的标准行)

| 件 | 是什么 / 何时用 | 通用性 | Agent 如何调用 |
|---|---|---|---|
| **标题控件行**(`toggle.html`) | 标准 labeled toggle row:左边标题,右边原生开关。**最高频** | ✅ 通用 | copy 进卡 body(`.function-content`),每个开关类设置占一行,填 `{label}`/`{id}-state` |

### B. 紧凑控件(放进行右侧 / 卡 header 的那个槽——**二选一,可互换**)

> 开关和下拉是**同一类兄弟**:都塞进 `toggle` 派生出的 row / single-control 右侧的 `CONTROL` 槽,都靠 `margin-left:auto` 靠右。换哪个由数据决定。

| 件 | 是什么 / 何时用 | 通用性 | Agent 如何调用 |
|---|---|---|---|
| **开关**(switch · **无独立文件**,内嵌在 `toggle.html`) | 开/关二选一(布尔值) | ✅ 通用 | 是 `toggle` 的默认右控件;填 `{id}-state`,加 `checked`=ON |
| **下拉**(`dropdown.html`) | 单选,但**选项多 / 位置紧**(如关机超时 15min…8h)。自定义 `<details>` 浮层,`position:fixed` 逃出滚动容器裁剪 | ✅ 通用 | 换进 `toggle`/single-control 的 `CONTROL` 槽;实证示例见附录的 auto-power-off |

### C. 整宽控件(占满一行,放在卡 body,**不能进 header**)

| 件 | 是什么 / 何时用 | 通用性 | Agent 如何调用 |
|---|---|---|---|
| **滑杆**(`slider.html`) | 一个值落在**有序**区间/档位(音量、强度、Sidetone 等级) | ✅ 通用 | copy 进 body;填 `{min}/{max}/{val}`;一行 `oninput` 驱动数值气泡 |
| **分段选择**(`segmented.html`) | 从 **2–4 个项选 1**、要全部可见 / 带图标(模式切换:ANC/Transparency) | ✅ 通用 | copy 进 body;加/删 `.segment` 配数量;可选条件面板。**选项+面板上限 6** |
| **预设网格**(`preset-grid.html`) | **4–6 个预设**平铺(EQ 预设、音效 profile) | ✅ 通用 | copy 进 body;2 列网格;末项可整行。**上限 6** |

### D. 辅助件

| 件 | 是什么 / 何时用 | 通用性 | Agent 如何调用 |
|---|---|---|---|
| **信息提示**(`info-tooltip.html`) | 控件旁的 ⓘ 图标 + hover 说明 | ✅ 通用(可选) | 有说明才 copy 进该行 `.function-icons`;没有就删掉那个 div |

**选哪个控件**(细则见 `subcontrols/README.md` + `headset/AGENTS.md` 选型表):
开/关→**开关**;有序值→**滑杆**;2–3 项→**分段**;4 项看语义(模式切换→分段 / 预设→网格);5–6 项→**预设网格**;选项多或位置紧→**下拉**。

---

## ② 通用功能卡骨架(空白卡壳 · `function-frame.html`)

> 当某功能在 `functions/` 里**没有对应 id 的卡**时,用这个空模板**按产品需求现拼**一张。

| 件 | 是什么 / 何时用 | 通用性 | Agent 如何调用 |
|---|---|---|---|
| **空白功能卡壳**(`function-frame.html`) | 一个**空卡模板**:标题 + 可选 ⓘ 槽 + 空 body 槽。往 body 里按需 copy ①的积木,拼出一张新卡 | ✅ 通用(万能兜底) | `headset-function` 复制它,填标题,再往 `data-slot="subcontrols"` 按序 copy ①积木 |

---

## ③ 可换内容的槽位 + 联动机制(slot / CSS · 嵌在上面文件 + `headset.css`)

> 这些不是独立文件,是模板里"能换内容 / 会联动"的位置和规则。

| 机制 | 是什么 / 何时用 | 通用性 | Agent 如何调用 |
|---|---|---|---|
| **可换控件槽**(header 右侧的 `CONTROL START/END`) | header 右侧控件要从默认**开关**换成**下拉**时用 | ✅ 通用,但**只限紧凑控件**:开关 ↔ 下拉(滑杆/分段/预设是整宽,禁入 header) | 把 `CONTROL` 块整段换成开关或下拉。**换法规则只有一份权威:`toggle.html`**;single-control 引用它 |
| **空卡的两个填充槽**(②骨架的 ⓘ 槽 / body 槽) | 用②空白卡壳现拼卡时 | ✅ 通用 | 往 body 槽按序 copy ①积木;有说明才往 ⓘ 槽放 info-tooltip |
| **分段条件面板**(`segment-panels`,在分段/预设内) | 选某一段后**冒出**一组子控件(选 ANC 露出 XYZ) | ✅ 通用(上限 6) | 用结构表达:第 N 段选中→第 N 面板显示,纯 CSS `:has()`,0 JS |
| **父子开关联动**(`subfn-group`) | 父开关 OFF 时**置灰**旗下子控件(Sidetone 关→滑杆变灰) | ✅ 通用 | 把父开关 + 依赖件包进 `.subfn-group`,纯 CSS `:has()` 置灰 |

---

## 维护规则(怎么更新这份清单)

发生以下情况时,**同一次改动里**更新本文件:

1. **新增积木 / 骨架 / 槽机制** → 在 ①②③ 对应类别加一行(是什么 / 何时用 / 通用性 / 调用),并更新第 0 节速览数量。
2. **改名 / 删除** → 改/删对应行;若旧名可能被人查找,在 [`function-card-architecture.md`](function-card-architecture.md) 旧名处留"(现名 …)"括注。
3. **通用性变化** → 更新该行通用性标记。
4. **调用规则变化**(路由、可换控件范围、控件选型表)→ 同步 `headset/AGENTS.md` + 本表"调用"列。
5. **增删功能卡** → 真实可用卡放 `functions/`(id 路由)、demo/范例放 `examples/`(不路由);更新文末附录对应组,别混。
6. 改完顶部"最后更新"日期。

> **对所有组件都成立的约束**:片段内**不写内联 `<style>`**,样式全进 `headset.css` 用 `shared/tokens.css` 的 token;
> markup 一律 **copy 不 generate**;生成期剥掉 `data-slot`/`data-instruction`/`data-property` 标记;
> **本系统不做 a11y**(无 aria/role/键盘导航/focus-ring,用户偏好)。

---

## 附录 · 现有的功能卡(A 在 `functions/` · B 在 `examples/`)

> 功能卡分两种:**A 现成可套用的**(真要用,直接复制/填槽)和 **B 演示样例**(开发时建来验证架构,**不是产品卡**)。
> A 放在 id 路由的 `functions/`;**B 已隔离到 `examples/`**(不参与 id 路由,gen-subpage 不从那复制)。
> 注意:即便有 A,真实产品的**其它**功能卡仍要**按需求**用 ①②③ 拼/定义——A 只是已经建好的那几张。

### A. 现成可套用的卡(在 `functions/`,id 路由)

| 卡 | 内含控件 | 怎么用 | 通用性 |
|---|---|---|---|
| **single-control** | 1 开关 | 任意"单个 header 控件、无内容区"功能的**通用模板**;右控件可换开关/下拉(规则见 toggle) | ✅ 通用模板 |
| **eq-audio** | 5 拖拽点 | 产品有音频均衡器就**直接套这张**;结构写死、固定专用、同页限一张 | ✅ 该功能的现成卡(固定) |
| **promotion-download** | 2 按钮 | 下载推广卡;**填槽**(图标/文案/CTA)即可换品牌复用(默认恰好是 Dell) | ✅ 填槽复用 |

### B. 演示样例(在 `examples/` · **不参与 id 路由**,开发时建来验证架构)

| 卡 | 内含控件 | 它其实是什么 | 备注 |
|---|---|---|---|
| **collaboration** | 2 开关+1 滑杆+ⓘ | **参考装配范例**:教 ①② 怎么拼出一张卡 | 仍被 frame/SKILL/README/single-control 当教学范例引用(指向 `examples/`) |
| **auto-power-off** | 1 下拉 | **"开关换下拉"的证明卡**(验证可换控件槽) | swap 能力的唯一实证 |
| **noise-control** | 1 开关+1 滑杆 | 弱模型测试用的**简化版**(≠ Figma 真三段降噪) | 真三段版待建 |

> **已隔离(2026-06-26)**:B 组从 `functions/` 移到 `examples/`、摘出 id 路由;同步改了 4 处教学引用
> (frame / SKILL / subcontrols README / single-control)+ `functions/README` + 预览宿主页;测试机型 **HS-DEMO** 的
> manifest 已改为引用 A 组真实卡(`eq-audio` + `promotion-download`),旧生成页已删(可用 gen-subpage 重生成)。
> 结果:教学范例 / swap 证明都保住,id 注册表只剩真实可用卡。
