"""Небольшие общие элементы интерфейса.

Здесь лежит то, что нужно сразу нескольким окнам: переключатель
из кнопок, выпадающий список со стрелкой, подписи полей, окна
с вопросом и сообщением.
"""

from typing import Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QPaintEvent
from PyQt6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QStyledItemDelegate,
    QVBoxLayout,
    QWidget,
)

from app.ui.icons import make_pixmap
from app.ui.theme import MUTED


class SegmentedControl(QFrame):
    """Переключатель из нескольких кнопок: выбрана только одна.

    Используется для сложности: «Все / Лёгкие / Средние / Сложные»
    на странице банка и «Лёгкий / Средний / Сложный» в форме вопроса.
    """

    changed = pyqtSignal()  # сигнал: выбрали другую кнопку

    def __init__(self, options: list[tuple[str, Any]], parent=None):
        """Создать кнопки по списку пар «надпись, значение»."""
        super().__init__(parent)
        self.setObjectName("segmented")
        self._values = [value for _, value in options]
        self._group = QButtonGroup(self)  # следит, что выбрана одна кнопка
        layout = QHBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(2)
        for index, (title, _) in enumerate(options):
            button = QPushButton(title)
            button.setCheckable(True)  # кнопка умеет оставаться нажатой
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            self._group.addButton(button, index)
            layout.addWidget(button)
        self._group.idClicked.connect(self._on_clicked)

    def value(self) -> Any:
        """Значение выбранной кнопки; None, если ничего не выбрано."""
        index = self._group.checkedId()
        return self._values[index] if index >= 0 else None

    def set_value(self, value: Any) -> None:
        """Выбрать кнопку с таким значением; если её нет, снять выбор."""
        self._group.setExclusive(False)  # иначе выбор нельзя снять совсем
        for index, own_value in enumerate(self._values):
            self._group.button(index).setChecked(own_value == value)
        self._group.setExclusive(True)

    def _on_clicked(self, index: int) -> None:
        """Сообщить наружу, что выбор изменился."""
        self.changed.emit()


class ComboBox(QComboBox):
    """Выпадающий список со стрелкой, нарисованной как на макете."""

    def __init__(self, parent=None):
        """Подготовить картинку стрелки."""
        super().__init__(parent)
        self._arrow = make_pixmap("arrow_down", MUTED, 16)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        # С этим делегатом строки раскрытого списка слушаются стилей.
        self.setItemDelegate(QStyledItemDelegate(self))

    def paintEvent(self, event: QPaintEvent | None) -> None:
        """Нарисовать список как обычно и добавить стрелку справа."""
        super().paintEvent(event)
        painter = QPainter(self)
        left = self.width() - 28
        top = (self.height() - 16) // 2
        painter.drawPixmap(left, top, self._arrow)
        painter.end()


class PlaceholderPage(QWidget):
    """Страница раздела, который будет сделан на следующем шаге."""

    def __init__(self, title: str, parent=None):
        """Показать заголовок раздела и пояснение."""
        super().__init__(parent)
        heading = QLabel(title)
        heading.setObjectName("pageTitle")
        hint = QLabel("раздел появится на следующем шаге разработки")
        hint.setObjectName("pageHint")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 28, 24)
        layout.setSpacing(4)
        layout.addWidget(heading)
        layout.addWidget(hint)
        layout.addStretch()


def make_caption(text: str) -> QLabel:
    """Подпись над полем формы: мелкие серые заглавные буквы."""
    label = QLabel(text.upper())
    label.setObjectName("caption")
    return label


def confirm(parent: QWidget, title: str, text: str, action: str) -> bool:
    """Спросить подтверждение; вернуть True, если нажата кнопка действия."""
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(text)
    box.setIcon(QMessageBox.Icon.Question)
    yes = box.addButton(action, QMessageBox.ButtonRole.AcceptRole)
    no = box.addButton("Отмена", QMessageBox.ButtonRole.RejectRole)
    box.setDefaultButton(no)  # случайный Enter ничего не удалит
    box.exec()
    return box.clickedButton() == yes


def show_message(parent: QWidget | None, title: str, text: str) -> None:
    """Показать окно с сообщением и кнопкой «Понятно»."""
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(text)
    box.setIcon(QMessageBox.Icon.Information)
    box.addButton("Понятно", QMessageBox.ButtonRole.AcceptRole)
    box.exec()


def ask_text(parent: QWidget, title: str, label: str) -> str | None:
    """Спросить одну строку текста; None, если нажата «Отмена»."""
    dialog = QInputDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setLabelText(label)
    dialog.setOkButtonText("Добавить")
    dialog.setCancelButtonText("Отмена")
    if dialog.exec():
        return dialog.textValue()
    return None
