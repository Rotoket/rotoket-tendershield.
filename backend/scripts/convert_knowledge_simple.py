"""
Простой скрипт для конвертации документов из backend/knowledge в Markdown
Использует Pandoc если доступен, иначе fallback на langchain loaders
"""

import os
import sys
from pathlib import Path
import logging
import subprocess

# Добавляем backend в путь
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Пути
BACKEND_KNOWLEDGE_DIR = BACKEND_DIR / "knowledge"
PROJECT_ROOT = BACKEND_DIR.parent
KNOWLEDGE_ROOT = PROJECT_ROOT / "knowledge"
KNOWLEDGE_LAWS_DIR = KNOWLEDGE_ROOT / "laws"
KNOWLEDGE_TEMPLATES_DIR = KNOWLEDGE_ROOT / "templates"

def check_pandoc() -> bool:
    """Проверяет доступность Pandoc"""
    try:
        result = subprocess.run(['pandoc', '--version'], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def convert_with_pandoc(input_path: Path, output_path: Path) -> bool:
    """Конвертирует файл через Pandoc"""
    try:
        cmd = ['pandoc', str(input_path), '-f', 'pdf', '-t', 'markdown', '-o', str(output_path)]
        if input_path.suffix.lower() in {'.docx', '.doc'}:
            cmd[2] = 'docx'
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return True
        else:
            logger.warning(f"Pandoc вернул код {result.returncode}: {result.stderr}")
            return False
    except Exception as e:
        logger.warning(f"Ошибка Pandoc: {e}")
        return False

def convert_with_langchain(input_path: Path) -> str:
    """Конвертирует файл через langchain loaders (fallback)"""
    try:
        from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader
        
        ext = input_path.suffix.lower()
        if ext == ".pdf":
            loader = PyMuPDFLoader(str(input_path))
        elif ext in {".docx", ".doc"}:
            loader = Docx2txtLoader(str(input_path))
        else:
            return ""
        
        docs = loader.load()
        content = "\n\n".join([doc.page_content for doc in docs])
        return content
    except Exception as e:
        logger.error(f"Ошибка langchain: {e}")
        return ""

def extract_law_metadata(filename: str) -> dict:
    """Извлекает метаданные закона из имени файла"""
    filename_lower = filename.lower()
    
    metadata = {
        "legal_basis": "CUSTOM",
        "applicable_to": [],
        "tags": [],
        "doc_type": "law",
        "title": filename.replace(".pdf", "").replace(".docx", "").replace(".doc", ""),
    }
    
    # Определяем закон
    if "44-фз" in filename_lower or "44 фз" in filename_lower:
        metadata["legal_basis"] = "FZ_44"
        metadata["applicable_to"] = ["44-ФЗ"]
        metadata["tags"] = ["контрактация", "закупки", "государственные закупки"]
        metadata["title"] = "Федеральный закон 44-ФЗ о контрактной системе (полный текст)"
        metadata["output_name"] = "fz-44-2013-full.md"
    elif "223-фз" in filename_lower or "223 фз" in filename_lower:
        metadata["legal_basis"] = "FZ_223"
        metadata["applicable_to"] = ["223-ФЗ"]
        metadata["tags"] = ["закупки", "госкорпорации", "естественные монополии"]
        metadata["title"] = "Федеральный закон 223-ФЗ о закупках отдельными видами юридических лиц (полный текст)"
        metadata["output_name"] = "fz-223-2011-full.md"
    elif "135-фз" in filename_lower or "135 фз" in filename_lower:
        metadata["legal_basis"] = "FZ_135"
        metadata["applicable_to"] = ["44-ФЗ", "223-ФЗ"]
        metadata["tags"] = ["антимонопольное", "конкуренция", "защита"]
        metadata["title"] = "Федеральный закон 135-ФЗ о защите конкуренции (полный текст)"
        metadata["output_name"] = "fz-135-2004-full.md"
    elif "152-фз" in filename_lower or "152 фз" in filename_lower:
        metadata["legal_basis"] = "FZ_152"
        metadata["applicable_to"] = ["44-ФЗ", "223-ФЗ"]
        metadata["tags"] = ["персональные данные", "ПДН", "конфиденциальность"]
        metadata["title"] = "Федеральный закон 152-ФЗ о персональных данных (полный текст)"
        metadata["output_name"] = "fz-152-2006-full.md"
    elif "272-фз" in filename_lower or "272 фз" in filename_lower:
        metadata["legal_basis"] = "FZ_272"
        metadata["applicable_to"] = ["44-ФЗ", "223-ФЗ"]
        metadata["tags"] = ["осмотр", "испытание", "товары"]
        metadata["title"] = "Федеральный закон 272-ФЗ об осмотре и испытании товаров (полный текст)"
        metadata["output_name"] = "fz-272-2012-full.md"
    elif "нмцк" in filename_lower or "расчет" in filename_lower or "rashet" in filename_lower:
        metadata["legal_basis"] = "FZ_44"
        metadata["applicable_to"] = ["44-ФЗ"]
        metadata["tags"] = ["нмцк", "расчет", "обоснование", "шаблон"]
        metadata["title"] = "Шаблон расчета НМЦК"
        metadata["doc_type"] = "template"
        metadata["output_name"] = "nmck-calculation-template.md"
    elif "постановление" in filename_lower:
        metadata["tags"] = ["постановление", "правительство"]
        metadata["title"] = filename.replace(".pdf", "").replace(".docx", "").replace(".doc", "")
        # Сохраняем в laws/ с оригинальным именем
        safe_name = filename.replace(".pdf", "").replace(".docx", "").replace(".doc", "")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in (' ', '-', '_')).strip()
        metadata["output_name"] = safe_name + ".md"
    else:
        # Неизвестный файл - сохраняем с оригинальным именем
        safe_name = filename.replace(".pdf", "").replace(".docx", "").replace(".doc", "")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in (' ', '-', '_')).strip()
        metadata["output_name"] = safe_name + ".md"
    
    return metadata

def main():
    """Основная функция конвертации"""
    if not BACKEND_KNOWLEDGE_DIR.exists():
        logger.error(f"❌ Папка {BACKEND_KNOWLEDGE_DIR} не найдена")
        return
    
    # Создаем папки
    KNOWLEDGE_LAWS_DIR.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Проверяем Pandoc
    has_pandoc = check_pandoc()
    if has_pandoc:
        logger.info("✅ Pandoc доступен, будет использован для конвертации")
    else:
        logger.warning("⚠️ Pandoc недоступен, будет использован fallback (langchain)")
    
    logger.info(f"📚 Конвертация документов из {BACKEND_KNOWLEDGE_DIR}...")
    
    converted = 0
    skipped = 0
    errors = 0
    
    for file_path in sorted(BACKEND_KNOWLEDGE_DIR.iterdir()):
        if file_path.is_dir():
            continue
        
        ext = file_path.suffix.lower()
        if ext not in {".pdf", ".docx", ".doc"}:
            logger.info(f"  ⏭️ Пропущен (неподдерживаемый формат): {file_path.name}")
            skipped += 1
            continue
        
        logger.info(f"  📄 Конвертация: {file_path.name}...")
        
        # Извлекаем метаданные
        metadata = extract_law_metadata(file_path.name)
        output_name = metadata.get("output_name", file_path.stem + ".md")
        
        # Определяем папку назначения
        if metadata.get("doc_type") == "template":
            output_dir = KNOWLEDGE_TEMPLATES_DIR
        else:
            output_dir = KNOWLEDGE_LAWS_DIR
        
        output_path = output_dir / output_name
        
        # Пропускаем если файл уже существует
        if output_path.exists():
            logger.info(f"  ⏭️ Пропущен (уже существует): {output_path.name}")
            skipped += 1
            continue
        
        # Конвертируем
        content = ""
        if has_pandoc:
            # Пробуем через Pandoc
            temp_output = output_path.with_suffix('.temp.md')
            if convert_with_pandoc(file_path, temp_output):
                try:
                    with open(temp_output, 'r', encoding='utf-8') as f:
                        content = f.read()
                    temp_output.unlink()  # Удаляем временный файл
                except Exception as e:
                    logger.warning(f"  ⚠️ Ошибка чтения Pandoc output: {e}")
                    content = convert_with_langchain(file_path)
            else:
                # Fallback на langchain
                content = convert_with_langchain(file_path)
        else:
            # Используем langchain
            content = convert_with_langchain(file_path)
        
        if not content:
            logger.error(f"  ❌ Не удалось конвертировать: {file_path.name}")
            errors += 1
            continue
        
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
        
        # Сохраняем
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            converted += 1
            logger.info(f"  ✅ Сохранен: {output_path}")
        except Exception as e:
            errors += 1
            logger.error(f"  ❌ Ошибка сохранения {output_path}: {e}")
    
    logger.info(f"\n{'='*60}")
    logger.info(f"✅ Конвертация завершена:")
    logger.info(f"  - Конвертировано: {converted}")
    logger.info(f"  - Пропущено: {skipped}")
    logger.info(f"  - Ошибок: {errors}")
    logger.info(f"{'='*60}")

if __name__ == "__main__":
    main()


