"""Главное окно: боковое меню слева и страницы разделов справа."""

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session

from app.services.generation_service import GenerationService
from app.services.question_service import QuestionService
from app.ui.bank_page import BankPage
from app.ui.icons import make_icon
from app.ui.theme import ACCENT, MUTED, ONLINE
from app.ui.widgets import PlaceholderPage

# Разделы программы: название и иконка. Порядок как в боковом меню.
SECTIONS = [
    ("Банк вопросов", "bank"),
    ("Генератор", "generator"),
    ("История", "history"),
    ("Настройки", "settings"),
]
BANK, GENERATOR, HISTORY, SETTINGS = range(4)
SIDEBAR_WIDTH = 220


class NavButton(QPushButton):
    """Пункт бокового меню: иконка, название и счётчик справа."""

    def __init__(self, title: str, icon_name: str, parent=None):
        """Создать пункт меню; пока он не выбран, иконка серая."""
        super().__init__("  " + title, parent)
        self.setObjectName("nav")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setIconSize(QSize(16, 16))
        self._icon_off = make_icon(icon_name, MUTED)
        self._icon_on = make_icon(icon_name, ACCENT)
        self.setIcon(self._icon_off)
        self.toggled.connect(self._on_toggled)
        self._badge = QLabel()
        self._badge.setObjectName("navBadge")
        # Щелчок по счётчику должен попадать в сам пункт меню.
        self._badge.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 12, 0)
        layout.addStretch()
        layout.addWidget(self._badge)

    def set_count(self, count: int) -> None:
        """Показать число записей справа от названия."""
        self._badge.setText(str(count))

    def _on_toggled(self, checked: bool) -> None:
        """У выбранного пункта иконка акцентного цвета."""
        self.setIcon(self._icon_on if checked else self._icon_off)


class Sidebar(QFrame):
    """Боковое меню: логотип, разделы и строка статуса."""

    section_chosen = pyqtSignal(int)  # сигнал: номер выбранного раздела

    def __init__(self, parent=None):
        """Собрать меню сверху вниз."""
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(SIDEBAR_WIDTH)
        self._group = QButtonGroup(self)  # выбран всегда один пункт
        self._buttons: list[NavButton] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 14)
        layout.setSpacing(4)
        layout.addLayout(self._build_logo())
        layout.addSpacing(18)
        for index, (title, icon_name) in enumerate(SECTIONS):
            button = NavButton(title, icon_name)
            self._group.addButton(button, index)
            self._buttons.append(button)
            layout.addWidget(button)
        layout.addStretch()
        layout.addWidget(self._build_status())
        self._buttons[BANK].setChecked(True)
        self._group.idClicked.connect(self.section_chosen)

    def set_count(self, section: int, count: int) -> None:
        """Обновить счётчик у раздела с этим номером."""
        self._buttons[section].set_count(count)

    @staticmethod
    def _build_logo() -> QHBoxLayout:
        """Логотип: жёлтый квадрат со знаком № и название программы."""
        mark = QLabel("№")
        mark.setObjectName("logoMark")
        mark.setFixedSize(32, 32)
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("ExamTicket")
        title.setObjectName("logoTitle")
        hint = QLabel("генератор билетов")
        hint.setObjectName("logoHint")
        names = QVBoxLayout()
        names.setSpacing(0)
        names.addWidget(title)
        names.addWidget(hint)
        logo = QHBoxLayout()
        logo.setContentsMargins(4, 0, 0, 0)
        logo.setSpacing(10)
        logo.addWidget(mark)
        logo.addLayout(names)
        logo.addStretch()
        return logo

    @staticmethod
    def _build_status() -> QLabel:
        """Строка внизу меню: программа работает без сети."""
        status = QLabel(
            f'<span style="color: {ONLINE};">●</span>'
            " офлайн · данные локально<br>v1.0 · Windows 10/11"
        )
        status.setObjectName("statusLine")
        status.setTextFormat(Qt.TextFormat.RichText)
        status.setContentsMargins(4, 0, 0, 0)
        return status


class MainWindow(QMainWindow):
    """Главное окно программы.

    Окно создаёт сервисы и передаёт их страницам. Сами страницы
    с базой не работают: они только вызывают сервисы.
    """

    def __init__(self, session: Session):
        """Собрать окно: меню, страницы и связи между ними."""
        super().__init__()
        self.setWindowTitle("ExamTicket — генератор экзаменационных билетов")
        self.resize(1280, 800)
        self.setMinimumSize(1024, 640)
        self._questions = QuestionService(session)
        self._generations = GenerationService(session)

        self._sidebar = Sidebar()
        self._bank_page = BankPage(self._questions)
        self._pages = QStackedWidget()  # показывает одну страницу из стопки
        self._pages.addWidget(self._bank_page)
        self._pages.addWidget(PlaceholderPage("Генератор билетов"))
        self._pages.addWidget(PlaceholderPage("История"))
        self._pages.addWidget(PlaceholderPage("Настройки"))

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._sidebar)
        layout.addWidget(self._pages, 1)
        self.setCentralWidget(central)

        self._sidebar.section_chosen.connect(self._pages.setCurrentIndex)
        self._bank_page.bank_changed.connect(self._update_counts)
        self._update_counts()

    def _update_counts(self) -> None:
        """Обновить счётчики в боковом меню."""
        self._sidebar.set_count(BANK, self._questions.count())
        self._sidebar.set_count(HISTORY, self._generations.count())
