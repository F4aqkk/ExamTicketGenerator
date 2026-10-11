"""Запуск программы «ExamTicket» одним файлом.

Этот файл нужен для сборки программы в exe: сборщик PyInstaller
начинает с него и сам находит весь остальной код.
"""

import sys

from app.main import main

if __name__ == "__main__":
    sys.exit(main())
