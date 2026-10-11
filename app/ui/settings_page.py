"""Страница «Настройки»: шапка документа, экспорт, интерфейс, данные."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.services.settings_service import EXPORT_FORMATS, SettingsService
from app.ui.icons import make_icon, make_pixmap
from app.ui.theme import ONLINE, TEXT
from app.ui.widgets import SegmentedControl, make_caption

TITLE_WIDTH = 230  # ширина столбика с названием раздела
FIELDS_WIDTH = 580  # шире поля настроек не растягиваются
SCALES = (100, 125, 150, 175)  # масштабы Windows, которые нужны по ТЗ


class SettingsPage(QWidget):
    """Страница настроек.

    Изменения записываются сразу, кнопки «Сохранить» нет. Сами
    настройки хранит и записывает в файл сервис настроек.
    """

    settings_changed = pyqtSignal()  # сигнал: настройки изменились
    backup_requested = pyqtSignal()  # сигнал: сохранить копию банка
    restore_requested = pyqtSignal()  # сигнал: восстановить банк из копии

    def __init__(self, service: SettingsService, parent=None):
        """Собрать страницу и показать текущие настройки."""
        super().__init__(parent)
        self._service = service
        sections = QWidget()
        sections_layout = QVBoxLayout(sections)
        sections_layout.setContentsMargins(32, 0, 28, 24)
        sections_layout.setSpacing(0)
        sections_layout.addWidget(self._build_header_section())
        sections_layout.addWidget(self._build_export_section())
        sections_layout.addWidget(self._build_interface_section())
        sections_layout.addWidget(self._build_data_section())
        sections_layout.addStretch()
        scroll = QScrollArea()  # разделы прокручиваются в невысоком окне
        scroll.setWidgetResizable(True)
        scroll.setWidget(sections)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_header())
        layout.addWidget(scroll, 1)
        self._show_settings()

    @staticmethod
    def current_scale() -> int:
        """Масштаб экрана в процентах: ближайший из тех, что есть на макете."""
        screen = QGuiApplication.primaryScreen()
        ratio = screen.devicePixelRatio() if screen is not None else 1.0
        return min(SCALES, key=lambda scale: abs(scale - ratio * 100))

    def _show_settings(self) -> None:
        """Заполнить поля сохранёнными настройками."""
        settings = self._service.settings
        self._organization.setText(settings.organization)
        self._discipline.setText(settings.discipline)
        self._teacher.setText(settings.teacher)
        self._format.set_value(settings.export_format)

    def _save(self) -> None:
        """Поле изменили: записать настройки и сообщить об этом."""
        self._service.update(
            organization=self._organization.text(),
            discipline=self._discipline.text(),
            teacher=self._teacher.text(),
            export_format=self._format.value(),
        )
        self.settings_changed.emit()

    @staticmethod
    def _build_header() -> QFrame:
        """Заголовок страницы."""
        title = QLabel("Настройки")
        title.setObjectName("pageTitle")
        hint = QLabel("применяются сразу")
        hint.setObjectName("pageHint")
        header = QFrame()
        header.setObjectName("pageHeader")
        layout = QVBoxLayout(header)
        layout.setContentsMargins(32, 24, 28, 20)
        layout.setSpacing(4)
        layout.addWidget(title)
        layout.addWidget(hint)
        return header

    @staticmethod
    def _build_section(title: str, hint: str, fields: QVBoxLayout) -> QFrame:
        """Раздел настроек: слева название и пояснение, справа поля."""
        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        hint_label = QLabel(hint)
        hint_label.setObjectName("sectionHint")
        hint_label.setWordWrap(True)
        names_box = QWidget()
        names_box.setFixedWidth(TITLE_WIDTH)
        names = QVBoxLayout(names_box)
        names.setContentsMargins(0, 0, 24, 0)
        names.setSpacing(6)
        names.addWidget(title_label)
        names.addWidget(hint_label)
        names.addStretch()
        fields_box = QWidget()
        fields_box.setMaximumWidth(FIELDS_WIDTH)
        fields_box.setLayout(fields)
        fields.setContentsMargins(0, 0, 0, 0)
        section = QFrame()
        section.setObjectName("section")
        layout = QHBoxLayout(section)
        layout.setContentsMargins(0, 28, 0, 28)
        layout.setSpacing(0)
        layout.addWidget(names_box)
        layout.addWidget(fields_box, 1)
        layout.addStretch()
        return section

    def _make_field(self) -> QLineEdit:
        """Поле ввода, которое записывает настройки после изменения."""
        field = QLineEdit()
        field.editingFinished.connect(self._save)
        return field

    def _build_header_section(self) -> QFrame:
        """Раздел «Шапка документа»: организация, дисциплина, преподаватель."""
        self._organization = self._make_field()
        self._discipline = self._make_field()
        self._teacher = self._make_field()
        discipline = QVBoxLayout()
        discipline.setSpacing(8)
        discipline.addWidget(make_caption("Дисциплина"))
        discipline.addWidget(self._discipline)
        teacher = QVBoxLayout()
        teacher.setSpacing(8)
        teacher.addWidget(make_caption("Преподаватель"))
        teacher.addWidget(self._teacher)
        pair = QHBoxLayout()
        pair.setSpacing(12)
        pair.addLayout(discipline, 1)
        pair.addLayout(teacher, 1)
        fields = QVBoxLayout()
        fields.setSpacing(8)
        fields.addWidget(make_caption("Образовательная организация"))
        fields.addWidget(self._organization)
        fields.addSpacing(8)
        fields.addLayout(pair)
        return self._build_section(
            "Шапка документа",
            "Эти данные печатаются в каждом билете.",
            fields,
        )

    def _build_export_section(self) -> QFrame:
        """Раздел «Экспорт»: формат, выбранный в генераторе по умолчанию."""
        options = [(name, name) for name in EXPORT_FORMATS]
        self._format = SegmentedControl(options)
        self._format.changed.connect(self._save)
        note = QLabel(
            "Кириллица и спецсимволы сохраняются корректно. "
            "Дата в формате ДД.ММ.ГГГГ."
        )
        note.setObjectName("sectionHint")
        note.setWordWrap(True)
        fields = QVBoxLayout()
        fields.setSpacing(12)
        fields.addWidget(self._format, 0, Qt.AlignmentFlag.AlignLeft)
        fields.addWidget(note)
        return self._build_section(
            "Экспорт",
            "Формат, который подсвечивается в генераторе по умолчанию.",
            fields,
        )

    def _build_interface_section(self) -> QFrame:
        """Раздел «Интерфейс»: язык и масштаб; оба только показываются."""
        language = QLineEdit("Русский")
        language.setEnabled(False)
        language.setFixedWidth(190)
        options = [(f"{scale}%", scale) for scale in SCALES]
        scale = SegmentedControl(options)
        scale.set_value(self.current_scale())
        scale.setEnabled(False)
        fields = QVBoxLayout()
        fields.setSpacing(8)
        fields.addWidget(make_caption("Язык"))
        fields.addWidget(language)
        fields.addSpacing(8)
        fields.addWidget(make_caption("Масштаб"))
        fields.addWidget(scale, 0, Qt.AlignmentFlag.AlignLeft)
        return self._build_section(
            "Интерфейс",
            "Язык фиксирован. Масштаб повторяет настройки Windows.",
            fields,
        )

    def _build_data_section(self) -> QFrame:
        """Раздел «Данные»: пояснение и кнопки резервной копии."""
        lock = QLabel()
        lock.setPixmap(make_pixmap("lock", ONLINE, 16))
        text = QLabel(
            "Офлайн-режим, один пользователь. Рекомендуем периодически "
            "делать резервную копию банка вопросов."
        )
        text.setWordWrap(True)
        card = QFrame()
        card.setObjectName("infoCard")
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(12)
        card_layout.addWidget(lock, 0, Qt.AlignmentFlag.AlignTop)
        card_layout.addWidget(text, 1)
        save_button = QPushButton(" Сохранить копию")
        save_button.setIcon(make_icon("export", TEXT))
        restore_button = QPushButton(" Восстановить")
        restore_button.setIcon(make_icon("import", TEXT))
        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        # Копию сохраняет и читает страница банка: это тот же экспорт
        # и импорт вопросов. Страница настроек только просит об этом.
        save_button.clicked.connect(self.backup_requested)
        restore_button.clicked.connect(self.restore_requested)
        for button in (save_button, restore_button):
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            buttons.addWidget(button)
        buttons.addStretch()
        fields = QVBoxLayout()
        fields.setSpacing(12)
        fields.addWidget(card)
        fields.addLayout(buttons)
        return self._build_section(
            "Данные",
            "Всё хранится на этом компьютере. Сервер и сеть не используются.",
            fields,
        )
