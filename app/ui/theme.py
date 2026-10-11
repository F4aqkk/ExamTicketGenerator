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
KNOB = "#fffefd"  # кружок переключателя
BACKDROP = "#15181c"  # фон вокруг листа в предпросмотре
PAPER = "#f6f3ec"  # лист билета
INK = "#1c1a16"  # текст на листе билета
INK_MUTED = "#8a8478"  # подписи на листе билета

FONT = "Segoe UI"  # основной шрифт Windows
MONO = "Consolas"  # моноширинный шрифт: номера, счётчики, подписи
SERIF = "Georgia"  # шрифт с засечками: текст на листе билета

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

/* Страница «Генератор билетов» */
QScrollArea {
    border: none;
}
#generatorPanel {
    border-right: 1px solid $border;
}
#panelFooter {
    border-top: 1px solid $border;
}
#summary {
    color: $muted;
}
#warning {
    color: $accent;
}
#stepper {
    border: 1px solid $outline;
    border-radius: 7px;
}
#stepper QToolButton, QToolButton#flat {
    background: transparent;
    border: none;
    border-radius: 5px;
    padding: 6px;
}
#stepper QToolButton:hover, QToolButton#flat:hover {
    background: $surface;
}
#stepperValue, #pageCounter {
    font-family: "$mono";
    font-size: 14px;
}
QLineEdit#stepperValue {
    background: transparent;
    border: none;
    padding: 0px;
}
QLineEdit#stepperValue:focus {
    border: none;
    color: $accent;
}
#levels {
    border: 1px solid $outline;
    border-radius: 8px;
}
#levelRow {
    border-top: 1px solid $border;
}
#switchTitle {
    font-weight: 600;
}
#switchHint {
    color: $muted;
    font-size: 11px;
}
#previewBar {
    border-bottom: 1px solid $border;
}
#pagesBar {
    border-top: 1px solid $border;
}
#previewCanvas {
    background: $backdrop;
}
QPushButton#chip {
    font-family: "$mono";
    font-size: 11px;
    padding: 8px 12px;
}
QPushButton#chip:checked {
    background: $accent;
    color: $accent_text;
    border: 1px solid $accent;
}
QPushButton#chip:disabled {
    background: $panel;
    color: $faint;
    border: 1px solid $border;
}
QPushButton#pageButton {
    color: $muted;
    border: none;
    padding: 6px 4px;
    min-width: 24px;
    font-family: "$mono";
    font-size: 11px;
    font-weight: 400;
}
QPushButton#pageButton:checked {
    background: $accent;
    color: $accent_text;
    font-weight: 700;
}

/* Страница «История» */
#historyRow {
    border-bottom: 1px solid $border;
}
#historyRow:hover {
    background: $panel;
}
#historyTitle {
    font-size: 14px;
    font-weight: 600;
}
#historyMeta {
    color: $muted;
    font-family: "$mono";
    font-size: 12px;
}

/* Страница «Настройки» */
#section {
    border-bottom: 1px solid $border;
}
#sectionTitle {
    font-size: 15px;
    font-weight: 600;
}
#sectionHint {
    color: $muted;
    font-size: 12px;
}
#infoCard {
    background: $panel;
    border: 1px solid $outline;
    border-radius: 8px;
}
QLineEdit:disabled {
    color: $muted;
}

/* Лист билета в предпросмотре */
#sheet {
    background: $paper;
    border-radius: 4px;
}
#sheet QLabel {
    color: $ink;
    font-family: "$serif";
    font-size: 15px;
}
#sheet QLabel#sheetOrganization {
    color: $ink_muted;
    font-size: 11px;
}
#sheet QLabel#sheetLine {
    font-size: 13px;
}
#sheet QLabel#sheetNumber {
    font-size: 22px;
    font-weight: 700;
}
#sheet QLabel#sheetIndex {
    font-weight: 700;
}
#sheet QLabel#sheetNote {
    color: $ink_muted;
    font-family: "$font";
    font-size: 10px;
}
#sheetRule {
    background: $ink;
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
        faint=FAINT,
        accent=ACCENT,
        accent_hover=ACCENT_HOVER,
        accent_text=ACCENT_TEXT,
        danger=DANGER,
        backdrop=BACKDROP,
        paper=PAPER,
        ink=INK,
        ink_muted=INK_MUTED,
        font=FONT,
        mono=MONO,
        serif=SERIF,
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
