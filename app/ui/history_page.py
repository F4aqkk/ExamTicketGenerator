"""Страница «История»: сохранённые генерации билетов."""

from datetime import datetime, timezone

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.models.generation import Generation
from app.services.generation_service import GenerationService
from app.ui.icons import make_icon
from app.ui.theme import MUTED, TEXT
from app.ui.widgets import clear_layout, confirm, plural

DATE_WIDTH = 120  # ширина столбика с датой
EMPTY_TEXT = (
    "Сохранённых генераций пока нет.\n"
    "Составьте билеты в разделе «Генератор», и они появятся здесь."
)


def format_date(created_at: str) -> str:
    """Дата создания в виде ДД.ММ.ГГГГ по местному времени.

    База хранит время по Гринвичу, например «2026-10-11 14:05:09».
    Если строка записана иначе, она возвращается как есть.
    """
    try:
        moment = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return created_at
    local = moment.replace(tzinfo=timezone.utc).astimezone()
    return local.strftime("%d.%m.%Y")


class HistoryPage(QWidget):
    """Страница истории генераций.

    Страница сама в базу не ходит: список она получает от сервиса
    генерации и через него же удаляет генерации.
    """

    open_requested = pyqtSignal(object)  # сигнал: открыть эту генерацию
    export_requested = pyqtSignal(object)  # сигнал: сохранить её в файл
    deleted = pyqtSignal(int)  # сигнал: удалена генерация с этим номером

    def __init__(self, service: GenerationService, parent=None):
        """Собрать страницу и показать генерации из базы."""
        super().__init__(parent)
        self._service = service
        self._rows = QVBoxLayout()  # сюда кладутся строки генераций
        self._rows.setSpacing(0)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addLayout(self._rows)
        content_layout.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        empty = QLabel(EMPTY_TEXT)
        empty.setObjectName("emptyLabel")
        empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty = empty
        self._scroll = scroll
        self._stack = QStackedWidget()  # подсказка или список генераций
        self._stack.addWidget(empty)
        self._stack.addWidget(scroll)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_header())
        layout.addWidget(self._stack, 1)
        self.reload()

    def reload(self) -> None:
        """Заново прочитать историю из базы и показать её."""
        generations = self._service.history()
        count = plural(
            len(generations),
            "сохранённая генерация",
            "сохранённые генерации",
            "сохранённых генераций",
        )
        self._counter.setText(count)
        clear_layout(self._rows)
        for generation in generations:
            self._rows.addWidget(self._build_row(generation))
        if generations:
            self._stack.setCurrentWidget(self._scroll)
        else:
            self._stack.setCurrentWidget(self._empty)

    def row_count(self) -> int:
        """Сколько генераций сейчас показано."""
        return self._rows.count()

    def _build_header(self) -> QFrame:
        """Заголовок страницы и число сохранённых генераций."""
        title = QLabel("История")
        title.setObjectName("pageTitle")
        self._counter = QLabel()
        self._counter.setObjectName("pageHint")
        header = QFrame()
        header.setObjectName("pageHeader")
        layout = QVBoxLayout(header)
        layout.setContentsMargins(32, 24, 28, 20)
        layout.setSpacing(4)
        layout.addWidget(title)
        layout.addWidget(self._counter)
        return header

    def _build_row(self, generation: Generation) -> QFrame:
        """Строка одной генерации: дата, название, темы и кнопки."""
        date = QLabel(format_date(generation.created_at))
        date.setObjectName("historyMeta")
        date.setFixedWidth(DATE_WIDTH)
        title = QLabel(generation.title)
        title.setObjectName("historyTitle")
        topics = QLabel(" · ".join(self._service.topic_names(generation)))
        topics.setObjectName("switchHint")
        texts = QVBoxLayout()
        texts.setSpacing(4)
        texts.addWidget(title)
        texts.addWidget(topics)
        tickets = generation.tickets_count
        per_ticket = generation.questions_per_ticket
        size_label = QLabel(f"{tickets} × {per_ticket}")
        size_label.setObjectName("historyMeta")
        size_label.setToolTip("Билетов × вопросов в билете")
        open_button = QPushButton(make_icon("file", TEXT), " Открыть")
        open_button.setCursor(Qt.CursorShape.PointingHandCursor)
        open_button.clicked.connect(
            lambda checked=False, item=generation: self._open(item)
        )
        export_button = self._make_icon_button("export", "Экспорт билетов")
        export_button.clicked.connect(
            lambda checked=False, item=generation: self._export(item)
        )
        delete_button = self._make_icon_button("delete", "Удалить генерацию")
        delete_button.clicked.connect(
            lambda checked=False, item=generation: self._delete(item)
        )
        row = QFrame()
        row.setObjectName("historyRow")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(32, 16, 28, 16)
        layout.setSpacing(12)
        layout.addWidget(date)
        layout.addLayout(texts, 1)
        layout.addWidget(size_label)
        layout.addSpacing(8)
        layout.addWidget(open_button)
        layout.addWidget(export_button)
        layout.addWidget(delete_button)
        return row

    @staticmethod
    def _make_icon_button(icon_name: str, tip: str) -> QToolButton:
        """Кнопка без рамки с одной иконкой и подсказкой."""
        button = QToolButton()
        button.setObjectName("flat")
        button.setIcon(make_icon(icon_name, MUTED))
        button.setIconSize(QSize(16, 16))
        button.setToolTip(tip)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        return button

    def _open(self, generation: Generation) -> None:
        """Нажали «Открыть»: попросить показать билеты в предпросмотре."""
        self.open_requested.emit(generation)

    def _export(self, generation: Generation) -> None:
        """Нажали значок экспорта: попросить сохранить билеты в файл."""
        self.export_requested.emit(generation)

    def _delete(self, generation: Generation) -> None:
        """Удалить генерацию после подтверждения."""
        agreed = confirm(
            self,
            "Удаление генерации",
            f"Удалить «{generation.title}» вместе с билетами?",
            "Удалить",
        )
        if not agreed:
            return
        generation_id = generation.id  # после удаления его уже не узнать
        self._service.delete(generation)
        self.reload()
        self.deleted.emit(generation_id)
