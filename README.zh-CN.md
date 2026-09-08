# dsh-skill-manager

> 中文说明 · [English README](README.md)

一个独立的命令行工具，用来整理你的 [DSH](https://github.com/asakuraki/) 技能。它**不是 DSH 插件**——只是把 skill 文件夹在根目录和 `_disabled\` 之间“剪切”，让 DSH 能看到或看不到它，同时维护一份你自己的分类 / 备注 / 收藏档案。

## 原理

DSH 读取用户级 skill 根目录（默认 `~\.dsh\skills`，可用环境变量 `DSH_SKILLS_ROOT` 覆盖）：

| 位置 | 含义 |
|------|------|
| 根目录下直接放的 skill 文件夹 | **已启用**——DSH 可读取 |
| `_disabled\` 子目录里的 skill 文件夹 | **已屏蔽**——DSH 不读取 |

所以 **启用 / 屏蔽就是纯文件夹剪切**：剪进 `_disabled\` 即隐藏，剪回即恢复。无需改配置、无需重启、不碰 DSH 本身。

你的档案（分类、备注、收藏、AI 简介）**只存在工具自己的 `data\` 文件夹**里，skill 文件夹从不会被改动。

## 语言切换

工具内置 **中 / 英文** 两种界面语言，可随时切换并记住选择。

- **命令行参数**：`python skill_manager.py --lang en`（本次生效）；`python skill_manager.py --lang zh` 
- **记忆设置**：`python skill_manager.py lang --lang en`（记住为英文，下次自动用）
- **交互菜单**：进入 `menu` 后按 `L`，输入 `zh` 或 `en` 即可切换
- **环境变量**：`DSH_SKILLS_LANG=en` 

优先级：`--lang` 参数 > `data/config.json` 的 `lang` 键 > 环境变量 `DSH_SKILLS_LANG` > 默认中文。

## 安装

需要 Python 3，无第三方依赖。下载后直接运行 `skill_manager.py` 即可。

> **可选图形界面**：`skill_manager_gui.py` 提供图形窗口（基于 **PySide6**）。使用前需把 PySide6 装进本地 `.venv`，然后双击 `skill-manager-gui.bat`（或运行 `python skill_manager_gui.py`）。

## 图形界面（可选）

双击 **`skill-manager-gui.bat`** 即可打开管理器窗口（需已安装 PySide6）。

- 左侧文件夹式分类树；右侧每个 skill 一张卡片，简介突出，卡片右上角开关一键启停。
- 点击卡片可改名 / 改简介 / 换分类 / 写备注（只存工具自己的 `data\` 档案，绝不改原 `SKILL.md`）。
- 搜索框、分类筛选、收藏图钉、拖放归类、白天/黑夜/随系统主题。
- **AI 整理**：用「①生成AI任务」导出待分类 skill，再把 AI 填好的文件用「②导入AI结果」并入。

安装图形界面依赖（一次即可）：

```powershell
.venv\Scripts\python.exe -m pip install PySide6
```

> 本仓库的 CLI 不依赖 PySide6，可独立使用；GUI 是可选项。

## 使用

```powershell
python skill_manager.py list        # 显示全部 skill（简介/分类/开关状态）
python skill_manager.py menu        # 交互菜单（日常推荐）
```

直接命令：

```powershell
python skill_manager.py on   --skill godot-tweening          # 启用
python skill_manager.py off  --skill godot-tweening          # 屏蔽
python skill_manager.py cat  --skill godot-2d-physics --cat "Godot-物理"
python skill_manager.py note --skill godot-tweening --note "做UI动画时用"
python skill_manager.py star --skill dsh-skill-ops           # 收藏/取消收藏
python skill_manager.py filter --filter "Godot-物理"          # 只看某分类
```

## AI 自动分类

skill 太多时，把新下载的丢进 `_disabled\`，让 AI 一次帮你分好类：

1. `python skill_manager.py template` — 生成 `data\ai_classify_task.json`，只包含**还待分类**的 skill。
2. 把这份文件丢给 AI——文件自解释，AI 填好 `category` / `description` / `note` 后原样还你。
3. `python skill_manager.py import --file data\ai_classify_task.json` — 把结果并入档案（不碰 skill 文件夹）。

可选：若有 `SKILL-MANIFEST.md`，运行 `python fill_ai_task.py` 可自动按官方清单填好任务文件。

## 命令速查

| 命令 | 说明 |
|------|------|
| `list` | 列出全部 skill（简介/分类/开关状态） |
| `menu` | 进入交互菜单 |
| `on --skill X` | 启用 X（剪回根目录） |
| `off --skill X` | 屏蔽 X（剪进 `_disabled`） |
| `cat --skill X --cat C` | 把 X 分到类 C |
| `note --skill X --note N` | 给 X 写备注 N |
| `star --skill X` | 收藏/取消收藏 X |
| `filter --filter C` | 只看属于 C 的 skill |
| `import --file F` | 导入 AI 填好的分类 JSON |
| `template [--all]` | 生成 AI 任务文件（默认只含待分类的） |
| `lang --lang en\|zh` | 切换并记住界面语言 |
| `--lang en\|zh` | 本次运行使用的界面语言 |

## FAQ

**会不会误删 skill？**
不会。启用/屏蔽只用 `shutil.move`（剪切）。若目标位置已有同名文件夹，会自动加 `_moved_<pid>` 后缀避免覆盖。

**它算插件吗？**
不算。它是独立脚本——不注册 DSH 插件、不改 patch、不注入。只移动文件夹并维护自己的 `data\` JSON 档案。

## 许可证

[MIT](LICENSE)