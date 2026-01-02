"""
MCP Client для работы со справочным слоем знаний.

ВАЖНО: MCP используется ТОЛЬКО для объяснений и справочной информации.
MCP НЕ влияет на Decision Engine, scoring, deal breakers, решения.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
import re

from config import settings

logger = logging.getLogger(__name__)


class MCPClient:
    """Клиент для работы с MCP-контентом (пока на локальных файлах)."""

    def __init__(self):
        self.enabled = settings.MCP_ENABLED
        self.content_path = Path(settings.MCP_CONTENT_PATH)
        self.disclaimer = self._load_disclaimer()

    def _load_disclaimer(self) -> str:
        """Загружает текст дисклеймера."""
        disclaimer_path = self.content_path / "disclaimer.md"
        if disclaimer_path.exists():
            try:
                return disclaimer_path.read_text(encoding="utf-8").strip()
            except Exception as e:
                logger.warning(f"Не удалось загрузить disclaimer: {e}")
        return "Информация носит справочный характер, не является юридическим заключением и не заменяет профессиональную правовую консультацию."

    def _find_law_file(self, law_code: str) -> Optional[Path]:
        """Находит файл закона по коду (44-ФЗ, 223-ФЗ и т.д.)."""
        # Нормализуем код: убираем пробелы, приводим к нужному формату
        law_code = law_code.replace(" ", "").replace("ФЗ", "-ФЗ").upper()
        if not law_code.endswith("-ФЗ"):
            law_code = law_code + "-ФЗ"
        
        # Пробуем разные варианты
        variants = [
            law_code,
            law_code.replace("-ФЗ", "FZ"),
            law_code.replace("-", "_"),
        ]
        
        laws_dir = self.content_path / "laws"
        for variant in variants:
            file_path = laws_dir / f"{variant}.md"
            if file_path.exists():
                return file_path
        
        return None

    def _find_pattern_file(self, pattern_name: str) -> Optional[Path]:
        """Находит файл паттерна по имени."""
        patterns_dir = self.content_path / "patterns"
        # Пробуем точное совпадение и варианты с подчёркиваниями/дефисами
        variants = [
            pattern_name,
            pattern_name.replace("_", "-"),
            pattern_name.replace("-", "_"),
        ]
        
        for variant in variants:
            file_path = patterns_dir / f"{variant}.md"
            if file_path.exists():
                return file_path
        
        return None

    def _find_glossary_file(self, term: str) -> Optional[Path]:
        """Находит файл глоссария по термину."""
        glossary_dir = self.content_path / "glossary"
        # Нормализуем термин
        term = term.lower().replace(" ", "_").replace("-", "_")
        
        variants = [
            term,
            term.replace("_", "-"),
        ]
        
        for variant in variants:
            file_path = glossary_dir / f"{variant}.md"
            if file_path.exists():
                return file_path
        
        return None

    def _search_content(self, query: str) -> List[Dict[str, Any]]:
        """Ищет контент по ключевым словам во всех файлах."""
        results = []
        query_lower = query.lower()
        
        # Ищем в laws
        laws_dir = self.content_path / "laws"
        if laws_dir.exists():
            for file_path in laws_dir.glob("*.md"):
                try:
                    content = file_path.read_text(encoding="utf-8")
                    if query_lower in content.lower():
                        results.append({
                            "type": "law",
                            "file": file_path.name,
                            "path": str(file_path.relative_to(self.content_path)),
                            "content": content[:500] + "..." if len(content) > 500 else content
                        })
                except Exception as e:
                    logger.warning(f"Ошибка чтения {file_path}: {e}")
        
        # Ищем в patterns
        patterns_dir = self.content_path / "patterns"
        if patterns_dir.exists():
            for file_path in patterns_dir.glob("*.md"):
                try:
                    content = file_path.read_text(encoding="utf-8")
                    if query_lower in content.lower():
                        results.append({
                            "type": "pattern",
                            "file": file_path.name,
                            "path": str(file_path.relative_to(self.content_path)),
                            "content": content[:500] + "..." if len(content) > 500 else content
                        })
                except Exception as e:
                    logger.warning(f"Ошибка чтения {file_path}: {e}")
        
        # Ищем в glossary
        glossary_dir = self.content_path / "glossary"
        if glossary_dir.exists():
            for file_path in glossary_dir.glob("*.md"):
                try:
                    content = file_path.read_text(encoding="utf-8")
                    if query_lower in content.lower():
                        results.append({
                            "type": "glossary",
                            "file": file_path.name,
                            "path": str(file_path.relative_to(self.content_path)),
                            "content": content
                        })
                except Exception as e:
                    logger.warning(f"Ошибка чтения {file_path}: {e}")
        
        return results

    async def explain_legal(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        analysis_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Объясняет правовой вопрос на основе MCP-контента.
        
        Args:
            question: Вопрос пользователя
            context: Дополнительный контекст (lawCode, pattern, term и т.д.)
            user_id: ID пользователя (для логирования)
            analysis_id: ID анализа (для логирования)
        
        Returns:
            {
                "explanation": str,
                "sources": List[str],
                "disclaimer": str
            }
        """
        if not self.enabled:
            return {
                "explanation": "Справочный слой временно недоступен.",
                "sources": [],
                "disclaimer": self.disclaimer
            }
        
        # Логируем запрос
        logger.info(
            f"MCP explain request: question='{question[:100]}', "
            f"user_id={user_id}, analysis_id={analysis_id}, context={context}"
        )
        
        sources = []
        explanation_parts = []
        
        # Если в контексте указан конкретный закон, паттерн или термин
        if context:
            # Закон
            if "lawCode" in context:
                law_file = self._find_law_file(context["lawCode"])
                if law_file:
                    try:
                        content = law_file.read_text(encoding="utf-8")
                        explanation_parts.append(content)
                        sources.append(str(law_file.relative_to(self.content_path)))
                    except Exception as e:
                        logger.warning(f"Ошибка чтения {law_file}: {e}")
            
            # Паттерн
            if "pattern" in context:
                pattern_file = self._find_pattern_file(context["pattern"])
                if pattern_file:
                    try:
                        content = pattern_file.read_text(encoding="utf-8")
                        explanation_parts.append(content)
                        sources.append(str(pattern_file.relative_to(self.content_path)))
                    except Exception as e:
                        logger.warning(f"Ошибка чтения {pattern_file}: {e}")
            
            # Термин из глоссария
            if "term" in context:
                glossary_file = self._find_glossary_file(context["term"])
                if glossary_file:
                    try:
                        content = glossary_file.read_text(encoding="utf-8")
                        explanation_parts.append(content)
                        sources.append(str(glossary_file.relative_to(self.content_path)))
                    except Exception as e:
                        logger.warning(f"Ошибка чтения {glossary_file}: {e}")
        
        # Если конкретных указаний нет, ищем по ключевым словам
        if not explanation_parts:
            search_results = self._search_content(question)
            if search_results:
                # Берём первый наиболее релевантный результат
                best_match = search_results[0]
                explanation_parts.append(best_match["content"])
                sources.append(best_match["path"])
        
        # Если ничего не нашли
        if not explanation_parts:
            explanation = (
                f"По запросу '{question}' не найдено справочной информации. "
                "Попробуйте уточнить вопрос или указать конкретный закон, термин или паттерн."
            )
        else:
            explanation = "\n\n".join(explanation_parts)
        
        return {
            "explanation": explanation,
            "sources": sources,
            "disclaimer": self.disclaimer
        }


# Глобальный экземпляр клиента
_mcp_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """Получить глобальный экземпляр MCP-клиента."""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client






































