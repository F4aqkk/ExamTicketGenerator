"""Тесты окон: окна открываются без экрана и показывают данные базы."""

import sys

import pytest
from PyQt6.QtWidgets import QApplication, QLineEdit

from app.services.question_service import QuestionData, QuestionService
from app.ui.bank_page import BankPage
from app.ui.main_window import MainWindow
from app.ui.question_dialog import QuestionDialog
from app.ui.question_table import QuestionTable
from app.ui.theme import apply_theme


@pytest.fixture(scope="session")
def qt_app():
    """Приложение Qt: одно на все тесты окон."""
    app = QApplication.instance()
    if not isinstance(app, QApplication):
        app = QApplication([])
    apply_theme(app)
    return app


@pytest.fixture
def qt_errors(monkeypatch):
    """Список ошибок, которые случились внутри Qt.

    Ошибка при рисовании окна до теста сама не доходит, поэтому
    собираем такие ошибки в список и в конце теста проверяем,
    что он пуст.
    """
    errors = []
    monkeypatch.setattr(
        sys,
        "excepthook",
        lambda error_type, error, trace: errors.append(error),
    )
    return errors


def fill_bank(session) -> QuestionService:
    """Положить в базу тему и три вопроса разной сложности."""
    service = QuestionService(session)
    topic = service.add_topic("SQL")
    for difficulty in (1, 2, 3):
        service.add_question(
            QuestionData(
                text=f"Вопрос сложности {difficulty}",
                answer="Ответ",
                topic_id=topic.id,
                task_type="Теория",
                difficulty=difficulty,
                tag_names="JOIN",
            )
        )
    return service


def test_main_window_shows_questions(qt_app, qt_errors, session):
    """Главное окно открывается, рисуется и показывает вопросы базы."""
    fill_bank(session)

    window = MainWindow(session)
    window.show()
    qt_app.processEvents()
    picture = window.grab()  # нарисовать окно в картинку
    table = window.findChild(QuestionTable)

    assert table.model().rowCount() == 3
    assert not picture.isNull()
    assert qt_errors == []
    window.close()


def test_search_field_filters_table(qt_app, qt_errors, session):
    """Текст в строке поиска оставляет в таблице подходящие вопросы."""
    page = BankPage(fill_bank(session))
    table = page.findChild(QuestionTable)

    page.findChild(QLineEdit).setText("сложности 2")
    page.refresh_table()

    assert table.model().rowCount() == 1
    assert table.question_at(0).difficulty == 2
    assert qt_errors == []


def test_question_dialog_saves_question(qt_app, qt_errors, session):
    """Форма «Новый вопрос» сохраняет вопрос через сервис."""
    service = fill_bank(session)
    dialog = QuestionDialog(service)
    dialog._text.setPlainText("Что делает GROUP BY?")
    dialog._answer.setPlainText("Группирует строки.")
    dialog._topic.setCurrentIndex(1)  # первая тема после «Выберите тему»
    dialog._tags.setText("SELECT, группировка")
    picture = dialog.grab()

    dialog._save()

    assert service.count() == 4
    assert service.search(text="group by")[0].difficulty == 2
    assert not picture.isNull()
    assert qt_errors == []


def test_question_dialog_rejects_empty_text(qt_app, qt_errors, session):
    """Форма без текста вопроса не сохраняется и пишет, что исправить."""
    service = fill_bank(session)
    dialog = QuestionDialog(service)

    dialog._save()

    assert service.count() == 3
    assert dialog._error.text() == "Введите текст вопроса."
    assert qt_errors == []
