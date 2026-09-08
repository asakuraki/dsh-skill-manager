#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dsh-skill-manager GUI (PySide6)
===============================
文件夹式分类 + 卡片式 skill 管理界面。
复用 skill_manager.py 的核心逻辑（开关=剪切，分类/简介为工具内档案）。

特性：
- 左侧分类树（含 已装/未装/全部 与自定义分类文件夹，可建子分类、拖放归类）
- 右侧卡片流（每个 skill 一行卡片，突出简介，右上角开关一键启停）
- 点击卡片编辑 名字/简介/分类（仅存工具内档案，不改原 SKILL.md）
- 「未装」分类下点击卡片 = 直接启用并消失到「已装」
- 三种主题：随系统 / 白天 / 黑夜
- AI 整理收入「菜单」二级入口（低频不占界面）

用法（依赖 PySide6，已装到 .venv）：
    .venv\\Scripts\\python.exe skill_manager_gui.py
"""
import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QMimeData, QRectF, Signal, QPointF
from PySide6.QtGui import QAction, QColor, QPainter, QBrush, QPen, QPolygonF
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QTreeWidget, QTreeWidgetItem, QPushButton, QComboBox,
    QFrame, QSplitter, QMenu, QDialog, QFormLayout, QLineEdit, QTextEdit,
    QMessageBox, QFileDialog, QToolBar, QInputDialog, QCheckBox,
)

CORE = Path(__file__).resolve().parent
sys.path.insert(0, str(CORE))
import skill_manager as core  # noqa: E402


# ---------------------------------------------------------------------------
# GUI 界面国际化（中/英）
# ---------------------------------------------------------------------------
# 复用 core 的语言状态（core.LANG / core.set_language / core.save_config）。
# 本文件用 gt(key, *args) 取 GUI 专用文案；语言切换时用重建窗口的方式刷新。

_GUI = {
    "zh": {
        "app_name": "DSH Skill 管理器",
        "window_title": "DSH Skill 管理器",
        "tree_all": "全部",
        "tree_installed": "已装",
        "tree_disabled": "未装",
        "tree_pinned": "收藏",
        "pin_tooltip": "收藏分类「{0}」",
        "drop_tooltip": "归类到「{0}」",
        "no_description": "（无简介）",
        "edit_title": "编辑 Skill（仅工具内生效）",
        "field_name": "名字",
        "field_desc": "简介",
        "field_uncat": "（未分类）",
        "field_category": "分类",
        "field_note": "备注",
        "edit_hint": "以上仅保存在本工具档案中，不会修改原 SKILL.md 的名字或内容。",
        "btn_cancel": "取消",
        "btn_save": "保存",
        "toolbar": "主工具栏",
        "search": "搜索",
        "search_ph": "按名字/简介/文件夹过滤…",
        "search_raw": "含原始说明",
        "search_raw_tip": "勾选后，搜索也会匹配每个 skill 的原始英文说明/关键词",
        "theme": "主题",
        "theme_auto": "随系统",
        "theme_light": "白天",
        "theme_dark": "黑夜",
        "btn_menu": "菜单",
        "menu_ai": "AI 整理",
        "menu_ai_gen": "① 生成 AI 分类任务",
        "menu_ai_imp": "② 导入 AI 分类结果",
        "menu_set_dir": "设置 skill 目录…",
        "menu_refresh": "刷新",
        "menu_cli": "用命令行打开",
        "menu_lang": "语言 / Language",
        "menu_lang_zh": "中文",
        "menu_lang_en": "English",
        "empty_hint": "这里还没有 skill。\n试试在左侧选其它分类，或用右上角滑块切换启停。",
        "dlg_find_dir": "寻找 skill 目录",
        "dlg_find_dir_body": "找不到 skill 目录：\n{0}\n\n是否选择你自己的 skill 目录？\n（选「否」则自动创建上面的默认目录）",
        "dlg_bad_dir": "无法创建目录",
        "dlg_bad_dir_body": "无法创建目录：\n{0}",
        "dlg_choose_dir": "选择 DSH skill 根目录（含各 skill 子文件夹）",
        "ctx_new_pin": "新建收藏分类",
        "ctx_new_pin_sub": "新建收藏子分类",
        "ctx_ren_pin": "重命名收藏分类",
        "ctx_del_pin": "删除收藏分类",
        "ctx_new": "新建分类",
        "ctx_new_sub": "新建子分类",
        "ctx_ren": "重命名分类",
        "ctx_del": "删除分类",
        "pin_tip": "点击收藏 / 取消收藏",
        "new_cat_title": "新建分类",
        "new_cat_label": "分类名：",
        "new_cat_sub_label": "在「{0}」下新建子分类：",
        "err_create": "无法创建",
        "ren_cat_title": "重命名分类",
        "ren_cat_label": "新的分类名：",
        "del_cat_title": "删除分类",
        "del_cat_body": "确定删除分类「{0}」吗？\n其下 skill 的归类将被清空（文件不受影响）。",
        "new_pin_title": "新建收藏分类",
        "new_pin_label": "收藏分类名：",
        "new_pin_sub_label": "在「{0}」下新建收藏子分类：",
        "ren_pin_title": "重命名收藏分类",
        "ren_pin_label": "新的收藏分类名：",
        "del_pin_title": "删除收藏分类",
        "del_pin_body": "确定删除收藏分类「{0}」吗？\n其下 skill 会留在收藏夹（取消该收藏分类），文件不受影响。",
        "gen_failed": "生成失败",
        "gen_failed_body": "生成任务文件失败：\n{0}",
        "task_ready": "任务文件已生成",
        "task_ready_body": "已生成：\n{0}\n\n步骤：\n1. 把这份文件交给 AI，AI 会填好分类/简介。\n2. AI 把填好的文件原样还给你。\n3. 点「② 导入 AI 分类结果」选它即可同步。\n\n现在就打开文件吗？",
        "ddl_ai_json": "选择 AI 生成的分类 JSON",
        "import_done": "导入完成",
        "import_done_body": "已导入 {0} 条档案。",
        "import_skipped": "\n跳过 {0} 条。",
        "cli_usage": "命令行用法",
        "cli_usage_body": "使用 .venv 下的 python 运行：\n\n  .venv\\Scripts\\python.exe skill_manager.py list\n  .venv\\Scripts\\python.exe skill_manager.py menu\n\n或在 powershell 里直接使用 skill_manager.py 的 on/off/cat/note/star 等命令。",
        "lang_welcome": "选择界面语言 / Choose language",
        "lang_zh": "中文",
        "lang_en": "English",
        "lang_saved": "语言已切换为 {0}",
    },
    "en": {
        "app_name": "DSH Skill Manager",
        "window_title": "DSH Skill Manager",
        "tree_all": "All",
        "tree_installed": "Installed",
        "tree_disabled": "Disabled",
        "tree_pinned": "Favorites",
        "pin_tooltip": "Favorite category \"{0}\"",
        "drop_tooltip": "Move to \"{0}\"",
        "no_description": "(no description)",
        "edit_title": "Edit Skill (tool-internal only)",
        "field_name": "Name",
        "field_desc": "Description",
        "field_uncat": "(uncategorized)",
        "field_category": "Category",
        "field_note": "Note",
        "edit_hint": "The above is stored only in the tool's own archive; it does not modify the name/content of the original SKILL.md.",
        "btn_cancel": "Cancel",
        "btn_save": "Save",
        "toolbar": "Main Toolbar",
        "search": "Search",
        "search_ph": "Filter by name/description/folder…",
        "search_raw": "Include raw text",
        "search_raw_tip": "When checked, search also matches each skill's raw English description/keywords",
        "theme": "Theme",
        "theme_auto": "System",
        "theme_light": "Light",
        "theme_dark": "Dark",
        "btn_menu": "Menu",
        "menu_ai": "AI organize",
        "menu_ai_gen": "① Generate AI classification task",
        "menu_ai_imp": "② Import AI result",
        "menu_set_dir": "Set skills directory…",
        "menu_refresh": "Refresh",
        "menu_cli": "Open with CLI",
        "menu_lang": "Language / 语言",
        "menu_lang_zh": "中文",
        "menu_lang_en": "English",
        "empty_hint": "No skills here yet.\nTry another category on the left, or toggle the switch on a card.",
        "dlg_find_dir": "Locate skills directory",
        "dlg_find_dir_body": "Skills directory not found:\n{0}\n\nChoose your own skills directory? (Selecting No creates the default above)",
        "dlg_bad_dir": "Cannot create directory",
        "dlg_bad_dir_body": "Cannot create directory:\n{0}",
        "dlg_choose_dir": "Choose the DSH skills root (contains the skill sub-folders)",
        "ctx_new_pin": "New favorite category",
        "ctx_new_pin_sub": "New favorite sub-category",
        "ctx_ren_pin": "Rename favorite category",
        "ctx_del_pin": "Delete favorite category",
        "ctx_new": "New category",
        "ctx_new_sub": "New sub-category",
        "ctx_ren": "Rename category",
        "ctx_del": "Delete category",
        "pin_tip": "Click to favorite / unfavorite",
        "new_cat_title": "New Category",
        "new_cat_label": "Category name:",
        "new_cat_sub_label": "New sub-category under \"{0}\":",
        "err_create": "Cannot create",
        "ren_cat_title": "Rename Category",
        "ren_cat_label": "New category name:",
        "del_cat_title": "Delete Category",
        "del_cat_body": "Delete category \"{0}\"?\nIts skills will be uncategorized (files are not affected).",
        "new_pin_title": "New Favorite Category",
        "new_pin_label": "Favorite category name:",
        "new_pin_sub_label": "New favorite sub-category under \"{0}\":",
        "ren_pin_title": "Rename Favorite Category",
        "ren_pin_label": "New favorite category name:",
        "del_pin_title": "Delete Favorite Category",
        "del_pin_body": "Delete favorite category \"{0}\"?\nIts skills stay in Favorites (this removes the favorite category); files are not affected.",
        "gen_failed": "Generation failed",
        "gen_failed_body": "Failed to generate task file:\n{0}",
        "task_ready": "Task file generated",
        "task_ready_body": "Generated:\n{0}\n\nSteps:\n1. Give this file to an AI; it fills in category/description.\n2. The AI returns the filled file to you.\n3. Click “② Import AI result” and select it to sync.\n\nOpen the file now?",
        "ddl_ai_json": "Select the AI-generated classification JSON",
        "import_done": "Import complete",
        "import_done_body": "Imported {0} entries.",
        "import_skipped": "\nSkipped {0} entries.",
        "cli_usage": "CLI usage",
        "cli_usage_body": "Run with the .venv python:\n\n  .venv\\Scripts\\python.exe skill_manager.py list\n  .venv\\Scripts\\python.exe skill_manager.py menu\n\nOr use on/off/cat/note/star etc. directly in powershell.",
        "lang_welcome": "Select interface language / 选择界面语言",
        "lang_zh": "中文",
        "lang_en": "English",
        "lang_saved": "Language switched to {0}",
    },
}


def is_en() -> bool:
    return core.get_language() == "en"


def gt(key: str, *args) -> str:
    """取当前语言下 GUI 文案，支持 {0}{1}…format。"""
    table = _GUI.get(core.get_language(), _GUI["zh"]) if is_en() else _GUI["zh"]
    s = table.get(key) or _GUI["zh"].get(key) or key
    if args:
        try:
            return s.format(*args)
        except (IndexError, KeyError):
            return s
    return s


# ---------------------------------------------------------------------------
# 主题（白天 / 黑夜 / 随系统）
# ---------------------------------------------------------------------------

class Theme:
    def __init__(self):
        self.palette = {
            "bg": "#1f2128",          # 窗口底
            "panel": "#262932",       # 面板/侧栏
            "card": "#2c303b",        # 卡片
            "border": "#3a3f4d",      # 分隔/描边
            "text": "#e8e9ed",        # 主文本
            "muted": "#9aa1ad",       # 次要文本
            "accent": "#3b82f6",      # 强调
            "on_accent": "#ffffff",
            "ok": "#22c55e",          # 启用/开
            "off": "#6b7280",         # 关闭/灰
            "danger": "#ef4444",
            "hover": "#343947",
            "selected": "#3a4161",
            "input_bg": "#1a1c22",
        }
        self.dark = True

    def set(self, key, value):
        self.palette[key] = value

    def apply_light(self):
        self.palette.update({
            "bg": "#f4f5f7", "panel": "#ffffff", "card": "#ffffff",
            "border": "#d8dbe0", "text": "#1f2329", "muted": "#6b7280",
            "accent": "#2f64d6", "on_accent": "#ffffff",
            "ok": "#16a34a", "off": "#9ca3af", "danger": "#dc2626",
            "hover": "#eef1f5", "selected": "#dce6ff", "input_bg": "#ffffff",
        })
        self.dark = False

    def apply_dark(self):
        self.palette.update({
            "bg": "#1f2128", "panel": "#262932", "card": "#2c303b",
            "border": "#3a3f4d", "text": "#e8e9ed", "muted": "#9aa1ad",
            "accent": "#3b82f6", "on_accent": "#ffffff",
            "ok": "#22c55e", "off": "#6b7280", "danger": "#ef4444",
            "hover": "#343947", "selected": "#3a4161", "input_bg": "#1a1c22",
        })
        self.dark = True

    def qss(self):
        p = self.palette
        return f"""
        QWidget {{ background: {p['bg']}; color: {p['text']}; font-size: 12px; }}
        QMainWindow, QDialog {{ background: {p['bg']}; }}
        QTreeWidget, QListWidget, QScrollArea {{ background: {p['panel']}; border: 1px solid {p['border']}; border-radius: 6px; }}
        QTreeWidget::item {{ height: 30px; padding-left: 4px; }}
        QTreeWidget::item:hover {{ background: {p['hover']}; }}
        QTreeWidget::item:selected {{ background: {p['selected']}; }}
        QPushButton {{
            background: {p['panel']}; border: 1px solid {p['border']};
            border-radius: 6px; padding: 5px 12px; color: {p['text']};
        }}
        QPushButton:hover {{ background: {p['hover']}; }}
        QPushButton.accent {{ background: {p['accent']}; color: {p['on_accent']}; border: none; }}
        QPushButton.accent:hover {{ background: {p['accent']}; }}
        QPushButton.plain {{ background: transparent; border: none; color: {p['accent']}; }}
        QComboBox {{ background: {p['panel']}; border: 1px solid {p['border']}; border-radius: 6px; padding: 4px 8px; }}
        QComboBox QAbstractItemView {{ background: {p['panel']}; selection-background-color: {p['selected']}; }}
        QLineEdit, QTextEdit {{
            background: {p['input_bg']}; border: 1px solid {p['border']};
            border-radius: 6px; padding: 5px 8px; color: {p['text']};
        }}
        QLineEdit:focus, QTextEdit:focus {{ border: 1px solid {p['accent']}; }}
        QMenu {{ background: {p['panel']}; border: 1px solid {p['border']}; }}
        QMenu::item {{ padding: 6px 22px; }}
        QMenu::item:selected {{ background: {p['selected']}; }}
        QLabel.muted {{ color: {p['muted']}; font-size: 11px; }}
        QLabel.title {{ font-size: 15px; font-weight: 600; }}
        QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0; }}
        QScrollBar::handle:vertical {{ background: {p['border']}; border-radius: 5px; min-height: 24px; }}
        QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
        QToolBar {{ background: {p['panel']}; border-bottom: 1px solid {p['border']}; spacing: 8px; padding: 4px 8px; }}
        """

    @staticmethod
    def system_is_dark() -> bool:
        """读取 Windows 深浅色设置（AppsUseLightTheme=0 → 深色）。"""
        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            ) as k:
                v, _ = winreg.QueryValueEx(k, "AppsUseLightTheme")
                return int(v) == 0
        except Exception:
            return False


# ---------------------------------------------------------------------------
# 分类树
# ---------------------------------------------------------------------------

class CategoryTree(QTreeWidget):
    """左侧分类树：顶部 全部/已装/未装/收藏，其下为自定义分类文件夹（可建子分类）。"""

    CAT_ALL = "__all__"
    CAT_INSTALLED = "__installed__"
    CAT_DISABLED = "__disabled__"
    CAT_PINNED = "__pinned__"
    PIN_PREFIX = "pin:"

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.setHeaderHidden(True)
        self.setDragEnabled(False)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)
        self.currentItemChanged.connect(self._on_selected)
        self.setMinimumWidth(200)

    # ---- 数据 ----
    def rebuild(self, selected_path=None):
        """重建整棵分类树。返回当前选中路径的类别标签（或 None）。"""
        self.blockSignals(True)
        self.clear()
        root = self.invisibleRootItem()

        def make(text, kind, count="", tooltip=""):
            it = QTreeWidgetItem([f"{text}" if not count else f"{text}"])
            it.setData(0, Qt.UserRole, kind)
            flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
            it.setFlags(flags)
            it.setToolTip(0, tooltip)
            return it

        # 统计
        n_all = len(self.app.all_skills)
        n_inst = sum(1 for s, _e in self.app.all_skills if not s["disabled"])
        n_dis = n_all - n_inst

        n_pin = sum(1 for _s, e in self.app.all_skills if e.get("starred"))
        for _text, tag, n in ((gt("tree_all"), self.CAT_ALL, n_all),
                              (gt("tree_installed"), self.CAT_INSTALLED, n_inst),
                              (gt("tree_disabled"), self.CAT_DISABLED, n_dis)):
            it = QTreeWidgetItem([f"{_text}  ({n})"])
            it.setData(0, Qt.UserRole, tag)
            it.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDropEnabled)
            root.addChild(it)

        # 「收藏」顶层节点（独立分类体系，与原分类并存）
        pin_root = QTreeWidgetItem([f"{gt('tree_pinned')}  ({n_pin})"])
        pin_root.setData(0, Qt.UserRole, self.CAT_PINNED)
        pin_root.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDropEnabled)
        pin_root.setExpanded(True)
        root.addChild(pin_root)

        # 收藏夹的子分类（独立于原分类）
        for folder in self.app.pin_categories():
            parts = [x for x in folder.split("/") if x.strip()]
            parent_pool = pin_root
            full = ""
            for part in parts:
                full = part if not full else f"{full}/{part}"
                node = None
                for j in range(parent_pool.childCount()):
                    ch = parent_pool.child(j)
                    if ch.text(0).split("  ")[0] == part:
                        node = ch
                        break
                if node is None:
                    node = QTreeWidgetItem([part])
                    node.setData(0, Qt.UserRole, self.PIN_PREFIX + full)
                    node.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable
                                  | Qt.ItemIsDropEnabled)
                    node.setToolTip(0, gt("pin_tooltip", full))
                    parent_pool.addChild(node)
                    node.setExpanded(True)
                parent_pool = node

        # 分类文件夹树（从 config 加载 + archive 里用到的归类并集）
        folders = self.app.category_folders()
        for folder in folders:
            parts = [x for x in folder.split("/") if x.strip()]
            if not parts:
                continue
            parent_item = None
            full = ""
            for i, part in enumerate(parts):
                full = part if not full else f"{full}/{part}"
                # 找已存在节点
                found = None
                pool = root if parent_item is None else parent_item
                for j in range(pool.childCount()):
                    ch = pool.child(j)
                    if ch.text(0).split("  ")[0] == part and ch.data(0, Qt.UserRole) not in (
                            self.CAT_ALL, self.CAT_INSTALLED, self.CAT_DISABLED):
                        found = ch
                        break
                if found is None:
                    it = QTreeWidgetItem([part])
                    it.setData(0, Qt.UserRole, full)
                    it.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable
                                | Qt.ItemIsDropEnabled | Qt.ItemIsDragEnabled)
                    it.setToolTip(0, gt("drop_tooltip", full))
                    pool.addChild(it)
                    if i == 0:
                        it.setExpanded(True)
                    parent_item = it
                else:
                    parent_item = found
        self.blockSignals(False)

        # 恢复选中
        if selected_path is not None:
            self._select_saved(selected_path)
        elif self.topLevelItemCount() > 0:
            self.setCurrentItem(self.topLevelItem(0))
        # 无选中时强制刷新一次
        self.refresh_view()

    def _select_saved(self, path):
        if path == self.CAT_ALL:
            self.setCurrentItem(self.topLevelItem(0))
            return
        if path == self.CAT_INSTALLED:
            self.setCurrentItem(self.topLevelItem(1))
            return
        if path == self.CAT_DISABLED:
            self.setCurrentItem(self.topLevelItem(2))
            return
        if path == self.CAT_PINNED:
            self.setCurrentItem(self.topLevelItem(3))
            return
        # 收藏分类路径（pin:xxx）→ 定位收藏根下的节点
        if path and path.startswith(self.PIN_PREFIX):
            full = path[len(self.PIN_PREFIX):]
            pin_root = self.topLevelItem(3)
            if pin_root:
                parts = [x for x in full.split("/") if x.strip()]
                node = pin_root
                for part in parts:
                    target = None
                    for j in range(node.childCount()):
                        if node.child(j).text(0).split("  ")[0] == part:
                            target = node.child(j)
                            break
                    if target is None:
                        break
                    node = target
                else:
                    self.setCurrentItem(node)
                    return
            self.setCurrentItem(self.topLevelItem(0))
            return
        # 分类路径 → 定位节点
        for i in range(self.topLevelItemCount()):
            top = self.topLevelItem(i)
            if top.data(0, Qt.UserRole) == path:
                self.setCurrentItem(top)
                return
        self.setCurrentItem(self.topLevelItem(0))

    @staticmethod
    def clean_label(text: str) -> str:
        return text  # labels already clean in this impl

    def current_target(self):
        """当前选中节点对应的类别标签（返回 CAT_* 或分类路径）。"""
        it = self.currentItem()
        if it is None:
            return self.CAT_ALL
        return it.data(0, Qt.UserRole) or self.CAT_ALL

    def refresh_view(self):
        self._on_selected(self.currentItem())

    def _on_selected(self, current, _prev=None):
        if current is None:
            current = self.topLevelItem(0)
        tag = current.data(0, Qt.UserRole)
        self.app.set_filter(tag)

    # ---- 右键菜单 ----
    def _context_menu(self, pos):
        it = self.itemAt(pos)
        tag = it.data(0, Qt.UserRole) if it else None
        menu = QMenu(self)
        is_magic = tag in (self.CAT_ALL, self.CAT_INSTALLED, self.CAT_DISABLED, self.CAT_PINNED)
        if tag == self.CAT_PINNED:
            add = menu.addAction(gt("ctx_new_pin"))
            add.triggered.connect(lambda: self.app.new_pin_category("", it))
            menu.exec(self.viewport().mapToGlobal(pos))
            return
        is_pin = bool(tag and tag.startswith(self.PIN_PREFIX))
        if is_pin:
            full = tag[len(self.PIN_PREFIX):]
            sub = menu.addAction(gt("ctx_new_pin_sub"))
            sub.triggered.connect(lambda: self.app.new_pin_category(full, it))
            menu.addSeparator()
            ren = menu.addAction(gt("ctx_ren_pin"))
            ren.triggered.connect(lambda: self.app.rename_pin_category(full))
            dele = menu.addAction(gt("ctx_del_pin"))
            dele.triggered.connect(lambda: self.app.delete_pin_category(full))
            menu.exec(self.viewport().mapToGlobal(pos))
            return
        add = menu.addAction(gt("ctx_new"))
        add.triggered.connect(lambda: self.app.new_category(self._parent_of(tag)))
        if it is not None and not is_magic:
            sub = menu.addAction(gt("ctx_new_sub"))
            sub.triggered.connect(lambda: self.app.new_category(tag))
            menu.addSeparator()
            ren = menu.addAction(gt("ctx_ren"))
            ren.triggered.connect(lambda: self.app.rename_category(tag))
            dele = menu.addAction(gt("ctx_del"))
            dele.triggered.connect(lambda: self.app.delete_category(tag))
        menu.exec(self.viewport().mapToGlobal(pos))

    def _parent_of(self, tag):
        if tag in (self.CAT_ALL, self.CAT_INSTALLED, self.CAT_DISABLED) or not tag:
            return ""
        return "/".join([x for x in tag.split("/")[:-1]])

    # ---- 拖放（接收卡片 → 归类） ----
    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat("application/x-skill-folder"):
            e.acceptProposedAction()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        e.acceptProposedAction()

    def dropEvent(self, e):
        folder = e.mimeData().data("application/x-skill-folder").data().decode("utf-8")
        if e.source() is self:
            e.ignore()
            return
        it = self.itemAt(e.position().toPoint())
        tag = it.data(0, Qt.UserRole) if it else None
        # 拖到 已装/未装 → 切换开关状态
        if tag == self.CAT_DISABLED:
            self.app.move_skill(folder, "off")
            e.acceptProposedAction()
            return
        if tag == self.CAT_INSTALLED:
            self.app.move_skill(folder, "on")
            e.acceptProposedAction()
            return
        if tag == self.CAT_ALL:
            e.acceptProposedAction()
            return
        # 拖到 收藏 → 收藏（保留其原收藏分类；若给分类节点则设收藏分类）
        if tag == self.CAT_PINNED:
            self.app.pin_skill(folder, "")
            e.acceptProposedAction()
            return
        if tag and tag.startswith(self.PIN_PREFIX):
            self.app.pin_skill(folder, tag[len(self.PIN_PREFIX):])
            e.acceptProposedAction()
            return
        # 拖到分类 → 归类（仅工具内，不动文件）
        if tag:
            self.app.assign_category(folder, tag)
            e.acceptProposedAction()
            return
        e.ignore()


# ---------------------------------------------------------------------------
# Skill 卡片
# ---------------------------------------------------------------------------

class ToggleSwitch(QWidget):
    """滑块式开关：右滑=开=绿（轨道绿），左滑=关=红（轨道红）。点击切换，发 clicked 信号。"""
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self.setFixedSize(48, 26)
        self.setCursor(Qt.PointingHandCursor)

    def set_checked(self, on: bool):
        self._checked = bool(on)
        self.update()

    def is_checked(self) -> bool:
        return self._checked

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.set_checked(not self._checked)
            self.clicked.emit()
            e.accept()  # 阻止事件冒泡到父级卡片（避免误开编辑框）
            return
        super().mouseReleaseEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            e.accept()  # 阻止按下事件冒泡到卡片
            return
        super().mousePressEvent(e)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        on = self._checked
        # 轨道颜色：开=绿，关=红
        track = QColor("#22c55e") if on else QColor("#ef4444")
        p.setPen(Qt.NoPen)
        rect = QRectF(1, 1, self.width() - 2, self.height() - 2)
        p.setBrush(QBrush(track))
        p.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)
        # 圆柄：右=开 / 左=关
        d = self.height() - 8
        y = (self.height() - d) / 2
        x = self.width() - d - 4 if on else 4
        p.setBrush(QBrush(QColor("#ffffff")))
        p.drawEllipse(QRectF(x, y, d, d))
        p.end()


class PinButton(QWidget):
    """自绘图钉按钮（不依赖彩色 emoji，颜色可控）：已收藏=琥珀色，未收藏=灰色。"""
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pinned = False
        self.setFixedSize(34, 28)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(gt("pin_tip"))

    def set_pinned(self, pinned: bool):
        if self._pinned != bool(pinned):
            self._pinned = bool(pinned)
            self.update()

    def is_pinned(self) -> bool:
        return self._pinned

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            e.accept()
            self.clicked.emit()
            return
        super().mouseReleaseEvent(e)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        color = QColor("#f59e0b") if self._pinned else QColor("#7c8189")
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(color))
        cx = w / 2.0
        # 圆头
        head_r = 7.5
        p.drawEllipse(QRectF(cx - head_r, 5, head_r * 2, head_r * 2))
        # 细腰 / 柄（让头到尾尖之间有收窄）
        p.drawRect(QRectF(cx - 2.2, 5 + head_r - 1, 4.4, 22 - (5 + head_r)))
        # 尖端（三角朝下）
        tip = QPolygonF([QPointF(cx - 4.0, 20), QPointF(cx + 4.0, 20), QPointF(cx, 24.0)])
        p.drawPolygon(tip)
        # 银色小帽高光（钉头闪光点）
        p.setBrush(QBrush(QColor(255, 255, 255, 120)))
        p.drawEllipse(QRectF(cx - head_r + 2.5, 6.5, 3.2, 3.2))
        p.end()


class SkillCard(QFrame):
    """单个 skill 卡片：名字 + 简介 + 文件夹；右上角滑块开关；点击打开编辑；支持拖拽。"""

    def __init__(self, app, skill, entry):
        super().__init__()
        self.app = app
        self.skill = skill
        self.entry = entry
        self.folder = skill["folder"]

        self.setObjectName("card")
        self.setProperty("card", True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(108)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(4)

        # 第一行：名字（左） + 钉（收藏） + 开关（右）
        top = QHBoxLayout()
        self.name_lbl = QLabel(app.display_name(skill, entry))
        self.name_lbl.setProperty("class", "title")
        self.name_lbl.setStyleSheet(f"font-size:14px; font-weight:600; color:{app.theme.palette['text']};")
        self.pin_btn = PinButton()
        self.pin_btn.set_pinned(bool(entry.get("starred")))
        self.pin_btn.clicked.connect(self._toggle_pin)
        self.switch = ToggleSwitch()
        self.switch.set_checked(not skill["disabled"])
        self.switch.clicked.connect(self._toggle_state)
        top.addWidget(self.name_lbl, 1)
        top.addWidget(self.pin_btn, 0, Qt.AlignRight)
        top.addWidget(self.switch, 0, Qt.AlignRight)
        lay.addLayout(top)

        # 第二行：简介（突出，字体加大）
        desc = core.skill_description(skill, entry)
        self.desc_lbl = QLabel(desc if desc else gt("no_description"))
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setProperty("class", "muted")
        self.desc_lbl.setStyleSheet(f"color:{self.app.theme.palette['muted']}; font-size:14px;")
        lay.addWidget(self.desc_lbl, 1)

        # 第三行：文件夹
        folder_lbl = QLabel(skill["folder"])
        folder_lbl.setProperty("class", "muted")
        folder_lbl.setStyleSheet(f"color:{self.app.theme.palette['muted']}; font-size:10px;")
        lay.addWidget(folder_lbl, 0, Qt.AlignRight)

        self.setStateEnabled()

    def setStateEnabled(self):
        self.switch.set_checked(not self.skill["disabled"])

    def _update_pin(self):
        self.pin_btn.set_pinned(bool(self.entry.get("starred")))

    def _toggle_pin(self):
        core.toggle_star(self.app.root_path, self.folder)
        # 同步本地条目标记 + 即时变色（否则要等整表重建才看到变化）
        self.entry["starred"] = not self.entry.get("starred", False)
        self._update_pin()
        # 刷新「收藏」节点计数与归档视图（不改变当前选中）
        self.app.refresh_all(keep=self.app.tree.current_target())

    def _toggle_state(self):
        on = not self.skill["disabled"]
        self.app.move_skill(self.folder, "off" if on else "on")

    # ---- 点击 → 行为（依据当前导航） ----
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.app.on_card_clicked(self)
        super().mouseReleaseEvent(e)

    # ---- 拖拽 ----
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_start = e.position().toPoint()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if not self._drag_start:
            super().mouseMoveEvent(e)
            return
        if (e.position().toPoint() - self._drag_start).manhattanLength() < 8:
            super().mouseMoveEvent(e)
            return
        drag = self._make_drag()
        drag.exec(Qt.MoveAction)
        self._drag_start = None

    def _make_drag(self):
        from PySide6.QtGui import QDrag
        drag = QDrag(self)
        mime = QMimeData()
        mime.setData("application/x-skill-folder", self.folder.encode("utf-8"))
        drag.setMimeData(mime)
        drag.setHotSpot(self.rect().topLeft())
        return drag


# ---------------------------------------------------------------------------
# 编辑对话框
# ---------------------------------------------------------------------------

class EditDialog(QDialog):
    def __init__(self, app, skill, entry, parent=None):
        super().__init__(parent)
        self.app = app
        self.skill = skill
        self.entry = entry
        self.setWindowTitle(gt("edit_title"))
        self.setMinimumWidth(460)
        self.setModal(True)

        form = QFormLayout(self)
        form.setSpacing(10)
        form.setContentsMargins(16, 16, 16, 16)

        self.name_edit = QLineEdit(app.display_name(skill, entry))
        form.addRow(gt("field_name"), self.name_edit)

        self.desc_edit = QTextEdit()
        self.desc_edit.setPlainText(core.skill_description(skill, entry))
        self.desc_edit.setFixedHeight(90)
        form.addRow(gt("field_desc"), self.desc_edit)

        self.cat_combo = QComboBox()
        self.cat_combo.setEditable(True)
        self.cat_combo.addItem(gt("field_uncat"), "")
        for c in app.category_folders():
            self.cat_combo.addItem(c, c)
        cur = (entry.get("category") or "").strip()
        idx = self.cat_combo.findData(cur)
        self.cat_combo.setCurrentIndex(idx if idx >= 0 else 0)
        form.addRow(gt("field_category"), self.cat_combo)

        self.note_edit = QLineEdit(entry.get("note") or "")
        form.addRow(gt("field_note"), self.note_edit)

        hint = QLabel(gt("edit_hint"))
        hint.setStyleSheet(f"color:{app.theme.palette['muted']}; font-size:11px;")
        hint.setWordWrap(True)
        form.addRow(hint)

        btns = QHBoxLayout()
        cancel = QPushButton(gt("btn_cancel"))
        cancel.clicked.connect(self.reject)
        save = QPushButton(gt("btn_save"))
        save.setProperty("class", "accent")
        save.clicked.connect(self._save)
        btns.addStretch(1)
        btns.addWidget(cancel)
        btns.addWidget(save)
        form.addRow(btns)

    def _save(self):
        sid = core._skill_id(self.skill)
        archive = core.load_archive()
        entry = core.ensure_archive_entry(archive, self.skill)
        entry["display_name"] = self.name_edit.text().strip()
        entry["ai_description"] = self.desc_edit.toPlainText().strip()
        # 分类：取组合框可见文本（兼容选中项或手动键入的新分类）
        cat = self.cat_combo.currentText().strip().strip("/")
        entry["category"] = cat if cat else ""
        entry["note"] = self.note_edit.text().strip()
        core.save_archive(archive)
        self.app.refresh_all()
        self.accept()


# ---------------------------------------------------------------------------
# 主窗口
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(gt("window_title"))
        self.resize(1180, 760)
        self.setMinimumSize(860, 520)

        self.theme = Theme()
        self.root_path = self._resolve_skills_root()
        self.mode = "auto"  # auto / light / dark
        self.selected_target = CategoryTree.CAT_ALL
        self._search_text = ""
        self._search_raw = False

        # 数据
        self.all_skills = []
        self._load_skills()
        self._apply_theme()

        # 顶部工具栏
        self._build_toolbar()

        # 主体
        splitter = QSplitter(Qt.Horizontal)
        self.tree = CategoryTree(self)
        splitter.addWidget(self.tree)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.card_container = QWidget()
        self.card_lay = QVBoxLayout(self.card_container)
        self.card_lay.setContentsMargins(12, 12, 12, 12)
        self.card_lay.setSpacing(8)
        self.card_lay.addStretch(1)
        self.scroll.setWidget(self.card_container)
        splitter.addWidget(self.scroll)
        splitter.setSizes([230, 900])
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

        self.tree.rebuild(self.selected_target)

    # ---------- 数据 ----------
    def _resolve_skills_root(self):
        """确定 skill 根目录：env > config记忆 > 默认。不存在则询问/自动创建。"""
        root = core.get_skills_root()  # 已按 env→config→默认 逻辑
        if not root.exists():
            # 发送软件给他人：默认目录很可能不存在，引导选择或自动创建
            ret = QMessageBox.question(
                self, gt("dlg_find_dir"),
                gt("dlg_find_dir_body", root),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if ret == QMessageBox.Yes:
                chosen = self._choose_skills_root()
                if chosen:
                    self._memorize_root(chosen)
                    root = chosen
        try:
            core.ensure_disabled_dir(root)
        except OSError as e:  # noqa: BLE001
            QMessageBox.warning(self, gt("dlg_bad_dir"), gt("dlg_bad_dir_body", e))
        return root

    def _choose_skills_root(self):
        d = QFileDialog.getExistingDirectory(self, gt("dlg_choose_dir"))
        return Path(d) if d else None

    def _memorize_root(self, path: Path):
        """把用户选的根目录存进 config，下次启动优先用它。"""
        core.save_config({"skills_root": str(path)})

    def change_skills_root(self):
        """菜单：重新设置 skill 目录并加载。"""
        chosen = self._choose_skills_root()
        if not chosen:
            return
        self._memorize_root(chosen)
        self.root_path = chosen
        try:
            core.ensure_disabled_dir(chosen)
        except OSError as e:  # noqa: BLE001
            QMessageBox.warning(self, gt("dlg_bad_dir"), gt("dlg_bad_dir_body", e))
        self.setWindowTitle(f"{gt('window_title')} · {chosen}")
        self.refresh_all(keep=CategoryTree.CAT_ALL)

    def _load_skills(self):
        installed, disabled = core.scan_skills(self.root_path)
        archive = core.load_archive()
        for s in installed + disabled:
            core.ensure_archive_entry(archive, s)
        core.save_archive(archive)
        self.archive = archive
        self.all_skills = [(s, core.ensure_archive_entry(archive, s))
                           for s in installed + disabled]

    def category_folders(self):
        """合并 config 分类树 + 已用归类，返回顶层【原分类】文件夹路径集合（忽略 pin: 开头项）。"""
        from_t = set()
        for c in core.load_category_tree():
            if not c.startswith("pin:"):
                from_t.add(c)
        from_a = set()
        for _s, e in self.all_skills:
            c = (e.get("category") or "").strip().strip("/")
            if c:
                from_a.add(c)
        return sorted(from_t | from_a)

    def pin_categories(self):
        """「收藏夹」内用到的独立分类路径（与原分类并存）。"""
        s = set()
        for _s, e in self.all_skills:
            if e.get("starred"):
                pc = (e.get("pin_category") or "").strip().strip("/")
                if pc:
                    s.add(pc)
        return sorted(s)

    def refresh_all(self, keep=None):
        self._load_skills()
        self.tree.rebuild(keep or self.tree.current_target())
        self.render_cards()

    def display_name(self, skill, entry):
        return core.display_name(skill, entry)

    # ---------- 工具栏 ----------
    def _build_toolbar(self):
        tb = QToolBar(gt("toolbar"), self)
        tb.setMovable(False)
        self.addToolBar(tb)

        title = QLabel(gt("app_name"))
        title.setStyleSheet(f"font-size:15px; font-weight:700; color:{self.theme.palette['text']};")
        tb.addWidget(title)
        tb.addSeparator()

        # 顶部搜索框（实时过滤卡片）
        tb.addWidget(QLabel(gt("search")))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(gt("search_ph"))
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setFixedWidth(220)
        self.search_edit.textChanged.connect(self._on_search)
        tb.addWidget(self.search_edit)
        # 是否连原始英文描述/关键词一起搜（默认严格，只搜名字/简介/文件夹）
        self.search_raw_cb = QCheckBox(gt("search_raw"))
        self.search_raw_cb.setToolTip(gt("search_raw_tip"))
        self.search_raw_cb.toggled.connect(self._on_search_mode)
        tb.addWidget(self.search_raw_cb)

        tb.addSeparator()

        tb.addWidget(QLabel(gt("theme")))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([gt("theme_auto"), gt("theme_light"), gt("theme_dark")])
        self.theme_combo.setFixedWidth(96)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_change)
        tb.addWidget(self.theme_combo)

        tb.addSeparator()

        # 「菜单」 —— 低频操作收二级
        menu_btn = QPushButton(gt("btn_menu"))
        menu_btn.setProperty("class", "plain")
        mb = QMenu(self)
        ai_act = QAction(gt("menu_ai"), self)
        ai_act.triggered.connect(self._ai_menu)
        mb.addAction(ai_act)
        dir_act = QAction(gt("menu_set_dir"), self)
        dir_act.triggered.connect(self.change_skills_root)
        mb.addAction(dir_act)
        rep = QAction(gt("menu_refresh"), self)
        rep.triggered.connect(self.refresh_all)
        mb.addAction(rep)
        cli = QAction(gt("menu_cli"), self)
        cli.triggered.connect(self._open_cli)
        mb.addAction(cli)
        # 语言切换
        lang_menu = mb.addMenu(gt("menu_lang"))
        zh_act = lang_menu.addAction(gt("lang_zh"))
        zh_act.triggered.connect(lambda: self._switch_lang("zh"))
        en_act = lang_menu.addAction(gt("lang_en"))
        en_act.triggered.connect(lambda: self._switch_lang("en"))
        menu_btn.setMenu(mb)
        tb.addWidget(menu_btn)

    def _switch_lang(self, lang: str):
        """切换界面语言并重建窗口（重建以刷新所有文案）。"""
        core.set_language(lang)
        try:
            core.save_config({"lang": core.get_language()})
        except Exception:  # noqa: BLE001
            pass
        # 重建整个窗口以应用新语言
        fn = globals().get("_REBUILD_FN")
        if fn is not None:
            fn()
        else:
            self.refresh_all()

    def _on_theme_change(self, idx):
        self.mode = ["auto", "light", "dark"][idx]
        self._apply_theme()

    def _on_search(self, text):
        self._search_text = (text or "").strip().lower()
        self.render_cards()

    def _on_search_mode(self, checked):
        self._search_raw = bool(checked)
        self.render_cards()

    def _apply_theme(self):
        if self.mode == "light":
            self.theme.apply_light()
        elif self.mode == "dark":
            self.theme.apply_dark()
        elif Theme.system_is_dark():
            self.theme.apply_dark()
        else:
            self.theme.apply_light()
        self.setStyleSheet(self.theme.qss())

    # ---------- 过滤 / 渲染 ----------
    def set_filter(self, target):
        """target: CAT_ALL / CAT_INSTALLED / CAT_DISABLED 或分类路径。"""
        self.selected_target = target
        self.render_cards()

    def _match(self, skill, entry):
        t = self.selected_target
        if t == CategoryTree.CAT_ALL:
            pass
        elif t == CategoryTree.CAT_INSTALLED:
            if skill["disabled"]:
                return False
        elif t == CategoryTree.CAT_DISABLED:
            if not skill["disabled"]:
                return False
        elif t == CategoryTree.CAT_PINNED:
            if not entry.get("starred"):
                return False
        elif t.startswith(CategoryTree.PIN_PREFIX):
            full = t[len(CategoryTree.PIN_PREFIX):]
            if not entry.get("starred"):
                return False
            pc = (entry.get("pin_category") or "").strip().strip("/")
            if not (pc and (pc == full or pc.startswith(full + "/"))):
                return False
        else:
            # 分类路径（含子分类）
            c = (entry.get("category") or "").strip().strip("/")
            if not (c and (c == t or c.startswith(t + "/"))):
                return False
        # 搜索过滤
        if self._search_text:
            parts = [skill.get("name", ""), skill["folder"],
                     skill.get("description", ""),  # SKILL.md 原始英文描述/关键词
                     entry.get("ai_description") or "",
                     core.display_name(skill, entry),
                     (entry.get("note") or "")]
            if not self._search_raw:
                # 默认严格：不把原始描述算进去，只用卡片显示的名字/简介/文件夹
                parts.remove(skill.get("description", ""))
            hay = " ".join(parts).lower()
            if self._search_text not in hay:
                return False
        return True

    def render_cards(self):
        # 清空
        while self.card_lay.count():
            it = self.card_lay.takeAt(0)
            w = it.widget()
            if w is not None:
                w.deleteLater()
        shown = 0
        # ON（已启用）排在上面，OFF（已屏蔽）排在下面
        ordered = sorted(self.all_skills,
                         key=lambda se: (0 if not se[0]["disabled"] else 1))
        for skill, entry in ordered:
            if not self._match(skill, entry):
                continue
            card = SkillCard(self, skill, entry)
            self.card_lay.insertWidget(self.card_lay.count() - 1, card)
            shown += 1
        # 空状态
        if shown == 0:
            empty = QLabel(gt("empty_hint"))
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(f"color:{self.theme.palette['muted']}; font-size:13px; padding:40px;")
            empty.setWordWrap(True)
            self.card_lay.insertWidget(0, empty)

    # ---------- 行为 ----------
    def on_card_clicked(self, card):
        """点击卡片 = 打开编辑（启用/屏蔽只通过右上角滑块切换）。"""
        dlg = EditDialog(self, card.skill, card.entry, self)
        dlg.exec()

    def move_skill(self, folder, target):
        """on/off 切换 + 刷新。"""
        if core.toggle(self.root_path, folder, target):
            self.refresh_all(keep=self.tree.current_target())

    def assign_category(self, folder, category):
        core.set_category(self.root_path, folder, category)
        self.refresh_all(keep=self.tree.current_target())

    # ---------- 分类管理 ----------
    def new_category(self, parent):
        name, ok = QInputDialog.getText(self, gt("new_cat_title"),
                                        gt("new_cat_label") if not parent else gt("new_cat_sub_label", parent),
                                        text="")
        if not ok or not name.strip():
            return
        # 归一到干净路径
        name = name.strip().strip("/")
        full = f"{parent}/{name}" if parent else name
        try:
            core.add_category(self.root_path, parent, name)
        except ValueError as e:
            QMessageBox.warning(self, gt("err_create"), str(e))
            return
        self._load_skills()
        self.tree.rebuild(full)
        # 展开新分类所在路径
        self._expand_to(full)

    def rename_category(self, tag):
        base = tag.split("/")[-1]
        name, ok = QInputDialog.getText(self, gt("ren_cat_title"), gt("ren_cat_label"), text=base)
        if not ok or not name.strip():
            return
        new_full = "/".join([x for x in tag.split("/")[:-1] if x] + [name.strip().strip("/")])
        core.rename_category_folder(self.root_path, tag, new_full)
        self._load_skills()
        self.tree.rebuild(new_full)

    def delete_category(self, tag):
        ret = QMessageBox.question(
            self, gt("del_cat_title"), gt("del_cat_body", tag),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if ret != QMessageBox.Yes:
            return
        core.delete_category_folder(self.root_path, tag)
        self._load_skills()
        self.tree.rebuild(CategoryTree.CAT_ALL)

    # ---------- 收藏夹分类管理（独立于原分类） ----------
    def pin_skill(self, folder, pin_cat):
        """把 skill 收藏；pin_cat 为空=未分类收藏，否则设收藏分类（与原分类并存）。"""
        core.set_pin_category(self.root_path, folder, pin_cat or "")
        self.refresh_all(keep=self.tree.current_target())

    def new_pin_category(self, parent, item):
        name, ok = QInputDialog.getText(self, gt("new_pin_title"),
                                        gt("new_pin_label") if not parent else gt("new_pin_sub_label", parent), text="")
        if not ok or not name.strip():
            return
        name = name.strip().strip("/")
        full = f"{parent}/{name}" if parent else name
        self.refresh_all(keep=CategoryTree.PIN_PREFIX + full)

    def rename_pin_category(self, full):
        base = full.split("/")[-1]
        name, ok = QInputDialog.getText(self, gt("ren_pin_title"), gt("ren_pin_label"), text=base)
        if not ok or not name.strip():
            return
        new_full = "/".join([x for x in full.split("/")[:-1] if x] + [name.strip().strip("/")])
        archive = core.load_archive()
        for e in archive.values():
            pc = (e.get("pin_category") or "").strip().strip("/")
            if pc == full or pc.startswith(full + "/"):
                e["pin_category"] = new_full + (pc[len(full):] if pc != full else "")
                e["starred"] = True
        core.save_archive(archive)
        self.refresh_all(keep=CategoryTree.PIN_PREFIX + new_full)

    def delete_pin_category(self, full):
        ret = QMessageBox.question(
            self, gt("del_pin_title"), gt("del_pin_body", full),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if ret != QMessageBox.Yes:
            return
        archive = core.load_archive()
        for e in archive.values():
            pc = (e.get("pin_category") or "").strip().strip("/")
            if pc == full or pc.startswith(full + "/"):
                e["pin_category"] = ""
        core.save_archive(archive)
        self.refresh_all(keep=CategoryTree.CAT_PINNED)

    def _expand_to(self, full):
        it = self.tree.topLevelItem(0)
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            if top.data(0, Qt.UserRole) == full:
                self.tree.setCurrentItem(top)
                return
        # 展开父链
        parts = [x for x in full.split("/") if x]
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            top.setExpanded(True)
            if top.data(0, Qt.UserRole) == parts[0]:
                top.setCurrentItem(top)
                return

    # ---------- AI 整理（二级菜单） ----------
    def _ai_menu(self):
        m = QMenu(self)
        gen = m.addAction(gt("menu_ai_gen"))
        gen.triggered.connect(self._gen_ai_task)
        imp = m.addAction(gt("menu_ai_imp"))
        imp.triggered.connect(self._imp_ai_file)
        m.exec(self.mapToGlobal(self.rect().topLeft()))

    def _gen_ai_task(self):
        try:
            dest = core.export_ai_task(self.root_path)
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, gt("gen_failed"), gt("gen_failed_body", e))
            return
        what = QMessageBox.question(
            self, gt("task_ready"), gt("task_ready_body", dest),
            QMessageBox.Yes | QMessageBox.No)
        if what == QMessageBox.Yes:
            try:
                os.startfile(str(dest))  # type: ignore[attr-defined]
            except OSError:
                pass

    def _imp_ai_file(self):
        path, _f = QFileDialog.getOpenFileName(
            self, gt("ddl_ai_json"), str(core.get_data_dir()),
            "JSON 文件 (*.json);;所有文件 (*.*)")
        if not path:
            return
        res = core.import_ai_file(self.root_path, path)
        self.refresh_all()
        if res and res.get("matched"):
            body = gt("import_done_body", res["matched"])
            if res.get("skipped"):
                body += gt("import_skipped", len(res["skipped"]))
            QMessageBox.information(self, gt("import_done"), body)

    def _open_cli(self):
        QMessageBox.information(self, gt("cli_usage"), gt("cli_usage_body"))


def _pick_language_if_unset(app):
    """首次启动（config 里还没有 lang）弹窗让用户选中/英文，记住选择。"""
    cfg = core.load_config()
    if cfg.get("lang") in ("zh", "en"):
        core.set_language(cfg["lang"])
        return
    env = os.environ.get("DSH_SKILLS_LANG")
    if env and env.strip().lower() in ("zh", "en"):
        core.set_language(env.strip().lower())
        return
    # 默认中文；用对话框让用户选
    box = QMessageBox()
    box.setWindowTitle("DSH Skill 管理器")
    box.setText("选择界面语言 / Choose interface language")
    zh = box.addButton(gt("lang_zh"), QMessageBox.AcceptRole)
    en = box.addButton(gt("lang_en"), QMessageBox.AcceptRole)
    box.exec()
    chosen = box.clickedButton()
    lang = "en" if chosen is en else "zh"
    core.set_language(lang)
    try:
        core.save_config({"lang": lang})
    except Exception:  # noqa: BLE001
        pass


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName(gt("app_name"))

    # 首次启动选语言（之后从 config 记忆）
    _pick_language_if_unset(app)

    def _open_window():
        w = MainWindow()
        globals()["_WINDOW"] = w
        w.show()
        return w

    def _rebuild():
        old = globals().get("_WINDOW")
        if old is not None:
            old.close()
            old.deleteLater()
        _open_window()

    globals()["_REBUILD_FN"] = _rebuild
    _open_window()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()