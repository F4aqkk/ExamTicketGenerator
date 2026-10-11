"""Небольшие общие элементы интерфейса.

Здесь лежит то, что нужно сразу нескольким окнам: переключатель
из кнопок, выпадающий список со стрелкой, счётчик «− число +»,
переключатель «включено / выключено», строка с галочкой, столбики
сложности, подписи полей, окна с вопросом, сообщением и выбором
файла, а также две маленькие функции: очистка раскладки и выбор
формы слова.
"""

from typing import Any

from pathlib import Path

from PyQt6.QtCore import (
    QPoint,
    QRect,
    QRegularExpression,
    QSize,
    QStandardPaths,
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QPaintEvent,
    QRegularExpressionValidator,
)
from PyQt6.QtWidgets import (
    QAbstractButton,
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStyledItemDelegate,
    QToolButton,
    QToolTip,
    QWidget,
)

from app.ui.icons import make_icon, make_pixmap
from app.ui.theme import (
    ACCENT,
    ACCENT_TEXT,
    BAR_OFF,
    DANGER,
    FONT,
    KNOB,
    MONO,
    MUTED,
    OUTLINE,
    TEXT,
)


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


class Stepper(QFrame):
    """Счётчик «− число +»: число в заданных границах.

    Число меняется кнопками или вводится с клавиатуры. Если набрать
    число за границами, поле краснеет и рядом появляется подсказка.
    Используется на странице генератора для количества билетов
    и количества вопросов каждой сложности.
    """

    changed = pyqtSignal()  # сигнал: число изменилось
    # Так выглядит счётчик, пока в нём набрано недопустимое число.
    WRONG_STYLE = (
        f"#stepper {{ border: 1px solid {DANGER}; }} "
        "QLineEdit#stepperValue, QLineEdit#stepperValue:focus "
        f"{{ color: {DANGER}; }}"
    )

    def __init__(self, value: int, minimum: int, maximum: int, parent=None):
        """Создать счётчик с начальным числом и границами."""
        super().__init__(parent)
        self.setObjectName("stepper")
        self._value = value
        self._minimum = minimum
        self._maximum = maximum
        self._wrong = False  # набрано ли сейчас недопустимое число
        self._field = QLineEdit()  # поле, в котором число можно набрать
        self._field.setObjectName("stepperValue")
        self._field.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._field.setFixedWidth(44)
        # В поле разрешены только цифры, не больше трёх.
        digits = QRegularExpression("[0-9]{0,3}")
        self._field.setValidator(QRegularExpressionValidator(digits, self))
        self._field.textEdited.connect(self._on_edited)
        self._field.editingFinished.connect(self._on_finished)
        self._minus = self._make_button("minus", "Меньше")
        self._minus.clicked.connect(self._decrease)
        self._plus = self._make_button("plus", "Больше")
        self._plus.clicked.connect(self._increase)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)
        layout.addWidget(self._minus)
        layout.addWidget(self._field)
        layout.addWidget(self._plus)
        self._show_value()

    def value(self) -> int:
        """Текущее число."""
        return self._value

    def is_wrong(self) -> bool:
        """Набрано ли сейчас число за границами."""
        return self._wrong

    def set_value(self, value: int) -> None:
        """Поставить число; за границы оно не выйдет."""
        value = max(self._minimum, min(value, self._maximum))
        changed = value != self._value
        self._value = value
        self._show_value()
        if changed:
            self.changed.emit()

    @staticmethod
    def _make_button(icon_name: str, tip: str) -> QToolButton:
        """Кнопка счётчика; если её держать, число меняется быстро."""
        button = QToolButton()
        button.setIcon(make_icon(icon_name, MUTED))
        button.setIconSize(QSize(14, 14))
        button.setToolTip(tip)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setAutoRepeat(True)
        return button

    def _decrease(self) -> None:
        """Нажали «−»: число на единицу меньше."""
        self.set_value(self._value - 1)

    def _increase(self) -> None:
        """Нажали «+»: число на единицу больше."""
        self.set_value(self._value + 1)

    def _on_edited(self, text: str) -> None:
        """В поле печатают: подходящее число учитывается сразу.

        Сам текст в поле не трогаем, чтобы не мешать печатать.
        """
        if not text:
            self._mark_wrong("")
            return
        number = int(text)
        if number > self._maximum:
            self._mark_wrong(f"Не больше {self._maximum}")
        elif number < self._minimum:
            self._mark_wrong(f"Не меньше {self._minimum}")
        else:
            self._mark_wrong("")
            if number != self._value:
                self._value = number
                self._update_buttons()
                self.changed.emit()

    def _on_finished(self) -> None:
        """Ввод закончен: нажали Enter или перешли в другое поле.

        Число за границами заменяется ближайшим допустимым, а пустое
        поле возвращает прежнее число.
        """
        text = self._field.text()
        self.set_value(int(text) if text else self._value)

    def _show_value(self) -> None:
        """Показать число в поле и обновить кнопки."""
        self._field.setText(str(self._value))
        self._mark_wrong("")
        self._update_buttons()

    def _mark_wrong(self, hint: str) -> None:
        """Покрасить счётчик в красный и показать подсказку.

        Пустая подсказка значит, что число допустимое: красный цвет
        и подсказка убираются.
        """
        if not hint and not self._wrong:
            return  # и так всё в порядке, менять нечего
        self._wrong = bool(hint)
        self.setStyleSheet(self.WRONG_STYLE if hint else "")
        if hint:
            below = self._field.mapToGlobal(QPoint(0, self._field.height()))
            QToolTip.showText(below, hint, self._field)
        else:
            QToolTip.hideText()

    def _update_buttons(self) -> None:
        """Выключить кнопку, которая упёрлась в границу."""
        self._minus.setEnabled(self._value > self._minimum)
        self._plus.setEnabled(self._value < self._maximum)


class ToggleSwitch(QAbstractButton):
    """Переключатель «включено / выключено», нарисованный как на макете."""

    def __init__(self, checked: bool = True, parent=None):
        """Создать переключатель в нужном положении."""
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(36, 20)

    def paintEvent(self, event: QPaintEvent | None) -> None:
        """Нарисовать дорожку и кружок: справа включено, слева выключено."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(ACCENT if self.isChecked() else OUTLINE))
        painter.drawRoundedRect(self.rect(), 10, 10)
        left = self.width() - 18 if self.isChecked() else 2
        painter.setBrush(QColor(KNOB))
        painter.drawEllipse(left, 2, 16, 16)
        painter.end()


class CheckRow(QAbstractButton):
    """Строка с галочкой: квадратик, название и число справа.

    Используется в списке тем на странице генератора.
    """

    HEIGHT = 34

    def __init__(self, title: str, count: int, parent=None):
        """Создать отмеченную строку с названием и числом."""
        super().__init__(parent)
        self._title = title
        self._count = count
        self._mark = make_pixmap("check", ACCENT_TEXT, 14)
        self.setCheckable(True)
        self.setChecked(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(self.HEIGHT)

    def sizeHint(self) -> QSize:
        """Желаемый размер строки; по ширине она растягивается сама."""
        return QSize(200, self.HEIGHT)

    def paintEvent(self, event: QPaintEvent | None) -> None:
        """Нарисовать квадратик с галочкой, название и число."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        box = QRect(10, (self.height() - 16) // 2, 16, 16)
        if self.isChecked():
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(ACCENT))
            painter.drawRoundedRect(box, 4, 4)
            painter.drawPixmap(box.left() + 1, box.top() + 1, self._mark)
        else:
            painter.setPen(QColor(OUTLINE))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(box, 4, 4)
        center = Qt.AlignmentFlag.AlignVCenter
        area = self.rect().adjusted(40, 0, -48, 0)
        painter.setPen(QColor(TEXT))
        painter.setFont(QFont(FONT, 10))
        title = painter.fontMetrics().elidedText(
            self._title,
            Qt.TextElideMode.ElideRight,
            area.width(),
        )
        painter.drawText(area, Qt.AlignmentFlag.AlignLeft | center, title)
        area = self.rect().adjusted(0, 0, -10, 0)
        painter.setPen(QColor(MUTED))
        painter.setFont(QFont(MONO, 9))
        count = str(self._count)
        painter.drawText(area, Qt.AlignmentFlag.AlignRight | center, count)
        painter.end()


def paint_level_bars(
    painter: QPainter,
    left: int,
    bottom: int,
    level: int,
) -> None:
    """Нарисовать три столбика сложности от левого нижнего угла.

    Закрашено столько столбиков, каков уровень: 1 лёгкий, 2 средний,
    3 сложный.
    """
    painter.setPen(Qt.PenStyle.NoPen)
    for step in range(3):  # столбики высотой 8, 12 и 16 точек
        height = 8 + 4 * step
        lit = step < level  # закрашен ли столбик
        painter.setBrush(QColor(ACCENT if lit else BAR_OFF))
        bar = QRect(left + step * 5, bottom - height, 3, height)
        painter.drawRoundedRect(bar, 1, 1)


class LevelBars(QWidget):
    """Значок сложности из трёх столбиков для строки формы."""

    def __init__(self, level: int, parent=None):
        """Запомнить уровень сложности: 1, 2 или 3."""
        super().__init__(parent)
        self._level = level
        self.setFixedSize(16, 16)

    def paintEvent(self, event: QPaintEvent | None) -> None:
        """Нарисовать столбики во весь значок."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        paint_level_bars(painter, 1, self.height(), self._level)
        painter.end()


def clear_layout(layout: QLayout) -> None:
    """Убрать из раскладки все элементы."""
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget() if item is not None else None
        if widget is not None:
            widget.hide()  # убрать с экрана сразу
            widget.deleteLater()  # а удалить, когда Qt освободится


def plural(number: int, one: str, few: str, many: str) -> str:
    """Число вместе со словом в нужной форме.

    Пример: 1 вопрос, 3 вопроса, 5 вопросов, 11 вопросов, 21 вопрос.
    """
    tail = number % 100
    if 11 <= tail <= 14:
        word = many
    elif number % 10 == 1:
        word = one
    elif 2 <= number % 10 <= 4:
        word = few
    else:
        word = many
    return f"{number} {word}"


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


def ask_save_file(parent: QWidget, title: str, name: str, kinds: str) -> str:
    """Спросить, куда сохранить файл; '' значит, что нажата «Отмена».

    Окно открывается в папке «Документы» с предложенным именем файла.
    Виды файлов записаны так: «Документ Word (*.docx);;Текст (*.txt)».
    """
    place = QStandardPaths.StandardLocation.DocumentsLocation
    folder = Path(QStandardPaths.writableLocation(place))
    path, _ = QFileDialog.getSaveFileName(
        parent,
        title,
        str(folder / name),
        kinds,
    )
    return path


def ask_open_file(parent: QWidget, title: str, kinds: str) -> str:
    """Спросить, какой файл открыть; '' значит, что нажата «Отмена»."""
    place = QStandardPaths.StandardLocation.DocumentsLocation
    folder = QStandardPaths.writableLocation(place)
    path, _ = QFileDialog.getOpenFileName(parent, title, folder, kinds)
    return path
