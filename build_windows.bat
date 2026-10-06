@echo off
REM Compila un .exe standalone (Windows) per il programma TED Calzature.
REM Esegui questo file su un PC Windows con Python 3.10+ installato
REM (scaricabile da https://www.python.org/downloads/ — spunta "Add to PATH").

setlocal
cd /d "%~dp0"

echo Creo un ambiente virtuale...
python -m venv venv_build
call venv_build\Scripts\activate.bat

echo Installo le dipendenze...
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo Compilo l'eseguibile...
pyinstaller --onefile --windowed --name TED_Calzature gui.py

echo.
echo Fatto. Trovi l'eseguibile in dist\TED_Calzature.exe
pause
