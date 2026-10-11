"""Где лежат файлы с данными программы: база и настройки."""

import sys
from pathlib import Path


def data_path(name: str) -> Path:
    """Путь к файлу данных с этим именем.

    У программы, собранной в exe-файл, данные лежат в папке рядом
    с этим файлом, откуда бы её ни запустили. При запуске из исходного
    кода файл берётся из текущей папки, то есть из папки проекта.
    """
    if getattr(sys, "frozen", False):  # так помечена сборка в exe
        return Path(sys.executable).parent / name
    return Path(name)
