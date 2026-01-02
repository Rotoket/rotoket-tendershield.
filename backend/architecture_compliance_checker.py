"""
Architecture Compliance Checker — ШАГ 9

Проверяет соответствие кода канонической архитектуре Tender Shield Pro.
"""

from typing import List, Tuple, Dict, Any
import ast
import os
from pathlib import Path


class ArchitectureViolation:
    """Нарушение архитектурных границ."""
    
    def __init__(self, file_path: str, line: int, violation_type: str, message: str):
        self.file_path = file_path
        self.line = line
        self.violation_type = violation_type
        self.message = message
    
    def __str__(self):
        return f"{self.file_path}:{self.line} [{self.violation_type}] {self.message}"


class ArchitectureComplianceChecker:
    """
    Проверяет соответствие кода канонической архитектуре.
    
    Правила проверки:
    1. MCP не должен обращаться к LLM
    2. Evidence Layer не должен обращаться к файлам напрямую
    3. Decision Logic Layer не должен видеть OCR/таблицы
    4. Decision Presentation Layer не должен пересчитывать риски
    5. UI Layer не должен обращаться к backend слоям напрямую
    """
    
    # Запрещённые импорты для каждого слоя
    FORBIDDEN_IMPORTS = {
        'mcp': [
            'ollama', 'openai', 'anthropic',  # LLM providers
            'gemini', 'claude', 'gpt',  # LLM models
        ],
        'evidence': [
            'open', 'read', 'write',  # Прямая работа с файлами (должно быть через MCP)
        ],
        'reasoning': [
            'preprocessor', 'mcp',  # Не должен видеть MCP/препроцессинг
            'ocr', 'table',  # Не должен видеть OCR/таблицы
        ],
        'presentation': [
            'reasoning', 'evidence',  # Не должен пересчитывать
        ],
        'ui': [
            'preprocessor', 'mcp', 'evidence', 'reasoning',  # Не должен обращаться к backend напрямую
        ],
    }
    
    # Запрещённые функции/методы
    FORBIDDEN_FUNCTIONS = {
        'mcp': [
            'analyze', 'decide', 'recommend',  # Принятие решений
            'classify_risk', 'calculate_risk',  # Интерпретация риска
        ],
        'evidence': [
            'aggregate', 'improve', 'enhance',  # Агрегация/улучшение
        ],
        'reasoning': [
            'read_file', 'open_file', 'process_file',  # Работа с файлами
        ],
        'presentation': [
            'recalculate', 'recompute', 'update_risk',  # Пересчёт рисков
        ],
    }
    
    def __init__(self, project_root: str = '.'):
        self.project_root = Path(project_root)
        self.violations: List[ArchitectureViolation] = []
    
    def check_file(self, file_path: str) -> List[ArchitectureViolation]:
        """
        Проверяет один файл на соответствие архитектуре.
        
        Returns:
            Список нарушений
        """
        violations = []
        file_path_obj = Path(file_path)
        
        # Определяем слой по пути файла
        layer = self._detect_layer(file_path_obj)
        if not layer:
            return violations  # Неизвестный слой, пропускаем
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=file_path)
            
            # Проверяем импорты
            violations.extend(self._check_imports(tree, file_path, layer))
            
            # Проверяем функции
            violations.extend(self._check_functions(tree, file_path, layer))
            
            # Проверяем вызовы запрещённых функций
            violations.extend(self._check_forbidden_calls(tree, file_path, layer))
            
        except SyntaxError:
            # Пропускаем файлы с синтаксическими ошибками
            pass
        except Exception as e:
            violations.append(ArchitectureViolation(
                file_path, 0, 'ERROR',
                f'Ошибка при проверке файла: {str(e)}'
            ))
        
        return violations
    
    def _detect_layer(self, file_path: Path) -> str:
        """Определяет слой по пути файла."""
        path_str = str(file_path)
        
        if 'mcp' in path_str.lower():
            return 'mcp'
        elif 'evidence' in path_str.lower() and 'preprocessor' in path_str.lower():
            return 'evidence'
        elif 'reasoning' in path_str.lower():
            return 'reasoning'
        elif 'decision_preview' in path_str.lower() or 'formatter' in path_str.lower():
            return 'presentation'
        elif file_path.suffix == '.tsx' or file_path.suffix == '.ts':
            if 'frontend' in path_str:
                return 'ui'
        
        return None
    
    def _check_imports(self, tree: ast.AST, file_path: str, layer: str) -> List[ArchitectureViolation]:
        """Проверяет импорты на запрещённые."""
        violations = []
        forbidden = self.FORBIDDEN_IMPORTS.get(layer, [])
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if any(forbidden_term in alias.name.lower() for forbidden_term in forbidden):
                            violations.append(ArchitectureViolation(
                                file_path, node.lineno, 'FORBIDDEN_IMPORT',
                                f'Слой {layer} не должен импортировать: {alias.name}'
                            ))
                elif isinstance(node, ast.ImportFrom):
                    if node.module and any(forbidden_term in node.module.lower() for forbidden_term in forbidden):
                        violations.append(ArchitectureViolation(
                            file_path, node.lineno, 'FORBIDDEN_IMPORT',
                            f'Слой {layer} не должен импортировать из: {node.module}'
                        ))
        
        return violations
    
    def _check_functions(self, tree: ast.AST, file_path: str, layer: str) -> List[ArchitectureViolation]:
        """Проверяет функции на запрещённые названия."""
        violations = []
        forbidden = self.FORBIDDEN_FUNCTIONS.get(layer, [])
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_name_lower = node.name.lower()
                for forbidden_term in forbidden:
                    if forbidden_term in func_name_lower:
                        violations.append(ArchitectureViolation(
                            file_path, node.lineno, 'FORBIDDEN_FUNCTION',
                            f'Слой {layer} не должен содержать функцию: {node.name}'
                        ))
        
        return violations
    
    def _check_forbidden_calls(self, tree: ast.AST, file_path: str, layer: str) -> List[ArchitectureViolation]:
        """Проверяет вызовы запрещённых функций."""
        violations = []
        forbidden = self.FORBIDDEN_FUNCTIONS.get(layer, [])
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name_lower = node.func.id.lower()
                    for forbidden_term in forbidden:
                        if forbidden_term in func_name_lower:
                            violations.append(ArchitectureViolation(
                                file_path, node.lineno, 'FORBIDDEN_CALL',
                                f'Слой {layer} не должен вызывать: {node.func.id}'
                            ))
        
        return violations
    
    def check_project(self, directories: List[str] = None) -> List[ArchitectureViolation]:
        """
        Проверяет весь проект на соответствие архитектуре.
        
        Args:
            directories: Список директорий для проверки (по умолчанию: backend, frontend)
        
        Returns:
            Список всех нарушений
        """
        if directories is None:
            directories = ['backend', 'frontend/src']
        
        all_violations = []
        
        for directory in directories:
            dir_path = self.project_root / directory
            if not dir_path.exists():
                continue
            
            # Рекурсивно обходим все Python/TypeScript файлы
            for file_path in dir_path.rglob('*.py'):
                if '__pycache__' in str(file_path):
                    continue
                all_violations.extend(self.check_file(str(file_path)))
            
            for file_path in dir_path.rglob('*.tsx'):
                all_violations.extend(self.check_file(str(file_path)))
            
            for file_path in dir_path.rglob('*.ts'):
                if 'node_modules' in str(file_path):
                    continue
                all_violations.extend(self.check_file(str(file_path)))
        
        return all_violations
    
    def generate_report(self, violations: List[ArchitectureViolation]) -> str:
        """Генерирует отчёт о нарушениях."""
        if not violations:
            return "✅ Архитектурных нарушений не обнаружено."
        
        report = f"❌ Обнаружено {len(violations)} архитектурных нарушений:\n\n"
        
        # Группируем по типам
        by_type: Dict[str, List[ArchitectureViolation]] = {}
        for violation in violations:
            if violation.violation_type not in by_type:
                by_type[violation.violation_type] = []
            by_type[violation.violation_type].append(violation)
        
        for violation_type, type_violations in by_type.items():
            report += f"\n## {violation_type} ({len(type_violations)} нарушений)\n\n"
            for violation in type_violations:
                report += f"  - {violation}\n"
        
        return report


def check_architecture_compliance(project_root: str = '.') -> Tuple[bool, str]:
    """
    Проверяет соответствие проекта архитектурным границам.
    
    Returns:
        (is_compliant, report) — соответствие и отчёт
    """
    checker = ArchitectureComplianceChecker(project_root)
    violations = checker.check_project()
    report = checker.generate_report(violations)
    return len(violations) == 0, report


if __name__ == '__main__':
    # Запуск проверки из командной строки
    is_compliant, report = check_architecture_compliance()
    print(report)
    exit(0 if is_compliant else 1)































