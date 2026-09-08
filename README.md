# dsh-skill-manager

DSH skill 管理工具 —— **独立 Python 脚本，不是 DSH 插件**。

它不装进 DSH、不注册任何插件机制，纯粹在你本机的 DSH skill 目录上做文件级「剪切」操作来开关 skill，并给你维护一份「档案」让你一眼看到每个 skill 是干什么的、怎么分类的。

---

## 原理（就一句话）

DSH 用户级 skill 根目录（默认 `~\.dsh\skills`，可用环境变量 `DSH_SKILLS_ROOT` 覆盖）

| 位置 | 含义 |
|------|------|
| 根目录下**直接**放的 skill 文件夹 | **已安装**，DSH 可读取 |
| `_disabled\` 子目录里的 skill 文件夹 | **被屏蔽**，DSH 不读取 |

所以 **ON / OFF 就是纯剪切**：

- **启用 (ON)** ：把 skill 文件夹从 `_disabled\` **剪回**根目录
- **屏蔽 (OFF)**：把 skill 文件夹从根目录 **剪进** `_disabled\`

DSH 只扫根目录的直接子目录，放进 `_disabled` 后它立刻读不到，拖回根目录立刻恢复——不需要改任何配置、不需要重启、不碰 DSH 本体。

> 额外好处：这个机制对 DSH **自带的可读写 skill 目录**生效，也和 DSH 的插件/注入机制完全解耦，干净、可逆、可一键回滚。

---

## 档案（数据）存在哪？

所有分类 / 备注 / 收藏 / 发现记录 **只存在本工具自己的文件夹里**，**绝不写进 skills 目录**：

```
dsh-skill-manager\
├─ skill_manager.py          ← 核心 + 命令行（单文件）
├─ skill_manager_gui.py      ← 图形界面（PySide6）
├─ skill_manager_gui_tk.py   ← 旧版 tkinter 界面（备份）
├─ 启动管理器GUI.bat         ← 双击即开图形界面
├─ fill_ai_task.py           ← 从 SKILL-MANIFEST.md 一键填好任务文件的脚本（可选）
├─ .venv\                    ← 本地 Python 虚拟环境（装 PySide6）
├─ samples\
│  └─ ai_classify.sample.json← AI 分类文件格式样例
└─ data\
   ├─ archive.json           ← 你的档案（分类、备注、收藏、AI简介、工具内显示名 display_name）
   ├─ config.json            ← 分类文件夹树结构（可新建/重命名/删除，含空分类）
   └─ ai_classify_task.json  ← 生成的「给 AI 填」的任务文件（可删）
```

skill 文件夹保持原样，DSH 目录一个字节都不会被本工具污染。

---

## 快速开始

### 0) 图形界面（推荐，双击即开）

双击 **`启动管理器GUI.bat`**（或 `python skill_manager_gui.py`）。界面基于 **PySide6**（已装在项目内 `.venv`，首次运行会自动用 `.venv` 的 python 启动）。

新版界面特点：
- **顶部搜索框**：按名字 / 简介 / 文件夹实时过滤卡片。
- **左侧文件夹式分类树**：`全部 / 已装 / 未装 / 收藏` + 你一手的分类文件夹（可建子分类）。进软件第一步就是按类别筛你需要看的 skill。
- **卡片式 skill 分布**：每个 skill 一行卡片，**简介最突出（大字号）**；卡片右上角滑块开关（**右滑=绿色=启用**、左滑=红色=屏蔽）一键启停，已启用的排在上面；滑块旁的**图钉（自绘图标）**可将常用 skill 收进**收藏夹**。
- **收藏夹（独立分类）**：左侧「收藏」文件夹。点卡片右上角 📌 即收藏（黄=已收藏，灰=未收藏）。收藏夹里的分类与卡片原本分类**互相独立、可并存**——把卡片拖进「收藏」下的分类即分配收藏分类，不影响它在原分类中的归类。
- **已装 / 未装 标签**：顶层两个文件夹即开关视图。切换开关只看右上角滑块。
- **拖放归类**：把卡片直接拖进左侧某个分类文件夹，即把该 skill 归到那个分类（仅改工具内档案，不动文件）。
- **点击卡片编辑**：改名、改简介、换分类、写备注——都只存在工具内档案（`data/archive.json`），**不会修改原 SKILL.md 的名字或内容**。
- **主题**：工具栏可切 `随系统 / 白天 / 黑夜`。
- **AI 整理**：低频操作收进工具栏「菜单」里的二级「AI 整理」子菜单（① 生成任务 → ② 导入结果）。

> 旧的 tkinter 版本已备份为 `skill_manager_gui_tk.py`，需要用回可手动运行它。
> 首次使用若未装 PySide6，请执行：`.venv\Scripts\python.exe -m pip install PySide6`。

### 1) 命令行查看全部 skill（含简介 + 分类 + 开关状态）

```powershell
cd E:\编程\通用默认工作区\dsh-skill-manager
python skill_manager.py list
```

输出里：
- `[开]` / `[关]` 表示当前启用 / 屏蔽状态
- `<分类>` 显示你手动分的类
- 每行 `↳ 简介` 默认从该 skill 的 `SKILL.md` frontmatter `description` 读出来；若你导入了 AI 简介，则优先显示 AI 简介（标注 `简介:AI`）

### 2) 交互菜单（推荐日常用）

```powershell
python skill_manager.py menu
```

```
 1  显示全部 skill（含简介/分类）
 2  启用 skill   (ON)
 3  屏蔽 skill   (OFF)
 4  分类 skill
 5  写备注 skill
 6  收藏/取消收藏
 7  按分类筛选查看
 8  刷新 & 重新建档
 9  帮助/说明
 0  退出
```

输入数字执行对应操作。切换 skill 时输入它的 **文件夹名或名字** 即可。

### 3) 命令行直接操作

```powershell
# 启用 / 屏蔽
python skill_manager.py on  --skill godot-tweening
python skill_manager.py off --skill godot-tweening

# 分类 / 备注 / 收藏
python skill_manager.py cat  --skill godot-2d-physics --cat "Godot-物理"
python skill_manager.py note --skill godot-tweening --note "做UI动画时用"
python skill_manager.py star --skill dsh-skill-ops

# 按分类筛选查看
python skill_manager.py filter --filter "Godot-物理"
```

---

## 🤖 AI 自动分类 & 简介导入（推荐流程）

skill 太多时，把新下载的 skill 丢进 `_disabled\` 后，让 AI 一次帮你把所有 skill 分好类并补一句话中文简介。工具生成一个「**自解释的任务文件**」——AI 读了不用你多说一句话，填完原样还给你，工具再一键同步进档案。档案仍只写进 `data/`，**不碰 skills 目录**。

### 完整流程（GUI 两步走）

> ① 先把你新下载的 skill 整个文件夹拖进技能根目录下的 `_disabled\`（默认 `~\.dsh\skills\_disabled\`）

1. **点「①生成AI任务」** ：工具扫描，把**还没分类/没简介**的 skill 生成一份 `data\ai_classify_task.json`，每个 skill 里已内嵌各自的原始简介（AI 据此理解，无需你额外说明），文件顶部还有给 AI 的操作说明。
2. **把这份文件丢给 AI，什么都不用说**：AI 读文件顶部说明，挨个填好 `category` / `description` / `note`，把文件原样还给你。
3. **点「②导入AI结果」** ：选 AI 填好的文件，工具自动并入档案——分类、中文简介、备注全部同步好。

命令行等价操作：`template` 生成任务文件 → 丢给 AI → `import --file data\ai_classify_task.json` 导回。

> 💡 **Godot skills 一键填好**：本机 godot 库自带 `SKILL-MANIFEST.md`（官方分类清单）。生成任务文件后，运行 `python fill_ai_task.py` 即可按官方清单自动把全部 skill 分类 + 中文简介填进任务文件，再 `import` 导入。`fill_ai_task.py` 内的 `DATA` 字典可自行增改。

### 关键特性

- **增量处理**：任务文件**只包含仍需要分类的 skill**（没分类 或 没 AI 简介），已分好的不会重复出现。每次生成都只挑还没搞定的。
- **文件自解释**：每个 skill 内嵌 `source_description`（它 SKILL.md 的自带简介）供 AI 参考，顶部有 instructions 告诉 AI 填什么——所以你「什么也不用说」。
- **AI 引入即优先显示**：AI 填的 `description` 作为「AI 简介」优先展示（列表标注 `简介:AI`），没填的仍读 SKILL.md 自带简介。

### 任务文件格式（AI 看到的）

```json
{
  "version": 1,
  "task": "请为每个 skill 填写 category（分类名）、description（一句中文简介）、note（选填备注）……（AI 的操作说明）",
  "skills": {
    "godot-2d-physics": {
      "source_description": "(该 skill 的 SKILL.md 自带简介，给 AI 参考，勿改)",
      "category": "Godot-物理",
      "description": "2D碰撞层/掩码、Area2D触发器、射线检测与手动物理查询。",
      "note": "碰撞判定基础"
    }
  }
}
```

- `skills` 的 **key** 用 skill 的 `name`，脚本也会按文件夹名兜底匹配；匹配不到的会提示跳过，不影响其余导入。
- `category`：分类名（自由定）。
- `description`：AI 写的一句话中文简介（填入后作为「AI 简介」优先展示）。
- `note`：备注（可选）。
- `source_description`、`needs`、`source_category` 是给 AI 看的参考/状态，导入时自动忽略。
- 入格式兼容旧模板 —— 也可以手写一个只有 `category/description/note` 的简化 JSON 来导入。
- 参考样例：`samples\ai_classify.sample.json`。

> 提示：觉得某些 skill 分类/简介不对，改好这份 JSON 再导一次即可覆盖；或直接在界面里选中它重新手填。

---

## 命令行参数速查

| 参数 | 说明 |
|------|------|
| `list` | 列出全部 skill（含简介/分类/开关状态） |
| `menu` | 进入交互菜单 |
| `on --skill X` | 启用 X（剪回根目录） |
| `off --skill X` | 屏蔽 X（剪进 `_disabled`） |
| `cat --skill X --cat C` | 给 X 分到类 C |
| `note --skill X --note N` | 给 X 写备注 N |
| `star --skill X` | 收藏/取消收藏 X |
| `filter --filter C` | 只看属于分类 C 的 skill |
| `import --file F` | 导入 AI 填好的分类 JSON（并入档案） |
| `template` | ① 生成 AI 任务文件（只含待分类 skill，丢给 AI 填）；`--all` 可含全部 |
| `skill_manager_gui.py` | 启动图形界面（或用 `启动管理器GUI.bat`） |

---

## 进阶 / 定制

- **换 skill 根目录**：默认是 `C:\Users\<用户名>\.dsh\skills`（不是写死某一台机器）。
  定位顺序（从高到低）：
  1. 环境变量 `DSH_SKILLS_ROOT` 指向任意目录；
  2. 在软件「菜单 → 设置 skill 目录…」里选过一次后，会把该目录存入 `data\config.json`，下次启动自动优先用它；
  3. 都未设置 → 用默认 `~\.dsh\skills`。
  → **分发软件给别人**：对方只要在「菜单 → 设置 skill 目录…」里选一次自己的目录即可，工具会记住。
- **自动新建 `_disabled`**：每个 skill 的启用/屏蔽原理是把文件夹移进 `_disabled\`。若目标机器没有 `_disabled` 文件夹，软件启动时会**自动创建**（根目录与 `_disabled` 一并 mkdir），无需手动建。
- **档案备份**：`data\archive.json` 就是全部档案，拷贝它即可迁移，与 skills 目录无关。
- **手动归类**：档案里每个 skill 可设 `category`（分类）、`note`（备注）、`starred`（收藏），全由你定，脚本只在扫描时自动把没见过的 skill 登记进档案（`auto_discovered`），不覆盖你的手填内容。

---

## 常见问题

**Q: 会不会误删 skill？**
不会。ON/OFF 只是 `shutil.move`（剪切），不删除任何内容。目标位置已存在同名时会自动加 `_moved_<pid>` 后缀避免覆盖。

**Q: 它算插件吗？**
不算。它是独立 Python 脚本，不注册 DSH 插件、不改 patch、不注入。唯一作用就是移动文件夹 + 维护自己的 JSON 档案。

**Q: 为什么我的分类显示「未分类」？**
因为还没手动分。脚本只自动登记新发现的 skill，分类完全由你通过 `cat` / 菜单第 4 项填写。
