"""
ФАЗА 4: MCP сервер для Knowledge Base поиска.

Предоставляет инструменты для поиска в Knowledge Base через RAG и прямого доступа к документам.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

try:
    from mcp import FastMCP
except ImportError:
    # Если MCP не установлен, создаем заглушку
    class FastMCP:
        def __init__(self, name: str):
            self.name = name
        
        def tool(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
        
        def run(self):
            pass

from rag_engine import get_law_snippets

logger = logging.getLogger(__name__)

# Инициализация MCP сервера
mcp = FastMCP("TenderShield-Knowledge-Base")

# Путь к Knowledge Base
KNOWLEDGE_BASE_ROOT = Path(__file__).resolve().parent.parent.parent / "knowledge"


@mcp.tool()
def search_knowledge_base(query: str, k: int = 5, doc_type: Optional[str] = None) -> dict:
    """
    Ищет релевантные документы в Knowledge Base через RAG.
    
    Args:
        query: Поисковый запрос
        k: Количество результатов
        doc_type: Тип документа для фильтрации (laws, standards, templates, examples, risks, canon, utils)
    
    Returns:
        dict с полями:
        - success: bool
        - results: List[Dict] - список релевантных фрагментов
        - total_found: int - общее количество найденных результатов
        - error: Optional[str]
    """
    try:
        # Используем RAG engine для поиска
        snippets = get_law_snippets(query, k=k)
        
        # Фильтруем по doc_type если указан
        if doc_type:
            filtered_snippets = []
            for snippet in snippets:
                metadata = snippet.get("metadata", {})
                source = metadata.get("source", "")
                if doc_type in source.lower():
                    filtered_snippets.append(snippet)
            snippets = filtered_snippets[:k]
        
        return {
            "success": True,
            "results": snippets,
            "total_found": len(snippets),
            "query": query,
            "doc_type": doc_type
        }
        
    except Exception as e:
        logger.error(f"Ошибка поиска в Knowledge Base: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "results": [],
            "total_found": 0
        }


@mcp.tool()
def get_knowledge_document(doc_path: str) -> dict:
    """
    Получает полный текст документа из Knowledge Base.
    
    Args:
        doc_path: Относительный путь к документу (например, "laws/fz-44-2013.md")
    
    Returns:
        dict с полями:
        - success: bool
        - content: str - содержимое документа
        - metadata: dict - метаданные из YAML front matter
        - error: Optional[str]
    """
    try:
        doc_file = KNOWLEDGE_BASE_ROOT / doc_path
        
        if not doc_file.exists():
            return {
                "success": False,
                "error": f"Документ не найден: {doc_path}"
            }
        
        # Читаем файл
        content = doc_file.read_text(encoding='utf-8')
        
        # Парсим YAML front matter если есть
        metadata = {}
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    import yaml
                    metadata = yaml.safe_load(parts[1]) or {}
                    content = parts[2].strip()
                except ImportError:
                    logger.warning("PyYAML не установлен, метаданные не извлечены")
                except Exception as e:
                    logger.warning(f"Ошибка парсинга YAML: {e}")
        
        return {
            "success": True,
            "content": content,
            "metadata": metadata,
            "doc_path": doc_path
        }
        
    except Exception as e:
        logger.error(f"Ошибка чтения документа: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def list_knowledge_documents(category: Optional[str] = None) -> dict:
    """
    Списывает все документы в Knowledge Base.
    
    Args:
        category: Категория для фильтрации (laws, standards, templates, examples, risks, canon, utils)
    
    Returns:
        dict с полями:
        - success: bool
        - documents: List[Dict] - список документов с метаданными
        - total: int - общее количество документов
        - error: Optional[str]
    """
    try:
        documents = []
        
        if category:
            # Ищем только в указанной категории
            category_dir = KNOWLEDGE_BASE_ROOT / category
            if category_dir.exists():
                for doc_file in category_dir.glob("*.md"):
                    documents.append({
                        "path": f"{category}/{doc_file.name}",
                        "name": doc_file.stem,
                        "category": category
                    })
        else:
            # Ищем во всех категориях
            categories = ["laws", "standards", "templates", "examples", "risks", "canon", "utils"]
            for cat in categories:
                cat_dir = KNOWLEDGE_BASE_ROOT / cat
                if cat_dir.exists():
                    for doc_file in cat_dir.glob("*.md"):
                        documents.append({
                            "path": f"{cat}/{doc_file.name}",
                            "name": doc_file.stem,
                            "category": cat
                        })
        
        return {
            "success": True,
            "documents": documents,
            "total": len(documents),
            "category": category
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения списка документов: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "documents": [],
            "total": 0
        }


@mcp.tool()
def get_blockers_for_law(procurement_law: str) -> dict:
    """
    Получает список блокеров для указанного закона о закупках.
    
    Args:
        procurement_law: "44-ФЗ" или "223-ФЗ"
    
    Returns:
        dict с полями:
        - success: bool
        - blockers: List[Dict] - список блокеров
        - law: str - закон
        - error: Optional[str]
    """
    try:
        # Нормализуем название закона
        law_normalized = procurement_law.lower().replace(' ', '-').replace('фз', 'fz')
        blockers_file = KNOWLEDGE_BASE_ROOT / "risks" / f"blockers-{law_normalized}.md"
        
        if not blockers_file.exists():
            # Пробуем альтернативные варианты
            if "44" in procurement_law:
                blockers_file = KNOWLEDGE_BASE_ROOT / "risks" / "blockers-44fz.md"
            elif "223" in procurement_law:
                blockers_file = KNOWLEDGE_BASE_ROOT / "risks" / "blockers-223fz.md"
        
        if not blockers_file.exists():
            return {
                "success": False,
                "error": f"Файл блокеров для {procurement_law} не найден"
            }
        
        content = blockers_file.read_text(encoding='utf-8')
        
        # Парсим блокеры из Markdown (упрощенно)
        blockers = []
        current_blocker = None
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('##') or line.startswith('###'):
                if current_blocker:
                    blockers.append(current_blocker)
                current_blocker = {
                    "title": line.lstrip('#').strip(),
                    "description": "",
                    "mitigation": ""
                }
            elif current_blocker:
                if "митигация" in line.lower() or "решение" in line.lower():
                    current_blocker["mitigation"] += line + " "
                else:
                    current_blocker["description"] += line + " "
        
        if current_blocker:
            blockers.append(current_blocker)
        
        return {
            "success": True,
            "blockers": blockers,
            "law": procurement_law,
            "source_file": str(blockers_file.relative_to(KNOWLEDGE_BASE_ROOT))
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения блокеров: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "blockers": []
        }


@mcp.tool()
def get_decision_framework(procurement_law: str) -> dict:
    """
    Получает канонический фреймворк принятия решений для указанного закона.
    
    Args:
        procurement_law: "44-ФЗ" или "223-ФЗ"
    
    Returns:
        dict с полями:
        - success: bool
        - framework: dict - структура фреймворка
        - law: str - закон
        - error: Optional[str]
    """
    try:
        # Нормализуем название закона
        law_normalized = procurement_law.lower().replace(' ', '-').replace('фз', 'fz')
        framework_file = KNOWLEDGE_BASE_ROOT / "canon" / f"decision-framework-{law_normalized}.md"
        
        if not framework_file.exists():
            # Пробуем альтернативные варианты
            if "44" in procurement_law:
                framework_file = KNOWLEDGE_BASE_ROOT / "canon" / "decision-framework-44fz.md"
            elif "223" in procurement_law:
                framework_file = KNOWLEDGE_BASE_ROOT / "canon" / "decision-framework-223fz.md"
        
        if not framework_file.exists():
            return {
                "success": False,
                "error": f"Фреймворк для {procurement_law} не найден"
            }
        
        content = framework_file.read_text(encoding='utf-8')
        
        # Парсим фреймворк из Markdown
        framework = {
            "steps": [],
            "matrix": {},
            "rules": []
        }
        
        current_step = None
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('##') and 'ШАГ' in line.upper():
                if current_step:
                    framework["steps"].append(current_step)
                current_step = {
                    "title": line.lstrip('#').strip(),
                    "content": ""
                }
            elif current_step:
                current_step["content"] += line + "\n"
            elif "→" in line or "->" in line:
                # Это правило из матрицы
                framework["rules"].append(line)
        
        if current_step:
            framework["steps"].append(current_step)
        
        return {
            "success": True,
            "framework": framework,
            "law": procurement_law,
            "source_file": str(framework_file.relative_to(KNOWLEDGE_BASE_ROOT))
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения фреймворка: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "framework": {}
        }


if __name__ == "__main__":
    # Запуск MCP сервера
    mcp.run()


