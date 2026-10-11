"""Где лежат файлы программы: база, настройки и значок."""

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


def resource_path(name: str) -> Path:
    """Путь к файлу, который поставляется вместе с программой.

    Так программа находит свой значок. У программы, собранной
    в exe-файл, такие файлы лежат во внутренней папке сборки. При запуске
    из исходного кода файл берётся из папки проекта, из какой бы папки
    программу ни запустили.
    """
    if getattr(sys, "frozen", False):  # так помечена сборка в exe
        return Path(getattr(sys, "_MEIPASS", ".")) / name
    return Path(__file__).resolve().parent.parent / name
