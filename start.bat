@echo off
chcp 65001 >nul
title ExamTicket
cd /d "%~dp0"

rem Start ExamTicket with one double click. Needs Python on the computer.
rem First run: creates the venv folder, installs the libraries from
rem requirements.txt and fills the database with sample questions.
rem Next runs: just opens the program.

set "PY="
py -3 --version >nul 2>nul && set "PY=py -3"
if not defined PY (
    python --version >nul 2>nul && set "PY=python"
)
if not defined PY (
    echo Python не найден на этом компьютере.
    echo Установите его с сайта https://www.python.org/downloads/
    echo При установке поставьте галочку "Add python.exe to PATH".
    echo Потом запустите этот файл ещё раз.
    pause
    exit /b 1
)

if not exist "venv\Scripts\python.exe" (
    echo [1/3] Создаю папку venv для библиотек...
    %PY% -m venv venv
    if errorlevel 1 (
        echo Не удалось создать папку venv.
        pause
        exit /b 1
    )
)

fc /b requirements.txt "venv\requirements.installed" >nul 2>nul
if errorlevel 1 (
    echo [2/3] Устанавливаю библиотеки. Нужен интернет, это займёт несколько минут...
    "venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
    if errorlevel 1 (
        echo Не удалось установить библиотеки. Проверьте интернет и запустите файл ещё раз.
        pause
        exit /b 1
    )
    copy /y requirements.txt "venv\requirements.installed" >nul
)

if not exist "exam_tickets.db" (
    echo [3/3] Создаю базу с примерами вопросов...
    "venv\Scripts\python.exe" -m app.seed
)

echo Программа запущена. Это окно закроется, когда вы закроете программу.
"venv\Scripts\python.exe" -m app.main
if errorlevel 1 pause
