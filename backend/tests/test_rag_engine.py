"""
Тесты для RAG-ингеста (ingest.py) и ретривера (rag_engine.py).

Важно: тесты не используют реальный Ollama/Chroma, а подменяют зависимости
фейковыми классами, чтобы не требовать запущенный ollama serve.
"""

import types
from pathlib import Path
from typing import List

import pytest

import ingest
import rag_engine


class FakeEmbeddings:
    """Простая заглушка для OllamaEmbeddings."""

    def __init__(self, *args, **kwargs):
        self.model = kwargs.get("model")

    def embed_query(self, text: str):
        # Возвращаем фиксированный вектор
        return [0.1] * 8


class FakeDoc:
    def __init__(self, content: str, metadata=None):
        self.page_content = content
        self.metadata = metadata or {}


class FakeChromaFromDocuments:
    """Заглушка для Chroma.from_documents, чтобы не ходить в реальную БД."""

    def __init__(self, documents, embedding, persist_directory):
        self.documents = documents
        self.embedding = embedding
        self.persist_directory = persist_directory

    def persist(self):
        # Ничего не делаем, но можно проверить, что метод вызывается
        pass


class FakeRetriever:
    def __init__(self, docs: List[FakeDoc]):
        self._docs = docs

    def get_relevant_documents(self, query: str):
        # Для простоты всегда возвращаем все документы
        return self._docs


class FakeChroma:
    """Заглушка для Chroma в rag_engine."""

    def __init__(self, persist_directory, embedding_function):
        self.persist_directory = persist_directory
        self.embedding_function = embedding_function
        # Подготовим тестовые документы
        self._docs = [
            FakeDoc("Штраф за просрочку 0.1% в день.", {"source": "44-ФЗ тест"}),
            FakeDoc("Обеспечение заявки 5% от НМЦК.", {"source": "44-ФЗ тест"}),
        ]

    @classmethod
    def from_documents(cls, documents, embedding, persist_directory):
        # Используется только в ingest, там мы подменяем отдельно
        return FakeChromaFromDocuments(documents, embedding, persist_directory)

    def as_retriever(self, search_kwargs=None):
        return FakeRetriever(self._docs)


@pytest.mark.asyncio
async def test_ingest_docs_creates_chunks_and_calls_chroma(tmp_path, monkeypatch):
    """Проверяем, что ingest_docs:
    - находит файлы в knowledge;
    - режет их на чанки;
    - вызывает Chroma.from_documents с непустым списком документов.
    """

    # Подменяем директории на временные
    knowledge_dir = tmp_path / "knowledge"
    chroma_dir = tmp_path / "chroma_db"
    knowledge_dir.mkdir(parents=True, exist_ok=True)

    # Создаём простой текстовый "закон"
    sample_file = knowledge_dir / "law_snippet.txt"
    sample_file.write_text("Штраф за просрочку составляет 0.1% в день от суммы контракта.", encoding="utf-8")

    monkeypatch.setattr(ingest, "KNOWLEDGE_DIR", knowledge_dir, raising=False)
    monkeypatch.setattr(ingest, "PERSIST_DIR", chroma_dir, raising=False)

    # Подменяем эмбеддинги и Chroma
    monkeypatch.setattr(ingest, "OllamaEmbeddings", FakeEmbeddings, raising=True)

    called = {}

    def fake_from_documents(documents, embedding, persist_directory):
        # Сохраняем информацию о вызове
        called["count"] = len(documents)
        called["persist_directory"] = persist_directory
        return FakeChromaFromDocuments(documents, embedding, persist_directory)

    monkeypatch.setattr(ingest.Chroma, "from_documents", staticmethod(fake_from_documents))

    # Запускаем индексацию
    ingest.ingest_docs()

    # Проверяем, что были созданы чанки и Chroma.from_documents вызван
    assert "count" in called
    assert called["count"] > 0
    assert Path(called["persist_directory"]).exists()


def test_get_law_snippets_returns_results(monkeypatch, tmp_path):
    """Проверяем, что rag_engine.get_law_snippets возвращает данные,
    когда Chroma и эмбеддинги подменены заглушками.
    """

    # Подменяем путь к базе на временный (условно существующий)
    chroma_dir = tmp_path / "chroma_db"
    chroma_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(rag_engine, "PERSIST_DIR", chroma_dir, raising=False)

    # Подменяем зависимости
    monkeypatch.setattr(rag_engine, "OllamaEmbeddings", FakeEmbeddings, raising=True)
    monkeypatch.setattr(rag_engine, "Chroma", FakeChroma, raising=True)

    # Сбрасываем внутреннее состояние ретривера
    rag_engine._retriever = None
    rag_engine._initialized = False

    snippets = rag_engine.get_law_snippets("штраф за просрочку 0.1%", k=2)

    assert isinstance(snippets, list)
    assert len(snippets) > 0
    assert any("штраф" in s["content"].lower() for s in snippets)





