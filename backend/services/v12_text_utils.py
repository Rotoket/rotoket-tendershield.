"""
Подготовка и фильтрация текста для v12 two-stage классификатора.

Используется перед отправкой фрагмента в LegalGroundingService.analyze и перед
логированием в V12PredictionLog, чтобы не подавать и не логировать бинарный/служебный мусор
(DOCX/XLS заголовки, XML, и т.п.).
"""
import re
import unicodedata


# Порог минимальной доли буквенно-цифровых/пробельных символов (остальное — мусор)
MIN_ALNUM_RATIO = 0.35

# Минимальная длина текста, чтобы не считать мусором короткие нормальные фразы
MIN_LENGTH_FOR_RATIO_CHECK = 80

# Паттерны начала бинарных/служебных данных (ZIP = PK, XML, HTML, OOXML)
GARBAGE_START_PATTERNS = re.compile(
    r"^(?:\s|[\x00-\x08\x0b\x0c\x0e-\x1f])*"
    r"(?:PK\s|<\?xml\s|<\s*html\s|\[Content_Types\]\.xml|"
    r"<w:document\s|xmlns:[\w-]+\s*=|<!DOCTYPE\s)",
    re.IGNORECASE | re.DOTALL
)

# Признаки мусора в коротком тексте (если длина < MIN_LENGTH_FOR_RATIO_CHECK)
GARBAGE_MARKERS = re.compile(
    r"\[Content_Types\]\.xml|word/document\.xml|_rels/\.rels|"
    r"<\?xml\s|xmlns[:=]|^\s*PK\s|^\s*<\s*\w+\s",
    re.IGNORECASE
)


def is_garbage_text(text: str) -> bool:
    """
    Возвращает True, если текст считается явно мусорным (бинарные заголовки, XML-служебный и т.п.).

    Критерии:
    - Очень короткий текст (< MIN_LENGTH) с маркерами мусора (Content_Types, xmlns, PK и т.д.).
    - Доля буквенно-цифровых/пробельных символов слишком мала (< MIN_ALNUM_RATIO).
    - Начало текста совпадает с типичными ZIP/XML/HTML заголовками.
    """
    if not text or not isinstance(text, str):
        return True
    s = text.strip()
    if len(s) < 50:
        return True
    if len(s) < MIN_LENGTH_FOR_RATIO_CHECK:
        if GARBAGE_MARKERS.search(s):
            return True
        return False
    alnum_whitespace = sum(
        1 for c in s
        if c.isalnum() or c.isspace() or c in ".,;:!?()-—–\"'«»"
    )
    ratio = alnum_whitespace / len(s)
    if ratio < MIN_ALNUM_RATIO:
        return True
    if GARBAGE_START_PATTERNS.match(s[:500]):
        return True
    return False


def clean_document_text_for_v12(text: str) -> str:
    """
    Очищает текст документа для v12: управляющие символы, лишние пробелы.
    Не меняет контракт: возвращает новую строку.
    """
    if not text or not isinstance(text, str):
        return ""
    out = []
    for c in text:
        if c in "\n\r\t ":
            out.append(c)
        elif unicodedata.category(c)[0] == "C":
            if c == "\n" or c == "\r" or c == "\t":
                out.append(c)
            else:
                out.append(" ")
        else:
            out.append(c)
    result = "".join(out)
    result = re.sub(r"[ \t]+", " ", result)
    result = re.sub(r"\n\s*\n\s*\n+", "\n\n", result)
    return result.strip()


def _first_readable_block_start(text: str, min_letters: int = 15) -> int:
    """
    Ищет начало первого «читаемого» блока: строка/участок с хотя бы min_letters
    букв (кириллица/латиница) подряд без преобладания тегов/скобок.
    """
    lines = text.replace("\r", "\n").split("\n")
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if len(line_stripped) < 10:
            continue
        letters = sum(1 for c in line_stripped if c.isalpha())
        if letters < min_letters:
            continue
        angle_brackets = line_stripped.count("<") + line_stripped.count(">")
        if angle_brackets * 2 > len(line_stripped):
            continue
        pos = text.find(line_stripped)
        if pos != -1:
            return pos
    return 0


def get_readable_start_for_v12(text: str, max_chars: int = 3000) -> str:
    """
    Возвращает фрагмент текста для v12: очищенный и обрезанный до max_chars.
    Если текст начинается с технического заголовка (XML и т.п.), пытается
    начать с первого «читаемого» блока (где есть достаточно букв).
    """
    if not text or not isinstance(text, str):
        return ""
    cleaned = clean_document_text_for_v12(text)
    if len(cleaned) <= max_chars:
        return cleaned
    start = 0
    if GARBAGE_START_PATTERNS.match(cleaned[:800]):
        start = _first_readable_block_start(cleaned)
    chunk = cleaned[start : start + max_chars]
    if not chunk.strip():
        return cleaned[:max_chars]
    return chunk
