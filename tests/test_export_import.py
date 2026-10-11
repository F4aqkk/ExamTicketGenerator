"""Тесты экспорта билетов и банка вопросов и импорта вопросов."""

import pytest

from app.repositories.question_repository import QuestionRepository
from app.services.documents import DocumentError, read_lines, read_table
from app.services.export_service import ExportService
from app.services.generation_service import GenerationService
from app.services.import_service import (
    ImportService,
    parse_blocks,
    parse_difficulty,
)
from app.services.question_service import QuestionData, QuestionService
from app.services.settings_service import SettingsService

FORMATS = ("txt", "docx", "pdf", "xlsx")
LONG_TEXT = "Объясните, чем внешний ключ отличается от первичного. " * 4


def fill_bank(session) -> QuestionService:
    """Банк: две темы, три вопроса разной сложности с ответами и тегами."""
    service = QuestionService(session)
    sql = service.add_topic("SQL")
    git = service.add_topic("Git")
    questions = [
        ("Что делает SELECT?", "Выбирает строки.", sql.id, 1, "запросы"),
        (LONG_TEXT.strip(), "Ссылкой на другую таблицу.", sql.id, 2, ""),
        ("Что делает git commit?", "", git.id, 3, "команды, история"),
    ]
    for text, answer, topic_id, difficulty, tags in questions:
        service.add_question(
            QuestionData(
                text=text,
                answer=answer,
                topic_id=topic_id,
                task_type="Теория",
                difficulty=difficulty,
                tag_names=tags,
            )
        )
    return service


@pytest.fixture
def settings(tmp_path):
    """Настройки во временной папке с заполненной шапкой документа."""
    service = SettingsService(tmp_path / "settings.json")
    service.update(
        organization="Колледж",
        discipline="Базы данных",
        teacher="Иванов И. И.",
    )
    return service


def file_text(path) -> str:
    """Весь текст файла одной строкой: так удобно искать в нём слова."""
    if path.suffix == ".xlsx":
        rows = read_table(path)
        return " ".join(" ".join(row) for row in rows)
    return " ".join(read_lines(path))


@pytest.mark.parametrize("extension", FORMATS)
def test_tickets_are_exported_without_answers(
    session,
    settings,
    tmp_path,
    extension,
):
    """Билеты сохраняются в каждый формат; ответов в файле нет."""
    fill_bank(session)
    generation = GenerationService(session).create("Экзамен", 2, {1: 1})
    path = tmp_path / f"tickets.{extension}"

    ExportService(session, settings).export_tickets(generation, path)
    text = file_text(path)

    assert "Что делает SELECT?" in text
    assert "Выбирает строки." not in text
    if extension != "xlsx":  # в таблице шапки документа нет
        assert "БИЛЕТ № 2" in text
        assert "КОЛЛЕДЖ" in text
        assert "Преподаватель: Иванов И. И." in text


@pytest.mark.parametrize("extension", FORMATS)
def test_tickets_are_exported_with_answers(
    session,
    settings,
    tmp_path,
    extension,
):
    """По просьбе преподавателя под вопросами печатаются ответы."""
    fill_bank(session)
    generation = GenerationService(session).create("Экзамен", 1, {1: 1})
    path = tmp_path / f"tickets.{extension}"
    service = ExportService(session, settings)

    service.export_tickets(generation, path, with_answers=True)

    assert "Выбирает строки." in file_text(path)


@pytest.mark.parametrize("extension", FORMATS)
def test_bank_export_is_read_back_by_import(
    session,
    settings,
    tmp_path,
    extension,
):
    """Банк, сохранённый в файл, восстанавливается из него без потерь."""
    fill_bank(session)
    path = tmp_path / f"bank.{extension}"
    repo = QuestionRepository(session)
    before = [
        (q.topic.name, q.text, q.answer, q.difficulty, q.task_type)
        for q in repo.search()
    ]
    tags_before = [sorted(tag.name for tag in q.tags) for q in repo.search()]

    saved = ExportService(session, settings).export_bank(path)
    for question in repo.search():
        repo.delete(question)
    result = ImportService(session).import_bank(path)
    after = [
        (q.topic.name, q.text, q.answer, q.difficulty, q.task_type)
        for q in repo.search()
    ]
    tags_after = [sorted(tag.name for tag in q.tags) for q in repo.search()]

    assert saved == 3
    assert result.added == 3
    assert after == before
    assert tags_after == tags_before


def test_import_skips_repeats_and_marks_unknown_difficulty(session, tmp_path):
    """Повторы пропускаются, нераспознанная сложность становится нулём."""
    fill_bank(session)
    path = tmp_path / "new.txt"
    path.write_text(
        "Вопрос: Что делает SELECT?\n"
        "Тема: sql\n"
        "\n"
        "Вопрос: Что такое ветка?\n"
        "Тема: Git\n"
        "Сложность: очень трудная\n"
        "Теги: КОМАНДЫ, ветки\n"
        "\n"
        "Тема: Git\n"
        "Сложность: лёгкая\n"
        "\n"
        "Вопрос: Вопрос без темы\n"
        "Сложность: 2\n"
        "Тип задания: практика\n",
        encoding="utf-8",
    )

    result = ImportService(session).import_bank(path)
    service = QuestionService(session)
    branch = service.search(text="ветка")[0]
    lonely = service.search(text="без темы")[0]

    assert (result.added, result.duplicates, result.empty) == (2, 1, 1)
    assert result.no_difficulty == 1
    assert branch.difficulty == 0
    assert sorted(tag.name for tag in branch.tags) == ["ветки", "команды"]
    assert len(service.get_tags()) == 4  # тег «команды» не создан повторно
    assert lonely.topic.name == "Без темы"
    assert (lonely.difficulty, lonely.task_type) == (2, "Практика")


def test_import_rejects_file_without_questions(session, tmp_path):
    """Файл без вопросов не импортируется, причина объясняется."""
    text_file = tmp_path / "empty.txt"
    text_file.write_text("Просто какой-то текст.\n", encoding="utf-8")
    wrong_type = tmp_path / "bank.odt"
    wrong_type.write_text("Вопрос: текст\n", encoding="utf-8")
    service = ImportService(session)

    with pytest.raises(DocumentError, match="не найдено ни одного вопроса"):
        service.import_bank(text_file)
    with pytest.raises(DocumentError, match="только файлы"):
        service.import_bank(wrong_type)

    assert QuestionService(session).count() == 0


def test_parse_difficulty_understands_words_and_digits():
    """Сложность читается из цифр и слов в любой форме."""
    assert parse_difficulty("Лёгкий") == 1
    assert parse_difficulty("легкая") == 1
    assert parse_difficulty(" средние ") == 2
    assert parse_difficulty("3") == 3
    assert parse_difficulty("Не задана") == 0
    assert parse_difficulty("") == 0


def test_parse_blocks_joins_long_text():
    """Строка без названия поля продолжает предыдущее поле."""
    lines = ["Вопрос: первая строка", "вторая строка", "Ответ: да", "", ""]

    records = parse_blocks(lines)

    assert records == [
        {"text": "первая строка\nвторая строка", "answer": "да"},
    ]
