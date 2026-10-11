"""Тесты выбора папки для файлов с данными и для значка."""

import sys
from pathlib import Path

from app.paths import data_path, resource_path


def test_data_is_in_current_folder_when_run_from_code():
    """При запуске из исходного кода файл берётся из текущей папки."""
    assert data_path("exam_tickets.db") == Path("exam_tickets.db")


def test_data_is_next_to_exe_in_built_program(monkeypatch, tmp_path):
    """У программы, собранной в exe, данные лежат рядом с exe-файлом."""
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "ExamTicket.exe"))

    assert data_path("settings.json") == tmp_path / "settings.json"


def test_icon_is_in_project_folder_when_run_from_code():
    """При запуске из исходного кода значок лежит в папке проекта."""
    icon_file = resource_path("icon.ico")

    assert icon_file == Path(__file__).resolve().parent.parent / "icon.ico"
    assert icon_file.exists()


def test_icon_is_inside_built_program(monkeypatch, tmp_path):
    """У программы, собранной в exe, значок лежит во внутренней папке."""
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

    assert resource_path("icon.ico") == tmp_path / "icon.ico"
