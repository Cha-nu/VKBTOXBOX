@echo off
rem Build a single-file exe (needs: pip install pyinstaller). Output: dist\vkb2xbox.exe
cd /d "%~dp0"
python -m PyInstaller --noconfirm --onefile --windowed --name vkb2xbox ^
  --add-data "config.example.json;." --collect-all vgamepad vkb2xbox_gui.py
if errorlevel 1 pause
