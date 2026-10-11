"""Страница «Генератор билетов»: правила выборки и предпросмотр."""

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractButton,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.models.generation import Generation
from app.services.documents import DocumentError, safe_file_name
from app.services.export_service import ExportService
from app.services.generation_service import (
    MAX_TICKETS,
    GenerationError,
    GenerationService,
)
from app.services.question_service import QuestionService
from app.services.settings_service import EXPORT_FORMATS, SettingsService
from app.ui.icons import make_icon
from app.ui.theme import ACCENT_TEXT, MUTED
from app.ui.ticket_sheet import TicketSheet
from app.ui.widgets import (
    CheckRow,
    LevelBars,
    Stepper,
    ToggleSwitch,
    ask_save_file,
    clear_layout,
    make_caption,
    show_message,
)

PANEL_WIDTH = 360  # ширина левой панели с правилами
MAX_PER_LEVEL = 20  # больше вопросов одной сложности счётчик не даст
START_TICKETS = 30  # числа при открытии страницы: контрольный
START_PER_LEVEL = 5  # сценарий из ТЗ, 30 билетов по 15 вопросов
LEVELS = [("Лёгкие", 1), ("Средние", 2), ("Сложные", 3)]
PAGE_BUTTONS = 12  # столько кнопок с номерами билетов видно внизу
NO_PAGES = "– / –"  # надпись между стрелками, пока билетов нет
EMPTY_TEXT = (
    "Задайте правила слева и нажмите «Сформировать билеты».\n"
    "Здесь появится предпросмотр."
)


class GeneratorPage(QWidget):
    """Страница генератора билетов.

    Слева задаются правила выборки, справа показывается предпросмотр
    билетов. Страница сама в базу не ходит: билеты составляет
    и сохраняет сервис генерации.
    """

    generated = pyqtSignal()  # сигнал: составлена новая генерация

    def __init__(
        self,
        generations: GenerationService,
        questions: QuestionService,
        settings: SettingsService,
        exporter: ExportService,
        parent=None,
    ):
        """Собрать страницу и показать темы из банка вопросов."""
        super().__init__(parent)
        self._service = generations
        self._questions = questions
        self._settings = settings
        self._exporter = exporter
        self._generation: Generation | None = None  # что в предпросмотре
        self._generation_id: int | None = None  # и её номер в базе
        self._page = 0  # номер показанного билета, счёт с нуля
        self._topic_rows: dict[int, CheckRow] = {}  # номер темы -> строка
        self._levels: dict[int, Stepper] = {}  # сложность -> счётчик
        body = QHBoxLayout()
        body.setSpacing(0)
        body.addWidget(self._build_panel())
        body.addLayout(self._build_preview(), 1)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_header())
        layout.addLayout(body, 1)
        self._set_preview_enabled(False)
        self.reload_topics()

    # ----- что страница умеет сообщить о форме -----

    def work_title(self) -> str:
        """Название работы без пробелов по краям."""
        return self._title.text().strip()

    def tickets_count(self) -> int:
        """Сколько билетов нужно составить."""
        return self._tickets.value()

    def counts(self) -> dict[int, int]:
        """Состав билета: сложность -> сколько таких вопросов в билете."""
        result = {}
        for level, stepper in self._levels.items():
            result[level] = stepper.value()
        return result

    def chosen_topic_ids(self) -> list[int]:
        """Номера отмеченных тем.

        Пустой список значит, что не отмечена ни одна тема.
        """
        chosen = []
        for topic_id, row in self._topic_rows.items():
            if row.isChecked():
                chosen.append(topic_id)
        return chosen

    def set_summary(self, text: str, warning: str = "") -> None:
        """Показать над кнопкой строку итога и предупреждение под ней."""
        self._summary.setText(text)
        self._warning.setText(warning)
        self._warning.setVisible(bool(warning))

    # ----- правила страницы: итог под формой и составление билетов -----

    def _update_summary(self) -> None:
        """Обновить строку «В выбранных темах … вопросов, требуется …».

        Вызывается при каждом изменении формы.
        """
        topic_ids = self.chosen_topic_ids()
        if not topic_ids:
            self.set_summary("Выберите хотя бы одну тему.")
            return
        available = self._service.available(topic_ids)
        have = sum(available.values())
        per_ticket = sum(self.counts().values())
        need = self.tickets_count() * per_ticket
        text = f"В выбранных темах {have} вопросов, требуется {need}."
        if have < need:
            warning = "Часть вопросов повторится между билетами."
            self.set_summary(text, warning)
        else:
            self.set_summary(text)

    def _generate(self) -> Generation | None:
        """Проверить правила и составить билеты.

        Возвращает сохранённую генерацию. Если составить билеты
        нельзя, показывает причину и ничего не возвращает.
        """
        try:
            return self._service.generate(
                self.work_title(),
                self.tickets_count(),
                self.counts(),
                self.chosen_topic_ids(),
                no_repeat=self._no_repeat.isChecked(),
                mix_topics=self._mix_topics.isChecked(),
            )
        except GenerationError as error:
            show_message(self, "Билеты не составлены", str(error))
            return None

    # ----- предпросмотр -----

    def show_generation(self, generation: Generation) -> None:
        """Показать билеты генерации в предпросмотре, начиная с первого."""
        self._generation = generation
        self._generation_id = generation.id
        self._set_preview_enabled(True)
        self._stack.setCurrentWidget(self._scroll)
        self._show_page(0)

    def close_generation(self, generation_id: int) -> None:
        """Убрать генерацию из предпросмотра, если показана именно она.

        Нужно, когда генерацию удалили на странице истории.
        """
        if self._generation_id != generation_id:
            return
        self._generation = None
        self._generation_id = None
        self._page = 0
        self._counter.setText(NO_PAGES)
        self._fill_page_buttons(0)
        self._set_preview_enabled(False)
        self._stack.setCurrentWidget(self._empty)

    def apply_settings(self) -> None:
        """Настройки изменились: обновить формат и шапку листа."""
        for button in self._formats.buttons():
            if button.text() == self._settings.settings.export_format:
                button.setChecked(True)
        self._show_page(self._page)

    def reload_topics(self) -> None:
        """Заново прочитать темы из банка; снятые отметки сохраняются."""
        unchecked = {
            topic_id
            for topic_id, row in self._topic_rows.items()
            if not row.isChecked()
        }
        clear_layout(self._topics_layout)
        self._topic_rows = {}
        for topic in self._questions.get_topics():
            row = CheckRow(topic.name, len(topic.questions))
            row.setChecked(topic.id not in unchecked)
            row.toggled.connect(self._on_form_changed)
            self._topics_layout.addWidget(row)
            self._topic_rows[topic.id] = row
        self._no_topics.setVisible(not self._topic_rows)
        self._on_form_changed()

    def _show_page(self, page: int) -> None:
        """Показать билет с этим номером (счёт с нуля)."""
        if self._generation is None:
            return
        tickets = self._generation.tickets
        self._page = max(0, min(page, len(tickets) - 1))
        settings = self._settings.settings
        discipline = ""
        if settings.discipline:
            discipline = f"Дисциплина: {settings.discipline}"
        self._sheet.show_ticket(
            tickets[self._page],
            self._generation.title,
            settings.organization,
            discipline,
        )
        self._counter.setText(f"{self._page + 1} / {len(tickets)}")
        self._previous.setEnabled(self._page > 0)
        self._next.setEnabled(self._page < len(tickets) - 1)
        self._fill_page_buttons(len(tickets))
        bar = self._scroll.verticalScrollBar()
        if bar is not None:
            bar.setValue(0)  # новый билет читаем с начала листа

    def _show_previous(self) -> None:
        """Стрелка влево: предыдущий билет."""
        self._show_page(self._page - 1)

    def _show_next(self) -> None:
        """Стрелка вправо: следующий билет."""
        self._show_page(self._page + 1)

    def _fill_page_buttons(self, total: int) -> None:
        """Кнопки с номерами билетов внизу.

        Все сто кнопок в ряд не поместятся, поэтому видна только
        часть ряда вокруг показанного билета.
        """
        for button in self._page_group.buttons():
            self._page_group.removeButton(button)
        clear_layout(self._pages_layout)
        first = min(self._page - PAGE_BUTTONS // 2, total - PAGE_BUTTONS)
        first = max(first, 0)
        for page in range(first, min(first + PAGE_BUTTONS, total)):
            button = QPushButton(str(page + 1))
            button.setObjectName("pageButton")
            button.setCheckable(True)
            button.setChecked(page == self._page)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            self._page_group.addButton(button, page)
            self._pages_layout.addWidget(button)
        self._pages_layout.addStretch()

    def _set_preview_enabled(self, enabled: bool) -> None:
        """Включить или выключить стрелки и кнопки экспорта."""
        self._previous.setEnabled(enabled)
        self._next.setEnabled(enabled)
        self._with_answers.setEnabled(enabled)
        for button in self._formats.buttons():
            button.setEnabled(enabled)

    # ----- действия пользователя -----

    def _on_form_changed(self) -> None:
        """Форма изменилась: пересчитать подписи под ней."""
        per_ticket = sum(self.counts().values())
        self._per_ticket.setText(f"вопросов в билете: {per_ticket}")
        self._update_summary()

    def _on_generate(self) -> None:
        """Нажали «Сформировать билеты»."""
        generation = self._generate()
        if generation is not None:
            self.show_generation(generation)
            self.generated.emit()

    def _export(self, button: QAbstractButton) -> None:
        """Нажали кнопку формата: сохранить показанные билеты в файл."""
        if self._generation is None:
            return
        self.export_generation(
            self._generation,
            button.text(),
            self._with_answers.isChecked(),
        )

    def export_generation(
        self,
        generation: Generation,
        format_name: str,
        with_answers: bool = False,
    ) -> None:
        """Спросить имя файла и сохранить в него билеты генерации.

        Без отдельной просьбы билеты сохраняются без ответов.
        """
        extension = format_name.lower()
        name = f"{safe_file_name(generation.title)}.{extension}"
        kinds = f"Файл {format_name} (*.{extension})"
        path = ask_save_file(self, "Экспорт билетов", name, kinds)
        if not path:
            return
        try:
            self._exporter.export_tickets(generation, path, with_answers)
        except DocumentError as error:
            show_message(self, "Экспорт не выполнен", str(error))
            return
        show_message(self, "Экспорт билетов", f"Билеты сохранены:\n{path}")

    # ----- сборка страницы -----

    @staticmethod
    def _build_header() -> QFrame:
        """Заголовок страницы и подсказка о порядке работы."""
        title = QLabel("Генератор билетов")
        title.setObjectName("pageTitle")
        hint = QLabel("правила выборки → предпросмотр → экспорт")
        hint.setObjectName("pageHint")
        header = QFrame()
        header.setObjectName("pageHeader")
        layout = QVBoxLayout(header)
        layout.setContentsMargins(32, 24, 28, 20)
        layout.setSpacing(4)
        layout.addWidget(title)
        layout.addWidget(hint)
        return header

    def _build_panel(self) -> QFrame:
        """Левая панель: правила сверху, итог и главная кнопка снизу."""
        self._title = QLineEdit()
        self._title.setPlaceholderText("Например: Промежуточная аттестация")
        self._topics_layout = QVBoxLayout()  # сюда кладутся строки тем
        self._topics_layout.setSpacing(2)
        self._no_topics = QLabel("В банке вопросов пока нет тем.")
        self._no_topics.setObjectName("switchHint")
        self._no_repeat = ToggleSwitch()
        self._no_repeat.toggled.connect(self._on_form_changed)
        self._mix_topics = ToggleSwitch()
        self._mix_topics.toggled.connect(self._on_form_changed)

        form = QWidget()
        layout = QVBoxLayout(form)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(8)
        layout.addWidget(make_caption("Название работы"))
        layout.addWidget(self._title)
        layout.addSpacing(10)
        layout.addLayout(self._build_tickets_row())
        layout.addSpacing(10)
        layout.addLayout(self._build_levels_caption())
        layout.addWidget(self._build_levels())
        layout.addSpacing(10)
        layout.addWidget(make_caption("Темы"))
        layout.addLayout(self._topics_layout)
        layout.addWidget(self._no_topics)
        layout.addSpacing(6)
        layout.addLayout(
            self._build_switch(
                self._no_repeat,
                "Не повторять вопросы",
                "Пока в банке есть неиспользованные",
            )
        )
        layout.addLayout(
            self._build_switch(
                self._mix_topics,
                "Разные темы в билете",
                "Когда позволяет банк",
            )
        )
        layout.addStretch()

        scroll = QScrollArea()  # правила прокручиваются в невысоком окне
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        scroll.setWidget(form)
        panel = QFrame()
        panel.setObjectName("generatorPanel")
        panel.setFixedWidth(PANEL_WIDTH)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 1, 0)
        panel_layout.setSpacing(0)
        panel_layout.addWidget(scroll, 1)
        panel_layout.addWidget(self._build_footer())
        return panel

    def _build_tickets_row(self) -> QHBoxLayout:
        """Строка «Количество билетов» со счётчиком."""
        self._tickets = Stepper(START_TICKETS, 1, MAX_TICKETS)
        self._tickets.changed.connect(self._on_form_changed)
        row = QHBoxLayout()
        row.addWidget(make_caption("Количество билетов"))
        row.addStretch()
        row.addWidget(self._tickets)
        return row

    def _build_levels_caption(self) -> QHBoxLayout:
        """Подпись «Состав билета» и число вопросов в билете справа."""
        self._per_ticket = QLabel()
        self._per_ticket.setObjectName("hint")
        row = QHBoxLayout()
        row.addWidget(make_caption("Состав билета"))
        row.addStretch()
        row.addWidget(self._per_ticket)
        return row

    def _build_levels(self) -> QFrame:
        """Рамка с тремя строками: лёгкие, средние и сложные вопросы."""
        frame = QFrame()
        frame.setObjectName("levels")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        for title, level in LEVELS:
            stepper = Stepper(START_PER_LEVEL, 0, MAX_PER_LEVEL)
            stepper.changed.connect(self._on_form_changed)
            self._levels[level] = stepper
            row = QFrame()
            if level != LEVELS[0][1]:  # над первой строкой линии нет
                row.setObjectName("levelRow")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(14, 8, 10, 8)
            row_layout.setSpacing(12)
            row_layout.addWidget(LevelBars(level))
            row_layout.addWidget(QLabel(title))
            row_layout.addStretch()
            row_layout.addWidget(stepper)
            layout.addWidget(row)
        return frame

    @staticmethod
    def _build_switch(
        switch: ToggleSwitch,
        title: str,
        hint: str,
    ) -> QHBoxLayout:
        """Переключатель с названием и пояснением под ним."""
        title_label = QLabel(title)
        title_label.setObjectName("switchTitle")
        hint_label = QLabel(hint)
        hint_label.setObjectName("switchHint")
        texts = QVBoxLayout()
        texts.setSpacing(0)
        texts.addWidget(title_label)
        texts.addWidget(hint_label)
        row = QHBoxLayout()
        row.setContentsMargins(0, 4, 0, 4)
        row.setSpacing(12)
        row.addWidget(switch, 0, Qt.AlignmentFlag.AlignTop)
        row.addLayout(texts)
        row.addStretch()
        return row

    def _build_footer(self) -> QFrame:
        """Низ панели: строка итога, предупреждение и главная кнопка."""
        self._summary = QLabel()
        self._summary.setObjectName("summary")
        self._summary.setWordWrap(True)
        self._warning = QLabel()
        self._warning.setObjectName("warning")
        self._warning.setWordWrap(True)
        button = QPushButton(
            make_icon("spark", ACCENT_TEXT),
            " Сформировать билеты",
        )
        button.setObjectName("primary")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setMinimumHeight(40)
        button.clicked.connect(self._on_generate)
        footer = QFrame()
        footer.setObjectName("panelFooter")
        layout = QVBoxLayout(footer)
        layout.setContentsMargins(24, 14, 24, 20)
        layout.setSpacing(6)
        layout.addWidget(self._summary)
        layout.addWidget(self._warning)
        layout.addSpacing(6)
        layout.addWidget(button)
        return footer

    def _build_preview(self) -> QVBoxLayout:
        """Правая часть: строка листания, лист билета, номера билетов."""
        self._sheet = TicketSheet()
        canvas = QWidget()  # тёмный фон, на котором лежит лист
        canvas.setObjectName("previewCanvas")
        canvas.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        canvas_layout = QVBoxLayout(canvas)
        canvas_layout.setContentsMargins(24, 24, 24, 24)
        canvas_layout.addWidget(self._sheet)  # лист встаёт по центру
        canvas_layout.addStretch()
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self._scroll.setWidget(canvas)
        self._empty = QLabel(EMPTY_TEXT)
        self._empty.setObjectName("emptyLabel")
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._stack = QStackedWidget()  # подсказка или лист билета
        self._stack.addWidget(self._empty)
        self._stack.addWidget(self._scroll)
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.addWidget(self._build_preview_bar())
        layout.addWidget(self._stack, 1)
        layout.addWidget(self._build_pages_bar())
        return layout

    def _build_preview_bar(self) -> QFrame:
        """Строка над листом: стрелки, «1 / 30» и кнопки форматов."""
        self._previous = self._make_arrow("arrow_left", "Предыдущий билет")
        self._previous.clicked.connect(self._show_previous)
        self._next = self._make_arrow("arrow_right", "Следующий билет")
        self._next.clicked.connect(self._show_next)
        self._counter = QLabel(NO_PAGES)
        self._counter.setObjectName("pageCounter")
        self._counter.setMinimumWidth(96)
        self._counter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        export_label = QLabel("Экспорт")
        export_label.setObjectName("hint")
        self._with_answers = ToggleSwitch(False)  # по умолчанию без ответов
        self._with_answers.setToolTip("Печатать под вопросами ответы")
        answers_label = QLabel("С ответами")
        answers_label.setObjectName("hint")
        bar = QFrame()
        bar.setObjectName("previewBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 10, 20, 10)
        layout.setSpacing(8)
        layout.addWidget(self._previous)
        layout.addWidget(self._counter)
        layout.addWidget(self._next)
        layout.addStretch()
        layout.addWidget(self._with_answers)
        layout.addWidget(answers_label)
        layout.addSpacing(12)
        layout.addWidget(export_label)
        self._formats = QButtonGroup(self)  # выбран всегда один формат
        for name in EXPORT_FORMATS:
            button = QPushButton(name)
            button.setObjectName("chip")
            button.setCheckable(True)
            button.setChecked(name == self._settings.settings.export_format)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            self._formats.addButton(button)
            layout.addWidget(button)
        self._formats.buttonClicked.connect(self._export)
        return bar

    def _build_pages_bar(self) -> QFrame:
        """Строка под листом: кнопки с номерами билетов."""
        self._page_group = QButtonGroup(self)
        self._page_group.idClicked.connect(self._show_page)
        self._pages_layout = QHBoxLayout()
        self._pages_layout.setSpacing(6)
        bar = QFrame()
        bar.setObjectName("pagesBar")
        bar.setFixedHeight(52)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.addLayout(self._pages_layout)
        return bar

    @staticmethod
    def _make_arrow(icon_name: str, tip: str) -> QToolButton:
        """Кнопка-стрелка для листания билетов."""
        button = QToolButton()
        button.setObjectName("flat")
        button.setIcon(make_icon(icon_name, MUTED))
        button.setIconSize(QSize(16, 16))
        button.setToolTip(tip)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        return button
