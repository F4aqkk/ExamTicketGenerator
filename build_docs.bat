@echo off
rem Build the documentation into docs\_build\html. Run from the project folder.
rem Needs: venv\Scripts\python.exe -m pip install -r docs\requirements.txt
venv\Scripts\python.exe -m sphinx -b html docs docs\_build\html
if errorlevel 1 exit /b 1
echo.
echo Done: docs\_build\html\index.html
