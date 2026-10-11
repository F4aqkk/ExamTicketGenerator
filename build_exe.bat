@echo off
rem Build ExamTicket.exe with PyInstaller. Run from the project folder.
rem Result: dist\ExamTicket\ExamTicket.exe
venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --windowed ^
  --name ExamTicket --icon icon.ico --add-data "icon.ico;." ^
  --collect-all docx --collect-all openpyxl ^
  --collect-all reportlab --collect-all pypdf ^
  run.py
if errorlevel 1 exit /b 1
if exist exam_tickets.db copy /y exam_tickets.db dist\ExamTicket\ >nul
if exist settings.json copy /y settings.json dist\ExamTicket\ >nul
echo.
echo Done: dist\ExamTicket\ExamTicket.exe
