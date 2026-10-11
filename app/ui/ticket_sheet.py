"""Лист билета для предпросмотра: так билет выглядит на бумаге."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app.models.question import Question
from app.models.ticket import Ticket
from app.services.question_service import DIFFICULTY_NAMES
from app.ui.widgets import clear_layout

SHEET_WIDTH = 640  # шире лист не становится
SHEET_MIN_WIDTH = 380  # а в узком окне сжимается до этой ширины
SHEET_MIN_HEIGHT = 720
INDEX_WIDTH = 28  # ширина столбика с номером вопроса


class TicketSheet(QFrame):
    """Светлый лист с одним билетом.

    Сверху шапка документа (организация, название работы, дисциплина),
    ниже номер билета и вопросы по порядку. Под каждым вопросом
    мелко подписаны его тема и сложность.
    """

    def __init__(self, parent=None):
        """Собрать пустой лист; билет показывается отдельным вызовом."""
        super().__init__(parent)
        self.setObjectName("sheet")
        self.setMinimumWidth(SHEET_MIN_WIDTH)
        self.setMaximumWidth(SHEET_WIDTH)
        self.setMinimumHeight(SHEET_MIN_HEIGHT)
        self._organization = self._make_label("sheetOrganization")
        self._organization.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title = self._make_label("sheetLine")
        self._discipline = self._make_label("sheetLine")
        self._discipline.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._number = self._make_label("sheetNumber")
        self._number.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rule = QFrame()  # тонкая линия под шапкой
        rule.setObjectName("sheetRule")
        rule.setFixedHeight(1)
        line = QHBoxLayout()
        line.setSpacing(16)
        line.addWidget(self._title, 1)
        line.addWidget(self._discipline, 1)
        self._questions = QVBoxLayout()  # сюда кладутся вопросы билета
        self._questions.setSpacing(18)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 40, 48, 40)
        layout.setSpacing(0)
        layout.addWidget(self._organization)
        layout.addSpacing(20)
        layout.addLayout(line)
        layout.addSpacing(10)
        layout.addWidget(rule)
        layout.addSpacing(28)
        layout.addWidget(self._number)
        layout.addSpacing(28)
        layout.addLayout(self._questions)
        layout.addStretch()

    def show_ticket(
        self,
        ticket: Ticket,
        title: str,
        organization: str = "",
        discipline: str = "",
    ) -> None:
        """Показать на листе билет с шапкой документа.

        Пустые строки шапки не показываются.
        """
        self._organization.setText(organization.upper())
        self._organization.setVisible(bool(organization))
        self._title.setText(title)
        self._discipline.setText(discipline)
        self._number.setText(f"БИЛЕТ № {ticket.number}")
        clear_layout(self._questions)  # убрать вопросы прошлого билета
        for item in ticket.ticket_questions:
            row = self._build_question(item.position, item.question)
            self._questions.addWidget(row)

    def number_text(self) -> str:
        """Заголовок показанного билета, например «БИЛЕТ № 1»."""
        return self._number.text()

    def question_count(self) -> int:
        """Сколько вопросов сейчас показано на листе."""
        return self._questions.count()

    @staticmethod
    def _make_label(name: str, text: str = "") -> QLabel:
        """Надпись листа; длинный текст переносится по словам."""
        label = QLabel(text)
        label.setObjectName(name)
        label.setWordWrap(True)
        return label

    def _build_question(self, position: int, question: Question) -> QWidget:
        """Один вопрос: номер слева, текст и подпись под ним справа."""
        index = self._make_label("sheetIndex", f"{position}.")
        index.setFixedWidth(INDEX_WIDTH)
        index.setAlignment(Qt.AlignmentFlag.AlignTop)
        text = self._make_label("sheetText", question.text)
        level = DIFFICULTY_NAMES.get(question.difficulty, "")
        note = f"{question.topic.name} · {level}".upper()
        column = QVBoxLayout()
        column.setSpacing(4)
        column.addWidget(text)
        column.addWidget(self._make_label("sheetNote", note))
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(index)
        layout.addLayout(column, 1)
        return row
