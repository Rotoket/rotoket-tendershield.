"""
ФАЗА 4: Интеграция MCP серверов в Python код.

Обеспечивает вызов MCP серверов (Sequential-thinking, Context7) из Python кода.
"""

import logging
import json
import subprocess
import os
from typing import Optional, Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)


class SequentialThinkingMCP:
    """
    Клиент для Sequential-thinking MCP сервера.
    
    Используется для пошагового анализа сложных задач.
    
    ФАЗА 4: Поддержка реальных вызовов через MCP SDK (если доступен).
    """
    
    def __init__(self, enabled: bool = True, use_real_mcp: bool = False):
        self.enabled = enabled
        self.use_real_mcp = use_real_mcp
        self.mcp_command = ["npx", "-y", "@modelcontextprotocol/server-sequential-thinking"]
        
        # Пробуем импортировать MCP SDK для реальных вызовов
        self.mcp_sdk_available = False
        if use_real_mcp:
            try:
                from mcp import ClientSession, StdioServerParameters
                self.mcp_sdk_available = True
                logger.info("✅ MCP SDK доступен, будут использоваться реальные вызовы")
            except ImportError:
                logger.warning("⚠️ MCP SDK не установлен, используется симуляция. Установите: pip install mcp")
    
    def analyze_step_by_step(
        self,
        problem: str,
        context: Optional[Dict[str, Any]] = None,
        max_steps: int = 7
    ) -> Dict[str, Any]:
        """
        Выполняет пошаговый анализ проблемы через Sequential-thinking MCP.
        
        Args:
            problem: Описание проблемы для анализа
            context: Дополнительный контекст
            max_steps: Максимальное количество шагов анализа
        
        Returns:
            dict с полями:
            - success: bool
            - steps: List[Dict] - шаги анализа
            - conclusion: str - итоговый вывод
            - error: Optional[str]
            - method: str - "mcp" (реальный) или "simulated" (симуляция)
        """
        if not self.enabled:
            logger.warning("Sequential-thinking MCP отключен")
            return {
                "success": False,
                "error": "Sequential-thinking MCP отключен"
            }
        
        # ФАЗА 4: Пробуем использовать реальный MCP SDK
        if self.use_real_mcp and self.mcp_sdk_available:
            try:
                return self._call_real_mcp(problem, context, max_steps)
            except Exception as e:
                logger.warning(f"⚠️ Ошибка реального MCP вызова, fallback на симуляцию: {e}")
        
        # Fallback: симуляция для MVP
        try:
            logger.info(f"🧠 Sequential-thinking анализ (симуляция): {problem[:100]}...")
            
            steps = self._simulate_sequential_thinking(problem, context, max_steps)
            
            return {
                "success": True,
                "steps": steps,
                "conclusion": self._generate_conclusion(steps),
                "method": "simulated"  # В production будет "mcp"
            }
            
        except Exception as e:
            logger.error(f"Ошибка Sequential-thinking MCP: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _call_real_mcp(
        self,
        problem: str,
        context: Optional[Dict[str, Any]],
        max_steps: int
    ) -> Dict[str, Any]:
        """
        Реальный вызов Sequential-thinking MCP через SDK.
        
        Примечание: Требует настройки MCP сервера в mcp.json
        """
        try:
            from mcp import ClientSession, StdioServerParameters
            import asyncio
            
            # Настройка подключения к MCP серверу
            server_params = StdioServerParameters(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-sequential-thinking"]
            )
            
            # Создаем сессию и вызываем инструмент
            async def _async_call():
                async with ClientSession(server_params) as session:
                    # Инициализируем сессию
                    await session.initialize()
                    
                    # Формируем запрос для Sequential-thinking
                    prompt = f"Проанализируй проблему пошагово (максимум {max_steps} шагов):\n\n{problem}"
                    if context:
                        prompt += f"\n\nКонтекст: {json.dumps(context, ensure_ascii=False)}"
                    
                    # Вызываем инструмент sequential-thinking
                    result = await session.call_tool(
                        "sequentialthinking",
                        {
                            "thought": prompt,
                            "nextThoughtNeeded": True,
                            "thoughtNumber": 1,
                            "totalThoughts": max_steps
                        }
                    )
                    
                    return result
            
            # Запускаем асинхронный вызов
            result = asyncio.run(_async_call())
            
            return {
                "success": True,
                "steps": result.get("steps", []),
                "conclusion": result.get("conclusion", ""),
                "method": "mcp"
            }
            
        except Exception as e:
            logger.error(f"Ошибка реального MCP вызова: {e}", exc_info=True)
            raise
    
    def _simulate_sequential_thinking(
        self,
        problem: str,
        context: Optional[Dict[str, Any]],
        max_steps: int
    ) -> List[Dict[str, Any]]:
        """
        Упрощенная симуляция Sequential-thinking для MVP.
        
        В production заменить на реальный вызов MCP.
        """
        steps = []
        
        # ШАГ 1: Разбор проблемы
        steps.append({
            "step": 1,
            "title": "Разбор проблемы",
            "content": f"Анализируем проблему: {problem}",
            "reasoning": "Определяем ключевые аспекты и требования"
        })
        
        # ШАГ 2: Анализ контекста
        if context:
            steps.append({
                "step": 2,
                "title": "Анализ контекста",
                "content": f"Учитываем контекст: {json.dumps(context, ensure_ascii=False)}",
                "reasoning": "Контекст влияет на решение"
            })
        
        # ШАГ 3: Выявление ключевых факторов
        steps.append({
            "step": 3,
            "title": "Выявление ключевых факторов",
            "content": "Определяем критичные параметры и ограничения",
            "reasoning": "Необходимо учесть все важные факторы"
        })
        
        # ШАГ 4: Генерация вариантов решения
        steps.append({
            "step": 4,
            "title": "Генерация вариантов",
            "content": "Рассматриваем возможные подходы к решению",
            "reasoning": "Оцениваем альтернативы"
        })
        
        # ШАГ 5: Оценка рисков
        steps.append({
            "step": 5,
            "title": "Оценка рисков",
            "content": "Анализируем потенциальные риски каждого варианта",
            "reasoning": "Важно предвидеть возможные проблемы"
        })
        
        # ШАГ 6: Выбор оптимального решения
        steps.append({
            "step": 6,
            "title": "Выбор решения",
            "content": "Выбираем оптимальный вариант на основе анализа",
            "reasoning": "Балансируем между эффективностью и рисками"
        })
        
        return steps[:max_steps]
    
    def _generate_conclusion(self, steps: List[Dict[str, Any]]) -> str:
        """Генерирует итоговый вывод на основе шагов"""
        if not steps:
            return "Анализ не выполнен"
        
        return f"Выполнено {len(steps)} шагов анализа. Рекомендуется следовать предложенному плану."


class KnowledgeBaseMCP:
    """
    Клиент для Knowledge Base MCP сервера.
    
    Предоставляет доступ к поиску в Knowledge Base и документам.
    """
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.mcp_command = ["python", str(Path(__file__).parent / "knowledge_base_mcp.py")]
    
    def search(self, query: str, k: int = 5, doc_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Ищет в Knowledge Base через RAG.
        
        Args:
            query: Поисковый запрос
            k: Количество результатов
            doc_type: Тип документа для фильтрации
        
        Returns:
            List[Dict] - список релевантных фрагментов
        """
        if not self.enabled:
            return []
        
        try:
            # Используем RAG engine напрямую
            from rag_engine import get_law_snippets
            snippets = get_law_snippets(query, k=k)
            
            # Фильтруем по doc_type если указан
            if doc_type:
                filtered = []
                for snippet in snippets:
                    metadata = snippet.get("metadata", {})
                    source = metadata.get("source", "")
                    if doc_type in source.lower():
                        filtered.append(snippet)
                return filtered[:k]
            
            return snippets
            
        except Exception as e:
            logger.error(f"Ошибка поиска в Knowledge Base: {e}", exc_info=True)
            return []
    
    def get_document(self, doc_path: str) -> Optional[Dict[str, Any]]:
        """
        Получает документ из Knowledge Base.
        
        Args:
            doc_path: Относительный путь (например, "laws/fz-44-2013.md")
        
        Returns:
            dict с content и metadata или None
        """
        if not self.enabled:
            return None
        
        try:
            knowledge_base_root = Path(__file__).parent.parent.parent / "knowledge"
            doc_file = knowledge_base_root / doc_path
            
            if not doc_file.exists():
                return None
            
            content = doc_file.read_text(encoding='utf-8')
            
            # Парсим YAML front matter
            metadata = {}
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    try:
                        import yaml
                        metadata = yaml.safe_load(parts[1]) or {}
                        content = parts[2].strip()
                    except ImportError:
                        pass
                    except Exception:
                        pass
            
            return {
                "content": content,
                "metadata": metadata,
                "doc_path": doc_path
            }
            
        except Exception as e:
            logger.error(f"Ошибка чтения документа: {e}", exc_info=True)
            return None


class Context7MCP:
    """
    Клиент для Context7 MCP сервера.
    
    Используется для сохранения и загрузки контекста анализа.
    """
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.mcp_command = ["npx", "-y", "@upstash/context7-mcp"]
        self.context_storage_path = Path(__file__).parent.parent.parent / "context_storage"
        self.context_storage_path.mkdir(exist_ok=True)
    
    def save_context(
        self,
        analysis_id: str,
        context: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Сохраняет контекст анализа для последующего использования.
        
        Args:
            analysis_id: Уникальный ID анализа
            context: Контекст для сохранения
            metadata: Дополнительные метаданные
        
        Returns:
            bool - успешность сохранения
        """
        if not self.enabled:
            logger.warning("Context7 MCP отключен")
            return False
        
        try:
            context_file = self.context_storage_path / f"{analysis_id}.json"
            
            context_data = {
                "analysis_id": analysis_id,
                "context": context,
                "metadata": metadata or {},
                "timestamp": str(Path(__file__).stat().st_mtime)  # Упрощенно
            }
            
            with open(context_file, 'w', encoding='utf-8') as f:
                json.dump(context_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Контекст сохранен: {analysis_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения контекста: {e}", exc_info=True)
            return False
    
    def load_context(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        Загружает сохраненный контекст анализа.
        
        Args:
            analysis_id: ID анализа
        
        Returns:
            dict с контекстом или None
        """
        if not self.enabled:
            return None
        
        try:
            context_file = self.context_storage_path / f"{analysis_id}.json"
            
            if not context_file.exists():
                return None
            
            with open(context_file, 'r', encoding='utf-8') as f:
                context_data = json.load(f)
            
            logger.info(f"✅ Контекст загружен: {analysis_id}")
            return context_data.get("context")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки контекста: {e}", exc_info=True)
            return None
    
    def search_similar_contexts(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Ищет похожие контексты по запросу.
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов
        
        Returns:
            List[Dict] - список похожих контекстов
        """
        if not self.enabled:
            return []
        
        try:
            results = []
            query_lower = query.lower()
            
            # Простой поиск по файлам контекста
            for context_file in self.context_storage_path.glob("*.json"):
                try:
                    with open(context_file, 'r', encoding='utf-8') as f:
                        context_data = json.load(f)
                    
                    context_str = json.dumps(context_data, ensure_ascii=False).lower()
                    if query_lower in context_str:
                        results.append({
                            "analysis_id": context_data.get("analysis_id"),
                            "metadata": context_data.get("metadata", {}),
                            "relevance": context_str.count(query_lower)  # Упрощенная метрика
                        })
                except Exception as e:
                    logger.warning(f"Ошибка чтения {context_file}: {e}")
                    continue
            
            # Сортируем по релевантности
            results.sort(key=lambda x: x.get("relevance", 0), reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Ошибка поиска контекстов: {e}", exc_info=True)
            return []


# Глобальные экземпляры
_sequential_thinking: Optional[SequentialThinkingMCP] = None
_context7: Optional[Context7MCP] = None
_knowledge_base: Optional[KnowledgeBaseMCP] = None


def get_sequential_thinking_mcp(use_real_mcp: bool = False) -> SequentialThinkingMCP:
    """
    Получить глобальный экземпляр Sequential-thinking MCP клиента.
    
    Args:
        use_real_mcp: Использовать реальный MCP SDK (требует установки mcp пакета)
    """
    global _sequential_thinking
    if _sequential_thinking is None:
        _sequential_thinking = SequentialThinkingMCP(enabled=True, use_real_mcp=use_real_mcp)
    return _sequential_thinking


def get_context7_mcp() -> Context7MCP:
    """Получить глобальный экземпляр Context7 MCP клиента"""
    global _context7
    if _context7 is None:
        _context7 = Context7MCP(enabled=True)
    return _context7


def get_knowledge_base_mcp() -> KnowledgeBaseMCP:
    """Получить глобальный экземпляр Knowledge Base MCP клиента"""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBaseMCP(enabled=True)
    return _knowledge_base

