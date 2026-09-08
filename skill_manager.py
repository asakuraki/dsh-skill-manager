#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dsh-skill-manager
=================
DSH skill 管理工具（独立 Python 脚本，不是 DSH 插件）。

原理
----
DSH 用户级 skill 根目录（默认 ~/.dsh/skills，可被环境变量 DSH_SKILLS_ROOT 覆盖）
- 根目录下**直接**放置的 skill 文件夹 = 已安装（DSH 可读取）
- `_disabled\\` 子目录里的 skill 文件夹 = 被屏蔽（DSH 不读取）

本工具的 ON/OFF 就是纯文件系统「剪切」操作：
  ON  : 把 skill 从 `_disabled\\` 剪回根目录
  OFF : 把 skill 从根目录剪进 `_disabled\\`

本工具会给每个 skill 建立「档案」（分类、备注、收藏等），档案只存在
本工具自己的 `data\\` 目录里（JSON），绝不动 skills 根目录，也不写回
skill 文件夹，保持 skills 目录干净。

作者设定的 hardcode 根目录可用环境变量覆盖：
  DSH_SKILLS_ROOT  -> skill 根目录（默认 ~/.dsh/skills，即用户主目录下）
"""

import os
import re
import sys
import json
import shutil
import argparse
from pathlib import Path

# Windows 控制台常为 GBK，强制 stdout/stderr 用 UTF-8 以免打印特殊字符崩溃
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# ---------------------------------------------------------------------------
# 常量 / 配置
# ---------------------------------------------------------------------------

DEFAULT_SKILLS_ROOT = str(Path.home() / ".dsh" / "skills")  # 分发通用默认
DISABLED_DIRNAME = "_disabled"
DATA_DIRNAME = "data"
ARCHIVE_FILENAME = "archive.json"
CONFIG_FILENAME = "config.json"


def get_skills_root() -> Path:
    """skill 根目录：优先环境变量 DSH_SKILLS_ROOT，否则用默认值。"""
    env = os.environ.get("DSH_SKILLS_ROOT")
    if env:
        return Path(env)
    # 若 config 里记忆了自定义目录（本工具设置过一次），优先使用之
    custom = load_config().get("skills_root")
    if custom:
        return Path(custom)
    return Path(DEFAULT_SKILLS_ROOT)


def load_config() -> dict:
    """读 data/config.json（工具自身配置：技能根目录 + 分类树等）。"""
    p = get_config_path()
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_config(data: dict):
    """写 data/config.json。合并已有键，不覆盖未知内容。"""
    get_data_dir().mkdir(parents=True, exist_ok=True)
    cur = load_config()
    cur.update(data)
    get_config_path().write_text(
        json.dumps(cur, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def ensure_disabled_dir(root: Path):
    """确保 skill 根目录与其 _disabled 子目录存在（分发到没有 _disabled 的机器时自动新建）。"""
    root.mkdir(parents=True, exist_ok=True)
    get_disabled_dir(root).mkdir(parents=True, exist_ok=True)


def get_data_dir() -> Path:
    """本工具的数据目录（档案存放处） = 脚本所在目录/data。"""
    return Path(__file__).resolve().parent / DATA_DIRNAME


def get_archive_path() -> Path:
    return get_data_dir() / ARCHIVE_FILENAME


def get_config_path() -> Path:
    return get_data_dir() / CONFIG_FILENAME


def get_disabled_dir(root: Path) -> Path:
    return root / DISABLED_DIRNAME


# ---------------------------------------------------------------------------
# SKILL.md frontmatter 解析
# ---------------------------------------------------------------------------

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def parse_frontmatter(text: str) -> dict:
    """从 SKILL.md 文本中提取 frontmatter 键值。返回 dict（可能为空）。"""
    result: dict = {}
    m = FRONTMATTER_RE.match(text or "")
    if not m:
        return result
    body = m.group(1)
    # 逐行解析 key: value，支持带引号与多行的 description
    current_key = None
    current_lines = []
    for line in body.splitlines():
        if not line.strip():
            continue
        if line[0].isspace() or line.startswith("\t"):
            # 续行（多行 description / 多行列表）
            if current_key is not None:
                current_lines.append(line.strip())
            continue
        key_match = re.match(r"^([A-Za-z0-9_\-]+)\s*:\s*(.*)$", line)
        if not key_match:
            continue
        # 落盘上一个 key
        if current_key is not None and current_lines:
            result[current_key] = clean_value("\n".join(current_lines))
        current_key = key_match.group(1)
        val = key_match.group(2).strip()
        current_lines = [val] if val else []
    if current_key is not None and current_lines:
        result[current_key] = clean_value("\n".join(current_lines))
    return result


def clean_value(raw: str) -> str:
    """去掉首尾引号，返回精简值。"""
    raw = raw.strip()
    if raw.startswith('"') and raw.endswith('"'):
        raw = raw[1:-1]
    elif raw.startswith("'") and raw.endswith("'"):
        raw = raw[1:-1]
    # 折叠多余空白
    raw = re.sub(r"\s+", " ", raw)
    return raw.strip()


def read_skill_md(skill_dir: Path) -> dict:
    """读取一个 skill 文件夹里的 SKILL.md，返回 {name, description, ...}。"""
    md = skill_dir / "SKILL.md"
    if not md.exists():
        return {}
    try:
        text = md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    return parse_frontmatter(text)


# ---------------------------------------------------------------------------
# 扫描
# ---------------------------------------------------------------------------

def scan_skills(root: Path):
    """
    扫描 skills 根目录，返回两个列表：
      installed: [{folder, dir, name, description}]
      disabled : [{folder, dir, name, description}]
    只认直接子目录；`_disabled` 本身被跳过。
    """
    disabled_dir = get_disabled_dir(root)

    def scan_dir(base: Path, is_disabled: bool):
        out = []
        if not base.exists():
            return out
        for child in sorted(base.iterdir()):
            if not child.is_dir():
                continue
            if child.name == DISABLED_DIRNAME:
                continue
            fm = read_skill_md(child)
            out.append({
                "folder": child.name,
                "dir": str(child),
                "name": fm.get("name") or child.name,
                "description": fm.get("description") or "",
                "disabled": is_disabled,
            })
        return out

    installed = scan_dir(root, False)
    disabled = scan_dir(disabled_dir, True)
    return installed, disabled


# ---------------------------------------------------------------------------
# 档案（archive）读写 —— 存在本工具的 data/ 里
# ---------------------------------------------------------------------------

def load_archive() -> dict:
    """读取档案。结构：{ skill_id: {category, note, starred, auto_discovered} }"""
    p = get_archive_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_archive(archive: dict):
    get_data_dir().mkdir(parents=True, exist_ok=True)
    p = get_archive_path()
    p.write_text(
        json.dumps(archive, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _skill_id(skill: dict) -> str:
    """用 frontmatter name 作为稳定档案主键；没有 name 就退回文件夹名。"""
    return skill.get("name") or skill["folder"]


def ensure_archive_entry(archive: dict, skill: dict):
    sid = _skill_id(skill)
    entry = archive.setdefault(sid, {
        "category": "",
        "note": "",
        "starred": False,
        "auto_discovered": False,
        "ai_description": "",   # AI 自动分类时填写的简介（可选，优先于 SKILL.md 自带简介）
        "display_name": "",     # 工具内显示名（可选，改它不碰原 SKILL.md/frontmatter）
        "pin_category": "",     # 收藏夹内的独立分类（与原 category 并存，互不影响）
    })
    return entry


# ---------------------------------------------------------------------------
# 展示
# ---------------------------------------------------------------------------

def skill_description(skill: dict, entry: dict) -> str:
    """简介：AI 填写的 ai_description 优先，其次 SKILL.md 自带 description。"""
    ai = (entry.get("ai_description") or "").strip()
    if ai:
        return ai
    return skill.get("description") or "（无简介）"


def display_line(skill: dict, entry: dict, idx: int):
    tag = "[开]" if not skill["disabled"] else "[关]"
    star = "*" if entry.get("starred") else " "
    cat = (entry.get("category") or "未分类").strip()
    folder = skill["folder"]
    name = skill["name"]
    desc = skill_description(skill, entry)
    src = "AI" if (entry.get("ai_description") or "").strip() else "SKILL.md"
    print(f"{idx:>3} {tag} {star} <{cat}>  {name}   [folder: {folder}] (简介:{src})")
    print(f"      ↳ {desc}")


def show_all(root: Path):
    installed, disabled = scan_skills(root)
    archive = load_archive()
    print("=" * 70)
    print(f"skill 根目录: {root}")
    print(f"已安装 {len(installed)} 个，已屏蔽 {len(disabled)} 个，合计 {len(installed)+len(disabled)} 个")
    print("=" * 70)

    idx = 0
    # 先显示已安装
    for s in installed:
        idx += 1
        entry = ensure_archive_entry(archive, s)
        display_line(s, entry, idx)
    print("-" * 70)
    for s in disabled:
        idx += 1
        entry = ensure_archive_entry(archive, s)
        display_line(s, entry, idx)
    print("=" * 70)
    # 把本次扫描自动发现的新 skill 落盘进档案
    save_archive(archive)
    print(f"（已安装在前 {len(installed)} 条，其后为已屏蔽）")


# ---------------------------------------------------------------------------
# ON / OFF 切换（纯剪切）
# ---------------------------------------------------------------------------

def toggle(root: Path, selector: str, target_state: str) -> bool:
    """
    target_state: "on"  -> 移到根目录（启用）
                  "off" -> 移到 _disabled（屏蔽）
    按 folder 名（或 frontmatter name）定位，安全剪切。
    返回是否成功。
    """
    installed, disabled = scan_skills(root)
    disabled_dir = get_disabled_dir(root)

    matches = [s for s in installed + disabled if
               s["folder"] == selector or s["name"] == selector]
    if not matches:
        print(f"✗ 找不到 skill: {selector}")
        return False

    # 若同名字命中多个，让用户选（通常用文件夹名最准）
    if len(matches) > 1:
        print(f"⚠ 存在多个同名字面量匹配，请用更精确的文件夹名。命中：")
        for m in matches:
            print(f"   - {m['folder']}  ({'已安装' if not m['disabled'] else '已屏蔽'})")
        return False

    skill = matches[0]
    src = Path(skill["dir"])
    dest_root = root if target_state == "on" else disabled_dir

    if not skill["disabled"] and target_state == "on":
        print(f"• {skill['name']} 已处于启用状态，跳过。")
        return True
    if skill["disabled"] and target_state == "off":
        print(f"• {skill['name']} 已处于屏蔽状态，跳过。")
        return True

    # 目标路径计算：如果目标目录下已存在同名，改名加 _moved 后缀避免覆盖
    dest_dir = dest_root / src.name
    if dest_dir.exists():
        dest_dir = dest_root / f"{src.name}_moved_{os.getpid()}"

    dest_root.mkdir(parents=True, exist_ok=True)
    try:
        shutil.move(str(src), str(dest_dir))
    except OSError as e:
        print(f"✗ 剪切失败 {skill['name']}: {e}")
        return False

    action = "启用" if target_state == "on" else "屏蔽"
    print(f"✓ 已{action}: {skill['name']}  →  {dest_dir}")
    return True


# ---------------------------------------------------------------------------
# 分类 / 备注 / 收藏
# ---------------------------------------------------------------------------

def get_skill_by_selector(root: Path, selector: str):
    installed, disabled = scan_skills(root)
    for s in installed + disabled:
        if s["folder"] == selector or s["name"] == selector:
            return s
    return None


def set_category(root: Path, selector: str, category: str):
    s = get_skill_by_selector(root, selector)
    if not s:
        print(f"✗ 找不到 skill: {selector}")
        return
    archive = load_archive()
    entry = ensure_archive_entry(archive, s)
    entry["category"] = category.strip()
    save_archive(archive)
    print(f"✓ 已把 [{s['name']}] 分类为: {category.strip() or '未分类'}")


def set_note(root: Path, selector: str, note: str):
    s = get_skill_by_selector(root, selector)
    if not s:
        print(f"✗ 找不到 skill: {selector}")
        return
    archive = load_archive()
    entry = ensure_archive_entry(archive, s)
    entry["note"] = note.strip()
    save_archive(archive)
    print(f"✓ 已给 [{s['name']}] 写备注: {note.strip()}")


def set_pin_category(root: Path, selector: str, category: str):
    """设置某收藏 skill 在『收藏夹』里的独立分类（与原本分类并存、互不影响）。"""
    s = get_skill_by_selector(root, selector)
    if not s:
        print(f"✗ 找不到 skill: {selector}")
        return
    archive = load_archive()
    entry = ensure_archive_entry(archive, s)
    entry["pin_category"] = category.strip().strip("/")
    if not entry.get("starred"):
        entry["starred"] = True  # 归入收藏夹分类即视为收藏
    save_archive(archive)
    print(f"✓ 已把 [{s['name']}] 的收藏分类设为: {category.strip().strip('/') or '（未分类收藏）'}")


def toggle_star(root: Path, selector: str):
    s = get_skill_by_selector(root, selector)
    if not s:
        print(f"✗ 找不到 skill: {selector}")
        return
    archive = load_archive()
    entry = ensure_archive_entry(archive, s)
    entry["starred"] = not entry.get("starred", False)
    save_archive(archive)
    print(f"{'☆ 收藏' if entry['starred'] else '★ 取消收藏'}: {s['name']}")


def display_name(skill: dict, entry: dict) -> str:
    """展示名：工具内自定义 display_name 优先，其次 SKILL.md frontmatter name。"""
    dn = (entry.get("display_name") or "").strip()
    return dn if dn else (skill.get("name") or skill["folder"])


def set_display_name(root: Path, selector: str, name: str):
    """设置工具内显示名（仅存档案，不修改原 SKILL.md 的 name/frontmatter）。"""
    s = get_skill_by_selector(root, selector)
    if not s:
        print(f"✗ 找不到 skill: {selector}")
        return
    archive = load_archive()
    entry = ensure_archive_entry(archive, s)
    entry["display_name"] = name.strip()
    save_archive(archive)
    print(f"✓ 已设置 [{s['name']}] 的工具内显示名: {name.strip() or '(还原为原名)'}")


def list_categories(root: Path) -> list:
    """返回当前所有已使用的分类路径列表（支持 “父/子” 斜杠分隔的子分类）。"""
    installed, disabled = scan_skills(root)
    archive = load_archive()
    cats = set()
    for s in installed + disabled:
        entry = ensure_archive_entry(archive, s)
        c = (entry.get("category") or "").strip().strip("/")
        if c:
            cats.add(c)
    return sorted(cats)


def rename_category(root: Path, old: str, new: str) -> int:
    """把某分类（含其子分类）重命名。返回改动条数。new 为空则删除该分类（仅清空归类）。"""
    old = (old or "").strip().strip("/")
    new = (new or "").strip().strip("/")
    installed, disabled = scan_skills(root)
    archive = load_archive()
    changed = 0
    for s in installed + disabled:
        entry = ensure_archive_entry(archive, s)
        c = (entry.get("category") or "").strip().strip("/")
        if not c:
            continue
        if c == old or c.startswith(old + "/"):
            if new:
                suffix = "" if c == old else c[len(old):]
                entry["category"] = new + suffix
            else:
                entry["category"] = ""
            changed += 1
    if changed:
        save_archive(archive)
    return changed


def add_category(root: Path, parent: str, name: str) -> str:
    """在 parent（可为空）下新建一个空分类路径，返回完整分类路径（如 “父/子”）。"""
    parent = (parent or "").strip().strip("/")
    name = (name or "").strip().strip("/")
    if not name:
        raise ValueError("分类名不能为空")
    full = f"{parent}/{name}" if parent else name
    tree = set(load_category_tree())
    tree.add(full)
    save_category_tree(sorted(tree))
    return full


# ---------------------------------------------------------------------------
# 分类树持久化 —— 文件夹式分类结构存在 data/config.json（与 skill 归档不同文件）
# ---------------------------------------------------------------------------

def load_category_tree() -> list:
    """读回用户定义的分类文件夹树（列表，每项是 “父/子” 路径）。"""
    p = get_config_path()
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    tree = data.get("categories") if isinstance(data, dict) else None
    if not isinstance(tree, list):
        return []
    return [str(x).strip().strip("/") for x in tree if str(x).strip().strip("/")]


def save_category_tree(tree: list):
    save_config({"categories": sorted(set(tree))})


def rename_category_folder(root: Path, old: str, new: str) -> int:
    """重命名分类树里的一个文件夹节点，并同步所有归属 skill 的归档。返回改动 skill 数。"""
    old = (old or "").strip().strip("/")
    new = (new or "").strip().strip("/")
    tree = load_category_tree()
    changed_skills = 0
    if old in tree:
        # 重命名树节点及子孙
        new_tree = []
        for f in tree:
            if f == old:
                new_tree.append(new)
            elif f.startswith(old + "/"):
                new_tree.append(new + f[len(old):])
            else:
                new_tree.append(f)
        save_category_tree(new_tree)
    # 同步归档里的归类
    installed, disabled = scan_skills(root)
    archive = load_archive()
    for s in installed + disabled:
        entry = ensure_archive_entry(archive, s)
        c = (entry.get("category") or "").strip().strip("/")
        if not c:
            continue
        if c == old or c.startswith(old + "/"):
            suffix = "" if c == old else c[len(old):]
            entry["category"] = new + suffix
            changed_skills += 1
    if changed_skills:
        save_archive(archive)
    return changed_skills


def delete_category_folder(root: Path, target: str) -> int:
    """删除分类树里的一个文件夹节点（含其子树），并清空归属 skill 的归类。返回改动 skill 数。"""
    target = (target or "").strip().strip("/")
    tree = load_category_tree()
    keep = [f for f in tree if not (f == target or f.startswith(target + "/"))]
    save_category_tree(keep)
    installed, disabled = scan_skills(root)
    archive = load_archive()
    changed = 0
    for s in installed + disabled:
        entry = ensure_archive_entry(archive, s)
        c = (entry.get("category") or "").strip().strip("/")
        if c and (c == target or c.startswith(target + "/")):
            entry["category"] = ""
            changed += 1
    if changed:
        save_archive(archive)
    return changed


# ---------------------------------------------------------------------------
# AI 自动分类文件导入
# ---------------------------------------------------------------------------
# AI（或人）把一堆 skill 的分类 / 简介 / 备注整理成一份 JSON 文件，本工具读取后
# 合并进档案，自动补上新的分类和说明。档案仍只写进 data/，不碰 skills 目录。
#
# 文件格式（version 1）：
# {
#   "version": 1,
#   "generated_by": "AI 名称（可选）",
#   "generated_at": "2026-09-08T12:00:00（可选）",
#   "skills": {
#     "<skill 名 或 文件夹名>": {
#       "category":    "分类名",
#       "description": "一句话简介（可选，会作为该 skill 的 AI 简介优先展示）",
#       "note":        "备注（可选）"
#     },
#     "..."
#   }
# }
# 键「skills」里的 key 用 skill 的 frontmatter name 或文件夹名皆可；脚本会匹配
# 当前扫描到的 skill（优先精确匹配文件夹名，其次名字）。

def import_ai_file(root: Path, filepath) -> dict:
    """读取 AI 生成的分类 JSON，合并进档案。返回 {matched, created_categories, skipped}。"""
    p = Path(filepath)
    if not p.exists():
        print(f"✗ 文件不存在: {filepath}")
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"✗ 无法解析 JSON: {e}")
        return {}

    skills_map = data.get("skills") if isinstance(data, dict) else None
    if not isinstance(skills_map, dict) or not skills_map:
        print("✗ 文件里没有有效的 skills 对象。")
        return {}

    installed, disabled = scan_skills(root)
    # 建一个 文件夹名 -> skill / 名字 -> skill 的索引
    by_folder = {s["folder"]: s for s in installed + disabled}
    by_name = {s["name"]: s for s in installed + disabled}

    archive = load_archive()
    matched = 0
    skipped = []
    new_categories = set()

    for sid, payload in skills_map.items():
        if not isinstance(payload, dict):
            skipped.append((sid, "条目不是对象"))
            continue
        # 定位 skill：先按文件夹名，再按名字
        skill = by_folder.get(str(sid)) or by_name.get(str(sid))
        if not skill:
            skipped.append((str(sid), "找不到对应 skill"))
            continue
        entry = ensure_archive_entry(archive, skill)
        if payload.get("category"):
            old = entry.get("category") or ""
            entry["category"] = str(payload["category"]).strip()
            if old != entry["category"]:
                new_categories.add(entry["category"])
        if payload.get("description"):
            entry["ai_description"] = str(payload["description"]).strip()
        if payload.get("note"):
            entry["note"] = str(payload["note"]).strip()
        matched += 1

    save_archive(archive)
    print(f"✓ 已导入 {matched} 条档案（新分类 {len(new_categories)} 个，跳过 {len(skipped)} 条）。")
    if skipped:
        print("  未匹配：")
        for sid, why in skipped:
            print(f"    - {sid}  ({why})")
    if new_categories:
        print("  新增分类：" + "、".join(sorted(new_categories)))
    return {"matched": matched, "skipped": skipped, "new_categories": new_categories}


def _skill_still_needs_classification(entry: dict) -> bool:
    """该 skill 是否还需要 AI 分类：没有分类 或 没有 AI 简介。"""
    return not (entry.get("category") or "").strip() or not (entry.get("ai_description") or "").strip()


def export_ai_task(root: Path, include_all: bool = False) -> Path:
    """
    生成一份「AI 分类任务文件」，交给 AI 填写后原样导回即可。
    关键设计（让用户「什么也不用说」，文件自解释）：
      1. 只收集还**需要分类**的 skill（没分类 或 没 AI 简介）——已分好的不重复处理；
         也可用 include_all=True 强制包含全部。
      2. 每个 skill 内嵌它 SKILL.md 的『源简介』(source_description)，AI 据此理解功能，
         无需另外说明。
      3. 文件顶部有给 AI 的 instructions 说明它要做什么、填哪几个字段、字段含义。
    字段约定：
      - category   : 必填，给一个简短的中文分类名
      - description: 必填，用一句中文概括这个 skill 是做什么的/何时用
      - note       : 选填，个人备注
    其他字段（source_description 等）是给 AI 看的参考/状态信息，导入时会被忽略。
    """
    installed, disabled = scan_skills(root)
    archive = load_archive()
    skills = installed + disabled

    out = {
        "version": 1,
        "task": "请为下面每个 skill 填写 category（分类名）、description（一句中文简介）、note（选填备注）。description 不要照抄 source_description，用你自己的话一句话讲清楚它做什么、何时用。source_description 与 needs 仅供你参考，不要改。只输出并更新这份 JSON 文件即可，不要额外解释。",
        "generated_by": "AI",
        "generated_at": "",
        "skills": {},
    }

    pending = 0
    for s in skills:
        entry = ensure_archive_entry(archive, s)
        need = _skill_still_needs_classification(entry)
        if not need and not include_all:
            continue
        pending += 1
        out["skills"][s["name"]] = {
            "source_description": skill_description(s, entry),
            "source_category": entry.get("category") or "",
            "needs": "分类+简介" if need else "刷新",
            "category": entry.get("category") or "",
            "description": entry.get("ai_description") or "",
            "note": entry.get("note") or "",
        }

    if not out["skills"]:
        get_data_dir().mkdir(parents=True, exist_ok=True)
        dest = get_data_dir() / "ai_classify_task.json"
        dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print("✓ 没有需要分类的 skill（都已分类且有简介）。仍生成了空任务文件供参考。")
        return dest

    get_data_dir().mkdir(parents=True, exist_ok=True)
    dest = get_data_dir() / "ai_classify_task.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ 已生成 AI 分类任务文件: {dest}（{pending} 个待分类 skill，已分类的已自动跳过）")
    print("  把这份文件丢给 AI，AI 填好后原样拿回来导入即可。")
    return dest


def export_import_template(root: Path, include_all: bool = False) -> Path:
    """旧名兼容入口：默认只含待分类的 skill（= export_ai_task）。"""
    return export_ai_task(root, include_all=include_all)


# ---------------------------------------------------------------------------
# 交互菜单
# ---------------------------------------------------------------------------

MENU_TEXT = """
┌─────────────────────────────────────────────┐
│  dsh-skill-manager                           │
│  1  显示全部 skill（含简介/分类）             │
│  2  启用 skill   (ON)                        │
│  3  屏蔽 skill   (OFF)                       │
│  4  分类 skill                               │
│  5  写备注 skill                             │
│  6  收藏/取消收藏                            │
│  7  按分类筛选查看                           │
│  8  刷新 & 重新建档                          │
│  9  帮助/说明                                │
│  0  退出                                     │
└─────────────────────────────────────────────┘
"""


def interactive(root: Path):
    print(MENU_TEXT)
    while True:
        try:
            cmd = input("\n> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n退出。")
            break
        if cmd in ("0", "q", "exit", "quit"):
            print("退出。")
            break
        elif cmd == "1":
            show_all(root)
        elif cmd == "2":
            selector = input("输入要启用的 skill（文件夹名/名字）: ").strip()
            if selector:
                toggle(root, selector, "on")
        elif cmd == "3":
            selector = input("输入要屏蔽的 skill（文件夹名/名字）: ").strip()
            if selector:
                toggle(root, selector, "off")
        elif cmd == "4":
            selector = input("输入要分类的 skill: ").strip()
            cat = input("分类名（回车清空）: ").strip()
            if selector:
                set_category(root, selector, cat)
        elif cmd == "5":
            selector = input("输入要写备注的 skill: ").strip()
            note = input("备注内容（回车清空）: ").strip()
            if selector:
                set_note(root, selector, note)
        elif cmd == "6":
            selector = input("输入要收藏/取消的 skill: ").strip()
            if selector:
                toggle_star(root, selector)
        elif cmd == "7":
            cat = input("输入分类名筛选: ").strip()
            show_by_category(root, cat)
        elif cmd == "8":
            print("重新扫描建档完成。")
            show_all(root)
        elif cmd == "9":
            print(MENU_TEXT)
        else:
            print(f"未知命令: {cmd}")


def show_by_category(root: Path, category: str):
    installed, disabled = scan_skills(root)
    archive = load_archive()
    cat = category.strip()
    hits = []
    for s in installed + disabled:
        entry = ensure_archive_entry(archive, s)
        if (entry.get("category") or "").strip() == cat:
            hits.append((s, entry))
    if not hits:
        print(f"没有属于分类「{cat}」的 skill。")
        return
    print(f"分类「{cat}」共 {len(hits)} 个:")
    for i, (s, e) in enumerate(hits, 1):
        display_line(s, e, i)


# ---------------------------------------------------------------------------
# 命令行入口
# ---------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(
        prog="skill_manager",
        description="DSH skill 管理工具（独立脚本，非插件）。档案存放在脚本旁的 data/ 目录。",
    )
    p.add_argument("action", nargs="?", default="menu",
                   help="list|on|off|cat|note|star|filter|import|template|task|menu")
    p.add_argument("--skill", help="skill 文件夹名或名字")
    p.add_argument("--cat", help="分类名（配合 cat）")
    p.add_argument("--note", help="备注内容（配合 note）")
    p.add_argument("--filter", help="分类名（配合 filter 查看）")
    p.add_argument("--file", help="AI 分类 JSON 文件路径（配合 import）")
    p.add_argument("--all", action="store_true",
                   help="template/task 时强制包含所有 skill（默认只含待分类的）")
    return p


def main():
    root = get_skills_root()
    if not root.exists():
        print(f"✗ skill 根目录不存在: {root}")
        print("  可用环境变量 DSH_SKILLS_ROOT 覆盖。")
        sys.exit(1)

    args = build_parser().parse_args()
    action = args.action

    if action == "menu":
        interactive(root)
    elif action == "list":
        show_all(root)
    elif action == "on":
        if not args.skill:
            print("需要 --skill 参数")
            sys.exit(1)
        toggle(root, args.skill, "on")
    elif action == "off":
        if not args.skill:
            print("需要 --skill 参数")
            sys.exit(1)
        toggle(root, args.skill, "off")
    elif action == "cat":
        if not args.skill or not args.cat:
            print("需要 --skill 与 --cat 参数")
            sys.exit(1)
        set_category(root, args.skill, args.cat)
    elif action == "note":
        if not args.skill or not args.note:
            print("需要 --skill 与 --note 参数")
            sys.exit(1)
        set_note(root, args.skill, args.note)
    elif action == "star":
        if not args.skill:
            print("需要 --skill 参数")
            sys.exit(1)
        toggle_star(root, args.skill)
    elif action == "filter":
        if not args.filter:
            print("需要 --filter 参数")
            sys.exit(1)
        show_by_category(root, args.filter)
    elif action == "import":
        if not args.file:
            print("需要 --file 参数（AI 分类 JSON 路径）")
            sys.exit(1)
        import_ai_file(root, args.file)
    elif action == "template":
        export_import_template(root, include_all=args.all)
    elif action == "task":
        export_ai_task(root, include_all=args.all)
    else:
        print(f"未知动作: {action}")
        build_parser().print_help()


if __name__ == "__main__":
    main()
