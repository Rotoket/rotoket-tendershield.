"""
Скрипт индексации юридических документов (RAG) в локальную векторную базу ChromaDB.

Идея:
- читаем все файлы из папки `backend/knowledge` (.pdf / .docx / .doc / .txt);
- режем на чанки (chunk_size=1000, chunk_overlap=200);
- считаем эмбеддинги через OllamaEmbeddings (qwen2.5-coder:7b, fallback: qwen2.5:0.5b или settings.OLLAMA_MODEL);
- сохраняем в `backend/chroma_db` (пересоздаём, если уже была).

Запуск:

    cd backend
    python ingest.py
"""

import logging
import os
import shutil
from pathlib import Path
from typing import List

from langchain_ollama import OllamaEmbeddings
from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader, TextLoader
from langchain_community.vectorstores import Chroma

try:
    # Предпочтительно использовать новый пакет текстовых сплиттеров
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    # Fallback на старый путь, если отдельный пакет не установлен
    from langchain.text_splitter import RecursiveCharacterTextSplitter

from config import settings


logger = logging.getLogger("ingest")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
PERSIST_DIR = BASE_DIR / "chroma_db"


def _load_documents() -> List:
    """Загружает документы из папки knowledge.

    Поддерживаемые форматы:
      - .pdf  (PyMuPDFLoader)
      - .docx / .doc (Docx2txtLoader)
      - .txt  (TextLoader)
    """
    if not KNOWLEDGE_DIR.exists():
        logger.warning(f"Папка с документами не найдена: {KNOWLEDGE_DIR}. Создаю пустую.")
        KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
        return []

    logger.info(f"📚 Поиск документов в {KNOWLEDGE_DIR} ...")
    docs: List = []
    supported_ext = {".pdf", ".docx", ".doc", ".txt"}

    count_files = 0
    for root, _, files in os.walk(KNOWLEDGE_DIR):
        for name in files:
            path = Path(root) / name
            ext = path.suffix.lower()
            if ext not in supported_ext:
                continue
            count_files += 1
            try:
                if ext == ".pdf":
                    loader = PyMuPDFLoader(str(path))
                elif ext in {".docx", ".doc"}:
                    loader = Docx2txtLoader(str(path))
                else:  # .txt
                    loader = TextLoader(str(path), encoding="utf-8")

                file_docs = loader.load()
                docs.extend(file_docs)
                logger.info(f"  ✓ Загружен файл: {path} (фрагментов: {len(file_docs)})")
            except Exception as e:
                logger.warning(f"  ⚠️ Не удалось прочитать файл {path}: {e}. Пропускаю.")

    logger.info(f"✅ Найдено файлов: {count_files}, всего документов (страниц/фрагментов): {len(docs)}")
    return docs


def _build_embeddings() -> OllamaEmbeddings:
    """Создаёт объект эмбеддингов с приоритетом qwen2.5-coder:7b, затем fallback."""
    models_to_try = [
        "qwen2.5-coder:7b",
        "qwen2.5:0.5b",
        getattr(settings, "OLLAMA_MODEL", "qwen2.5:0.5b"),
    ]

    last_error = None
    for m in models_to_try:
        try:
            logger.info(f"🔤 Инициализация эмбеддингов OllamaEmbeddings (модель: {m}, base_url={settings.OLLAMA_BASE_URL})")
            emb = OllamaEmbeddings(model=m, base_url=settings.OLLAMA_BASE_URL)
            # Пробный вызов, чтобы убедиться, что модель реально доступна
            _ = emb.embed_query("тестовая проверка подключения")
            logger.info(f"✅ Эмбеддинги инициализированы (модель: {m})")
            return emb
        except Exception as e:
            last_error = e
            logger.warning(f"⚠️ Не удалось инициализировать эмбеддинги для модели {m}: {e}")

    raise RuntimeError(f"Не удалось инициализировать OllamaEmbeddings. Последняя ошибка: {last_error}")


def ingest_docs() -> None:
    """Основной процесс индексации документов в ChromaDB."""
    logger.info("🚀 Запуск процесса индексации документов (RAG / ChromaDB)")

    # 1. Загружаем документы
    documents = _load_documents()
    if not documents:
        logger.warning("⚠️ Не найдено ни одного документа для индексации. Добавьте файлы в папку `backend/knowledge`.")
        return

    # 2. Разбиваем на чанки
    logger.info("✂️  Нарезка документов на чанки...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(documents)
    logger.info(f"✅ Создано чанков: {len(chunks)}")

    # 3. Пересоздаём папку для ChromaDB
    if PERSIST_DIR.exists():
        logger.info(f"🧹 Удаляю старую базу ChromaDB: {PERSIST_DIR}")
        shutil.rmtree(PERSIST_DIR, ignore_errors=True)
    PERSIST_DIR.mkdir(parents=True, exist_ok=True)

    # 4. Эмбеддинги
    embeddings = _build_embeddings()

    # 5. Создание и сохранение ChromaDB
    logger.info(f"💾 Создание векторной базы ChromaDB в {PERSIST_DIR} ...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(PERSIST_DIR),
    )
    vectorstore.persist()
    logger.info("🎉 Индексация завершена. Векторная база успешно создана.")


if __name__ == "__main__":
    try:
        ingest_docs()
    except Exception as exc:
        logger.error(f"❌ Ошибка при индексации документов: {exc}")


