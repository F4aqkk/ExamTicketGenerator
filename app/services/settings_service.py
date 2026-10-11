"""Настройки программы: шапка документа и формат экспорта.

Настройки хранятся в небольшом файле рядом с базой данных. Таблицы
для них в базе нет: это параметры программы, а не данные банка
вопросов.
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from app.paths import data_path

SETTINGS_FILE = "settings.json"
EXPORT_FORMATS = ("DOCX", "PDF", "XLSX", "TXT")


@dataclass
class Settings:
    """То, что преподаватель задал на странице настроек."""

    organization: str = ""  # образовательная организация
    discipline: str = ""  # дисциплина
    teacher: str = ""  # преподаватель
    export_format: str = EXPORT_FORMATS[0]  # формат экспорта по умолчанию


class SettingsService:
    """Читает настройки из файла и записывает их обратно."""

    def __init__(self, path: str | Path | None = None):
        """Запомнить путь к файлу и прочитать из него настройки.

        Если путь не передан, файл настроек лежит рядом с базой.
        """
        self._path = Path(path) if path else data_path(SETTINGS_FILE)
        self.settings = self._load()

    def update(self, **changes: str) -> Settings:
        """Изменить указанные настройки и сразу записать их в файл."""
        for name, value in changes.items():
            if not hasattr(self.settings, name):
                raise AttributeError(f"Нет такой настройки: {name}")
            setattr(self.settings, name, value.strip())
        self._fix_format(self.settings)
        text = json.dumps(asdict(self.settings), ensure_ascii=False, indent=2)
        self._path.write_text(text, encoding="utf-8")
        return self.settings

    def _load(self) -> Settings:
        """Прочитать настройки из файла.

        Если файла ещё нет или он испорчен, берутся настройки
        по умолчанию: программа запускается в любом случае.
        """
        settings = Settings()
        try:
            saved = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return settings
        if not isinstance(saved, dict):
            return settings
        for name in asdict(settings):
            if isinstance(saved.get(name), str):
                setattr(settings, name, saved[name])
        self._fix_format(settings)
        return settings

    @staticmethod
    def _fix_format(settings: Settings) -> None:
        """Неизвестный формат экспорта заменить форматом по умолчанию."""
        if settings.export_format not in EXPORT_FORMATS:
            settings.export_format = EXPORT_FORMATS[0]
