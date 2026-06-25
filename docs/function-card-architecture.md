# 功能卡片(Function Card)架构 · 设计讨论与决策记录

> **文档性质**:这不是最终规范(spec),而是一份**思考过程记录(thinking log / design journal)**。
> 它如实记录我们围绕"子页面里的功能卡片到底是什么、怎么组织、怎么交互"这一主题、跨几十轮
> 的讨论:每一步提出了什么、考虑过哪些方案、争论的焦点、做出的决定,以及**我中途几次推翻自己
> 的判断**。刻意写得啰嗦、丰富,优先保真而非简洁。
>
> **状态**:架构仍在收敛中,文末"待办/未决"列出尚未落地的部分。**以现有 codebase 为准**;
> 与 [`methodology.md`](methodology.md) 冲突时,codebase 优先(那份方法论部分章节已过时)。
>
> **怎么读**:第 0 节交代起点;第 1–8 节是按时间顺序的讨论演变;第 4、5 节是你点名要单独记录
> 的两个争议(Skill/Snippet/Snapshot、Slot vs 其他形态);第 9 节是当前收敛出的模型;第 10 节是
> 决策日志(含被撤销的决定);第 11 节待办;第 12 节术语表。

---

## 0. 起点与背景

### 0.1 三层架构与"以 codebase 为准"

整个产品 UI 生成系统是三层:

- **设计令牌层** `shared/tokens.css` —— 颜色/字体/圆角/阴影等视觉常量,全品类共享,极少改。
- **品类模板层** —— 每个品类(headset/mouse/…)自己的页面骨架 + 布局样式;以 headset 为 pilot。
- **机型数据层** —— 每个具体机型一份 manifest(清单)+ 生成出来的内容烤死的成品页。

有一份外部方法论文档(`docs/methodology.md`,"Product UI Generation Methodology v1.0"),是**参照,不是法律**。它部分框架已过时;**与现有 codebase 冲突时以 codebase 为准**。已确认的几处分歧:
- §9.5 把 skill 嵌在品类目录下;**codebase 把所有 skill 平铺在仓库根** `.agents/skills/`,用 `<category>-...` 前缀命名(Devin 只发现 depth-1 的 `SKILL.md`,嵌套实测失败,2026-06-24)。
- 方法论用 "Mouse" 举例;**真实 pilot 是 headset**。
- §3 倾向 `data-instruction` 让 AI 生成;**codebase 更严:markup 一律从预写片段逐字复制,不按描述生成**,未知 enum 就 HALT 问。

### 0.2 讨论开始前的代码现状

讨论"功能卡片"之前,headset 品类只有 4 个 skill:
- `headset-gen-homepage` —— 从 `home.manifest` 生成主页 `index.html`。
- `headset-gen-subpage` —— 从子页 manifest 生成任意子页(一个框架装所有子页)。
- `headset-control-generic` —— **未知控件的兜底生成器**(§9.4 的 fallback)。
- `headset-shared` —— 不是 skill,是共享片段:`connection/`(wired/bluetooth/unpair)、`icons/`、`feature-button.html`。

注册表 `headset-gen-subpage/templates/controls/` 当时**是空的**(只有 README);`headset/models/` 没有任何真实 manifest;icons 只有 `audio.svg` 一个。

### 0.3 用到的方法论章节(贯穿全程)

- **§3 槽机制**:模板只留"空槽 + 标记",数据在生成期填进去。
- **§4 变体(variant)**:从有限互斥的枚举里选一个(如连接方式 wired/bluetooth),用离散状态机,按 enum 选对应整块。
- **§5 列表(list)**:同类、数量不定的集合(如功能按钮 2/3/4 个),数据驱动循环渲染。
- **§5.2 注册表(registry)**:同一东西只定义一次,按 id 引用,防 drift。
- **§9.3**:子页不需要专属 skill,一个框架 skill + manifest 就够。
- **§9.4 控件层**:已知→带预置模板的片段/skill;未知→兜底生成;高频→提升固化。
- **§9.7**:强触发词 + 硬路由 + 显式调用 + 自检 + "copy 不 create" 防弱模型瞎编。

---

## 1. 缘起:从"feature generated skills"问起

**你的输入(大意)**:方法论里写了一些 skill,记得有一块"feature generated skills",是用来生成产品 function/feature 能力的吧?子页 feature content 里那些 function,是有类似 skill 规划的吧?

**辨析的关键点 ——"feature" 被用在两层**:
- **Feature Zone / feature 按钮(§5)**:主页上点进子页的入口按钮(Mic Settings、EQ…)。它们是**列表项**,从 `home.manifest` 的 `features[]` 数据驱动、复制同一个 `feature-button.html`。**不是 skill。**
- **子页内部的"功能/控件"(§9.4)**:真正实现产品 function 能力的交互件。**这才是有 skill 规划的那块** = control 层。

**当时结论(已确认)**:control 层基本是空的——只有兜底 `headset-control-generic`,没有任何具体控件快照,也没有专用 `headset-control-<id>` skill。这是 §9.4 "按需生长" 的设计:先有框架和兜底,具体控件等真实 manifest 出现再补。

---

## 2. 第一次落地:`control-generic` → `headset-function`

**你的输入**:就是那个 `headset-control-generic`,改个名,"Control Generic"太宽泛 —— 改成 **`headset-function`**。先写个模板,因为之后会有很多不同的功能,大概 5、6、7、8 个。

**我的处理与判断**:
- 提醒:这个 skill 原定位是"未知控件的兜底生成器";直接改名 + 写模板,顺势把它升级为"按统一模板生成一个功能模块"的生成器。
- 做了 **control → function 的全量词汇迁移**(连接区 `control-zone` 是另一个概念,保持不动):
  - skill `headset-control-generic` → `headset-function`
  - 注册表目录 `templates/controls/` → `templates/functions/`
  - manifest 字段 `controls[]` → `functions[]`;slot `data-slot="controls"` → `data-slot="functions"`
  - 未来专用 skill 命名 `headset-control-<id>` → `headset-function-<id>`
  - 同步更新:根 `AGENTS.md`、`headset/AGENTS.md`、`README.md`、`headset/models/README.md`、`gen-subpage` 的 SKILL + frame、registry README;`docs/methodology.md` 不动(参照原文)。
- 新增 `headset-function/templates/function-frame.html` 和 `headset.css` 里的 `.function-module` 等样式。

**当时给的 function 形态 = 单行模块**:`.function-module` = label + 可选 description + 一个 affordance 区(单行)。**⚠️ 这个形态后来被证明错了**(见第 5 节)。

**状态**:这批改名 `git add` 了但**没 commit**(随后你转入架构讨论,一直没回到这批;它至今未提交,见第 11 节)。

---

## 3. 关键背景输入:两层架构 + 10–20 个功能

**你的输入(大意)**:耳机的 feature/function 通常固定,约 **10–20 个**;不同型号各异,但有一批像模板一样是标配。架构记得是**两层**(之前可能想过三层):
1. **第一层:已有的模板 Skill** —— 生成固定功能。比如 Collaboration,排版/布局/架构/内部小功能都预先设计固定;新耳机需求里提到 Collaboration,就直接调用对应 Skill,把模板整段复制进来,模板存在就不用改。
2. **第二层:处理新/未知功能** —— 出现库里找不到的新功能名,就新建一个 Skill 专门构建这个未知功能。

**我的映射 + 当时疑问**:
- 第二层 = 我们刚改名的 `headset-function`(自带兜底模板)。已经有了。
- 第一层(已知功能库) = 目前空的,我留的位置是 `functions/<id>.html` 快照注册表。
- 抛出一个结构疑问:第一层应该是"独立 skill"还是"快照文件"?数字应改 5-8 → 10-20;并提出"已设计好的已知功能预先建出来不算投机"。

---

## 4. 【争议 A】Skill vs 片段(Snippet)vs 快照(Snapshot)

> 这是你点名要单独记录的争议之一。下面把三个词的定义、你态度的演变、完整优劣对比、以及最终
> 判定都记下来。

### 4.1 三个词到底指什么

- **快照(Snapshot)/ 片段(Snippet)文件**:一段**静态 HTML + 值槽**(`data-property=...`),放在注册表目录里(如 `functions/collaboration.html` 或 `headset-shared/connection/bluetooth.html`)。`gen-subpage`/`gen-homepage` 按 id 查到就 **copy + 填值**。它**不做任何决策**,就是被复制的素材。(本文里"快照"和"片段"基本同义,都指这种"被复制的静态素材";细微差别是"快照"更强调"某个已知东西冻结下来的成品长相"。)
- **独立 Skill**:一个带 `SKILL.md` 的**文件夹**,Devin 会发现它、可 `@skills:` 点名调用。它能**跑逻辑、做判断、调用别的 skill**,文件夹里还能放模板片段等素材。

**关键洞察**:如果一个已知功能是"固定写死"的,把它做成 Skill,等于"快照文件 + 一层 SKILL.md 外壳 + 一份发现成本",外壳并没换来新能力。**Skill 只在"要做静态文件做不到的事(逻辑/判断/调子 skill)"时才回本。**

### 4.2 你态度的演变(如实记录)

- 起初(第 3 节)你描述第一层是"调用对应的 Skill",我据此一度推荐"每个已知功能一个独立 Skill"。
- 你随后问"快照文件注册表是什么意思?",我解释了(就是 4.1 的快照那条 + `gen-subpage` 按 id 查找复制的流程)。
- 然后你明确松口:"**把固定不变的内容放到 `headset-gen-subpage` 下面 template 里的 function 中,也没问题。直接复制也可以,哪怕有 10 个 function 也没关系。其实不同路径的逻辑都是一致的,思维方式也一样,只是存放的路径不同而已。**"
- 也就是说:**Skill vs 快照不是这套架构的胜负手——两条路逻辑相同,只是存放位置不同**;你倾向用快照,数量多也无所谓。

### 4.3 完整优劣对比

**方案 A:快照文件**

优点:
- **零常驻上下文成本**:Devin 不发现它,描述不进 session 开场预算;只有真被 copy 时才进上下文。再多也不占开场。
- **没有"AI 跳过 skill"的毛病**:`gen-subpage` 一条硬指令"按 id copy `functions/<id>.html`",是确定性路径查找,不存在"AI 自己决定要不要用"这个失败面(§9.7 的核心痛点)。
- **轻**:一个功能 = 一个 HTML 文件,无 frontmatter/description/procedure/self-check 样板。改功能 = 改这一个文件。
- **与现有代码库一致**:`connection/*.html`、`feature-button.html`、`icons/*.svg` 现在就是这么干的——copy 片段、各自都没有独立 skill。
- **扩展无上限不污染命名空间**:加第 21 个 = 丢一个文件,skill 列表纹丝不动。

缺点:
- **装不下逻辑**:只能"复制 + 填值";要条件渲染/调子 skill/多步决策,它做不到。
- **自我广告弱**:得 `ls functions/` 才知道有哪些(靠 README/约定记录),不像 skill 的 description 自报"我何时该被用"。

**方案 B:每个已知功能一个独立 Skill**

优点:
- **能装逻辑**:SKILL.md 可写生成步骤、条件判断、`@skills:` 调子控件——适合需要现搭/组合的复杂功能。
- **自描述/可点名**:description 摆明"何时用我",显式调用,目录即功能目录。
- **强隔离**:每功能自带模板 + 规则 + 自检,边界清楚。

缺点:
- **常驻上下文成本 × N**:Devin 开场加载每个 skill 的 name+description;10–20 个就是 10–20 行常驻,还加重"skill 太多→选择瘫痪"(§9.7.3 自己警告的)。
- **重新引入"AI 跳过 skill"失败面**:skill 是"AI 自己判断要不要调",正是它会"假装没看见"的那条路;要靠强触发词 + 硬路由 + 自检堵。
- **样板重**:每功能一份完整 SKILL.md,10–20 份要写要维护。
- **对固定功能是纯浪费**:写死的功能套个 skill 外壳只增成本不增能力。
- **与现有模式不一致**:出现"连接块用快照、function 用 skill"两套并行,正是 drift。
- **不能嵌套**:Devin 只认 depth-1(实测过),只能平铺在根。

### 4.4 判定与后续精化

**判定标准(一句话)**:**功能是"固定写死的素材" → 快照文件;功能"需要跑生成逻辑" → Skill。**
- 已知功能默认用**快照/数据**,**不为每个功能开 skill**。
- 需要逻辑的只有一处——"现搭未知功能"——已由**单个** `headset-function`(第二层)兜住,逻辑集中在这一个 skill。
- 这就是"§9.4 说做成 skill,但 codebase 改成快照"那个已确认的"以 codebase 为准"点。

**后续精化(第 8 节之后)**:被当快照存的,**精确地说是"子控件片段"`subcontrols/<type>.html`,不是整个 function**。function 不再是冻结快照,而是"数据驱动拼装"(见第 5、9 节)。

---

## 5. 【争议 B】它是"一个整块"还是"槽位列表"?(形态之争)

> 你点名的另一个争议。这一节如实记录"功能卡片到底长什么形态"的认知演变,**包括我两次推翻
> 自己**。

### 5.1 形态 v1:单行模块(改名那轮)

第 2 节里我把 function 做成单行 `.function-module`(label + description + 一个 affordance)。**错在**:把"功能"想成了一个单一控件。

### 5.2 形态 v2:function = 一整块 Content Area 模板;并(错误地)提出 1:1

**你的输入(大意)**:独立 Skill 里也有 Template、有写好的 HTML;流程是查到对应 Skill,**这个 Skill 其实就是子页面,也就是 Content Area 的内容**;按功能/内容查 Skill,有的已有模板,直接复制粘贴。

我据此**推断 1:1**:一个子页 = 一个功能 = 一整块 Content Area 模板,并提议**撤掉 `functions[]` 列表**。**⚠️ 这一步后来被截图推翻(下一小节)。** 当时我已明说这是【推断】并请你确认是否 1:1。

### 5.3 形态 v3:截图推翻 1:1 —— Content Area 是"功能列表"

**你的输入**:发来一张 **Audio Settings** 子页截图,并指出:不是 1:1。子页的 Content Area 里可能有 1/2/3 个功能,不固定。这张图里有三个功能:**Noise Control、Collaboration、Multimedia**。

**这直接证明**:
- 一个子页(Audio Settings)的 Content Area = **一列功能**(数量可变),不是单一功能。
- 我上一轮的"1:1、撤掉列表"**作废**;**最初那版 `functions[]` 列表方向是对的**,该保留。
- 要修的是:一个"功能"是**有标题、内部带多个子控件的整块卡片**(Collaboration = 标题 + 两个开关 + 滑杆),不是单行。所以 v1 的 `.function-module`/`function-frame.html` 形态要升级成"卡片块"。

四级层级因此定死:**Feature(主页按钮/子页)→ Content Area(装 1~N 个功能)→ Function(有标题的卡片)→ Sub-control(功能内部的小控件)。**

### 5.4 形态 v4:冻结快照不行 → 数据驱动拼装

在此之前我推荐"已知功能 = 冻结快照、原样复制"。**你用真实 case 戳穿了它**:

**你的输入(几个真实 use case)**:
- 下一款耳机有 Collaboration 和 Mic Noise Cancellation,但**没有 Sidetone**。(删子控件)
- 或:有 Collaboration,但没有 Mic Noise Cancellation 和 Sidetone;它把 Mic Noise Cancellation **改名叫 Noise Cancellation**——名字像,但**根本不是同一个功能**。(换成另一个)
- Noise Control:大多产品有 ANC/Transparency/Off 三个模式;下一个可能有**第 4、第 5 个模式**;或反过来**只要 ANC + Transparency,删掉 Off**。(子控件内部选项数在变)

**我承认 v4 修正**(这是细化粒度,不是又翻案,核心原则"固定结构 + 差异进数据"没变,只是我把"固定"放错了层级):
- 一份"写死的 collaboration.html"没法原样复制——一复制就要删元素/改名/改选项数,等于在拷贝出来的 HTML 上打补丁,又脆又乱。
- **把"固定素材"下沉到子控件层**:固定的是 `subcontrols/<type>.html`(toggle/slider/segmented/preset-grid 的**外形**);**function = 数据驱动的拼装**(卡片外壳 + 按列表拷子控件片段)。
- **身份认 id,不认名字**:"看起来像但不是同一个" → 不同 id → 不同片段(未知→第二层现搭);永远不是"改名复用"。
- 你的删/改/增全是改数据,素材一行不动。

### 5.5 形态 v5(收敛):递归槽位

**你的输入**:这种功能卡片本质上由一个个"**槽位**"组成,从上到下排列:第一个槽放什么功能、第二个、第三个;有时一个槽,有时两个,不固定。

**我确认并补一刀:槽位是递归的。** 这正是方法论的槽(§3)+ 列表(§5),你自己重新推导了出来。整套架构坍缩成**一个原语**:

> **有序的槽位列表;每个槽由数据决定填什么;数量可变;可递归。**

并且:你说的"槽位"就是模板里**已有的 `data-slot`**(主页 `feature-zone`、子页 `functions` 区都是槽),只是现在递归用到了功能卡片内部。这说明模型自洽:从 Content Area 到最里层子控件,全程只有"槽 + 数据填充"这一件事。

### 5.6 形态演变小结

| 版本 | 形态 | 触发/依据 | 结局 |
|---|---|---|---|
| v1 | 单行 `.function-module` | 改名那轮顺手做的 | 被 v3 升级 |
| v2 | function = 整块 Content Area;**1:1** | 你说"Skill 就是子页" | **被 v3 推翻** |
| v3 | Content Area = 功能列表;function = 卡片 | Audio Settings 截图 | 保留(回到列表) |
| v4 | function = 数据驱动拼装;固定素材下沉到子控件 | 删/改/增真实 case | 保留 |
| v5 | **递归槽位列表**(综合) | 你的"槽位"心智 | **当前收敛** |

---

## 6. 真实用例与数据(固化讨论中出现的所有具体素材)

### 6.1 Audio Settings 截图(参考规格)

子页标题 **Audio Settings**,Content Area 三个功能:

1. **Noise Control** —— 三选一分段控件,3 张带图标的卡片:**ANC**(选中,蓝底白字,耳机图标)、**Transparency**(白,图标)、**Off**(白,图标)。
2. **Collaboration** —— 标题 + ⓘ 信息图标;内含:**Mic Noise Cancellation**(右侧 OFF + 开关)、**Sidetone**(右侧 OFF + 开关),下方一个**滑杆 1—2—3**(当前在 2)。
3. **Multimedia** —— 标题 + ⓘ;预设网格:**Default**(选中,蓝)、**Bass Boost**、**Speech Boost**、**Treble Boost**,底部 **Custom**(整行)。

→ 形态归纳:这一屏只用了 **3~4 种 archetype**:segmented(带图标卡片)、toggle-row、slider、option-grid(预设)。名字(ANC、Mic Noise Cancellation、Bass Boost)和选项数都是**数据**,不是新素材。

### 6.2 Collaboration 的"固定基座 + 机型增量"

- 基座 = Mic Noise Cancellation + Sidetone + 滑杆,10 款通用。
- 未来某款要在 Collaboration 下**加一个专属子功能** → 在大模板基础上加 nuance/alternative。
- 处理:基座固定子控件 + 一个 **extra 槽**;增量/替代来自 manifest 数据,**基座文件不动**;新子控件若库里没有 → 第二层现搭再塞进槽。(这是 v4/v5 的"槽 + 数据"在子控件层的体现。)

### 6.3 变体 case 清单(全靠改数据)

| case | 处理 |
|---|---|
| Collaboration 没有 Sidetone | 该功能的子控件(槽)列表去掉 `sidetone` |
| Noise Control 只要 ANC + Transparency(删 Off) | segmented 的 `modes` 列表 = `[anc, transparency]` |
| Noise Control 加第 4/5 个模式 | `modes` 列表加项 |
| Mic Noise Cancellation → Noise Cancellation(不是同一个) | 换成另一个 id `noise-cancellation`;已知→拷片段,未知→`headset-function` 现搭 |

### 6.4 Sidetone 5 模式:Dropdown 还是 Slider?

判据是**这 5 个是不是有序档位**:有序(1–5 级)→ Slider;无序命名(5 个预设)→ Dropdown。"有序与否"是数据属性。你也提到"按习惯 Sidetone 必须用 slider"——那就当成一条**写死的领域约定**。

### 6.5 条件显隐:选 ANC 冒出子功能(可变、可嵌套)

**你的输入**:选 ANC 模式后,会出现一些可开关的子功能;**这些是编造的例子**——实际可能有、可能没有、可能冒出两个,甚至子功能里再套子功能一/二。有没有、有几个、套几层,全是按产品变的数据。

→ 模型落点:这是"槽"往下嵌套一层。某个 mode 选中后,从它内部的**条件槽**里按数据冒出 0/1/2+ 个子功能(还是 §5 列表);子功能本身又可以是"带槽位的卡片"(递归)。弱模型不决定有没有/几个/几层,数据说了算。

### 6.6 功能预设与标准框架(default-dominant —— 默认占绝大多数)

**你的输入(背景补充)**:功能卡只要能对应到 ID,**几乎都有预设的显示状态和组合;除非用户特别提出修改,否则大部分是固定搭配("雷打不动")**。也就是:**预设(default)占绝大多数,覆盖(override)是例外。**

**标准子控件框架(最常见的槽形态)**:**左边 Title(功能名),右边组件(Toggle / Dropdown)**。大部分"开关类"功能都用这个标准行;它就是子控件层最高频的那个 archetype。

**几个功能的预设(authored once,机型默认直接用)**:
| 功能 | archetype | 默认组成 | 可变范围(仅在明确要求时) |
|---|---|---|---|
| Noise Control | Segment Control(固定用) | 3 张大卡片:ANC / Transparency / Off | 增减其中某一项(±1) |
| Multimedia | 模式网格 | 默认 5 个模式 | 最多 6 个(2×3 布局);默认通常雷打不动 |
| Sidetone | 复合(两个槽) | 上 Toggle + 下 Slider | 产品支持即固定此布局 |

**含义,以及它如何解开 §4 的"快照 vs 数据"之争**:常规机型"支持某功能 = 引用 ID = 拿到固定预设",体验上等于"复制现成的";只有明确要求改时才在 manifest 里覆盖。所以:
- **预设就是当初想要的那个"快照"**,但**存成数据(组成定义)**,因此可覆盖。
- 常规走预设 → **快照般简单**(引用 ID 即得固定搭配);例外走覆盖 → **数据般灵活**(删/改/增)。
- 这也校正了 §5.4 的语气:那一节为了说明"覆盖是真实存在的",把可变性讲得很重;**实际权重是反过来的——默认固定占绝大多数,可变是少数**。两者不矛盾:固定的是"默认",灵活的是"覆盖时";关键是预设存成数据、而非冻结 HTML,所以两头都成立。

**对工作量的含义**:这意味着授权成本可控——把 ~10–20 个功能的预设组成各 authored 一次,机型大多只是"引用 ID",不用每台重写。

---

## 7. 控件选型:什么时候 toggle / slider / dropdown(写死 vs 推断)

**你的输入(大意)**:LLM 有时需要基于逻辑的合理推断。比如 on/off 用什么 UI、子功能怎么显示、切模式怎么布局、Sidetone 5 模式用 dropdown 还是 slider……有些逻辑可以写死(Sidetone→slider),有些不能写死就得让大模型推。到底什么时候用 toggle/dropdown/slider?

**我给的框架 —— 分两个"时刻"**:

| | 编写期(设计稿 → 数据) | 生成期(数据 → HTML) |
|---|---|---|
| 谁干 | 强模型 + 人审 | 弱模型,照单拼装 |
| 认知 | 高:可推理、判断 | 零:确定性 copy + fill |
| 产出 | 显式可审的组成数据 + 规则表 | 页面 |

**结论**:**LLM 该推理,但推理只发生在编写期,且结果必须冻结成数据;生成期不再推。**

**多数"用哪个控件"其实是规则,不是逐个猜。规则有两层。**

**第一层:数据形状 → archetype 家族**

| 参数的形状 | 控件家族 | 性质 |
|---|---|---|
| 开/关(布尔,2 个互斥) | Toggle | 写死规则 |
| 一个值落在**有序**区间/档位 | Slider | 写死规则 |
| 从 N 个**无序**项选 1 | **Select 家族**(见第二层) | 写死规则 |
| 一个可点击的动作/入口 | **Button 家族**(见第二层) | 写死规则 |
| 一组预设、卡片平铺 | Option-grid | 默认规则,可覆盖 |

**第二层:家族内选哪个呈现**(同一数据形状下、可互换的呈现;判据大半可写死)

| 场景 | 选项 | 判据(写死的规则) | 默认 |
|---|---|---|---|
| 单选枚举(Select 家族) | **Segmented vs Dropdown** | 数量 + 空间:≤5~6 个、要全部可见 / 带图标卡片 → Segmented;数量更多或位置紧 → Dropdown | 视数量,常规 Segmented |
| 动作/入口(Button 家族) | **Button vs Hyperlink-button** | 语义:跳到另一个页面/视图 → Hyperlink(真 `<a href>`,与现有 `feature-button` 一致);原地执行动作(应用/重置/某开关行为)→ Button | 导航默认 Hyperlink |

> 注:button/link 这条代码库里已半 embodied —— 现有 `feature-button.html` 就是 `<a href>`(导航用 hyperlink),第二层只是把现状写成明文。

**三张表覆盖后,绝大多数"用哪个控件"从"推断"变"查表"**:①第一层 形状→家族;②第二层 家族内呈现(segmented/dropdown、button/link);③领域约定表(Sidetone→slider、降噪→带图标 segmented、on/off→toggle…)。剩下真模糊的,**编写期让强模型推一次 → 写成显式数据 → 人复核**;之后生成期照数据出,不再推。

**关键原则**:**数据里显式写明 archetype id = 唯一真相;三张表只是编写期的指南 + 默认值,不是运行时裁决者。** 不做"magic 自动选组件"引擎——呈现选择部分是规则(数量/空间)、部分是设计意图(icon 卡片 vs 文字网格 vs 下拉),全自动会抹掉设计意图(§2.1 错误抽象比重复更贵)。

> 把这三张表正式写进 `AGENTS.md` 是待办(第 11 节)——它们是"保证 AI 选对控件"的机制载体,且**只在编写期用、生成期不查**。

---

## 8. 交互模型:从"静态烤死"到"真交互"再到"原生组件"

### 8.1 出发点:方法论主张生成期烤死

§3.1 把数据消费从"运行时"移到"生成期":一次生成一个状态、内容烤死、不做运行时 show/hide。前提是"一次一个机型、一种连接状态、静态展示"。

### 8.2 你选了"真交互"

针对"选 ANC 实时冒出 XYZ、切模式重绘"这类动态行为,我给了 A(静态稿)/ B(真交互)两条路,**你选 B:真交互。**

**边界划清——两种 state,只有一种变交互**:

| state 的轴 | 处理 | 变不变 |
|---|---|---|
| 跨产品/型号/连接(哪台机、wired/bluetooth、有哪些功能) | 生成期烤死一个(§3.1 仍管) | 不变,静态 |
| 单台机面板内、终端用户操作(拨开关、选模式、拖 slider、条件显隐) | 运行时 | ✅ 真交互 |

诚实标注:选真交互,就意味着在控件这层**确实要"预埋 + 运行时 show/hide"**(XYZ 先在 DOM、选 ANC 才显示)——这正是 §3.1 当初说别干的。这是**明知故犯的覆盖**,理由是 §3.1 假设"静态展示页",不适用"可操作控制面板";以产品决策为准。

### 8.3 你的关键洞察:行为是组件原生自带的 → 用原生表单控件,零 JS

**你的输入(大意)**:真交互不需要弱模型猜/重建,这些交互是组件原生自带的:Toggle 必然有开/关;Segmented/Button 必然有选中/未选中(顶多加 hover);Slider 必然有拖动/更新数值。用了组件,状态就在里面了,没必要为弱模型再做一套。并再次确认:纯前端、不入库、不持久化,刷新回默认。

**我确认并升级(承认这比我提的 `headset.js` 运行时更好)**:用**原生 HTML 表单控件**,行为是浏览器给的:

| 子控件 | 原生元素 | 自带行为(0 JS) |
|---|---|---|
| Toggle | `<input type="checkbox">`(CSS 描成开关) | 勾/取消、选中态 |
| Segmented | 一组 `<input type="radio" name=…>` | 单选互斥、选中态 |
| Slider | `<input type="range">` | 拖动、数值更新 |
| Dropdown | `<select>` | 展开、选择 |

- 选中/hover 用 CSS(`:checked`/`:hover`)写进 `headset.css`。
- **连"选 ANC 冒出 XYZ"都能纯 CSS**:`#mode-anc:checked ~ .anc-extra { display:block }`(兄弟选择器,0 JS)。
- 因此**撤掉 `headset.js` 那一层**。诚实保留的极少数例外(都是一行原生属性,不是框架):想让 slider 实时显示数字 → 一个 `oninput`;条件元素必须是触发控件的 CSS 兄弟节点,排不开的个别情况一行 JS 兜底。

### 8.4 嵌套条件显隐的深度边界

- **浅层(模式 → 直接挂的子功能,一层)**:纯 CSS `:checked ~`,0 JS。
- **深层嵌套(子功能里再按状态露更深的东西)**:CSS 兄弟链会变脆。这种用**一个通用的声明式显隐引擎**更稳——markup 写 `data-show-when="mode==anc"`,一段写一次的通用 JS 读它干活。**仍是通用引擎读数据、弱模型只声明关系、不写专属 JS。**

### 8.5 scope 确认

**纯前端、不入库、不持久化、刷新回默认**——一个可操作的 UI 面板演示。(你确认两次。)

---

## 9. 当前收敛出的模型(综合)

### 9.1 一个原语:递归槽位列表

```
Content Area      = 一列槽位 → 每个槽放一张功能卡片(Noise Control / Collaboration / …)
  └─ 功能卡片      = 一列槽位 → 每个槽放一个子控件(toggle / slider / segmented / …)
       └─ 某个槽   = 也可以放"又带槽位的卡片"(嵌套:选 ANC 冒出的那组子功能)
            └─ …   递归下去
```

> **有序的槽位列表;每个槽由数据决定填什么;数量可变;可递归。**

弱模型从头到尾只做一件事:**看到一个槽 → 按数据里的 archetype 拷对应片段 → 填值。** 有几个槽、填什么、要不要嵌套——全是数据。

### 9.2 层结构(模板/规则侧 ↔ 数据侧)

```
模板/规则侧                                  数据侧(manifest)
──────────────────────────────────────     ──────────────────────────────────
1. tokens.css      设计常量                  (无)
2. headset.css     布局 + 子控件样式          (无)
                   + :checked/:hover 状态
                   + 浅层条件显隐
3. page frames     gen-homepage/gen-subpage  home.manifest: identity+connection+features[]
   (骨架 + 槽 data-slot,copy+fill)           <subpage>.manifest: title + functions[](槽列表)
4. Functions       卡片外壳(标题+ⓘ)         每个功能: id + 子控件槽列表(+ 默认组成可覆盖)
   = 数据驱动拼装
5. Sub-controls    subcontrols/<type>.html    每个子控件: archetype + 值(label/选项/默认/有序?)
   (原生表单控件片段,行为浏览器自带)         + 可选 reveals(条件子槽,0/N,可嵌套)
```

### 9.3 两层(known/unknown)落在"子控件 archetype"

- **已知 archetype**(toggle-row/segmented/slider/preset-grid…)→ 有片段 → copy + 填(第一层)。archetype 数量少而有界(十种上下),按需生长,补得完。
- **未知 archetype** → `headset-function`(第二层)现搭;复现了再固化成片段(§9.4)。
- **已知功能的"默认组成"**(标准 Collaboration = 哪几个子控件)= 数据(注册表,§5.2),按 id 引用,机型可覆盖(删/改/增)。
- **preset-first(默认占绝大多数,见 §6.6)**:每个功能 ID 都有一份固定预设组成("雷打不动");常规机型只是"引用 ID 拿预设",覆盖是例外。预设存成数据而非冻结 HTML,所以常规简单 + 例外可改两头都成立。
- **最高频的子控件 archetype = 标准行**:左 Title + 右组件(Toggle/Dropdown)。Sidetone 这类则是固定的复合(上 Toggle + 下 Slider);Noise Control 固定 Segment Control;Multimedia 固定模式网格(默认 5、最多 6 的 2×3)。
- **archetype 清单是开放/临时的(用户确认 2026-06-25)**:目前列出的(toggle-row、segmented、slider、dropdown、option-grid/preset-grid、标准行……)只是当下想到的**起点,不是封闭枚举**——以后会补充或修改。增/改一个 archetype 走"未知 → 现搭 → 复现后固化"那条路(§9.4),并**顺带更新 §7 的两层决策表和受影响的预设**。这正是"按需生长"的体现,不需要一开始就枚举全。

### 9.4 与方法论的映射

- 对齐:§3(槽)、§4(变体:archetype enum 选片段)、§5(列表:槽列表、模式列表)、§5.2(注册表:默认组成按 id)、§9.3(子页一个框架 skill)、§9.4(已知片段/未知兜底/高频提升)、§9.7.4(copy 不 create)。
- **扩展**(codebase 比方法论细一层):方法论把"控件"当单层原子;真实 function 是**复合**的,故拆成 **function 卡片 + sub-control 原子两层**,并递归用到卡片内部。
- **覆盖**:§3.1 "生成期烤死、不做运行时显隐" 在**控件交互层被真交互覆盖**(8.2);跨型号/连接仍烤死。

### 9.5 诚实的边界与风险

- **抽象会漏**:若两个视觉模式真不同(Noise Control 带图标卡片 vs Multimedia 纯文字网格),就做成两个 archetype,别硬并(§2.1"错误的抽象比重复更贵")。archetype 数量因此会多一两个,但仍有界。
- **深层嵌套显隐**:纯 CSS 兄弟链会脆,需要通用声明引擎兜底(8.4)。
- **真交互违背 §3.1**:已知故犯,见 8.2。

---

## 10. 决策日志

| # | 决定 | 出现轮次 | 理由 | 状态 |
|---|---|---|---|---|
| D1 | 方法论参照、codebase 优先 | 起点 | 用户明示;方法论部分过时 | 生效 |
| D2 | `headset-control-generic` → `headset-function`,control→function 全量迁移 | 第 2 节 | 名字太宽泛;保持一致防 drift | **已 git add 未 commit** |
| D3 | function 形态 = 单行模块 | 第 2 节 | 当时理解 | **已撤销**(被 D9 取代) |
| D4 | 两层架构:已知 copy / 未知现搭 | 第 3 节 | 用户背景 | 生效 |
| D5 | 一个子页 = 一个功能(1:1),撤掉列表 | 5.2 | 误读"Skill 就是子页" | **已撤销**(被截图推翻) |
| D6 | 已知功能用快照/数据,不为每功能开 skill | 第 4 节 | 见 4.3 优劣;逻辑只需一处 | 生效 |
| D7 | Content Area = 功能列表(1~N) | 5.3 | Audio Settings 截图 | 生效 |
| D8 | 固定素材下沉到子控件;function = 数据驱动拼装;身份认 id | 5.4 | 删/改/增真实 case | 生效 |
| D9 | function = 卡片块(标题 + 子控件),非单行 | 5.3/5.4 | 截图 | 生效(替代 D3) |
| D10 | 控件选型:三张表(①形状→家族 ②家族内呈现 segmented/dropdown、button/link ③领域约定)+ 编写期推一次冻成数据;不做 runtime 选择引擎 | 第 7 节 | 把推断收敛成查表 | 生效(待写进 AGENTS.md) |
| D11 | 真交互(而非静态稿) | 8.2 | 用户选 B | 生效 |
| D12 | 用原生表单控件 + CSS,几乎零 JS;撤掉 `headset.js` | 8.3 | 行为浏览器自带,更贴"copy 不构造" | 生效(替代早先的 headset.js 提案) |
| D13 | 深层嵌套显隐用通用声明引擎 `data-show-when` 兜底 | 8.4 | CSS 兄弟链脆 | 生效(仅深嵌套) |
| D14 | 纯前端、不入库、刷新回默认 | 8.2/8.5 | 用户确认两次 | 生效 |
| D15 | 收敛为"递归槽位列表"单一原语 | 5.5 | 用户"槽位"心智 | **当前模型** |
| D16 | **preset-first**:每个功能 ID 一份固定预设组成,默认占绝大多数,覆盖是例外;预设存成数据 | 6.6 | 用户背景:"对应到 ID 几乎都有预设、雷打不动" | 生效(坐实 D6/D8,非反转) |

---

## 11. 待办 / 未决

- [ ] **commit D2 那批改名**(`headset-function` 迁移)——目前 `git add` 了但未提交。
- [ ] **把 function 形态从单行(v1)升级成"卡片 + 子控件槽"**:重做 `function-frame.html` 和 `.function-module` 等样式(目前还是改名那轮的单行版,与 D9 不符)。
- [ ] **新增 `headset-shared/subcontrols/`**(或等价位置):`segmented.html`、`toggle-row.html`、`slider.html`、`preset-grid.html` 等原生控件片段,按需生长。
- [ ] **把控件选型的三张表写进 `AGENTS.md`**(D10 载体):①形状→家族;②家族内呈现选择(Segmented/Dropdown 的数量阈值、Button/Hyperlink 的语义);③领域约定表。只在编写期用,生成期不查。
- [ ] **建 Audio Settings 参考实现**:Content Area 三个槽(Noise Control/Collaboration/Multimedia),Noise Control 选 ANC 时从条件槽冒出子功能;原生交互 + CSS 显隐;配最小 `home.manifest` + `audio-settings.manifest`;跑 `gen-subpage` 出真页对照,并特意出一个"删 Sidetone + Noise Control 只留 2 模式 + 条件子功能"的偏离款验证。
- [ ] **已知功能"默认组成"的存放形式**敲定(数据片段 / 注册表条目)与 `gen-subpage` 的覆盖合并逻辑。
- [ ] `headset/models/` 仍无真实 manifest;icons 仅 `audio.svg`——参考实现会补齐需要的图标/数据。

---

## 12. 术语表

- **Feature(主页入口)**:主页 Feature Zone 的按钮,`features[]` 一项,点进去是一个子页。**不是 skill**,复制 `feature-button.html`。
- **子页(sub-page)**:如 "Audio Settings",有标题 + Content Area;由一个框架 skill `gen-subpage` 生成,**不为每个子页开 skill**(§9.3)。
- **Content Area**:子页的内容区,= 一列**功能槽**(1~N 个,可变)。
- **Function / 功能卡片**:Content Area 里的一张有标题的卡片(Noise Control / Collaboration / Multimedia)。内部 = 一列**子控件槽**。**用数据驱动拼装,不是冻结快照。**
- **Sub-control / 子控件**:功能内部的小控件(开关/滑杆/分段/预设网格)。用**原生表单控件片段**,行为浏览器自带。
- **Slot / 槽位**:模板里的填充位(代码里的 `data-slot`)。**递归**:Content Area、功能卡片、子控件层层都是"槽列表"。
- **Archetype / 形态**:子控件的"外形类别"(toggle-row/segmented/slider/dropdown/preset-grid…)。**少而有界**;名字/选项是数据。
- **Snippet / Snapshot / 片段 / 快照**:被复制的静态 HTML 素材(+ 值槽)。子控件片段、连接块、feature-button 都属此类。
- **Skill**:带 `SKILL.md` 的文件夹,能跑逻辑。这里只有框架 skill(`gen-homepage`/`gen-subpage`)和未知功能现搭器(`headset-function`);**不为每个已知功能开 skill**。
- **Layer 1 / 已知**:有片段/默认组成 → copy + 填。
- **Layer 2 / 未知**:`headset-function` 现搭 → 复现后固化(§9.4)。
- **Manifest / 清单 / 组成数据**:机型/子页的内容数据。决定有哪些功能、每个功能哪些子控件槽、每个子控件的值与 archetype、条件 reveals。
- **Reveal / 条件显隐**:某状态(如选 ANC)下才出现的条件槽,0/N、可嵌套;浅层 CSS、深层声明引擎。
- **编写期(authoring) vs 生成期(generation)**:推理/判断只在编写期发生并冻结成数据;生成期确定性拼装、不推。

---

*本记录随讨论推进持续更新。最新收敛模型见第 9 节;尚未落地项见第 11 节。*
