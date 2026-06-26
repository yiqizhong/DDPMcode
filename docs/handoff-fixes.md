# Handoff — 组件 & 调用规则修复清单

> **执行者**: Codex (gpt-5.5, reasoning=high) 自主修复;之后由 Claude review。
> **仓库**: DDPMcode（headset 品类 UI 生成系统，三层架构）。
> **冷启动须知**: 你没有此前对话的记忆。本文件是唯一上下文,自包含。先读"背景"再动手。

---

## 0. 背景（必读，30 秒）

这是一个"产品 UI 生成系统":强模型在**编写期(authoring)**把设计意图冻结成预写片段 + 数据;
**弱模型在生成期(generation)只做"看到槽 → 按 archetype 复制对应片段 → 填值"**,不推理、不瞎编。
核心防线是 **"copy, don't create"**(§9.7.4):任何 markup 都从预写片段逐字复制,绝不按描述生成。

- 设计令牌 `shared/tokens.css` → 品类样式 `headset/headset.css` → 页面骨架(skills) → 机型数据(manifest)。
- 方法论 `docs/methodology.md` 是**参照,不是法律**;**与 codebase 冲突时以 codebase 为准**。
- 架构决策日志在 [`docs/function-card-architecture.md`](function-card-architecture.md)(下称"架构文档"),
  里面的 **D1–D18** 是已生效决策,**§7** 是控件选型规则,**§8** 是交互模型。引用它们时按编号查。

四级层级:**Feature(主页按钮/子页) → Content Area(装 1~N 张功能卡) → Function(有标题的卡片)
→ Sub-control(卡内小控件:toggle/slider/segmented/preset-grid/dropdown)**。

---

## 1. 已定决策（不要重新讨论，直接按此执行）

1. **Dropdown 保留自定义件**:不回退到原生 `<select>`。保住 `subcontrols/dropdown.html` 现有的
   Figma 精修外观(`<details>/<summary>` + 自定义 `<ul>`)。要做的是**修裁剪 + 补键盘可选 + 更新文档**
   承认它是"有意的自定义件"。
2. **关键词路由降级为编写期提示**:关键词匹配表**不再覆盖 manifest 的 id**;它改成"编写期挑 id 的参考
   提示"。**生成期(gen-subpage)只按 id 查找**复制快照,否则走 `headset-function`。并修掉危险子串。

---

## 2. 全量问题清单（不筛选）

> 标号:`C*` = 组件/代码;`R*` = 调用规则/文档。每条含 **位置 / 现象 / 根因 / 要做的修改 / 验收**。

### C1 —【P1】Dropdown 展开浮层被 `.content-area` 的 overflow 裁剪
- **位置**: [`headset/headset.css:247`](../headset/headset.css)（`.content-area { overflow-y:auto }`）、
  `headset.css:1127-1144`（`.dropdown-list { position:absolute }`）、
  [`.agents/skills/headset-shared/subcontrols/dropdown.html`](../.agents/skills/headset-shared/subcontrols/dropdown.html)。
- **现象/根因**: dropdown 落地在子页 `.content-area` 内,而该容器 `overflow-y:auto`(按 CSS 规范 x 也算
  `auto`),成为裁剪/滚动容器。`.dropdown-list` 是 `position:absolute` 浮层,展开时会被 content-area
  裁掉;靠近长页面底部时列表被截断或顶出滚动条。预览宿主页 `_preview-card.html` 不带 content-area 外壳,
  所以预览里看不出来。
- **要做的修改**(按已定决策①,保留自定义件):让展开的列表**永不被祖先 overflow 裁剪**,同时保持现有
  Figma 视觉(尺寸/颜色/圆角/chevron 一致)。可接受方案二选一,你判断哪个更稳:
  (a) 用原生 **Popover API**(`popover` 属性 + CSS anchor positioning)让列表渲染到 top layer;
  (b) 保留 `<details>`,列表改 `position:fixed`,用一小段内联脚本在 open 时按 trigger 位置定位
  (滚动/resize 时更新或关闭)。**额外补键盘可选**:↑/↓ 移动高亮、Enter 选中、Esc 关闭、Home/End。
- **验收**: 把 dropdown 放进一个带 `overflow-y:auto`、内容超高的 content-area,滚到底部展开 → 列表完整浮在
  内容之上、不被裁剪;键盘可在不用鼠标的情况下打开并选中某项;选中后回填 trigger 文本并关闭。

### C2 —【P2】eq-audio.html 注释与代码全面不符 + 顶部死区 + 状态属性不一致
- **位置**: [`.agents/skills/headset-gen-subpage/templates/functions/eq-audio.html`](../.agents/skills/headset-gen-subpage/templates/functions/eq-audio.html)。
- **现象/根因**: commit 把 EQ 从 7 档(+4..−2)删成 **6 档(+3..−2)、5 个拖拽点**,但注释没跟着改:
  - L2 `3-band`（实际 5 点）、L4 `±12 dB`（实际 +3..−2）、L98 `7 discrete stops: top (+4 dB)`
    （实际数组只有 6 个 `STOPS_Y=[45.67,71.33,97,122.67,148.33,174]`）、L55 `initial: Bass +4`
    （实际 cy=45.67=+3）、L56 列了 7 个含已删除的 `y=20`。
  - 顶部 manifest cy 公式仍按旧常量(含 +4 / `MIN_Y=20`),弱模型按它填初始 cy 会落在非档位点(初始值不
    snap,只有拖拽才 snap),圆点停在网格线之间。
  - 死区: 竖直网格线仍从 `y=20` 画到 174(L42-46),但最高可达档位是 45.67,顶部约 25px 永远够不到。
  - 拖拽后写 `data-value`(L170),而初始/manifest 用 `data-property`(L58-77),回读状态两处不一致;首次
    拖拽前 `data-value` 为空。
- **要做的修改**:
  - **(必做)** 把上述所有注释改成与"6 档 +3..−2 / 5 个拖拽点"一致;顶部 cy 换算公式改用正确常量
    (0dB=122.67、最高 +3=45.67、最低 −2=174、6 档),并明确"manifest 给的 cy 必须落在 6 个档位之一"。
  - **(必做)** 统一状态属性:拖拽时更新的属性 与 manifest 读取/填充的属性一致(建议拖拽也写
    `data-property` 对应值,或在初始化时把 `data-value` 写上,使任何时刻可一致回读)。不要新增运行时状态层。
  - **(建议,视觉风险低再做)** 消除顶部死区:把竖直网格线 `y1` 与 clip rect 顶部对齐到最高档位
    `45.67`(其余 cx/间距/0dB 线/标签**不动**)。**若你不确定不会改变观感,就跳过几何改动、只保留注释与
    属性修复,并在 PR 说明里标出。**
  - **(可选,低优先)** `getScreenCTM().a`(L165)用 x 缩放算 y 位移,严格应是 `.d`;当前等比缩放下两者
    相等,可改可不改。
  - **(记录,不改代码)** SVG 使用固定 id(`eq-audio`/`eq-grad-audio`…),同页两张 EQ 卡会冲突;当前一页
    一张,作为"单实例约束"在文件顶部注释里写明即可。
- **验收**: 浏览器打开仍能拖拽、曲线/渐变正确;注释与代码一致;任意时刻能从一个统一属性回读 5 个档位值。

### C3 —【P2】promotion-download.html 文档契约与 markup 不符
- **位置**: [`.agents/skills/headset-gen-subpage/templates/functions/promotion-download.html:5,28`](../.agents/skills/headset-gen-subpage/templates/functions/promotion-download.html)。
- **现象/根因**: L5 注释让你"把内联 SVG 换成 `<img ... data-property="promo-icon-src">`",但 L28 **已经
  是 `<img>`** 且**没有 `data-property`**。文档承诺的 `promo-icon-src` 填充槽在 markup 里不存在,manifest
  无法按文档替换图标。(默认资源 `headset/assets/dell-audio-icon.png` 存在,图不裂。)
- **要做的修改**: 二选一并保持一致——给 L28 的 `<img>` 加上 `data-property="promo-icon-src"`(让文档承诺
  的槽真实存在),并把 L5 过时的"replace the inline SVG"措辞改成与现状(已是 `<img>`)一致。顶部
  `data-property slots` 列表里补上 `promo-icon-src`。
- **验收**: 文档列出的每个 `data-property` 槽都能在 markup 中找到对应元素;无"内联 SVG"残留措辞。

### C4 —【P3】可替换槽(Swappable Slot)说明过宽
- **位置**: [`.agents/skills/headset-shared/subcontrols/control-row.html:12-16`](../.agents/skills/headset-shared/subcontrols/control-row.html)、
  [`.agents/skills/headset-gen-subpage/templates/functions/single-control.html:13-18`](../.agents/skills/headset-gen-subpage/templates/functions/single-control.html)。
- **现象/根因**: 两处说"可替换成**另一个 sub-control 模板**的控件"。但 slider/segmented/preset-grid 都是
  `width:100%` 的整块控件,塞进 `.function-header` 这个 flex 行会撑坏布局。**真正能换进 header 槽的只有
  `switch` ↔ `dropdown`**(两者都有 `margin-left:auto`)。
- **要做的修改**: 把两处说明收窄为"仅可替换为**紧凑型 header 控件**(目前是 toggle switch 或
  `dropdown.html`);slider/segmented/preset-grid 等整宽控件**不可**放进 header 行,它们属于卡片 body"。
- **验收**: 两个文件的 swap 说明一致且明确限定到 switch/dropdown。

### C5 —【P3】杂项稳健性
- **subfn-child 置灰后仍可 Tab 聚焦**: [`headset.css:893-896`](../headset/headset.css) 只设 `opacity:0.4 +
  pointer-events:none`,被置灰的 `.subfn-child` 里的原生控件仍可键盘聚焦/操作。**修**: 同时阻止键盘交互
  (如对 `.subfn-group:has(.subfn-toggle:not(:checked)) .subfn-child` 内的可聚焦控件加效果,使其不可聚焦/
  不可操作——优先纯 CSS;若 CSS 做不到对原生 input 真正禁用,在 README 注明这是已知限制即可,不要为此引入大段 JS)。
- **segment-icon 空白残留风险**: [`segmented.html:34`](../.agents/skills/headset-shared/subcontrols/segmented.html) 不用图标时留的是 HTML 注释,
  `:empty`(headset.css:958)能命中注释→隐藏 OK;但若作者删注释只留空白换行就不再 `:empty`,会占 24×24。
  **修**: 在 segmented.html 注释里强调"不用图标时**整段删除** `.segment-icon` span(勿留空白)",与现有
  preset-grid 的处理一致。
- **segment 面板硬上限 6**: [`headset.css:1012-1017`](../headset/headset.css) 只映射到 `nth-child(6)`。preset/segmented 选项本就 ≤6,
  相符。**修**: 仅在 segmented.html / preset-grid.html 注释里写明"选项 + 面板上限 6"。

### R1 —【P1】"No hiding" 非协商规则 与 segmented 条件面板 直接冲突
- **位置**: [`headset/AGENTS.md:38-39`](../headset/AGENTS.md)(`No hiding: never display-hide a variant and never
  pre-embed-and-hide`)对阵 `headset.css:1005`(`.segment-panel { display:none }`)+
  `segmented.html:49-62`(预埋全部面板)。架构 §8.2(docs:378)已说明这是**明知故犯的覆盖**。
- **现象/根因**: "No hiding" 本是针对**跨机型 variant 轴**(选哪个连接块/哪些功能)的生成期烤死原则;但写成
  了无条件全局禁令,而新 segmented 条件面板正是"预埋 + display:none + :has() 揭示"。弱模型读 AGENTS.md 会把
  新组件判成违规。这个覆盖只写进了架构日志,**没同步到 AGENTS.md**。
- **要做的修改**: 改写 `headset/AGENTS.md` 的 "No hiding" 条目,**把禁令限定到"跨机型 variant 轴"**
  (连接块/功能列表等生成期一次性选择仍然 presence/absence、不得 display-hide),并**显式开口子**:
  "单台机面板内的**终端用户真交互**(segmented 条件面板、选中态、subfn 置灰、浅层条件 reveal)允许预埋 +
  CSS `:has()`/`:checked` 揭示——见架构 §8.2/D11/D12"。措辞与架构文档一致。
- **验收**: AGENTS.md 不再与 segmented/subfn 机制自相矛盾;读者能据此判断 segmented 面板**合规**。

### R2 —【P2】路由:关键词覆盖 id 违背 D8 + 两套路由未统一
- **位置**: [`.agents/skills/headset-gen-subpage/templates/functions/README.md:14-37`](../.agents/skills/headset-gen-subpage/templates/functions/README.md)(关键词表 + "overrides
  whatever id the manifest assigns")、[`gen-subpage SKILL:57-60`](../.agents/skills/headset-gen-subpage/SKILL.md)、
  [`headset/AGENTS.md:28-30`](../headset/AGENTS.md)(只写 id 查找)。架构 **D8**(docs:197)明文"身份认 id,不认名字"。
- **现象/根因**: 两套并行路由——(a) id 查找(操作契约 SKILL/AGENTS),(b) 关键词按名字命中并**覆盖 id**
  (只在 README)。关键词层(b)在 SKILL/AGENTS 里完全没提(未打通),且"按名字命中覆盖 id"与 D8 直接矛盾。
- **要做的修改**(按已定决策②):
  - 把 README 关键词表**降级为"编写期(authoring)挑 id 的参考提示"**:删除/改写"overrides the id the
    manifest assigns"等覆盖语义;明确"**生成期不做关键词匹配**;它只帮编写者在写 manifest 时选对 `id`"。
  - 结构规则"exactly one boolean → single-control"同样标为**编写期指引**(帮编写者给该功能选 `single-control`
    这个 id),不是生成期的自动改写。
  - 确认 `gen-subpage SKILL` 与 `headset/AGENTS.md` 的 function 路由是**纯 id 查找 → 否则 headset-function**,
    与 README 不再冲突;如需要,在 SKILL/AGENTS 加一句"function 路由只认 manifest 的 `id`(D8);关键词表是编
    写期参考,不在生成期执行"。
- **验收**: 全仓库不存在"生成期按描述名字覆盖 id"的指令;README、SKILL、AGENTS 对 function 路由口径一致且
  贴合 D8。

### R3 —【P3】'eq' 等关键词子串过度匹配
- **位置**: [`functions/README.md:31`](../.agents/skills/headset-gen-subpage/templates/functions/README.md)(`eq` 列为 partial-match 触发词)。
- **现象/根因**: 规则是"case-insensitive **partial match**";`eq` 子串会命中 **frequency / request /
  sequence** 等无关词。(此项随 R2 一并处理,因为关键词表已降级为编写期提示,但危险子串仍要修。)
- **要做的修改**: 把 `eq`(以及其它过短/易误伤的 token)改为**词边界/整词匹配**或更具体的短语(如
  `equalizer`、`sound eq`、`eq curve`),并在表头把匹配规则从"partial match"改为"whole-word /
  phrase match"。promotion 那行的 token 也顺带核一遍。
- **验收**: 用 "frequency response"、"request"、"sequence" 测试不再命中 eq-audio。

### R4 —【P2】dropdown 实现 ≠ 文档规定的调用模式
- **位置**: 架构 [§8.3 / D12](function-card-architecture.md)(docs:391,478,§8.3 表把 Dropdown 写成原生
  `<select>`、零 JS)对阵实际 `subcontrols/dropdown.html`(`<details>` + 自定义 `<ul>` + 选择用内联 JS)。
- **现象/根因**: 文档的交互模型卖点是"原生表单控件、几乎零 JS";dropdown 实际是自定义件(带 JS、有 C1 的
  裁剪与键盘问题)。文档与产物不一致。
- **要做的修改**(按已定决策①,保留自定义件): 更新架构 §8.3 与 D12 那张表里 Dropdown 这一行,注明
  "**Dropdown 是有意的自定义件**(`<details>/<summary>` + CSS + 少量脚本),不用原生 `<select>`——因为需要
  Figma 自定义列表外观;它是该交互模型里**对'原生优先'的一个登记在案的例外**(理由 + 由此产生的键盘/浮层
  处理见 C1)"。不要删掉原"原生优先"原则,只登记这个例外。
- **验收**: 架构文档对 Dropdown 的描述与 `dropdown.html` 实现一致;"例外"有明文记录。

### R5 —【P2】§7 控件选型三张表 不在任何 operational 文件里
- **位置**: 三张表只在架构 [§7](function-card-architecture.md)(docs:332-357);AGENTS.md(根 + headset)都没有;
  架构自己标为待办(docs:497 / D10)。
- **现象/根因**: "用哪个控件"(形状→家族;家族内 segmented/dropdown 阈值;button/link 语义;领域约定)是
  编写期决策规则,却只躺在 reference-only 的设计日志,没进调用路径载体。
- **要做的修改**: 在 [`headset/AGENTS.md`](../headset/AGENTS.md) 新增一节"控件选型(仅编写期用,生成期不查)",把架构 §7 的
  **三张表**原样落进去(下面已抄好,直接用),并注明"这些规则只在编写 manifest/设计片段时用;生成期照
  manifest 里显式的 archetype id 出,不在运行时自动选组件(§7 / D10)"。
  - **表①(数据形状 → archetype 家族)**:布尔2态→Toggle;有序区间/档位→Slider;N个无序选1→Select家族
    (segmented/dropdown);可点击动作/入口→Button家族(button/link);一组预设卡片平铺→Option-grid(preset-grid)。
  - **表②(家族内呈现)**:Select 家族 segmented vs dropdown——≤5~6 且要全部可见 / 带图标卡片→Segmented;
    数量更多或位置紧→Dropdown。Button 家族 button vs link——跳到另一页面/视图→Hyperlink(`<a href>`,
    与 feature-button 一致);原地执行动作→Button。
  - **表③(领域约定,写死)**:Sidetone→Slider;声学环境模式(ANC/Transparency/hear-through…)→带图标
    Segmented;on/off→Toggle。
  - 另注:segmented vs preset-grid 的细则已在 `subcontrols/README.md`,在新增节里指过去即可,别重复正文。
- **验收**: 在 headset/AGENTS.md 能查到"何时 segmented/dropdown/preset-grid、button/link";并明确仅编写期用。

### R6 —【P3】命名法过时偏向 per-function skill + 设计日志旧名
- **位置**: [`AGENTS.md:33-43`](../AGENTS.md)(`<role>=function` 的 `<name>` 举例 `headset-function-eq`,把每功能一个
  skill 当正路);[`docs/function-card-architecture.md`](function-card-architecture.md) 多处仍引用旧文件名 `toggle-row`(已重命名为
  `control-row`)、`toggle-single`(已为 `single-control`)。
- **现象/根因**: 架构已收敛"快照优先,不为每功能开 skill"(D6/D17/D18,实际 5 张全是快照、0 个 per-function
  skill);根 AGENTS.md 的命名示例仍主推 `headset-function-<id>` skill 路径,导向过时。设计日志里的 `toggle-row`
  是历史记录,但会误导按文件名查找的人。
- **要做的修改**:
  - 根 `AGENTS.md` 命名小节:把 `headset-function-<id>`(per-function skill)明确标注为**罕见/默认不用**,
    点明"已知功能默认走 `templates/functions/<id>.html` **快照**(D6/D17/D18);per-function skill 仅在该功能
    确实需要跑生成逻辑时才开,目前没有"。保留 anti-sprawl 既有措辞。
  - `docs/function-card-architecture.md`:这是历史思考日志,**正文叙事不必改写**;但在引用旧名处(如 §6.7、
    §11、§12 术语表)各加一句脚注/括注"(已重命名:`toggle-row`→`control-row`、`toggle-single`→
    `single-control`)",避免有人据旧名去查找。不要大改这份日志的结构。
- **验收**: 根 AGENTS.md 命名示例不再把 per-function skill 当默认;旧文件名处都有"现名"提示。

---

## 3. 修复优先级（按步骤,先做 Phase 1）

> 逻辑:先修"会误导生成器执行 / 功能性 bug"的,再修"会被照抄的文档契约",最后护栏打磨。每个 Phase 内
> 各条互相独立,可并行。

**Phase 1 — 契约冲突 & 功能性 bug（最高优先,先修）**
1. **R1** "No hiding" 开口子(否则新组件与契约自相矛盾)。
2. **R2** 路由统一:关键词降级、不覆盖 id、生成期纯 id。
3. **R3** 修危险关键词子串(随 R2)。
4. **C1** dropdown 裁剪 + 键盘可选(唯一真功能性 bug)。

**Phase 2 — 会被照抄的文档/契约不符（再修）**
5. **C2** eq-audio 注释/属性修复(几何改动谨慎,见该条)。
6. **C3** promo 文档/markup 对齐。
7. **R4** dropdown 文档登记为自定义件例外。
8. **R5** §7 三张表写进 headset/AGENTS.md。

**Phase 3 — 护栏 & 打磨（最后）**
9. **C4** swap 说明收窄到 switch/dropdown。
10. **C5** subfn-child 聚焦 / segment-icon 空白 / 面板上限 6 注释。
11. **R6** 命名法 + 旧名脚注。

---

## 4. 约束（务必遵守）

- **不要 commit、不要 push、不要建分支**;只改工作区文件,保持易回滚。改动尽量小而局部,不动无关代码。
- **不跑任何破坏性 git 命令**(reset --hard / clean / checkout -- 覆盖等)。
- **不引入构建系统/依赖/框架**。脚本只在确有必要时用,且尽量内联、单文件、少量(贴合"近零 JS"理念)。
- **样式只进 `headset/headset.css`**;严禁内联 `<style>`;颜色/圆角等用 `shared/tokens.css` 的 token。
- 改 archetype 片段时,若与"参考装配范例" `functions/collaboration.html` 等快照有关,保持向后一致。
- **不要新建临时预览文件并留下**(`_preview-*` 之类已 gitignore,别新增残留)。
- 如某条(尤其 C2 几何、C1 方案选择)你判断有观感/兼容风险,**就保守处理并在最终说明里标注"未做/部分做 +
  原因"**,不要硬改。诚实报告 > 假装全绿。

## 5. 交付（改完输出这些，供 review）

1. **改动文件清单** + 每个文件一句话说明改了什么。
2. **逐条 Phase 1/2/3 的状态**:完成 / 部分完成 / 跳过(+原因)。
3. **C1 你选了哪种裁剪方案**(Popover API 还是 fixed+脚本)、为何;键盘支持加了哪些键。
4. **C2 是否动了 SVG 几何**;若动了,说明改了哪几行、预期观感影响。
5. 任何你认为清单判断有误、或修复引入新风险的地方,直说。
