@echo off
rem dsh-skill-manager GUI 启动器：双击即开图形界面（PySide6 装在 .venv 内）
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" skill_manager_gui.py
) else (
    start "" pythonw skill_manager_gui.py
)