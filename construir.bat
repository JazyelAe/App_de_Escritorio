@echo off
rem Empaqueta DeskData Pro en un solo .exe (requiere: pip install -r requirements.txt)
pyinstaller --noconfirm --onefile --windowed --name DeskDataPro --icon icons\app_icon.ico ^
  --add-data "datos\semilla.json;datos" --add-data "datos\ejemplo_importar.csv;datos" ^
  --add-data "icons\app_icon.png;icons" main.py
echo Listo: dist\DeskDataPro.exe
