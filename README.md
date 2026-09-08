# dsh-skill-manager

A small standalone CLI tool to organize your [DSH](https://github.com/asakuraki/) skills. It is **not a DSH plugin** — it simply moves skill folders between the root and a `_disabled\` folder so DSH can or cannot see them, and keeps your own archive of categories, notes, and favorites.

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

## FAQ

**Can it accidentally delete a skill?** No. Enable/disable only uses `shutil.move` (cut/paste). If the destination already has a same-named folder, it gets a `_moved_<pid>` suffix.

**Is it a plugin?** No. It's a standalone script — no DSH plugin registration, no patches, no injection. It only moves folders and maintains its own `data\` JSON archive.

## License

[MIT](LICENSE)