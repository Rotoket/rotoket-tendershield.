"""
Легкая индексация для быстрого поиска по базе знаний без эмбеддингов.
Создает простой текстовый индекс для мгновенного поиска.
"""

import logging
import os
from pathlib import Path
from typing import List, Dict, Any
import json
import re

from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader, TextLoader

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
INDEX_FILE = BASE_DIR / "knowledge_index.json"

# Кеш индекса в памяти
_index_cache: Dict[str, Any] = {}


def _load_documents() -> List[Dict[str, Any]]:
    """Загружает документы из папки knowledge и создает легкий индекс."""
    if not KNOWLEDGE_DIR.exists():
        logger.warning(f"Папка с документами не найдена: {KNOWLEDGE_DIR}")
        return []
    
    documents = []
    supported_ext = {".pdf", ".docx", ".doc", ".txt"}
    
    for root, _, files in os.walk(KNOWLEDGE_DIR):
        for name in files:
            path = Path(root) / name
            ext = path.suffix.lower()
            if ext not in supported_ext:
                continue
            
            try:
                if ext == ".pdf":
                    loader = PyMuPDFLoader(str(path))
                elif ext in {".docx", ".doc"}:
                    loader = Docx2txtLoader(str(path))
                else:  # .txt
                    loader = TextLoader(str(path), encoding="utf-8")
                
                file_docs = loader.load()
                
                # Разбиваем на чанки по 500 символов для быстрого поиска
                for idx, doc in enumerate(file_docs):
                    content = doc.page_content
                    # Разбиваем на предложения для лучшего поиска
                    sentences = re.split(r'[.!?]\s+', content)
                    chunk_size = 500
                    
                    current_chunk = ""
                    chunk_idx = 0
                    
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) < chunk_size:
                            current_chunk += sentence + ". "
                        else:
                            if current_chunk:
                                documents.append({
                                    "id": f"{path.stem}_{chunk_idx}",
                                    "file": name,
                                    "path": str(path),
                                    "content": current_chunk.strip(),
                                    "law": _extract_law_reference(name, current_chunk),
                                })
                                chunk_idx += 1
                            current_chunk = sentence + ". "
                    
                    # Добавляем последний чанк
                    if current_chunk:
                        documents.append({
                            "id": f"{path.stem}_{chunk_idx}",
                            "file": name,
                            "path": str(path),
                            "content": current_chunk.strip(),
                            "law": _extract_law_reference(name, current_chunk),
                        })
                
                logger.info(f"  ✓ Проиндексирован файл: {name} ({len(file_docs)} фрагментов)")
            except Exception as e:
                logger.warning(f"  ⚠️ Не удалось прочитать файл {path}: {e}")
    
    return documents


def _extract_law_reference(filename: str, content: str) -> str:
    """Извлекает ссылку на закон из имени файла или содержимого."""
    filename_lower = filename.lower()
    content_lower = content.lower()
    
    if "44-фз" in filename_lower or "44-фз" in content_lower or "44 фз" in content_lower:
        return "44-ФЗ"
    elif "223-фз" in filename_lower or "223-фз" in content_lower or "223 фз" in content_lower:
        return "223-ФЗ"
    elif "135-фз" in filename_lower or "135-фз" in content_lower:
        return "135-ФЗ"
    elif "152-фз" in filename_lower or "152-фз" in content_lower:
        return "152-ФЗ"
    elif "нмцк" in filename_lower or "нмцк" in content_lower:
        return "44-ФЗ (НМЦК)"
    else:
        return "Норма закона"


def build_index() -> Dict[str, Any]:
    """Строит легкий индекс документов."""
    logger.info("🔍 Построение легкого индекса базы знаний...")
    
    documents = _load_documents()
    
    index = {
        "version": "1.0",
        "total_documents": len(documents),
        "documents": documents,
    }
    
    # Сохраняем индекс в файл
    try:
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Индекс сохранен: {INDEX_FILE} ({len(documents)} документов)")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения индекса: {e}")
    
    return index


def load_index() -> Dict[str, Any]:
    """Загружает индекс из файла или строит заново."""
    global _index_cache
    
    if _index_cache:
        return _index_cache
    
    # Пробуем загрузить из файла
    if INDEX_FILE.exists():
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                _index_cache = json.load(f)
            logger.info(f"✅ Индекс загружен из файла: {len(_index_cache.get('documents', []))} документов")
            return _index_cache
        except Exception as e:
            logger.warning(f"⚠️ Не удалось загрузить индекс: {e}. Строим заново...")
    
    # Строим новый индекс
    _index_cache = build_index()
    return _index_cache


def search_fast(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Быстрый текстовый поиск по индексу без эмбеддингов.
    
    Args:
        query: Поисковый запрос
        limit: Максимальное количество результатов
    
    Returns:
        Список найденных документов
    """
    if not query or not query.strip():
        return []
    
    index = load_index()
    documents = index.get("documents", [])
    
    if not documents:
        logger.warning("[Fast Search] Индекс пуст. Запустите build_index() для создания индекса.")
        return []
    
    query_lower = query.lower()
    query_words = query_lower.split()
    
    results = []
    scores = {}
    
    # Простой поиск по словам с подсчетом релевантности
    for doc in documents:
        content_lower = doc.get("content", "").lower()
        file_lower = doc.get("file", "").lower()
        
        score = 0
        
        # Точное совпадение запроса
        if query_lower in content_lower:
            score += 10
        
        # Поиск по словам
        for word in query_words:
            if len(word) < 3:  # Пропускаем короткие слова
                continue
            # Подсчет вхождений
            count = content_lower.count(word)
            score += count * 2
            
            # Бонус за вхождение в название файла
            if word in file_lower:
                score += 5
        
        if score > 0:
            scores[doc["id"]] = score
            results.append({
                "id": doc["id"],
                "file": doc["file"],
                "path": doc["path"],
                "content": doc["content"][:300] + "..." if len(doc["content"]) > 300 else doc["content"],
                "law": doc.get("law", "Норма закона"),
                "score": score,
            })
    
    # Сортируем по релевантности
    results.sort(key=lambda x: x["score"], reverse=True)
    
    # Берем топ результатов
    top_results = results[:limit]
    
    logger.info(f"[Fast Search] Найдено результатов: {len(top_results)} по запросу '{query}'")
    return top_results


if __name__ == "__main__":
    # Строим индекс при запуске скрипта
    logging.basicConfig(level=logging.INFO)
    build_index()





















