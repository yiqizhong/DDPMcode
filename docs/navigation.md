# 项目导航 · 阅读地图（什么阶段读哪些文件）

> **用途**:不用每次从头读全仓库。先看这一页 → 按"任务"找到该读/该改的**那几个文件**。
> 这是**入口索引 + 任务路由**,不重复别处内容,只指路。最后更新:2026-06-26。

---

## 1. 一句话:这是什么项目

一个**产品 UI 生成系统**(headset 为 pilot)。强模型在**编写期**把设计意图冻结成"预写片段 + manifest 数据";
**弱模型在生成期只复制片段 + 填值,不生成、不推断**("copy, don't create")。三层:

```
设计令牌 shared/tokens.css  →  品类样式 headset/headset.css  →  页面骨架(skills)  →  机型数据(manifest)
```

---

## 2. 文件结构总览(每行一句话 + 属于哪层)

```
AGENTS.md                       根 agent map:三层架构、skill 命名/防 sprawl、copy-not-create、build 契约
docs/
  navigation.md                 ← 你在这(阅读地图)
  component-catalog.md          【组件清单】所有可复用组件 + 何时用 + 通用性 + 调用方式(活清单)
  function-card-architecture.md 【设计日志】为什么这么设计:D1–D18 决策、§7 控件选型、§8 交互模型(长,历史)
  methodology.md                外部方法论(仅参考,与 codebase 冲突时以 codebase 为准;顶部有"已被代码取代"清单)
headset/
  AGENTS.md                     【headset 操作契约】路由、非协商规则、控件选型三表、目录树 —— 干活前先读这
  headset.css                   品类布局 + 所有组件样式 + 交互(:has/:checked/subfn/面板/dropdown)
  models/<MODEL>/               机型 manifest + 生成出的成品页(目前无真机型;HS-DEMO 已 gitignore)
shared/tokens.css               设计令牌(颜色/字体/圆角…),全品类共享
.agents/skills/                 Devin 在仓库根发现的 skill(folder + SKILL.md)
  headset-gen-homepage/         生成 index.html(home-frame.html)
  headset-gen-subpage/          生成任意子页(subpage-frame.html)
    templates/functions/        【现成可套用卡 · id 路由】eq-audio / promotion-download / single-control + README
    templates/examples/         【演示/教学范例 · 不路由】collaboration / auto-power-off / noise-control + README
  headset-function/             无快照时的兜底卡构建器(function-frame.html = 卡壳)
  headset-shared/               不是 skill,是共享片段:
    subcontrols/                6 个原子片段(.html) + README(原子规则 + segmented/preset 细则)
    connection/                 连接块片段(bluetooth/wired/unpair)
    icons/  feature-button.html  图标库 + 功能按钮
```

---

## 3. 按任务的阅读/修改路线(核心)

| 我要做什么 | 读/改哪些文件(按顺序) | 注意 |
|---|---|---|
| **改一个原子片段**(toggle/slider/segmented/preset/dropdown/info) | `subcontrols/<name>.html`(片段本身) → `subcontrols/README.md`(原子规则) → `headset/headset.css`(它的样式) | 片段无内联 `<style>`;样式全在 headset.css |
| **加/改一张功能卡** | 有快照→直接改 `functions/<id>.html`;无→`headset-function/templates/function-frame.html`(卡壳)+`subcontrols/*`(原子)拼;对照 `component-catalog.md` | 卡按 manifest 的 `id` 路由(D8) |
| **改"可替换控件(swap)"规则** | **只改** `subcontrols/toggle.html`(唯一权威);`single-control.html` 引用它,别在它里重写 | 只允许 switch ↔ dropdown 进 header |
| **改"用哪个控件"的选型规则** | `headset/AGENTS.md` §"Control Selection"(operational) | 为什么这么定 → `function-card-architecture.md` §7 |
| **改路由**(哪个 id→哪张卡 / 关键词) | `functions/README.md` + `headset-gen-subpage/SKILL.md` + `headset/AGENTS.md` 路由段 | 生成期纯 id;关键词表仅编写期 |
| **改样式 / 加 token** | 组件样式→`headset/headset.css`;颜色等 token→`shared/tokens.css` | 禁内联 `<style>`,token 优先 |
| **加连接块 / feature 按钮 / 图标** | `headset-shared/connection|icons|feature-button.html` + 各自 README | 也是 copy 片段,未知 enum 就 HALT |
| **理解整体为什么这么设计** | `function-card-architecture.md`(决策日志 D1–D18 + §节) | 长,只在需要"为什么"时读 |
| **想知道有哪些组件、各自通用不通用** | `component-catalog.md` | 一站式清单 |

---

## 4. 权威源对照(防 drift / 别重复读)

每件事只有**一个**真相源,改的时候认准它:

| 主题 | 唯一真相源 | 其它文件的角色 |
|---|---|---|
| 三层架构 / skill 命名 / 防 sprawl | `AGENTS.md`(根) | — |
| headset 路由 + 非协商规则 + 控件选型表 | `headset/AGENTS.md` | — |
| 组件清单 / 通用性 | `docs/component-catalog.md` | — |
| swap 规则(可替换 header 控件) | `subcontrols/toggle.html` | single-control 引用它 |
| segmented vs preset-grid 细则 | `subcontrols/README.md` | AGENTS 只给家族级表 |
| 设计决策的"为什么" | `function-card-architecture.md` | 历史/思考日志,不是当前规范 |
| 样式 | `headset/headset.css` | token 在 tokens.css |
| methodology.md | — | **仅参考**(顶部列了已被代码取代的点),冲突以 codebase 为准 |

---

## 5. 新人/新会话最短上手顺序

1. 本页(navigation.md)—— 知道东西在哪。
2. `headset/AGENTS.md` —— 干活的硬规则 + 目录树。
3. 要碰组件 → `docs/component-catalog.md` 找到对应项 → 跳到它的文件。
4. 只有需要"为什么这么设计"时,才去翻 `function-card-architecture.md`。

> 维护:文件结构/权威源变化时更新本页第 2、4 节 + 顶部日期。
