"""Настройки Sphinx для документации программы «ExamTicket».

Сборка из папки проекта:
    venv\\Scripts\\python.exe -m sphinx -b html docs docs\\_build\\html
Готовая документация открывается файлом docs\\_build\\html\\index.html.
"""

import sys
from pathlib import Path

# Папка проекта: из неё Sphinx берёт код, чтобы прочитать docstrings.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

project = "ExamTicket"
author = "студент группы ИСП 34"
copyright = "2026, " + author
release = "1.0"
language = "ru"

extensions = [
    "sphinx.ext.autodoc",  # описание кода из docstrings
    "sphinx.ext.viewcode",  # ссылки «[исходный код]» у классов и функций
]

autodoc_default_options = {
    "members": True,  # все открытые классы, методы и функции
    "show-inheritance": True,  # от какого класса унаследован класс
    # служебные поля SQLAlchemy у базового класса моделей
    "exclude-members": "metadata, registry",
}
autodoc_member_order = "bysource"  # в том порядке, как в файле
autodoc_typehints = "description"  # типы в описании, а не в заголовке

exclude_patterns = ["_build"]
html_theme = "alabaster"
html_title = "ExamTicket — документация"
html_static_path = []


def keep_backslashes(app, what, name, obj, options, lines):
    r"""Сохранить обратные косые черты в путях Windows из docstrings.

    Для Sphinx знак \ служебный и пропадает: «venv\Scripts» превратился
    бы в «venvScripts». Поэтому каждый такой знак удваивается.
    """
    lines[:] = [line.replace("\\", "\\\\") for line in lines]


def setup(app):
    """Подключить обработку docstrings к сборке документации."""
    app.connect("autodoc-process-docstring", keep_backslashes)
