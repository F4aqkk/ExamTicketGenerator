"""Тесты выбора папки для файлов с данными."""

import sys
from pathlib import Path

from app.paths import data_path


def test_data_is_in_current_folder_when_run_from_code():
    """При запуске из исходного кода файл берётся из текущей папки."""
    assert data_path("exam_tickets.db") == Path("exam_tickets.db")


def test_data_is_next_to_exe_in_built_program(monkeypatch, tmp_path):
    """У программы, собранной в exe, данные лежат рядом с exe-файлом."""
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "ExamTicket.exe"))

    assert data_path("settings.json") == tmp_path / "settings.json"
