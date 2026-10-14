"""Тесты выбора папки для файлов с данными и для значка."""

import sys
from pathlib import Path

from app import paths
from app.paths import data_path, resource_path


def test_data_is_in_current_folder_when_run_from_code():
    """При запуске из исходного кода файл берётся из текущей папки."""
    assert data_path("exam_tickets.db") == Path("exam_tickets.db")


def test_data_is_next_to_exe_in_built_program(monkeypatch, tmp_path):
    """У программы, собранной в exe, данные лежат рядом с exe-файлом."""
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "ExamTicket.exe"))

    assert data_path("settings.json") == tmp_path / "settings.json"


def test_write_is_allowed_in_existing_folder(tmp_path):
    """В обычную папку писать можно, пробный файл не остаётся."""
    assert paths.can_write(tmp_path) is True
    assert list(tmp_path.iterdir()) == []


def test_no_write_in_missing_folder(tmp_path):
    """В несуществующую папку писать нельзя."""
    assert paths.can_write(tmp_path / "такой папки нет") is False


def test_spare_folder_is_inside_local_appdata(monkeypatch, tmp_path):
    """Запасная папка данных лежит в %LOCALAPPDATA%."""
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    assert paths.spare_folder() == tmp_path / "ExamTicket"


def test_data_moves_to_profile_when_folder_is_read_only(
    monkeypatch,
    tmp_path,
):
    """Если в папку программы писать нельзя, данные идут в профиль."""
    monkeypatch.setattr(paths, "can_write", lambda folder: False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    expected = tmp_path / "ExamTicket" / "exam_tickets.db"
    assert data_path("exam_tickets.db") == expected
    assert expected.parent.is_dir()  # папка создаётся сразу


def test_ready_database_is_copied_to_profile(monkeypatch, tmp_path):
    """Готовая база из папки программы один раз копируется в профиль."""
    program = tmp_path / "ExamTicket"
    program.mkdir()
    (program / "exam_tickets.db").write_bytes(b"\x01bank")
    monkeypatch.setattr(paths, "main_folder", lambda: program)
    monkeypatch.setattr(paths, "can_write", lambda folder: False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "profile"))

    result = data_path("exam_tickets.db")

    assert result == tmp_path / "profile" / "ExamTicket" / "exam_tickets.db"
    assert result.read_bytes() == b"\x01bank"


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
