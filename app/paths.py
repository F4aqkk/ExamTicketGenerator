"""Где лежат файлы программы: база, настройки и значок."""

import os
import shutil
import sys
import tempfile
from pathlib import Path

APP_FOLDER = "ExamTicket"  # имя папки программы в профиле пользователя


def main_folder() -> Path:
    """Папка, в которой программа хранит данные обычным образом.

    У программы, собранной в exe-файл, это папка рядом с этим файлом,
    откуда бы её ни запустили. При запуске из исходного кода это
    текущая папка, то есть папка проекта.
    """
    if getattr(sys, "frozen", False):  # так помечена сборка в exe
        return Path(sys.executable).parent
    return Path()


def spare_folder() -> Path:
    """Запасная папка данных в профиле пользователя.

    В Windows это папка ExamTicket внутри %LOCALAPPDATA%. Если такой
    переменной окружения нет, берётся скрытая папка в домашней папке
    пользователя.
    """
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local) / APP_FOLDER
    return Path.home() / ("." + APP_FOLDER.lower())


def can_write(folder: Path) -> bool:
    """Можно ли создать файл в этой папке.

    Проверка делается пробным временным файлом: он сразу удаляется.
    Папки нет, прав нет или диск только для чтения — ответ «нельзя».
    """
    try:
        with tempfile.TemporaryFile(dir=folder):
            pass
    except OSError:
        return False
    return True


def data_path(name: str) -> Path:
    """Путь к файлу данных с этим именем.

    Обычно файл лежит в папке программы. Если записывать в неё нельзя
    (папку положили на диск только для чтения или в защищённое место
    вроде Program Files), файл берётся из запасной папки в профиле
    пользователя. Готовый файл из папки программы копируется туда
    один раз, чтобы банк вопросов не потерялся.
    """
    folder = main_folder()
    if can_write(folder):
        return folder / name
    spare = spare_folder()
    try:
        spare.mkdir(parents=True, exist_ok=True)
    except OSError:  # и в профиль писать нельзя: ведём себя как раньше
        return folder / name
    target = spare / name
    source = folder / name
    if not target.exists() and source.is_file():
        try:
            shutil.copy2(source, target)
        except OSError:  # копия не обязательна: программа создаст файл
            pass
    return target


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
