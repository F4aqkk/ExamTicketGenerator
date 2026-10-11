"""Экспорт билетов и банка вопросов в файлы DOCX, PDF, XLSX, TXT.

Сервис решает, ЧТО записать в файл: какие строки и в каком порядке.
КАК записать файл нужного формата, знает модуль documents.
"""

from pathlib import Path

from sqlalchemy.orm import Session

from app.models.generation import Generation
from app.models.question import Question
from app.models.ticket import Ticket
from app.repositories.question_repository import QuestionRepository
from app.services.documents import (
    CENTER,
    NOTE,
    TABLE_FORMAT,
    TITLE,
    Line,
    file_format,
    write_pages,
    write_table,
)
from app.services.question_service import DIFFICULTY_NAMES
from app.services.settings_service import SettingsService

# Названия полей вопроса в файле банка. По ним же файл читает импорт.
BANK_FIELDS = ("Тема", "Сложность", "Тип задания", "Теги", "Вопрос", "Ответ")
BANK_COLUMNS = ["Тема", "Сложность", "Тип задания", "Вопрос", "Ответ", "Теги"]
BANK_WIDTHS = [24, 14, 14, 70, 50, 24]  # ширина столбцов таблицы банка
NO_ANSWER = "не указан"


class ExportService:
    """Сохраняет билеты и банк вопросов в файл выбранного формата."""

    def __init__(self, session: Session, settings: SettingsService):
        """Запоминает репозиторий вопросов и сервис настроек."""
        self.questions = QuestionRepository(session)
        self._settings = settings

    def export_tickets(
        self,
        generation: Generation,
        path: str | Path,
        with_answers: bool = False,
    ) -> None:
        """Сохранить билеты генерации в файл; формат берётся из имени.

        Ответы под вопросами печатаются, только если об этом попросили:
        по умолчанию билеты сохраняются без ответов.
        """
        if file_format(path) == TABLE_FORMAT:
            self._tickets_table(generation, path, with_answers)
            return
        pages = []  # каждый билет на своей странице
        for ticket in generation.tickets:
            pages.append(self._ticket_page(generation, ticket, with_answers))
        write_pages(path, pages)

    def export_bank(self, path: str | Path) -> int:
        """Сохранить весь банк вопросов в файл; вернуть число вопросов.

        Такой файл служит резервной копией: его читает импорт.
        """
        questions = self.questions.search()
        if file_format(path) == TABLE_FORMAT:
            rows = [self._bank_row(question) for question in questions]
            write_table(path, "Банк вопросов", BANK_COLUMNS, rows, BANK_WIDTHS)
        else:
            lines = []
            for question in questions:
                lines.extend(self._bank_lines(question))
            write_pages(path, [lines])
        return len(questions)

    def _ticket_page(
        self,
        generation: Generation,
        ticket: Ticket,
        with_answers: bool,
    ) -> list[Line]:
        """Строки одного билета: шапка, номер, вопросы, преподаватель."""
        settings = self._settings.settings
        page = []
        if settings.organization:
            page.append(Line(settings.organization.upper(), CENTER))
        page.append(Line(generation.title, CENTER))
        if settings.discipline:
            page.append(Line(f"Дисциплина: {settings.discipline}", CENTER))
        page.append(Line(""))
        page.append(Line(f"БИЛЕТ № {ticket.number}", TITLE))
        page.append(Line(""))
        for item in ticket.ticket_questions:
            question = item.question
            page.append(Line(f"{item.position}. {question.text}"))
            page.append(Line(self._note(question), NOTE))
            if with_answers:
                answer = question.answer or NO_ANSWER
                page.append(Line(f"Ответ: {answer}", NOTE))
        if settings.teacher:
            page.append(Line(""))
            page.append(Line(f"Преподаватель: {settings.teacher}"))
        return page

    def _tickets_table(
        self,
        generation: Generation,
        path: str | Path,
        with_answers: bool,
    ) -> None:
        """Билеты в виде таблицы: одна строка на каждый вопрос."""
        header = ["Билет", "№", "Вопрос", "Тема", "Сложность"]
        widths = [8, 6, 80, 24, 14]
        if with_answers:
            header.append("Ответ")
            widths.append(50)
        rows = []
        for ticket in generation.tickets:
            for item in ticket.ticket_questions:
                question = item.question
                row = [
                    ticket.number,
                    item.position,
                    question.text,
                    question.topic.name,
                    DIFFICULTY_NAMES.get(question.difficulty, ""),
                ]
                if with_answers:
                    row.append(question.answer)
                rows.append(row)
        write_table(path, "Билеты", header, rows, widths)

    @staticmethod
    def _note(question: Question) -> str:
        """Подпись под вопросом в билете: тема и сложность."""
        level = DIFFICULTY_NAMES.get(question.difficulty, "")
        return f"{question.topic.name} · {level}"

    @staticmethod
    def _bank_values(question: Question) -> dict[str, str]:
        """Поля вопроса для файла банка: название поля -> значение."""
        return {
            "Тема": question.topic.name,
            "Сложность": DIFFICULTY_NAMES.get(question.difficulty, ""),
            "Тип задания": question.task_type,
            "Теги": ", ".join(tag.name for tag in question.tags),
            "Вопрос": question.text,
            "Ответ": question.answer,
        }

    def _bank_row(self, question: Question) -> list[str]:
        """Строка таблицы банка в порядке её столбцов."""
        values = self._bank_values(question)
        return [values[column] for column in BANK_COLUMNS]

    def _bank_lines(self, question: Question) -> list[Line]:
        """Вопрос в текстовом файле: «Поле: значение» и пустая строка.

        Пустые строки внутри текста убираются: пустая строка в файле
        означает конец вопроса.
        """
        lines = []
        for name, value in self._bank_values(question).items():
            parts = [part for part in value.splitlines() if part.strip()]
            lines.append(Line(f"{name}: " + "\n".join(parts)))
        lines.append(Line(""))
        return lines
