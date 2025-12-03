"""
RAG-движок для работы с локальной векторной базой юридических документов (ChromaDB).

Назначение:
- загрузка уже проиндексированной базы из `backend/chroma_db`;
- поиск релевантных фрагментов законов по тексту тендера;
- безопасная работа: при отсутствии базы или ошибках — возврат пустого списка,
  чтобы не ломать основной анализ.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

from config import settings

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
PERSIST_DIR = BASE_DIR / "chroma_db"

_retriever = None  # type: ignore[var-annotated]
_initialized = False


def _build_embeddings() -> OllamaEmbeddings:
    """Создаёт объект эмбеддингов с приоритетом моделей qwen."""
    models_to_try = [
        "qwen2.5-coder:7b",
        "qwen2.5:0.5b",
        getattr(settings, "OLLAMA_MODEL", "qwen2.5:0.5b"),
    ]

    last_error: Optional[Exception] = None
    for m in models_to_try:
        try:
            logger.info(f"[RAG] Инициализация эмбеддингов OllamaEmbeddings (модель: {m})")
            emb = OllamaEmbeddings(model=m, base_url=settings.OLLAMA_BASE_URL)
            # Пробный запрос для проверки связи
            _ = emb.embed_query("проверка связи с RAG-моделью")
            logger.info(f"[RAG] Эмбеддинги готовы (модель: {m})")
            return emb
        except Exception as e:  # noqa: BLE001
            last_error = e
            logger.warning(f"[RAG] Не удалось инициализировать модель {m}: {e}")

    raise RuntimeError(f"[RAG] Не удалось инициализировать OllamaEmbeddings. Последняя ошибка: {last_error}")


def _init_retriever(k: int = 5):
    """Ленивая инициализация ретривера Chroma.

    Не бросает исключения наружу: при ошибке просто возвращает None.
    """
    global _retriever, _initialized

    if _initialized:
        return _retriever

    _initialized = True

    if not PERSIST_DIR.exists():
        logger.info(f"[RAG] Папка с ChromaDB не найдена: {PERSIST_DIR}. RAG будет отключён.")
        return None

    try:
        embeddings = _build_embeddings()
        vectorstore = Chroma(
            persist_directory=str(PERSIST_DIR),
            embedding_function=embeddings,
        )
        _retriever = vectorstore.as_retriever(search_kwargs={"k": k})
        logger.info(f"[RAG] Ретривер инициализирован, база: {PERSIST_DIR}")
        return _retriever
    except Exception as e:  # noqa: BLE001
        logger.error(f"[RAG] Ошибка инициализации ретривера: {e}")
        _retriever = None
        return None


def get_law_snippets(query_text: str, k: int = 5) -> List[Dict[str, Any]]:
    """Возвращает список релевантных фрагментов законов для поданного текста.

    Параметры:
        query_text: текст тендерной документации (можно передавать усечённый фрагмент).
        k: максимальное количество возвращаемых фрагментов.

    Возвращает:
        Список словарей вида:
        {
            "content": "<текст фрагмента>",
            "metadata": { ... }  # путь к файлу, страница и т.п.
        }
    """
    if not query_text or not query_text.strip():
        return []

    retriever = _init_retriever(k=k)
    if retriever is None:
        return []

    try:
        docs = retriever.get_relevant_documents(query_text)
        results: List[Dict[str, Any]] = []
        for d in docs:
            results.append(
                {
                    "content": d.page_content,
                    "metadata": getattr(d, "metadata", {}) or {},
                }
            )
        logger.info(f"[RAG] Найдено релевантных фрагментов: {len(results)}")
        return results
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[RAG] Ошибка при поиске фрагментов: {e}")
        return []




