"""Форма «Новый вопрос». Она же служит для изменения вопроса."""

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.models.question import Question
from app.services.question_service import (
    TASK_TYPES,
    QuestionData,
    QuestionError,
    QuestionService,
)
from app.ui.icons import make_icon
from app.ui.theme import MUTED
from app.ui.widgets import (
    ComboBox,
    SegmentedControl,
    ask_text,
    make_caption,
    show_message,
)

DIFFICULTY_CHOICE = [("Лёгкий", 1), ("Средний", 2), ("Сложный", 3)]
NEW_TOPIC = -1  # условный номер пункта «+ Новая тема…»
WIDTH = 520


class QuestionDialog(QDialog):
    """Окно с полями вопроса: текст, ответ, тема, тип, сложность, теги.

    Если вопрос не передан, форма добавляет новый. Если передан,
    поля заполняются его данными и кнопка «Сохранить» изменяет его.
    Проверяет и сохраняет данные сервис банка вопросов.
    """

    def __init__(
        self,
        service: QuestionService,
        question: Question | None = None,
        parent: QWidget | None = None,
    ):
        """Собрать форму и заполнить поля."""
        super().__init__(parent)
        self._service = service
        self._question = question
        self._topic_index = 0  # выбранная тема до открытия списка
        self.setObjectName("questionDialog")
        self.setModal(True)
        # Окно без системной рамки: заголовок и крестик рисуем сами,
        # а прозрачный фон даёт карточке скруглённые углы.
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(WIDTH)

        card = QFrame()
        card.setObjectName("dialogCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(1, 1, 1, 1)
        card_layout.setSpacing(0)
        card_layout.addWidget(self._build_header())
        card_layout.addWidget(self._build_fields())
        card_layout.addWidget(self._build_footer())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(card)

        if question is None:
            self._fill_topics()
            self._difficulty.set_value(2)  # по умолчанию «Средний»
        else:
            self._load(question)
        self._text.setFocus()

    def exec(self) -> int:
        """Показать форму, затемнив на это время главное окно."""
        overlay = self._make_overlay()
        try:
            return super().exec()
        finally:
            if overlay is not None:
                overlay.deleteLater()

    def _make_overlay(self) -> QWidget | None:
        """Полупрозрачная тёмная плёнка поверх главного окна."""
        parent = self.parentWidget()
        if parent is None:
            return None
        overlay = QWidget(parent)
        overlay.setObjectName("overlay")
        overlay.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        overlay.setGeometry(parent.rect())
        overlay.show()
        overlay.raise_()
        return overlay

    def _build_header(self) -> QFrame:
        """Заголовок формы и кнопка закрытия."""
        title = "Новый вопрос"
        if self._question is not None:
            title = "Изменение вопроса"
        title_label = QLabel(title)
        title_label.setObjectName("dialogTitle")
        close_button = QToolButton()
        close_button.setObjectName("closeButton")
        close_button.setIcon(make_icon("close", MUTED))
        close_button.setIconSize(QSize(16, 16))
        close_button.setToolTip("Закрыть без сохранения")
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.clicked.connect(self.reject)

        header = QFrame()
        header.setObjectName("dialogHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 16, 16, 16)
        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(close_button)
        return header

    def _build_fields(self) -> QWidget:
        """Поля формы сверху вниз, как на макете."""
        self._text = QPlainTextEdit()
        self._text.setFixedHeight(110)
        self._text.setTabChangesFocus(True)  # Tab ведёт к следующему полю
        self._answer = QPlainTextEdit()
        self._answer.setFixedHeight(72)
        self._answer.setTabChangesFocus(True)
        self._topic = ComboBox()
        self._topic.activated.connect(self._on_topic_chosen)
        self._task_type = ComboBox()
        self._task_type.addItems(TASK_TYPES)
        self._difficulty = SegmentedControl(DIFFICULTY_CHOICE)
        self._tags = QLineEdit()
        self._tags.setPlaceholderText("JOIN, подзапросы")

        topic_column = QVBoxLayout()
        topic_column.setSpacing(8)
        topic_column.addWidget(make_caption("Тема"))
        topic_column.addWidget(self._topic)
        type_column = QVBoxLayout()
        type_column.setSpacing(8)
        type_column.addWidget(make_caption("Тип задания"))
        type_column.addWidget(self._task_type)
        columns = QHBoxLayout()
        columns.setSpacing(16)
        columns.addLayout(topic_column, 1)
        columns.addLayout(type_column, 1)

        tags_hint = QLabel("через запятую")
        tags_hint.setObjectName("hint")
        tags_caption = QHBoxLayout()
        tags_caption.addWidget(make_caption("Теги"))
        tags_caption.addStretch()
        tags_caption.addWidget(tags_hint)

        fields = QWidget()
        layout = QVBoxLayout(fields)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(8)
        layout.addWidget(make_caption("Текст вопроса"))
        layout.addWidget(self._text)
        layout.addSpacing(8)
        layout.addWidget(make_caption("Ответ"))
        layout.addWidget(self._answer)
        layout.addSpacing(8)
        layout.addLayout(columns)
        layout.addSpacing(8)
        layout.addWidget(make_caption("Сложность"))
        layout.addWidget(self._difficulty, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addSpacing(8)
        layout.addLayout(tags_caption)
        layout.addWidget(self._tags)
        return fields

    def _build_footer(self) -> QFrame:
        """Низ формы: место для ошибки и кнопки «Отмена», «Сохранить»."""
        self._error = QLabel()
        self._error.setObjectName("formError")
        self._error.setWordWrap(True)
        cancel_button = QPushButton("Отмена")
        cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_button.setAutoDefault(False)
        cancel_button.clicked.connect(self.reject)
        save_button = QPushButton("Сохранить")
        save_button.setObjectName("primary")
        save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        save_button.setDefault(True)  # Enter в поле тегов сохраняет форму
        save_button.clicked.connect(self._save)

        footer = QFrame()
        footer.setObjectName("dialogFooter")
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(8)
        layout.addWidget(self._error, 1)
        layout.addWidget(cancel_button)
        layout.addWidget(save_button)
        return footer

    def _fill_topics(self, chosen_id: int | None = None) -> None:
        """Заполнить список тем и выбрать тему с этим номером."""
        self._topic.clear()
        self._topic.addItem("Выберите тему", None)
        for topic in self._service.get_topics():
            self._topic.addItem(topic.name, topic.id)
        self._topic.addItem("+ Новая тема…", NEW_TOPIC)
        index = self._topic.findData(chosen_id) if chosen_id else 0
        self._topic.setCurrentIndex(max(index, 0))
        self._topic_index = self._topic.currentIndex()

    def _load(self, question: Question) -> None:
        """Перенести данные вопроса в поля формы."""
        self._text.setPlainText(question.text)
        self._answer.setPlainText(question.answer)
        self._fill_topics(question.topic_id)
        if self._task_type.findText(question.task_type) < 0:
            self._task_type.addItem(question.task_type)  # редкий тип
        self._task_type.setCurrentText(question.task_type)
        self._difficulty.set_value(question.difficulty)
        self._tags.setText(", ".join(tag.name for tag in question.tags))

    def _on_topic_chosen(self, index: int) -> None:
        """В списке тем выбрали пункт; для «+ Новая тема…» спросить имя."""
        if self._topic.itemData(index) != NEW_TOPIC:
            self._topic_index = index
            return
        name = ask_text(self, "Новая тема", "Название темы:")
        if name is None:  # нажали «Отмена»: вернуть прежний выбор
            self._topic.setCurrentIndex(self._topic_index)
            return
        try:
            topic = self._service.add_topic(name)
        except QuestionError as error:
            show_message(self, "Тема не добавлена", str(error))
            self._topic.setCurrentIndex(self._topic_index)
            return
        self._fill_topics(topic.id)

    def _read(self) -> QuestionData:
        """Собрать то, что введено в поля формы."""
        topic_id = self._topic.currentData()
        if topic_id == NEW_TOPIC:
            topic_id = None
        return QuestionData(
            text=self._text.toPlainText(),
            answer=self._answer.toPlainText(),
            topic_id=topic_id,
            task_type=self._task_type.currentText(),
            difficulty=self._difficulty.value() or 0,
            tag_names=self._tags.text(),
        )

    def _save(self) -> None:
        """Сохранить вопрос; если данные неполные, показать, что не так."""
        data = self._read()
        try:
            if self._question is None:
                self._service.add_question(data)
            else:
                self._service.update_question(self._question, data)
        except QuestionError as error:
            self._error.setText(str(error))
            return
        self.accept()
