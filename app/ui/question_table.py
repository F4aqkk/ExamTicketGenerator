"""Таблица вопросов на странице «Банк вопросов».

Таблица собрана из трёх частей (подход «модель – представление»):
модель отдаёт данные вопросов, делегат рисует ячейки как на макете,
а сама таблица показывает строки и сообщает о нажатиях. Qt рисует
только те строки, что видны на экране, поэтому 1500 вопросов
открываются так же быстро, как 15.
"""

from PyQt6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QRect,
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import QColor, QFont, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableView,
)

from app.models.question import Question
from app.services.question_service import DIFFICULTY_NAMES
from app.ui.icons import make_pixmap
from app.ui.theme import (
    ACCENT,
    BAR_OFF,
    BORDER,
    CHIP,
    FAINT,
    FONT,
    MONO,
    MUTED,
    PANEL,
    TEXT,
)

# Номера столбцов таблицы.
NUMBER, QUESTION, TOPIC, DIFFICULTY, TASK_TYPE, EDIT, DELETE = range(7)
TITLES = ("№", "ВОПРОС", "ТЕМА", "СЛОЖНОСТЬ", "ТИП", "", "")
WIDTHS = {  # ширина столбцов; столбец вопроса занимает всё остальное
    NUMBER: 72,
    TOPIC: 200,
    DIFFICULTY: 140,
    TASK_TYPE: 110,
    EDIT: 36,
    DELETE: 60,
}
ROW_HEIGHT = 72
HEADER_HEIGHT = 40
PADDING = 12  # отступ текста от левого края ячейки
FIRST_PADDING = 32  # отступ первого столбца, как у заголовка страницы
CHIP_HEIGHT = 20  # высота плашки тега
ICON_SIZE = 16


class QuestionTableModel(QAbstractTableModel):
    """Модель: отвечает таблице, сколько в ней строк и что в ячейках."""

    def __init__(self, parent=None):
        """Создать пустую модель."""
        super().__init__(parent)
        self._questions: list[Question] = []

    def set_questions(self, questions: list[Question]) -> None:
        """Заменить список вопросов и перерисовать таблицу."""
        self.beginResetModel()
        self._questions = list(questions)
        self.endResetModel()

    def question_at(self, row: int) -> Question:
        """Вопрос, который показан в строке с этим номером."""
        return self._questions[row]

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Число строк равно числу вопросов."""
        return 0 if parent.isValid() else len(self._questions)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Число столбцов таблицы."""
        return 0 if parent.isValid() else len(TITLES)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        """Текст ячейки или подсказка к ней."""
        if not index.isValid():
            return None
        question = self._questions[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return self._text(question, index)
        if role == Qt.ItemDataRole.ToolTipRole:
            return self._tooltip(question, index.column())
        return None

    def headerData(
        self,
        section,
        orientation,
        role=Qt.ItemDataRole.DisplayRole,
    ):
        """Надпись в шапке столбца."""
        is_title = role == Qt.ItemDataRole.DisplayRole
        if is_title and orientation == Qt.Orientation.Horizontal:
            return TITLES[section]
        return None

    @staticmethod
    def _text(question: Question, index: QModelIndex) -> str | None:
        """Текст ячейки для каждого столбца."""
        column = index.column()
        if column == NUMBER:
            return f"{index.row() + 1:02d}"  # 01, 02, 03 ...
        if column == QUESTION:
            return " ".join(question.text.split())  # в одну строку
        if column == TOPIC:
            return question.topic.name
        if column == DIFFICULTY:
            return DIFFICULTY_NAMES.get(question.difficulty, "")
        if column == TASK_TYPE:
            return question.task_type
        return None

    @staticmethod
    def _tooltip(question: Question, column: int) -> str | None:
        """Всплывающая подсказка: полный вопрос или название кнопки."""
        if column == QUESTION:
            return question.text
        if column == EDIT:
            return "Изменить вопрос"
        if column == DELETE:
            return "Удалить вопрос"
        return None


class QuestionDelegate(QStyledItemDelegate):
    """Делегат: рисует ячейки таблицы так, как они выглядят на макете."""

    def __init__(self, table: "QuestionTable"):
        """Запомнить таблицу и заранее подготовить шрифты и иконки."""
        super().__init__(table)
        self._table = table
        self._font = QFont(FONT, 10)
        self._mono = QFont(MONO, 9)
        self._small = QFont(MONO, 8)
        self._icons = {
            (EDIT, False): make_pixmap("edit", FAINT, ICON_SIZE),
            (EDIT, True): make_pixmap("edit", TEXT, ICON_SIZE),
            (DELETE, False): make_pixmap("delete", FAINT, ICON_SIZE),
            (DELETE, True): make_pixmap("delete", TEXT, ICON_SIZE),
        }

    def paint(
        self,
        painter: QPainter | None,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> None:
        """Нарисовать одну ячейку: фон, линию снизу и содержимое."""
        if painter is None:
            return
        rect = option.rect
        column = index.column()
        hovered = index.row() == self._table.hover_row()
        painter.save()
        if hovered:
            painter.fillRect(rect, QColor(PANEL))
        painter.setPen(QColor(BORDER))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())
        # Сглаживание включаем после линии, иначе она станет размытой.
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if column == QUESTION:
            question = self._table.question_at(index.row())
            self._paint_question(painter, rect, index.data(), question)
        elif column == DIFFICULTY:
            question = self._table.question_at(index.row())
            self._paint_difficulty(painter, rect, index.data(), question)
        elif column in (EDIT, DELETE):
            self._paint_icon(painter, rect, self._icons[column, hovered])
        elif column == NUMBER:
            area = rect.adjusted(FIRST_PADDING, 0, 0, 0)
            self._paint_text(painter, area, index.data(), self._mono, MUTED)
        else:
            area = rect.adjusted(PADDING, 0, -PADDING, 0)
            self._paint_text(painter, area, index.data(), self._font, MUTED)
        painter.restore()

    @staticmethod
    def _paint_text(
        painter: QPainter,
        area: QRect,
        text: str | None,
        font: QFont,
        color: str,
    ) -> None:
        """Одна строка текста; если не помещается, в конце многоточие."""
        painter.setFont(font)
        painter.setPen(QColor(color))
        metrics = painter.fontMetrics()
        text = metrics.elidedText(
            text or "",
            Qt.TextElideMode.ElideRight,
            area.width(),
        )
        align = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        painter.drawText(area, align, text)

    def _paint_question(
        self,
        painter: QPainter,
        rect: QRect,
        text: str,
        question: Question,
    ) -> None:
        """Текст вопроса и под ним плашки с тегами."""
        area = rect.adjusted(PADDING, 0, -PADDING, 0)
        painter.setFont(self._font)
        line_height = painter.fontMetrics().height()
        block_height = line_height
        if question.tags:
            block_height += 6 + CHIP_HEIGHT
        top = area.top() + (area.height() - block_height) // 2
        line = QRect(area.left(), top, area.width(), line_height)
        self._paint_text(painter, line, text, self._font, TEXT)
        self._paint_tags(painter, area, top + line_height + 6, question)

    def _paint_tags(
        self,
        painter: QPainter,
        area: QRect,
        top: int,
        question: Question,
    ) -> None:
        """Плашки тегов в ряд; что не поместилось, не рисуется."""
        painter.setFont(self._small)
        metrics = painter.fontMetrics()
        left = area.left()
        for tag in question.tags:
            label = "#" + tag.name
            width = metrics.horizontalAdvance(label) + 12
            if left + width > area.right():
                break
            chip = QRect(left, top, width, CHIP_HEIGHT)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(CHIP))
            painter.drawRoundedRect(chip, 4, 4)
            painter.setPen(QColor(MUTED))
            painter.drawText(chip, Qt.AlignmentFlag.AlignCenter, label)
            left += width + 6

    def _paint_difficulty(
        self,
        painter: QPainter,
        rect: QRect,
        text: str,
        question: Question,
    ) -> None:
        """Индикатор из трёх столбиков и название уровня сложности."""
        left = rect.left() + PADDING
        bottom = rect.center().y() + 8
        painter.setPen(Qt.PenStyle.NoPen)
        for step in range(3):  # столбики высотой 8, 12 и 16 точек
            height = 8 + 4 * step
            lit = step < question.difficulty  # закрашен ли столбик
            painter.setBrush(QColor(ACCENT if lit else BAR_OFF))
            bar = QRect(left + step * 5, bottom - height, 3, height)
            painter.drawRoundedRect(bar, 1, 1)
        area = rect.adjusted(PADDING + 24, 0, -PADDING, 0)
        self._paint_text(painter, area, text, self._font, MUTED)

    @staticmethod
    def _paint_icon(painter: QPainter, rect: QRect, pixmap: QPixmap) -> None:
        """Иконка кнопки по центру ячейки по высоте."""
        left = rect.left() + PADDING
        top = rect.top() + (rect.height() - ICON_SIZE) // 2
        painter.drawPixmap(left, top, pixmap)


class QuestionTable(QTableView):
    """Таблица вопросов: показывает строки и сообщает о нажатиях."""

    edit_requested = pyqtSignal(object)  # сигнал: изменить этот вопрос
    delete_requested = pyqtSignal(object)  # сигнал: удалить этот вопрос

    def __init__(self, parent=None):
        """Собрать таблицу: модель, делегат, размеры и поведение."""
        super().__init__(parent)
        self._hover_row = -1  # номер строки под курсором; -1 = нет такой
        self._model = QuestionTableModel(self)
        self.setModel(self._model)
        self.setItemDelegate(QuestionDelegate(self))
        self._setup_view()
        self._setup_columns()
        self.clicked.connect(self._on_clicked)
        self.doubleClicked.connect(self._on_double_clicked)
        self.entered.connect(self._on_entered)
        self.viewportEntered.connect(self._clear_hover)

    def set_questions(
        self,
        questions: list[Question],
        keep_position: bool = False,
    ) -> None:
        """Показать в таблице этот список вопросов.

        Обычно таблица прокручивается к началу. После изменения или
        удаления вопроса удобнее остаться на том же месте списка.
        """
        position = self.verticalScrollBar().value()
        self._hover_row = -1
        self._model.set_questions(questions)
        self.verticalScrollBar().setValue(position if keep_position else 0)

    def question_at(self, row: int) -> Question:
        """Вопрос в строке с этим номером."""
        return self._model.question_at(row)

    def hover_row(self) -> int:
        """Номер строки, над которой сейчас курсор."""
        return self._hover_row

    def leaveEvent(self, event) -> None:
        """Курсор ушёл с таблицы: убрать подсветку строки."""
        self._clear_hover()
        super().leaveEvent(event)

    def _setup_view(self) -> None:
        """Внешний вид и поведение таблицы."""
        self.setShowGrid(False)  # линии между строками рисует делегат
        self.setMouseTracking(True)  # чтобы знать строку под курсором
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setVerticalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel,
        )
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        rows = self.verticalHeader()
        rows.hide()
        rows.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        rows.setDefaultSectionSize(ROW_HEIGHT)

    def _setup_columns(self) -> None:
        """Шапка таблицы и ширина столбцов."""
        header = self.horizontalHeader()
        header.setFixedHeight(HEADER_HEIGHT)
        header.setHighlightSections(False)
        header.setSectionsClickable(False)
        header.setMinimumSectionSize(32)
        header.setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        )
        header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(QUESTION, QHeaderView.ResizeMode.Stretch)
        for column, width in WIDTHS.items():
            self.setColumnWidth(column, width)

    def _on_clicked(self, index: QModelIndex) -> None:
        """Нажатие на иконку в строке: изменить или удалить вопрос."""
        question = self.question_at(index.row())
        if index.column() == EDIT:
            self.edit_requested.emit(question)
        elif index.column() == DELETE:
            self.delete_requested.emit(question)

    def _on_double_clicked(self, index: QModelIndex) -> None:
        """Двойной щелчок по строке открывает вопрос для изменения."""
        if index.column() not in (EDIT, DELETE):
            self.edit_requested.emit(self.question_at(index.row()))

    def _on_entered(self, index: QModelIndex) -> None:
        """Курсор вошёл в ячейку: подсветить строку, сменить курсор."""
        self._set_hover(index.row())
        on_icon = index.column() in (EDIT, DELETE)
        shape = Qt.CursorShape.PointingHandCursor
        if not on_icon:
            shape = Qt.CursorShape.ArrowCursor
        self.viewport().setCursor(shape)

    def _clear_hover(self) -> None:
        """Курсор не над строкой: убрать подсветку."""
        self._set_hover(-1)
        self.viewport().setCursor(Qt.CursorShape.ArrowCursor)

    def _set_hover(self, row: int) -> None:
        """Запомнить строку под курсором и перерисовать таблицу."""
        if row != self._hover_row:
            self._hover_row = row
            self.viewport().update()
