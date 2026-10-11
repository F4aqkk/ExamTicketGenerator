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

from app.models.generation import Generation
from app.services.export_service import ExportService
from app.services.generation_service import GenerationService
from app.services.import_service import ImportService
from app.services.question_service import QuestionService
from app.services.settings_service import SettingsService
from app.ui.bank_page import BankPage
from app.ui.generator_page import GeneratorPage
from app.ui.history_page import HistoryPage
from app.ui.icons import make_icon
from app.ui.settings_page import SettingsPage
from app.ui.theme import ACCENT, MUTED, ONLINE

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

    def choose(self, section: int) -> None:
        """Отметить в меню раздел с этим номером."""
        self._buttons[section].setChecked(True)

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

    def __init__(
        self,
        session: Session,
        settings: SettingsService | None = None,
    ):
        """Собрать окно: меню, страницы и связи между ними.

        Сервис настроек можно передать свой (так делают тесты);
        иначе настройки читаются из файла рядом с базой.
        """
        super().__init__()
        self.setWindowTitle("ExamTicket — генератор экзаменационных билетов")
        self.resize(1280, 800)
        self.setMinimumSize(1024, 640)
        self._questions = QuestionService(session)
        self._generations = GenerationService(session)
        self._settings = settings or SettingsService()
        self._exporter = ExportService(session, self._settings)
        self._importer = ImportService(session)

        self._sidebar = Sidebar()
        self._bank_page = BankPage(
            self._questions,
            self._exporter,
            self._importer,
        )
        self._generator_page = GeneratorPage(
            self._generations,
            self._questions,
            self._settings,
            self._exporter,
        )
        self._history_page = HistoryPage(self._generations)
        self._settings_page = SettingsPage(self._settings)
        self._pages = QStackedWidget()  # показывает одну страницу из стопки
        self._pages.addWidget(self._bank_page)
        self._pages.addWidget(self._generator_page)
        self._pages.addWidget(self._history_page)
        self._pages.addWidget(self._settings_page)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._sidebar)
        layout.addWidget(self._pages, 1)
        self.setCentralWidget(central)

        self._sidebar.section_chosen.connect(self._show_section)
        self._bank_page.bank_changed.connect(self._update_counts)
        self._generator_page.generated.connect(self._on_generated)
        self._history_page.open_requested.connect(self._open_generation)
        self._history_page.export_requested.connect(self._export_generation)
        self._history_page.deleted.connect(self._on_deleted)
        self._settings_page.backup_requested.connect(
            self._bank_page.export_bank,
        )
        self._settings_page.restore_requested.connect(
            self._bank_page.import_bank,
        )
        self._settings_page.settings_changed.connect(
            self._generator_page.apply_settings,
        )
        self._update_counts()

    def _show_section(self, section: int) -> None:
        """Открыть раздел с этим номером."""
        if section == GENERATOR:
            # Пока работали в банке, темы и их вопросы могли измениться.
            self._generator_page.reload_topics()
        self._pages.setCurrentIndex(section)

    def _on_generated(self) -> None:
        """Составлены новые билеты: обновить историю и счётчики."""
        self._history_page.reload()
        self._update_counts()

    def _open_generation(self, generation: Generation) -> None:
        """В истории нажали «Открыть»: показать билеты в генераторе."""
        self._generator_page.show_generation(generation)
        self._sidebar.choose(GENERATOR)
        self._show_section(GENERATOR)

    def _export_generation(self, generation: Generation) -> None:
        """В истории нажали экспорт: сохранить билеты в файл.

        Формат берётся из настроек, билеты сохраняются без ответов.
        """
        self._generator_page.export_generation(
            generation,
            self._settings.settings.export_format,
        )

    def _on_deleted(self, generation_id: int) -> None:
        """В истории удалили генерацию: убрать её из предпросмотра."""
        self._generator_page.close_generation(generation_id)
        self._update_counts()

    def _update_counts(self) -> None:
        """Обновить счётчики в боковом меню."""
        self._sidebar.set_count(BANK, self._questions.count())
        self._sidebar.set_count(HISTORY, self._generations.count())
