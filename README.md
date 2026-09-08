# dsh-skill-manager

> English · [中文说明](README.zh-CN.md)

A small standalone CLI tool to organize your [DSH](https://github.com/asakuraki/) skills. It is **not a DSH plugin** — it simply moves skill folders between the root and a `_disabled\` folder so DSH can or cannot see them, and keeps your own archive of categories, notes, and favorites.

The CLI interface is **fully bilingual (English / 中文)** and the language is remembered between runs.

## Language

The tool ships with both **English** and **Chinese** interfaces:

- **Per-run flag**: `python skill_manager.py --lang en` or `--lang zh`
- **Persist a choice**: `python skill_manager.py lang --lang en` (remembered for next runs)
- **Interactive menu**: run `menu` and press `L`, then type `zh` or `en`
- **Environment variable**: `DSH_SKILLS_LANG=en`

Priority: `--lang` flag > `data\config.json` `lang` key > env `DSH_SKILLS_LANG` > default Chinese.

## How it works

DSH reads skills from the user-level skills root (default `~\.dsh\skills`, overridable via the `DSH_SKILLS_ROOT` env var):

| Location | Meaning |
|----------|---------|
| directly in the root | **enabled** — visible to DSH |
| inside `_disabled\` | **hidden** — ignored by DSH |

So **enable / disable is pure folder moving**: cut into `_disabled\` to hide, cut back to show. No config changes, no restart, nothing touches DSH itself.

Your archive (categories, notes, favorites, AI descriptions) is stored **only in the tool's own `data\` folder** — skill folders are never modified.

## Install

Requires Python 3. No third-party packages. Clone or download and run `skill_manager.py`.

> **Optional GUI**: `skill_manager_gui.py` provides a graphical window (built on **PySide6**). To use it, install PySide6 into the local `.venv` and launch via `skill-manager-gui.bat` (or `python skill_manager_gui.py`).

## GUI

Double-click **`skill-manager-gui.bat`** to open the manager window (PySide6 must be installed — see below).

- Folder-style category tree on the left; each skill is a card on the right with its description highlighted and a one-click enable/disable switch on the top-right.
- Click a card to edit its display name / description / category / note (stored only in the tool's own `data\` archive — never touches the original `SKILL.md`).
- Search box, category filter, favorites pin, drag-and-drop to categorize, and light / dark / system themes.
- **AI 整理**: use the "AI task" step to export unclassified skills, then "Import AI result" to merge the AI-filled JSON.

To install the GUI dependency (once):

```powershell
.venv\Scripts\python.exe -m pip install PySide6
```

> The CLI in this repo is fully functional without PySide6; the GUI is optional.

## Usage

```powershell
python skill_manager.py list        # show all skills (summary, category, on/off state)
python skill_manager.py menu        # interactive menu (recommended for daily use)
```

Direct commands:

```powershell
python skill_manager.py on   --skill godot-tweening        # enable
python skill_manager.py off  --skill godot-tweening        # disable
python skill_manager.py cat  --skill godot-2d-physics --cat "Godot-Physics"
python skill_manager.py note --skill godot-tweening --note "Use for UI animation"
python skill_manager.py star --skill dsh-skill-ops         # toggle favorite
python skill_manager.py filter --filter "Godot-Physics"    # show only a category
```

## AI-assisted categorization

Got too many skills? Drop new ones into `_disabled\`, then let an AI categorize them for you:

1. `python skill_manager.py template` — generates `data\ai_classify_task.json` with only the skills that still need a category/description.
2. Send that file to an AI — it's self-explanatory; the AI fills in `category` / `description` / `note` and returns it.
3. `python skill_manager.py import --file data\ai_classify_task.json` — merges the results into your archive (without touching the skill folders).

Optional: `python fill_ai_task.py` auto-fills the file from a `SKILL-MANIFEST.md` if you have one.

## CLI reference

| Action | Description |
|--------|-------------|
| `list` | List all skills (summary, category, on/off) |
| `menu` | Open the interactive menu |
| `on --skill X` | Enable X (move back to root) |
| `off --skill X` | Disable X (move into `_disabled`) |
| `cat --skill X --cat C` | Set X's category to C |
| `note --skill X --note N` | Set X's note to N |
| `star --skill X` | Toggle favorite on X |
| `filter --filter C` | Show only skills in category C |
| `import --file F` | Merge an AI-filled JSON into the archive |
| `template [--all]` | Generate the AI task file (by default only unclassified skills) |
| `lang --lang en\|zh` | Switch and remember the interface language |
| `--lang en\|zh` | Set the interface language for this run |

## FAQ

**Can it accidentally delete a skill?** No. Enable/disable only uses `shutil.move` (cut/paste). If the destination already has a same-named folder, it gets a `_moved_<pid>` suffix.

**Is it a plugin?** No. It's a standalone script — no DSH plugin registration, no patches, no injection. It only moves folders and maintains its own `data\` JSON archive.

## License

[MIT](LICENSE)