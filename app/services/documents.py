"""Чтение и запись файлов DOCX, PDF, XLSX и TXT.

Здесь нет ничего про билеты и вопросы: модуль умеет только записать
готовые строки в файл нужного формата и прочитать строки обратно.
Что именно писать и как понимать прочитанное, решают сервисы
экспорта и импорта.

Библиотеки форматов подключаются внутри функций. Если какая-то
из них не установлена, программа всё равно запускается, а при работе
с этим форматом объясняет, что нужно поставить.
"""

import importlib
import os
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

TEXT_FORMATS = ("DOCX", "PDF", "TXT")  # документы из строк текста
TABLE_FORMAT = "XLSX"  # таблица
NORMAL, TITLE, CENTER, NOTE = "normal", "title", "center", "note"
PAGE_BORDER = "=" * 60  # так в текстовом файле отделяются страницы
FORBIDDEN = '\\/:*?"<>|'  # знаки, которых не бывает в имени файла
WRONG_FORMAT = "Поддерживаются только файлы DOCX, PDF, XLSX и TXT."
BROKEN_FILE = "Не удалось прочитать файл: он повреждён или другого формата."
LIBRARIES = {  # формат -> (модуль, название для установки)
    "DOCX": ("docx", "python-docx"),
    "XLSX": ("openpyxl", "openpyxl"),
    "PDF": ("reportlab", "reportlab"),
}
# Шрифты с русскими буквами для PDF: обычный и жирный.
PDF_FONTS = [
    ("times.ttf", "timesbd.ttf"),
    ("arial.ttf", "arialbd.ttf"),
    ("LiberationSerif-Regular.ttf", "LiberationSerif-Bold.ttf"),
    ("DejaVuSerif.ttf", "DejaVuSerif-Bold.ttf"),
]
FONT_FOLDERS = [
    Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts",
    Path("/usr/share/fonts/truetype/liberation"),
    Path("/usr/share/fonts/truetype/dejavu"),
]


class DocumentError(Exception):
    """Ошибка работы с файлом; её текст можно показать в окне."""


@dataclass
class Line:
    """Одна строка документа и её вид."""

    text: str
    style: str = NORMAL  # обычная, заголовок, по центру или пояснение


def file_format(path: str | Path) -> str:
    """Формат файла по его расширению: DOCX, PDF, XLSX или TXT."""
    suffix = Path(path).suffix.lstrip(".").upper()
    if suffix not in TEXT_FORMATS and suffix != TABLE_FORMAT:
        raise DocumentError(WRONG_FORMAT)
    return suffix


def safe_file_name(title: str) -> str:
    """Имя файла из названия: без знаков, запрещённых в Windows."""
    name = "".join(" " if sign in FORBIDDEN else sign for sign in title)
    return " ".join(name.split()) or "Без названия"


def write_pages(path: str | Path, pages: list[list[Line]]) -> None:
    """Записать страницы из строк в файл TXT, DOCX или PDF."""
    writers = {"TXT": _write_txt, "DOCX": _write_docx, "PDF": _write_pdf}
    writer = writers[file_format(path)]
    try:
        writer(Path(path), pages)
    except OSError as error:  # например, файл открыт в другой программе
        raise DocumentError(f"Не удалось записать файл: {error}") from None


def write_table(
    path: str | Path,
    title: str,
    header: list[str],
    rows: list[list],
    widths: list[int],
) -> None:
    """Записать таблицу в файл XLSX: строка заголовков и строки данных."""
    openpyxl = _library("openpyxl", TABLE_FORMAT)
    styles = _library("openpyxl.styles", TABLE_FORMAT)
    utils = _library("openpyxl.utils", TABLE_FORMAT)
    book = openpyxl.Workbook()
    sheet = book.active
    sheet.title = title
    sheet.append(header)
    for row in rows:
        sheet.append(row)
    for cell in sheet[1]:
        cell.font = styles.Font(bold=True)
    for number, width in enumerate(widths, start=1):
        letter = utils.get_column_letter(number)
        sheet.column_dimensions[letter].width = width
    sheet.freeze_panes = "A2"  # заголовки остаются на месте при прокрутке
    try:
        book.save(str(path))
    except OSError as error:
        raise DocumentError(f"Не удалось записать файл: {error}") from None


def read_lines(path: str | Path) -> list[str]:
    """Прочитать строки текста из файла TXT, DOCX или PDF."""
    readers = {"TXT": _read_txt, "DOCX": _read_docx, "PDF": _read_pdf}
    reader = readers[file_format(path)]
    try:
        return reader(Path(path))
    except DocumentError:
        raise
    except Exception:  # чужой файл может быть испорчен как угодно
        raise DocumentError(BROKEN_FILE) from None


def read_table(path: str | Path) -> list[list[str]]:
    """Прочитать строки таблицы из файла XLSX; пустые ячейки это ''."""
    openpyxl = _library("openpyxl", TABLE_FORMAT)
    try:
        book = openpyxl.load_workbook(str(path), read_only=True)
        rows = []
        for row in book.active.iter_rows(values_only=True):
            rows.append([_cell_text(value) for value in row])
        book.close()
    except Exception:  # чужой файл может быть испорчен как угодно
        raise DocumentError(BROKEN_FILE) from None
    return rows


def _library(name: str, file_type: str):
    """Подключить библиотеку формата; если её нет, объяснить, что поставить."""
    try:
        return importlib.import_module(name)
    except ImportError:
        package = LIBRARIES.get(file_type, (name, name))[1]
        raise DocumentError(
            f"Для файлов {file_type} не установлена библиотека {package}. "
            "Установите её командой:\n"
            f"venv\\Scripts\\python.exe -m pip install {package}"
        ) from None


def _cell_text(value) -> str:
    """Значение ячейки таблицы как текст: 2.0 это «2», пусто это ''."""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _write_txt(path: Path, pages: list[list[Line]]) -> None:
    """Текстовый файл: страницы разделяются чертой из знаков «=»."""
    blocks = ["\n".join(line.text for line in page) for page in pages]
    text = f"\n\n{PAGE_BORDER}\n\n".join(blocks) + "\n"
    # utf-8-sig: с такой пометкой Блокнот Windows верно покажет кириллицу.
    path.write_text(text, encoding="utf-8-sig")


def _read_txt(path: Path) -> list[str]:
    """Строки текстового файла в кодировке UTF-8 или Windows-1251."""
    data = path.read_bytes()
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = data.decode("cp1251")
    return text.splitlines()


def _write_docx(path: Path, pages: list[list[Line]]) -> None:
    """Документ Word: каждая страница начинается с нового листа."""
    docx = _library("docx", "DOCX")
    shared = _library("docx.shared", "DOCX")
    center = _library("docx.enum.text", "DOCX").WD_ALIGN_PARAGRAPH.CENTER
    document = docx.Document()
    sheet = document.sections[0]  # лист А4 с полями, как в PDF
    sheet.page_width, sheet.page_height = shared.Mm(210), shared.Mm(297)
    sheet.left_margin, sheet.right_margin = shared.Mm(20), shared.Mm(15)
    sheet.top_margin = sheet.bottom_margin = shared.Mm(20)
    base = document.styles["Normal"]
    base.font.name = "Times New Roman"
    base.font.size = shared.Pt(13)
    base.paragraph_format.space_after = shared.Pt(0)
    base.paragraph_format.line_spacing = 1.0
    for page_number, page in enumerate(pages):
        for line_number, line in enumerate(page):
            paragraph = document.add_paragraph()
            run = paragraph.add_run(line.text)
            if page_number and not line_number:
                paragraph.paragraph_format.page_break_before = True
            if line.style in (TITLE, CENTER):
                paragraph.alignment = center
            if line.style == TITLE:
                run.bold = True
                run.font.size = shared.Pt(16)
            if line.style == NOTE:
                run.italic = True
                run.font.size = shared.Pt(10)
            if line.style == NORMAL:
                paragraph.paragraph_format.space_before = shared.Pt(4)
    document.save(str(path))


def _read_docx(path: Path) -> list[str]:
    """Строки документа Word: абзацы, разбитые по переносам строк."""
    docx = _library("docx", "DOCX")
    lines = []
    for paragraph in docx.Document(str(path)).paragraphs:
        lines.extend(paragraph.text.split("\n"))
    return lines


def _write_pdf(path: Path, pages: list[list[Line]]) -> None:
    """Документ PDF на листах А4 со шрифтом, в котором есть кириллица."""
    platypus = _library("reportlab.platypus", "PDF")
    sheet = _library("reportlab.lib.pagesizes", "PDF").A4
    styles = _pdf_styles()
    story = []  # всё, что нужно разместить на листах, по порядку
    for page_number, page in enumerate(pages):
        if page_number:
            story.append(platypus.PageBreak())
        for line in page:
            if not line.text:
                story.append(platypus.Spacer(1, 10))
                continue
            text = escape(line.text).replace("\n", "<br/>")
            story.append(platypus.Paragraph(text, styles[line.style]))
    document = platypus.SimpleDocTemplate(
        str(path),
        pagesize=sheet,
        leftMargin=57,
        rightMargin=42,
        topMargin=57,
        bottomMargin=57,
    )
    document.build(story)


def _read_pdf(path: Path) -> list[str]:
    """Строки текста со всех листов PDF."""
    pypdf = _library("pypdf", "PDF")
    lines = []
    for page in pypdf.PdfReader(str(path)).pages:
        lines.extend((page.extract_text() or "").splitlines())
    return lines


def _pdf_styles() -> dict:
    """Виды строк для PDF: шрифт, размер и выравнивание каждого."""
    make = _library("reportlab.lib.styles", "PDF").ParagraphStyle
    regular, bold = _pdf_fonts()
    return {
        NORMAL: make(
            NORMAL,
            fontName=regular,
            fontSize=13,
            leading=17,
            spaceBefore=4,
        ),
        TITLE: make(
            TITLE,
            fontName=bold,
            fontSize=16,
            leading=22,
            alignment=1,
        ),
        CENTER: make(
            CENTER,
            fontName=regular,
            fontSize=12,
            leading=16,
            alignment=1,
        ),
        NOTE: make(NOTE, fontName=regular, fontSize=10, leading=14),
    }


def _pdf_fonts() -> tuple[str, str]:
    """Подключить к PDF шрифт с русскими буквами: обычный и жирный.

    Встроенные шрифты PDF кириллицу не знают, поэтому берётся шрифт
    из системы: в Windows это Times New Roman.
    """
    metrics = _library("reportlab.pdfbase.pdfmetrics", "PDF")
    fonts = _library("reportlab.pdfbase.ttfonts", "PDF")
    for folder in FONT_FOLDERS:
        for regular, bold in PDF_FONTS:
            if (folder / regular).exists() and (folder / bold).exists():
                names = ("ExamRegular", "ExamBold")
                for name, file in zip(names, (regular, bold)):
                    font = fonts.TTFont(name, str(folder / file))
                    metrics.registerFont(font)
                return names
    raise DocumentError("Для PDF не найден шрифт с русскими буквами.")
