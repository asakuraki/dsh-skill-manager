@echo off
rem dsh-skill-manager GUI launcher: double-click to open the manager window (PySide6 lives in .venv)
rem Uses pythonw to avoid a console window.
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" skill_manager_gui.py
) else (
    start "" pythonw skill_manager_gui.py
)