"""Страница «Банк вопросов»: поиск, фильтры, таблица, импорт и экспорт."""

from datetime import date

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.models.question import Question
from app.services.documents import DocumentError
from app.services.export_service import ExportService
from app.services.import_service import ImportResult, ImportService
from app.services.question_service import (
    BANK_LIMIT,
    QuestionError,
    QuestionService,
)
from app.ui.icons import make_icon
from app.ui.question_dialog import QuestionDialog
from app.ui.question_table import QuestionTable
from app.ui.theme import ACCENT_TEXT, MUTED, TEXT
from app.ui.widgets import (
    ComboBox,
    SegmentedControl,
    ask_open_file,
    ask_save_file,
    confirm,
    plural,
    show_message,
)

DIFFICULTY_FILTER = [
    ("Все", None),
    ("Лёгкие", 1),
    ("Средние", 2),
    ("Сложные", 3),
    ("Без сложности", 0),  # вопросы, сложность которых не распознал импорт
]
SEARCH_DELAY = 250  # миллисекунд ждём после последней буквы в поиске
OPEN_KINDS = "Файлы банка вопросов (*.xlsx *.docx *.pdf *.txt)"
SAVE_KINDS = (
    "Таблица Excel (*.xlsx);;Документ Word (*.docx);;"
    "Документ PDF (*.pdf);;Текстовый файл (*.txt)"
)


def describe_import(result: ImportResult) -> str:
    """Итог импорта словами для окна с сообщением."""
    lines = [f"Добавлено вопросов: {result.added}."]
    if result.duplicates:
        lines.append(f"Уже были в банке и пропущены: {result.duplicates}.")
    if result.empty:
        lines.append(f"Пропущено записей без текста вопроса: {result.empty}.")
    if result.no_difficulty:
        lines.append(
            f"Сложность не распознана: {result.no_difficulty}. Такие "
            "вопросы не попадают в билеты: найдите их фильтром "
            "«Без сложности» и укажите сложность."
        )
    return "\n".join(lines)


class BankPage(QWidget):
    """Страница банка вопросов.

    Страница сама в базу и в файлы не ходит: вопросы она получает
    и изменяет через сервис банка, а файлы читают и пишут сервисы
    импорта и экспорта.
    """

    bank_changed = pyqtSignal()  # сигнал: вопрос добавлен или удалён

    def __init__(
        self,
        service: QuestionService,
        exporter: ExportService,
        importer: ImportService,
        parent=None,
    ):
        """Собрать страницу и показать вопросы из базы."""
        super().__init__(parent)
        self._service = service
        self._exporter = exporter
        self._importer = importer
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(SEARCH_DELAY)
        self._search_timer.timeout.connect(self.refresh_table)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_header())
        layout.addWidget(self._build_filters())
        layout.addWidget(self._build_table(), 1)
        self.reload()

    def reload(self, keep_position: bool = False) -> None:
        """Заново прочитать из базы счётчик, списки фильтров и вопросы."""
        count = self._service.count()
        text = f"{count} из {BANK_LIMIT} записей · хранится локально"
        self._counter.setText(text)
        self._fill_filter(
            self._topic_filter,
            "Все темы",
            self._service.get_topics(),
        )
        self._fill_filter(
            self._tag_filter,
            "Все теги",
            self._service.get_tags(),
        )
        self.refresh_table(keep_position)

    def refresh_table(self, keep_position: bool = False) -> None:
        """Показать вопросы, которые подходят под поиск и фильтры."""
        questions = self._service.search(
            text=self._search.text().strip(),
            difficulty=self._difficulty_filter.value(),
            topic_id=self._topic_filter.currentData(),
            tag_id=self._tag_filter.currentData(),
        )
        self._table.set_questions(questions, keep_position)
        if questions:
            self._table_stack.setCurrentWidget(self._table)
        else:
            self._empty_label.setText(self._empty_text())
            self._table_stack.setCurrentWidget(self._empty_label)

    def import_bank(self) -> None:
        """Добавить в банк вопросы из файла, который выберет пользователь."""
        path = ask_open_file(self, "Импорт вопросов", OPEN_KINDS)
        if not path:
            return
        try:
            result = self._importer.import_bank(path)
        except DocumentError as error:
            show_message(self, "Импорт не выполнен", str(error))
            return
        self.reload()
        self.bank_changed.emit()
        show_message(self, "Импорт вопросов", describe_import(result))

    def export_bank(self) -> None:
        """Сохранить весь банк в файл: это резервная копия вопросов."""
        today = date.today().strftime("%d.%m.%Y")
        name = f"Банк вопросов {today}.xlsx"
        path = ask_save_file(self, "Экспорт банка", name, SAVE_KINDS)
        if not path:
            return
        try:
            count = self._exporter.export_bank(path)
        except DocumentError as error:
            show_message(self, "Экспорт не выполнен", str(error))
            return
        saved = plural(count, "вопрос", "вопроса", "вопросов")
        text = f"В файл записано: {saved}.\n{path}"
        show_message(self, "Экспорт банка", text)

    def _build_header(self) -> QFrame:
        """Заголовок: название, счётчик записей и три кнопки."""
        title = QLabel("Банк вопросов")
        title.setObjectName("pageTitle")
        self._counter = QLabel()
        self._counter.setObjectName("pageHint")
        titles = QVBoxLayout()
        titles.setSpacing(4)
        titles.addWidget(title)
        titles.addWidget(self._counter)

        import_button = QPushButton(make_icon("import", TEXT), " Импорт")
        import_button.clicked.connect(self.import_bank)
        export_button = QPushButton(
            make_icon("export", TEXT),
            " Экспорт банка",
        )
        export_button.clicked.connect(self.export_bank)
        add_button = QPushButton(
            make_icon("plus", ACCENT_TEXT),
            " Добавить вопрос",
        )
        add_button.setObjectName("primary")
        add_button.clicked.connect(self._add_question)

        header = QFrame()
        header.setObjectName("pageHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(32, 24, 28, 20)
        layout.setSpacing(8)
        layout.addLayout(titles)
        layout.addStretch()
        for button in (import_button, export_button, add_button):
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(button, 0, Qt.AlignmentFlag.AlignVCenter)
        return header

    def _build_filters(self) -> QWidget:
        """Строка поиска, списки тем и тегов, переключатель сложности."""
        self._search = QLineEdit()
        self._search.setPlaceholderText("Поиск по тексту и тегам")
        self._search.setClearButtonEnabled(True)
        self._search.addAction(
            make_icon("search", MUTED),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        self._search.textChanged.connect(self._on_search)
        self._topic_filter = ComboBox()
        self._topic_filter.currentIndexChanged.connect(self._on_filter)
        self._tag_filter = ComboBox()
        self._tag_filter.currentIndexChanged.connect(self._on_filter)
        self._difficulty_filter = SegmentedControl(DIFFICULTY_FILTER)
        self._difficulty_filter.set_value(None)  # выбрано «Все»
        self._difficulty_filter.changed.connect(self._on_filter)

        filters = QWidget()
        layout = QVBoxLayout(filters)
        layout.setContentsMargins(32, 12, 28, 16)
        layout.setSpacing(12)
        layout.addWidget(self._search)
        layout.addWidget(self._topic_filter)
        layout.addWidget(self._tag_filter)
        layout.addWidget(
            self._difficulty_filter,
            0,
            Qt.AlignmentFlag.AlignLeft,
        )
        return filters

    def _build_table(self) -> QStackedWidget:
        """Таблица вопросов и надпись, которая видна вместо пустой таблицы."""
        self._table = QuestionTable()
        self._table.edit_requested.connect(self._edit_question)
        self._table.delete_requested.connect(self._delete_question)
        self._empty_label = QLabel()
        self._empty_label.setObjectName("emptyLabel")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._table_stack = QStackedWidget()
        self._table_stack.addWidget(self._table)
        self._table_stack.addWidget(self._empty_label)
        return self._table_stack

    @staticmethod
    def _fill_filter(combo: ComboBox, title: str, items: list) -> None:
        """Заполнить список фильтра и сохранить прежний выбор."""
        chosen = combo.currentData()
        combo.blockSignals(True)  # пока заполняем, таблицу не обновляем
        combo.clear()
        combo.addItem(title, None)
        for item in items:
            combo.addItem(item.name, item.id)
        combo.setCurrentIndex(max(combo.findData(chosen), 0))
        combo.blockSignals(False)

    def _empty_text(self) -> str:
        """Что написать вместо пустой таблицы."""
        if self._service.count() == 0:
            return "В банке пока нет вопросов. Нажмите «Добавить вопрос»."
        return "По этим условиям ничего не найдено."

    def _on_search(self, text: str) -> None:
        """В поиске набрали букву: обновить таблицу после короткой паузы.

        Пауза нужна, чтобы не искать заново после каждой буквы,
        пока человек ещё печатает.
        """
        self._search_timer.start()

    def _on_filter(self, *args) -> None:
        """Фильтр изменился: показать подходящие вопросы."""
        self.refresh_table()

    def _add_question(self) -> None:
        """Открыть форму «Новый вопрос»."""
        dialog = QuestionDialog(self._service, parent=self.window())
        if dialog.exec():
            self.reload()
            self.bank_changed.emit()

    def _edit_question(self, question: Question) -> None:
        """Открыть форму с данными вопроса для изменения."""
        dialog = QuestionDialog(self._service, question, self.window())
        if dialog.exec():
            self.reload(keep_position=True)

    def _delete_question(self, question: Question) -> None:
        """Удалить вопрос после подтверждения."""
        text = " ".join(question.text.split())
        if len(text) > 120:
            text = text[:120] + "…"
        agreed = confirm(
            self,
            "Удаление вопроса",
            f"Удалить вопрос?\n\n{text}",
            "Удалить",
        )
        if not agreed:
            return
        try:
            self._service.delete_question(question)
        except QuestionError as error:
            show_message(self, "Вопрос не удалён", str(error))
            return
        self.reload(keep_position=True)
        self.bank_changed.emit()
