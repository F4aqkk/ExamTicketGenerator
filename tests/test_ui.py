"""Тесты окон: окна открываются без экрана и показывают данные базы."""

import sys

import pytest
from PyQt6.QtWidgets import QApplication, QLineEdit, QPushButton

from app.services.documents import read_lines
from app.services.export_service import ExportService
from app.services.generation_service import GenerationService
from app.services.import_service import ImportService
from app.services.question_service import QuestionData, QuestionService
from app.services.settings_service import SettingsService
from app.ui import bank_page, generator_page, history_page
from app.ui.bank_page import BankPage
from app.ui.generator_page import GeneratorPage
from app.ui.history_page import HistoryPage, format_date
from app.ui.main_window import GENERATOR, MainWindow
from app.ui.question_dialog import QuestionDialog
from app.ui.question_table import QuestionTable
from app.ui.settings_page import SettingsPage
from app.ui.theme import apply_theme
from app.ui.ticket_sheet import TicketSheet
from app.ui.widgets import Stepper, plural


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


@pytest.fixture
def settings(tmp_path):
    """Настройки во временной папке: настоящий файл тесты не трогают."""
    return SettingsService(tmp_path / "settings.json")


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


def make_bank_page(session, settings) -> BankPage:
    """Страница банка над банком из трёх вопросов одной темы."""
    return BankPage(
        fill_bank(session),
        ExportService(session, settings),
        ImportService(session),
    )


def test_main_window_shows_questions(qt_app, qt_errors, session, settings):
    """Главное окно открывается, рисуется и показывает вопросы базы."""
    fill_bank(session)

    window = MainWindow(session, settings)
    window.show()
    qt_app.processEvents()
    picture = window.grab()  # нарисовать окно в картинку
    table = window.findChild(QuestionTable)

    assert table.model().rowCount() == 3
    assert not picture.isNull()
    assert qt_errors == []
    window.close()


def test_search_field_filters_table(qt_app, qt_errors, session, settings):
    """Текст в строке поиска оставляет в таблице подходящие вопросы."""
    page = make_bank_page(session, settings)
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


def test_generator_page_reads_form(qt_app, qt_errors, session, settings):
    """Страница генератора рисуется и сообщает, что выбрано в форме."""
    questions = fill_bank(session)
    topic = questions.get_topics()[0]

    page = GeneratorPage(
        GenerationService(session),
        questions,
        settings,
        ExportService(session, settings),
    )
    picture = page.grab()  # нарисовать страницу в картинку

    assert page.work_title() == ""
    assert page.tickets_count() == 30
    assert page.counts() == {1: 5, 2: 5, 3: 5}
    assert page.chosen_topic_ids() == [topic.id]
    assert not picture.isNull()
    assert qt_errors == []


def test_generator_page_shows_tickets(qt_app, qt_errors, session, settings):
    """Предпросмотр показывает билеты генерации и листает их."""
    questions = fill_bank(session)
    generations = GenerationService(session)
    generation = generations.create("Экзамен", 2, {1: 1, 2: 1})
    exporter = ExportService(session, settings)
    page = GeneratorPage(generations, questions, settings, exporter)
    sheet = page.findChild(TicketSheet)

    page.show_generation(generation)
    first = sheet.number_text()
    page._show_next()
    picture = page.grab()

    assert first == "БИЛЕТ № 1"
    assert sheet.number_text() == "БИЛЕТ № 2"
    assert sheet.question_count() == 2
    assert page._counter.text() == "2 / 2"
    assert not picture.isNull()
    assert qt_errors == []


def test_stepper_accepts_typed_number(qt_app, qt_errors):
    """В счётчик можно набрать число с клавиатуры."""
    stepper = Stepper(5, 1, 100)
    changes = []
    stepper.changed.connect(lambda: changes.append(stepper.value()))

    stepper._field.setText("42")
    stepper._on_edited("42")  # так поле сообщает о каждой набранной цифре
    typed = stepper.value()
    stepper._field.setText("250")
    stepper._on_edited("250")
    wrong_while_typing = stepper.is_wrong()
    stepper._on_finished()  # так поле сообщает, что ввод закончен
    too_big = stepper.value()
    stepper._field.setText("")
    stepper._on_finished()

    assert typed == 42
    assert wrong_while_typing  # поле красное, пока число слишком большое
    assert not stepper.is_wrong()  # после исправления красный цвет убран
    assert too_big == 100
    assert stepper.value() == 100
    assert stepper._field.text() == "100"
    assert changes == [42, 100]
    assert qt_errors == []


def test_stepper_stays_inside_limits(qt_app, qt_errors):
    """Счётчик «− число +» не выходит за свои границы."""
    stepper = Stepper(5, 1, 6)

    stepper._increase()
    stepper._increase()
    upper = stepper.value()
    stepper.set_value(-3)

    assert upper == 6
    assert stepper.value() == 1
    assert qt_errors == []


def make_generator_page(session, settings) -> GeneratorPage:
    """Страница генератора над банком из трёх вопросов одной темы."""
    questions = fill_bank(session)
    return GeneratorPage(
        GenerationService(session),
        questions,
        settings,
        ExportService(session, settings),
    )


def test_summary_counts_questions(qt_app, qt_errors, session, settings):
    """Под формой написано, сколько вопросов есть и сколько требуется."""
    page = make_generator_page(session, settings)
    enough = "В выбранных темах 3 вопросов, требуется 3."

    start_text = page._summary.text()
    start_warning = page._warning.text()
    page._tickets.set_value(1)
    for stepper in page._levels.values():
        stepper.set_value(1)

    assert start_text == "В выбранных темах 3 вопросов, требуется 450."
    assert start_warning == "Часть вопросов повторится между билетами."
    assert page._summary.text() == enough
    assert page._warning.text() == ""
    assert qt_errors == []


def test_summary_asks_to_choose_topic(qt_app, qt_errors, session, settings):
    """Если не отмечена ни одна тема, страница просит выбрать тему."""
    page = make_generator_page(session, settings)

    for row in page._topic_rows.values():
        row.setChecked(False)

    assert page.chosen_topic_ids() == []
    assert page._summary.text() == "Выберите хотя бы одну тему."
    assert qt_errors == []


def test_generate_button_makes_tickets(qt_app, qt_errors, session, settings):
    """Кнопка «Сформировать билеты» сохраняет генерацию и показывает её."""
    page = make_generator_page(session, settings)
    signals = []
    page.generated.connect(lambda: signals.append("generated"))
    page._title.setText("Экзамен")
    page._tickets.set_value(2)
    for stepper in page._levels.values():
        stepper.set_value(1)

    page._on_generate()
    picture = page.grab()

    assert page._service.count() == 1
    assert page.findChild(TicketSheet).number_text() == "БИЛЕТ № 1"
    assert page._counter.text() == "1 / 2"
    assert signals == ["generated"]
    assert not picture.isNull()
    assert qt_errors == []


def test_generate_button_explains_error(
    qt_app,
    qt_errors,
    session,
    settings,
    monkeypatch,
):
    """Без названия работы билеты не составляются, причина показана."""
    messages = []
    monkeypatch.setattr(
        generator_page,
        "show_message",
        lambda parent, title, text: messages.append(text),
    )
    page = make_generator_page(session, settings)

    page._on_generate()

    assert messages == ["Введите название работы."]
    assert page._service.count() == 0
    assert qt_errors == []


def test_history_page_lists_and_deletes(
    qt_app,
    qt_errors,
    session,
    monkeypatch,
):
    """История показывает генерации и удаляет их после подтверждения."""
    fill_bank(session)
    generations = GenerationService(session)
    first = generations.create("Зачёт", 1, {1: 1})
    generations.create("Экзамен", 2, {1: 1, 2: 1})
    monkeypatch.setattr(history_page, "confirm", lambda *args: True)
    page = HistoryPage(generations)
    deleted = []
    page.deleted.connect(deleted.append)
    exported = []
    page.export_requested.connect(exported.append)
    first_id = first.id

    rows_before = page.row_count()
    counter_before = page._counter.text()
    picture = page.grab()
    page._export(first)
    page._delete(first)

    assert rows_before == 2
    assert counter_before == "2 сохранённые генерации"
    assert page.row_count() == 1
    assert page._counter.text() == "1 сохранённая генерация"
    assert deleted == [first_id]
    assert len(exported) == 1
    assert not picture.isNull()
    assert qt_errors == []


def test_settings_page_saves_settings(qt_app, qt_errors, tmp_path):
    """Страница настроек записывает изменения в файл."""
    path = tmp_path / "settings.json"
    page = SettingsPage(SettingsService(path))
    signals = []
    page.settings_changed.connect(lambda: signals.append("changed"))

    requests = []
    page.backup_requested.connect(lambda: requests.append("копия"))
    page.restore_requested.connect(lambda: requests.append("восстановить"))

    page._organization.setText("Колледж")
    page._discipline.setText("Базы данных")
    page._format.set_value("PDF")
    page._save()
    for button in page.findChildren(QPushButton):
        if button.text().strip() in ("Сохранить копию", "Восстановить"):
            button.click()
    picture = page.grab()
    saved = SettingsService(path).settings

    assert saved.organization == "Колледж"
    assert saved.discipline == "Базы данных"
    assert saved.export_format == "PDF"
    assert signals == ["changed"]
    assert requests == ["копия", "восстановить"]
    assert not picture.isNull()
    assert qt_errors == []


def test_history_opens_generation_in_generator(
    qt_app,
    qt_errors,
    session,
    settings,
):
    """«Открыть» в истории показывает билеты в разделе «Генератор»."""
    fill_bank(session)
    generation = GenerationService(session).create("Экзамен", 2, {1: 1})
    settings.update(organization="Колледж", discipline="Базы данных")
    window = MainWindow(session, settings)
    sheet = window.findChild(TicketSheet)

    window._history_page._open(generation)
    pictures = []
    for section in range(window._pages.count()):  # нарисовать все страницы
        window._pages.setCurrentIndex(section)
        pictures.append(window.grab())
    window._on_deleted(generation.id)

    assert sheet.number_text() == "БИЛЕТ № 1"
    assert sheet._organization.text() == "КОЛЛЕДЖ"
    assert sheet._discipline.text() == "Дисциплина: Базы данных"
    assert window._sidebar._buttons[GENERATOR].isChecked()
    assert all(not picture.isNull() for picture in pictures)
    assert window._generator_page._generation is None
    assert qt_errors == []


def test_format_date_shows_day_month_year():
    """Дата из базы показывается в виде ДД.ММ.ГГГГ."""
    assert format_date("2026-10-11 12:00:00") == "11.10.2026"
    assert format_date("не дата") == "не дата"


def test_plural_chooses_word_form():
    """Слово после числа ставится в нужной форме."""
    forms = ("вопрос", "вопроса", "вопросов")

    assert plural(1, *forms) == "1 вопрос"
    assert plural(3, *forms) == "3 вопроса"
    assert plural(5, *forms) == "5 вопросов"
    assert plural(11, *forms) == "11 вопросов"
    assert plural(21, *forms) == "21 вопрос"


@pytest.fixture
def dialogs(monkeypatch):
    """Подменить окна выбора файла и окна с сообщением.

    В тестах некому нажимать кнопки, поэтому окна не открываются:
    имя файла берётся из словаря, а тексты сообщений складываются
    в список. Возвращает этот словарь: в нём «path» и «messages».
    """
    state = {"path": "", "messages": []}
    for module in (bank_page, generator_page):
        monkeypatch.setattr(
            module,
            "ask_save_file",
            lambda parent, title, name, kinds: state["path"],
        )
        monkeypatch.setattr(
            module,
            "show_message",
            lambda parent, title, text: state["messages"].append(text),
        )
    monkeypatch.setattr(
        bank_page,
        "ask_open_file",
        lambda parent, title, kinds: state["path"],
    )
    return state


def test_format_button_saves_tickets_to_file(
    qt_app,
    qt_errors,
    session,
    settings,
    dialogs,
    tmp_path,
):
    """Кнопка формата сохраняет билеты; ответы только по переключателю."""
    page = make_generator_page(session, settings)
    generation = page._service.create("Экзамен", 1, {1: 1})
    page.show_generation(generation)
    plain = tmp_path / "plain.txt"
    answers = tmp_path / "answers.txt"
    button = [b for b in page._formats.buttons() if b.text() == "TXT"][0]

    dialogs["path"] = str(plain)
    page._export(button)
    page._with_answers.setChecked(True)
    dialogs["path"] = str(answers)
    page._export(button)

    assert "БИЛЕТ № 1" in read_lines(plain)
    assert "Ответ: Ответ" not in read_lines(plain)
    assert "Ответ: Ответ" in read_lines(answers)
    assert len(dialogs["messages"]) == 2
    assert qt_errors == []


def test_cancelled_export_writes_nothing(
    qt_app,
    qt_errors,
    session,
    settings,
    dialogs,
):
    """Если в окне выбора файла нажали «Отмена», ничего не происходит."""
    page = make_generator_page(session, settings)
    generation = page._service.create("Экзамен", 1, {1: 1})

    page.export_generation(generation, "DOCX")  # путь к файлу пустой

    assert dialogs["messages"] == []
    assert qt_errors == []


def test_bank_page_exports_and_imports_bank(
    qt_app,
    qt_errors,
    session,
    settings,
    dialogs,
    tmp_path,
):
    """Кнопки банка сохраняют вопросы в файл и читают их из файла."""
    page = make_bank_page(session, settings)
    copy = tmp_path / "bank.txt"
    extra = tmp_path / "extra.txt"
    extra.write_text(
        "Тема: SQL\nСложность: непонятная\nВопрос: Что такое индекс?\n",
        encoding="utf-8",
    )
    changes = []
    page.bank_changed.connect(lambda: changes.append("changed"))

    dialogs["path"] = str(copy)
    page.export_bank()
    dialogs["path"] = str(extra)
    page.import_bank()
    page._difficulty_filter.set_value(0)  # фильтр «Без сложности»
    page.refresh_table()
    table = page.findChild(QuestionTable)

    assert "Вопрос: Вопрос сложности 2" in read_lines(copy)
    assert page._service.count() == 4
    assert table.model().rowCount() == 1
    assert table.question_at(0).text == "Что такое индекс?"
    assert "В файл записано: 3 вопроса." in dialogs["messages"][0]
    assert "Добавлено вопросов: 1." in dialogs["messages"][1]
    assert "Без сложности" in dialogs["messages"][1]
    assert changes == ["changed"]
    assert qt_errors == []


def test_import_explains_wrong_file(
    qt_app,
    qt_errors,
    session,
    settings,
    dialogs,
    tmp_path,
):
    """Файл неподходящего вида не импортируется, причина показана."""
    page = make_bank_page(session, settings)
    wrong = tmp_path / "bank.odt"
    wrong.write_text("Вопрос: текст", encoding="utf-8")

    dialogs["path"] = str(wrong)
    page.import_bank()

    assert dialogs["messages"] == [
        "Поддерживаются только файлы DOCX, PDF, XLSX и TXT.",
    ]
    assert page._service.count() == 3
    assert qt_errors == []
