"""
Architecture Boundary Guard — ШАГ 11

Проверяет соблюдение архитектурных границ (ШАГИ 3-9).
"""

from typing import List, Dict, Any, Tuple
import re
from pathlib import Path


class ArchitectureBoundaryViolation:
    """Нарушение архитектурных границ."""
    
    def __init__(self, file_path: str, line: int, layer: str, violation_type: str, message: str):
        self.file_path = file_path
        self.line = line
        self.layer = layer
        self.violation_type = violation_type
        self.message = message
    
    def __str__(self):
        return f"{self.file_path}:{self.line} [{self.layer}] {self.violation_type}: {self.message}"


class ArchitectureBoundaryGuard:
    """
    Проверяет соблюдение архитектурных границ.
    
    Правила:
    1. LLM не вызывается в MCP Extraction Layer
    2. Evidence Layer не содержит reasoning
    3. Decision Layer не обращается к raw данным
    4. UI не содержит risk-логики
    5. Audit слой append-only
    """
    
    # Запрещённые паттерны для каждого слоя
    FORBIDDEN_PATTERNS = {
        'mcp_extraction': [
            (r'ollama|openai|anthropic|gemini|claude|gpt', 'LLM вызов в MCP Layer'),
            (r'\.analyze\(|\.decide\(|\.recommend\(', 'Принятие решений в MCP Layer'),
            (r'classify_risk|calculate_risk|interpret_risk', 'Интерпретация риска в MCP Layer'),
        ],
        'evidence': [
            (r'reasoning|reason_about|derive_risk', 'Reasoning в Evidence Layer'),
            (r'RiskSignal|DecisionGraph|DecisionPreview', 'Decision-логика в Evidence Layer'),
            (r'\.aggregate\(|\.improve\(|\.enhance\(', 'Агрегация/улучшение Evidence'),
        ],
        'decision_logic': [
            (r'open\(|read_file\(|process_file\(', 'Работа с файлами в Decision Layer'),
            (r'ocr|table_extraction|raw_text', 'Доступ к OCR/таблицам в Decision Layer'),
            (r'preprocessor|mcp_processor', 'Обращение к MCP/препроцессору в Decision Layer'),
        ],
        'decision_presentation': [
            (r'recalculate|recompute|update_risk', 'Пересчёт рисков в Presentation Layer'),
            (r'RiskSignal|Contradiction|EvidenceObject', 'Работа с Risk/Evidence в Presentation Layer'),
        ],
        'audit': [
            (r'\.update\(|\.modify\(|\.delete\(|\.remove\(', 'Изменение snapshots в Audit Layer'),
            (r'overwrite|rewrite|fix_old', 'Перезапись истории в Audit Layer'),
        ],
        'ui': [
            (r'preprocessor|mcp|evidence|reasoning', 'Обращение к backend слоям в UI'),
            (r'calculate_risk|classify_risk|derive_risk', 'Risk-логика в UI'),
        ],
    }
    
    # Паттерны для определения слоя по пути файла
    LAYER_PATTERNS = {
        'mcp_extraction': [r'mcp[/\\]', r'preprocessor\.py', r'extraction'],
        'evidence': [r'evidence', r'preprocessor\.py'],
        'decision_logic': [r'reasoning', r'decision.*logic'],
        'decision_presentation': [r'decision_preview.*formatter', r'presentation'],
        'audit': [r'audit', r'versioning', r'snapshot'],
        'ui': [r'frontend', r'\.tsx$', r'\.ts$'],
    }
    
    def __init__(self, project_root: str = '.'):
        self.project_root = Path(project_root)
        self.violations: List[ArchitectureBoundaryViolation] = []
    
    def detect_layer(self, file_path: Path) -> str:
        """Определяет слой по пути файла."""
        path_str = str(file_path).replace('\\', '/')
        
        for layer, patterns in self.LAYER_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, path_str, re.IGNORECASE):
                    return layer
        
        return 'unknown'
    
    def check_file(self, file_path: str) -> List[ArchitectureBoundaryViolation]:
        """Проверяет один файл на нарушение границ."""
        violations = []
        file_path_obj = Path(file_path)
        layer = self.detect_layer(file_path_obj)
        
        if layer == 'unknown':
            return violations  # Пропускаем неизвестные файлы
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Проверяем запрещённые паттерны для этого слоя
            forbidden = self.FORBIDDEN_PATTERNS.get(layer, [])
            
            for line_num, line in enumerate(lines, 1):
                for pattern, message in forbidden:
                    if re.search(pattern, line, re.IGNORECASE):
                        violations.append(ArchitectureBoundaryViolation(
                            file_path, line_num, layer,
                            'BOUNDARY_VIOLATION', message
                        ))
        
        except Exception as e:
            violations.append(ArchitectureBoundaryViolation(
                file_path, 0, layer,
                'ERROR', f'Ошибка при проверке: {str(e)}'
            ))
        
        return violations
    
    def check_project(self, directories: List[str] = None) -> List[ArchitectureBoundaryViolation]:
        """Проверяет весь проект."""
        if directories is None:
            directories = ['backend', 'frontend/src']
        
        all_violations = []
        
        for directory in directories:
            dir_path = self.project_root / directory
            if not dir_path.exists():
                continue
            
            # Рекурсивно обходим все файлы
            for file_path in dir_path.rglob('*.py'):
                if '__pycache__' in str(file_path) or 'venv' in str(file_path):
                    continue
                all_violations.extend(self.check_file(str(file_path)))
            
            for file_path in dir_path.rglob('*.tsx'):
                if 'node_modules' in str(file_path):
                    continue
                all_violations.extend(self.check_file(str(file_path)))
            
            for file_path in dir_path.rglob('*.ts'):
                if 'node_modules' in str(file_path):
                    continue
                all_violations.extend(self.check_file(str(file_path)))
        
        return all_violations
    
    def generate_report(self, violations: List[ArchitectureBoundaryViolation]) -> str:
        """Генерирует отчёт о нарушениях."""
        if not violations:
            return "✅ Архитектурных нарушений границ не обнаружено."
        
        report = f"❌ Обнаружено {len(violations)} нарушений архитектурных границ:\n\n"
        
        # Группируем по слоям
        by_layer: Dict[str, List[ArchitectureBoundaryViolation]] = {}
        for violation in violations:
            if violation.layer not in by_layer:
                by_layer[violation.layer] = []
            by_layer[violation.layer].append(violation)
        
        for layer, layer_violations in by_layer.items():
            report += f"\n## Слой: {layer} ({len(layer_violations)} нарушений)\n\n"
            for violation in layer_violations:
                report += f"  - {violation}\n"
        
        return report


def check_architecture_boundaries(project_root: str = '.') -> Tuple[bool, str]:
    """
    Проверяет соблюдение архитектурных границ.
    
    Returns:
        (is_compliant, report) — соответствие и отчёт
    """
    guard = ArchitectureBoundaryGuard(project_root)
    violations = guard.check_project()
    report = guard.generate_report(violations)
    return len(violations) == 0, report


if __name__ == '__main__':
    is_compliant, report = check_architecture_boundaries()
    print(report)
    exit(0 if is_compliant else 1)

