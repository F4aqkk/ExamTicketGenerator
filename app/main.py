"""Точка входа: запуск программы «ExamTicket».

Запуск из папки проекта:
    venv\\Scripts\\python.exe -m app.main
"""

import sys
import traceback

from PyQt6.QtCore import QLibraryInfo, QTranslator
from PyQt6.QtWidgets import QApplication

from app.database import SessionLocal, init_db
from app.ui.main_window import MainWindow
from app.ui.theme import apply_theme
from app.ui.widgets import show_message


def install_russian(app: QApplication) -> None:
    """Перевести на русский стандартные надписи Qt (меню полей ввода)."""
    folder = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    translator = QTranslator(app)
    if translator.load("qtbase_ru", folder):
        app.installTranslator(translator)


def main() -> int:
    """Создать приложение, открыть главное окно и ждать его закрытия."""
    app = QApplication(sys.argv)
    app.setApplicationName("ExamTicket")
    apply_theme(app)
    install_russian(app)
    init_db()  # создать таблицы, если базы ещё нет
    session = SessionLocal()  # одна сессия базы на всё время работы

    def show_error(error_type, error, trace) -> None:
        """Непредвиденная ошибка: отменить изменения и показать окно.

        Без этого программа молча закрывалась бы при любой ошибке.
        """
        traceback.print_exception(error_type, error, trace)
        session.rollback()
        show_message(
            None,
            "Ошибка",
            f"Произошла непредвиденная ошибка:\n{error}\n\n"
            "Последнее действие отменено, данные в базе не испорчены.",
        )

    sys.excepthook = show_error
    window = MainWindow(session)
    window.show()
    code = app.exec()
    session.close()
    return code


if __name__ == "__main__":
    sys.exit(main())
