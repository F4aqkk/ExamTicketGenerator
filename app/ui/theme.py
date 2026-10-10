"""Оформление интерфейса: цвета, шрифты и стили по макету Figma."""

from string import Template

from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import QApplication

# Цвета взяты с макета главной формы «Банк вопросов».
BACKGROUND = "#121418"  # фон страниц и полей ввода
PANEL = "#1a1d22"  # боковое меню, обычные кнопки, карточка формы
SURFACE = "#22262d"  # выбранный пункт меню и переключателя
BORDER = "#25262a"  # тонкие разделительные линии
OUTLINE = "#33373e"  # рамки кнопок и полей
TEXT = "#ebe8e1"  # основной текст
MUTED = "#9296a0"  # второстепенный текст
FAINT = "#52555c"  # неактивные иконки
ACCENT = "#e9b44c"  # акцентный цвет: главные кнопки, выделение
ACCENT_HOVER = "#f0c467"  # акцентная кнопка под курсором
ACCENT_TEXT = "#1a1407"  # текст на акцентной кнопке
CHIP = "#202226"  # фон тега в таблице
BAR_OFF = "#35373a"  # незакрашенный столбик индикатора сложности
ONLINE = "#86c7a2"  # точка статуса в боковом меню
DANGER = "#e5786d"  # текст ошибки в форме

FONT = "Segoe UI"  # основной шрифт Windows
MONO = "Consolas"  # моноширинный шрифт: номера, счётчики, подписи

# Стили Qt (QSS) похожи на CSS. Слова с $ заменяются цветами выше.
STYLE = Template("""
QWidget {
    color: $text;
    font-family: "$font";
    font-size: 13px;
}
QMainWindow, QDialog {
    background: $background;
}
QToolTip {
    background: $surface;
    color: $text;
    border: 1px solid $outline;
    padding: 4px 8px;
}

/* Боковое меню */
#sidebar {
    background: $panel;
    border-right: 1px solid $border;
}
#logoMark {
    background: $accent;
    color: $accent_text;
    border-radius: 7px;
    font-family: "$mono";
    font-size: 14px;
    font-weight: 700;
}
#logoTitle {
    font-size: 15px;
    font-weight: 600;
}
#logoHint, #statusLine {
    color: $muted;
    font-family: "$mono";
    font-size: 11px;
}
QPushButton#nav {
    background: transparent;
    color: $muted;
    border: none;
    border-left: 2px solid transparent;
    border-radius: 6px;
    padding: 9px 10px;
    font-size: 14px;
    font-weight: 400;
    text-align: left;
}
QPushButton#nav:hover {
    background: transparent;
    color: $text;
}
QPushButton#nav:checked {
    background: $surface;
    color: $text;
    border-left: 2px solid $accent;
    font-weight: 600;
}
#navBadge {
    color: $muted;
    font-family: "$mono";
    font-size: 11px;
}

/* Заголовок страницы */
#pageHeader {
    border-bottom: 1px solid $border;
}
#pageTitle {
    font-size: 24px;
    font-weight: 700;
}
#pageHint, #hint {
    color: $muted;
    font-family: "$mono";
    font-size: 12px;
}
#emptyLabel {
    color: $muted;
    font-size: 14px;
}

/* Кнопки */
QPushButton {
    background: $panel;
    color: $text;
    border: 1px solid $outline;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 600;
}
QPushButton:hover {
    background: $surface;
}
QPushButton:pressed {
    background: $background;
}
QPushButton#primary {
    background: $accent;
    color: $accent_text;
    border: 1px solid $accent;
}
QPushButton#primary:hover {
    background: $accent_hover;
    border: 1px solid $accent_hover;
}
QToolButton#closeButton {
    background: transparent;
    border: none;
    border-radius: 4px;
    padding: 4px;
}
QToolButton#closeButton:hover {
    background: $surface;
}

/* Поля ввода и выпадающие списки */
QLineEdit, QPlainTextEdit, QComboBox {
    background: $background;
    color: $text;
    border: 1px solid $outline;
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: $accent;
    selection-color: $accent_text;
}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
    border: 1px solid $accent;
}
QComboBox::drop-down {
    border: none;
    width: 32px;
}
QComboBox::down-arrow {
    image: none;
}
QComboBox QAbstractItemView {
    background: $panel;
    color: $text;
    border: 1px solid $outline;
    outline: none;
    padding: 4px;
    selection-background-color: $surface;
    selection-color: $text;
}
QComboBox QAbstractItemView::item {
    min-height: 28px;
    padding: 0px 8px;
}

/* Переключатель «Все / Лёгкие / Средние / Сложные» */
#segmented {
    border: 1px solid $outline;
    border-radius: 7px;
}
#segmented QPushButton {
    background: transparent;
    color: $muted;
    border: 1px solid transparent;
    border-radius: 5px;
    padding: 6px 12px;
    font-weight: 400;
}
#segmented QPushButton:hover {
    color: $text;
}
#segmented QPushButton:checked {
    background: $surface;
    color: $text;
    border: 1px solid $outline;
    font-weight: 600;
}

/* Таблица вопросов */
QTableView {
    background: $background;
    border: none;
    border-top: 1px solid $border;
}
QHeaderView {
    background: $background;
}
QHeaderView::section {
    background: $background;
    color: $muted;
    border: none;
    border-bottom: 1px solid $border;
    padding: 0px 12px;
    font-family: "$mono";
    font-size: 11px;
}
QHeaderView::section:first {
    padding-left: 32px;
}
QScrollBar:vertical {
    background: $background;
    width: 10px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: $outline;
    border-radius: 5px;
    min-height: 32px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

/* Форма «Новый вопрос» */
#overlay {
    background: rgba(0, 0, 0, 150);
}
#questionDialog {
    background: transparent;
}
#dialogCard {
    background: $panel;
    border: 1px solid $outline;
    border-radius: 12px;
}
#dialogHeader {
    border-bottom: 1px solid $border;
}
#dialogFooter {
    border-top: 1px solid $border;
}
#dialogTitle {
    font-size: 17px;
    font-weight: 700;
}
#caption {
    color: $muted;
    font-size: 11px;
    font-weight: 700;
}
#formError {
    color: $danger;
}
""")


def build_stylesheet() -> str:
    """Собрать текст стилей: подставить цвета и шрифты вместо слов с $."""
    return STYLE.substitute(
        background=BACKGROUND,
        panel=PANEL,
        surface=SURFACE,
        border=BORDER,
        outline=OUTLINE,
        text=TEXT,
        muted=MUTED,
        accent=ACCENT,
        accent_hover=ACCENT_HOVER,
        accent_text=ACCENT_TEXT,
        danger=DANGER,
        font=FONT,
        mono=MONO,
    )


def build_palette() -> QPalette:
    """Тёмная палитра для частей окна, которые не описаны в стилях."""
    colors = {
        QPalette.ColorRole.Window: BACKGROUND,
        QPalette.ColorRole.WindowText: TEXT,
        QPalette.ColorRole.Base: BACKGROUND,
        QPalette.ColorRole.AlternateBase: PANEL,
        QPalette.ColorRole.Text: TEXT,
        QPalette.ColorRole.PlaceholderText: MUTED,
        QPalette.ColorRole.Button: PANEL,
        QPalette.ColorRole.ButtonText: TEXT,
        QPalette.ColorRole.Highlight: ACCENT,
        QPalette.ColorRole.HighlightedText: ACCENT_TEXT,
        QPalette.ColorRole.ToolTipBase: SURFACE,
        QPalette.ColorRole.ToolTipText: TEXT,
    }
    palette = QPalette()
    for role, color in colors.items():
        palette.setColor(role, QColor(color))
    return palette


def apply_theme(app: QApplication) -> None:
    """Включить тёмное оформление для всей программы."""
    app.setStyle("Fusion")  # одинаковая основа на любой версии Windows
    app.setFont(QFont(FONT, 10))
    app.setPalette(build_palette())
    app.setStyleSheet(build_stylesheet())
