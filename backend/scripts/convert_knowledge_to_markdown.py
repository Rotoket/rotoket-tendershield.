"""
Скрипт для конвертации документов из backend/knowledge в Markdown
для Knowledge Base v3.0

Использование:
    python backend/scripts/convert_knowledge_to_markdown.py
"""

import os
import sys
from pathlib import Path
import logging

# Добавляем backend в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader
from services.pandoc_service import docx_to_markdown, PandocServiceError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Пути
BACKEND_DIR = Path(__file__).parent.parent
BACKEND_KNOWLEDGE_DIR = BACKEND_DIR / "knowledge"
KNOWLEDGE_ROOT = BACKEND_DIR.parent / "knowledge"
KNOWLEDGE_LAWS_DIR = KNOWLEDGE_ROOT / "laws"

def convert_pdf_to_markdown(pdf_path: Path) -> str:
    """Конвертирует PDF в Markdown"""
    try:
        loader = PyMuPDFLoader(str(pdf_path))
        docs = loader.load()
        
        # Объединяем все страницы
        content = "\n\n".join([doc.page_content for doc in docs])
        
        # Базовое форматирование
        content = content.replace("\n\n\n", "\n\n")
        
        return content
    except Exception as e:
        logger.error(f"Ошибка конвертации PDF {pdf_path}: {e}")
        return ""

def convert_docx_to_markdown(docx_path: Path) -> str:
    """Конвертирует DOCX в Markdown (с приоритетом Pandoc)"""
    try:
        # Пробуем через Pandoc (лучше для таблиц)
        try:
            markdown = docx_to_markdown(str(docx_path))
            return markdown
        except (PandocServiceError, Exception) as e:
            logger.warning(f"Pandoc недоступен для {docx_path}, используем fallback: {e}")
        
        # Fallback: через Docx2txtLoader
        loader = Docx2txtLoader(str(docx_path))
        docs = loader.load()
        content = "\n\n".join([doc.page_content for doc in docs])
        return content
    except Exception as e:
        logger.error(f"Ошибка конвертации DOCX {docx_path}: {e}")
        return ""

def extract_law_metadata(filename: str, content: str) -> dict:
    """Извлекает метаданные закона из имени файла и содержимого"""
    filename_lower = filename.lower()
    content_lower = content.lower()
    
    metadata = {
        "legal_basis": "CUSTOM",
        "applicable_to": [],
        "tags": [],
        "doc_type": "law",
        "title": filename.replace(".pdf", "").replace(".docx", "").replace(".doc", ""),
    }
    
    # Определяем закон
    if "44-фз" in filename_lower or "44-фз" in content_lower or "44 фз" in content_lower:
        metadata["legal_basis"] = "FZ_44"
        metadata["applicable_to"] = ["44-ФЗ"]
        metadata["tags"] = ["контрактация", "закупки", "государственные закупки"]
        metadata["title"] = "Федеральный закон 44-ФЗ о контрактной системе"
    elif "223-фз" in filename_lower or "223-фз" in content_lower or "223 фз" in content_lower:
        metadata["legal_basis"] = "FZ_223"
        metadata["applicable_to"] = ["223-ФЗ"]
        metadata["tags"] = ["закупки", "госкорпорации", "естественные монополии"]
        metadata["title"] = "Федеральный закон 223-ФЗ о закупках отдельными видами юридических лиц"
    elif "135-фз" in filename_lower or "135-фз" in content_lower:
        metadata["legal_basis"] = "FZ_135"
        metadata["applicable_to"] = ["44-ФЗ", "223-ФЗ"]
        metadata["tags"] = ["антимонопольное", "конкуренция", "защита"]
        metadata["title"] = "Федеральный закон 135-ФЗ о защите конкуренции"
    elif "152-фз" in filename_lower or "152-фз" in content_lower:
        metadata["legal_basis"] = "FZ_152"
        metadata["applicable_to"] = ["44-ФЗ", "223-ФЗ"]
        metadata["tags"] = ["персональные данные", "ПДН", "конфиденциальность"]
        metadata["title"] = "Федеральный закон 152-ФЗ о персональных данных"
    elif "272-фз" in filename_lower or "272-фз" in content_lower:
        metadata["legal_basis"] = "FZ_272"
        metadata["applicable_to"] = ["44-ФЗ", "223-ФЗ"]
        metadata["tags"] = ["осмотр", "испытание", "товары"]
        metadata["title"] = "Федеральный закон 272-ФЗ об осмотре и испытании товаров"
    elif "нмцк" in filename_lower or "расчет" in filename_lower:
        metadata["legal_basis"] = "FZ_44"
        metadata["applicable_to"] = ["44-ФЗ"]
        metadata["tags"] = ["нмцк", "расчет", "обоснование"]
        metadata["title"] = f"Обоснование НМЦК: {filename}"
        metadata["doc_type"] = "template"
    elif "постановление" in filename_lower:
        metadata["tags"] = ["постановление", "правительство"]
        metadata["title"] = filename.replace(".pdf", "").replace(".docx", "").replace(".doc", "")
    
    return metadata

def convert_file_to_markdown(file_path: Path) -> tuple[str, dict]:
    """Конвертирует файл в Markdown и возвращает контент + метаданные"""
    ext = file_path.suffix.lower()
    
    if ext == ".pdf":
        content = convert_pdf_to_markdown(file_path)
    elif ext in {".docx", ".doc"}:
        content = convert_docx_to_markdown(file_path)
    else:
        logger.warning(f"Неподдерживаемый формат: {ext}")
        return "", {}
    
    if not content:
        return "", {}
    
    metadata = extract_law_metadata(file_path.name, content)
    
    # Формируем Markdown с метаданными
    metadata_yaml = f"""---
legal_basis: {metadata['legal_basis']}
applicable_to: {metadata['applicable_to']}
tags: {metadata['tags']}
doc_type: "{metadata['doc_type']}"
title: "{metadata['title']}"
source_file: "{file_path.name}"
---

"""
    
    markdown_content = metadata_yaml + f"# {metadata['title']}\n\n" + content
    
    return markdown_content, metadata

def main():
    """Основная функция конвертации"""
    if not BACKEND_KNOWLEDGE_DIR.exists():
        logger.error(f"Папка {BACKEND_KNOWLEDGE_DIR} не найдена")
        return
    
    # Создаем папку для законов
    KNOWLEDGE_LAWS_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"📚 Конвертация документов из {BACKEND_KNOWLEDGE_DIR}...")
    
    converted = 0
    skipped = 0
    errors = 0
    
    for file_path in BACKEND_KNOWLEDGE_DIR.iterdir():
        if file_path.is_dir():
            continue
        
        ext = file_path.suffix.lower()
        if ext not in {".pdf", ".docx", ".doc"}:
            continue
        
        logger.info(f"  Конвертация: {file_path.name}...")
        
        markdown_content, metadata = convert_file_to_markdown(file_path)
        
        if not markdown_content:
            errors += 1
            logger.warning(f"  ⚠️ Не удалось конвертировать: {file_path.name}")
            continue
        
        # Определяем имя выходного файла
        output_name = file_path.stem + ".md"
        
        # Если это закон - используем стандартное имя
        if metadata.get("legal_basis") == "FZ_44":
            output_name = "fz-44-2013-full.md"
        elif metadata.get("legal_basis") == "FZ_223":
            output_name = "fz-223-2011-full.md"
        elif metadata.get("legal_basis") == "FZ_135":
            output_name = "fz-135-2004-full.md"
        elif metadata.get("legal_basis") == "FZ_152":
            output_name = "fz-152-2006-full.md"
        elif metadata.get("legal_basis") == "FZ_272":
            output_name = "fz-272-2012-full.md"
        elif "нмцк" in file_path.name.lower() or "расчет" in file_path.name.lower():
            # Это шаблон обоснования НМЦК
            output_name = "nmck-calculation-template.md"
            # Сохраняем в templates/
            output_path = KNOWLEDGE_TEMPLATES_DIR / output_name
        else:
            # Сохраняем в laws/ с оригинальным именем
            output_path = KNOWLEDGE_LAWS_DIR / output_name
        
        # Сохраняем
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            converted += 1
            logger.info(f"  ✅ Сохранен: {output_path}")
        except Exception as e:
            errors += 1
            logger.error(f"  ❌ Ошибка сохранения {output_path}: {e}")
    
    logger.info(f"\n✅ Конвертация завершена:")
    logger.info(f"  - Конвертировано: {converted}")
    logger.info(f"  - Пропущено: {skipped}")
    logger.info(f"  - Ошибок: {errors}")

if __name__ == "__main__":
    main()

