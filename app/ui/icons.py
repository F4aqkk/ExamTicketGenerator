"""Иконки интерфейса.

Каждая иконка описана коротким рисунком в формате SVG (линии
в квадрате 24×24). Функции ниже превращают рисунок в картинку
нужного цвета и размера, поэтому файлы с иконками не нужны.
"""

from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

# Название иконки -> её линии.
SHAPES = {
    "bank": '<path d="M4 3 H20 V21 H4 Z M4 16 H20"/>',
    "generator": (
        '<path d="M12 3 L21 8 L12 13 L3 8 Z"/>'
        '<path d="M3 12 L12 17 L21 12"/>'
        '<path d="M3 16 L12 21 L21 16"/>'
    ),
    "history": '<circle cx="12" cy="12" r="9"/><path d="M12 7 V12 L15.5 14"/>',
    "settings": (
        '<path d="M4 6 H13 M17 6 H20 M4 12 H7 M11 12 H20 M4 18 H15 '
        'M19 18 H20"/>'
        '<circle cx="15" cy="6" r="2"/>'
        '<circle cx="9" cy="12" r="2"/>'
        '<circle cx="17" cy="18" r="2"/>'
    ),
    "search": '<circle cx="11" cy="11" r="7"/><path d="M16.5 16.5 L21 21"/>',
    "import": '<path d="M12 16 V4 M7 9 L12 4 L17 9 M5 20 H19"/>',
    "export": '<path d="M12 4 V16 M7 11 L12 16 L17 11 M5 20 H19"/>',
    "plus": '<path d="M12 5 V19 M5 12 H19"/>',
    "edit": '<path d="M4 20 H8 L19 9 L15 5 L4 16 Z M13 7 L17 11"/>',
    "delete": (
        '<path d="M4 7 H20 M9 7 V4 H15 V7 M6 7 L7 20 H17 L18 7 '
        'M10 11 V16 M14 11 V16"/>'
    ),
    "close": '<path d="M6 6 L18 18 M18 6 L6 18"/>',
    "arrow_down": '<path d="M6 9 L12 15 L18 9"/>',
}

SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
    '<g fill="none" stroke="{color}" stroke-width="1.8" '
    'stroke-linecap="round" stroke-linejoin="round">{shape}</g>'
    "</svg>"
)

SHARPNESS = 2  # рисуем вдвое крупнее, чтобы иконка была чёткой при 150 %


def make_pixmap(name: str, color: str, size: int = 16) -> QPixmap:
    """Нарисовать иконку по названию заданным цветом и размером."""
    svg = SVG.format(color=color, shape=SHAPES[name])
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap = QPixmap(size * SHARPNESS, size * SHARPNESS)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(SHARPNESS)
    return pixmap


def make_icon(name: str, color: str, size: int = 16) -> QIcon:
    """Иконка для кнопки: та же картинка, завёрнутая в значок Qt."""
    return QIcon(make_pixmap(name, color, size))
