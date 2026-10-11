"""Тесты настроек программы."""

from app.services.settings_service import SettingsService


def test_settings_have_defaults_without_file(tmp_path):
    """Файла настроек ещё нет: берутся настройки по умолчанию."""
    service = SettingsService(tmp_path / "settings.json")

    assert service.settings.organization == ""
    assert service.settings.export_format == "DOCX"


def test_update_saves_settings_to_file(tmp_path):
    """Изменённые настройки записываются в файл и читаются заново."""
    path = tmp_path / "settings.json"
    service = SettingsService(path)

    service.update(organization="  Колледж  ", export_format="PDF")
    saved = SettingsService(path).settings

    assert saved.organization == "Колледж"
    assert saved.export_format == "PDF"
    assert saved.discipline == ""


def test_broken_file_gives_defaults(tmp_path):
    """Испорченный файл настроек не мешает запуску программы."""
    path = tmp_path / "settings.json"
    path.write_text("это не настройки", encoding="utf-8")

    service = SettingsService(path)

    assert service.settings.export_format == "DOCX"


def test_unknown_export_format_is_replaced(tmp_path):
    """Неизвестный формат экспорта заменяется форматом по умолчанию."""
    service = SettingsService(tmp_path / "settings.json")

    service.update(export_format="ODT")

    assert service.settings.export_format == "DOCX"
