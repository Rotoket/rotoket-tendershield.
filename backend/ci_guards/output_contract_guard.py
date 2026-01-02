"""
Output Contract Guard — ШАГ 11

Проверяет, что выход всегда board-ready (ШАГ 5).
"""

from typing import List, Dict, Any, Tuple, Optional
import re
import json
from pathlib import Path


class OutputContractViolation:
    """Нарушение контракта вывода."""
    
    def __init__(self, file_path: str, line: int, violation_type: str, message: str):
        self.file_path = file_path
        self.line = line
        self.violation_type = violation_type
        self.message = message
    
    def __str__(self):
        return f"{self.file_path}:{self.line} {self.violation_type}: {self.message}"


class OutputContractGuard:
    """
    Проверяет, что выход всегда board-ready.
    
    Правила:
    1. Есть решение (3 значения: PARTICIPATE, DO_NOT_PARTICIPATE, PARTICIPATE_WITH_CONDITIONS)
    2. Есть "Почему" (2-4 причины)
    3. Есть "Ключевой риск"
    4. Нет вероятностей
    5. Нет числовых оценок риска
    6. Нет смягчающего языка
    """
    
    # Запрещённые слова/фразы в выводе
    FORBIDDEN_WORDS = [
        (r'вероятно|probably|likely|возможно', 'Вероятностные формулировки'),
        (r'%\s*вероятность|probability.*%|шанс.*%', 'Процентные вероятности'),
        (r'риск.*\d+%|risk.*\d+%', 'Числовые оценки риска'),
        (r'рекомендуем|recommend|советуем|advise', 'Рекомендации'),
        (r'лучше|better|optimal|оптимально', 'Оценочные суждения'),
        (r'AI считает|model thinks|algorithm suggests', 'AI-лексика'),
        (r'может привести|might lead|could result', 'Гипотетические формулировки'),
    ]
    
    # Обязательные поля Decision Preview
    REQUIRED_FIELDS = [
        'decision',
        'decision_label',
        'why',
        'main_risk',
        'management_load',
    ]
    
    def __init__(self, project_root: str = '.'):
        self.project_root = Path(project_root)
        self.violations: List[OutputContractViolation] = []
    
    def check_file(self, file_path: str) -> List[OutputContractViolation]:
        """Проверяет один файл на нарушение контракта вывода."""
        violations = []
        
        # Проверяем только файлы, связанные с Decision Preview
        if 'decision_preview' not in file_path.lower() and 'formatter' not in file_path.lower():
            return violations
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Проверяем запрещённые слова
            for line_num, line in enumerate(lines, 1):
                for pattern, message in self.FORBIDDEN_WORDS:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Пропускаем комментарии, строки документации и описания правил
                        if (line.strip().startswith('#') or line.strip().startswith('//') or 
                            'FORBIDDEN_WORD' in line or 'не используй' in line.lower() or 
                            'не используешь' in line.lower()):
                            continue
                        violations.append(OutputContractViolation(
                            file_path, line_num,
                            'FORBIDDEN_WORD',
                            f'{message}: "{line.strip()[:100]}"'
                        ))
            
            # Проверяем наличие обязательных полей в структурах данных
            if 'DecisionPreview' in content or 'decision_preview' in content:
                for field in self.REQUIRED_FIELDS:
                    # Ищем определение структуры/класса
                    if f'class DecisionPreview' in content or f'interface DecisionPreview' in content:
                        # Проверяем наличие поля
                        field_pattern = rf'{field}[:=]|"{field}"|field.*{field}'
                        if not re.search(field_pattern, content, re.IGNORECASE):
                            violations.append(OutputContractViolation(
                                file_path, 0,
                                'MISSING_FIELD',
                                f'Отсутствует обязательное поле: {field}'
                            ))
        
        except Exception as e:
            violations.append(OutputContractViolation(
                file_path, 0,
                'ERROR',
                f'Ошибка при проверке: {str(e)}'
            ))
        
        return violations
    
    def check_project(self, directories: List[str] = None) -> List[OutputContractViolation]:
        """Проверяет весь проект."""
        if directories is None:
            directories = ['backend', 'frontend/src']
        
        all_violations = []
        
        for directory in directories:
            dir_path = self.project_root / directory
            if not dir_path.exists():
                continue
            
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
    
    def generate_report(self, violations: List[OutputContractViolation]) -> str:
        """Генерирует отчёт о нарушениях."""
        if not violations:
            return "✅ Нарушений контракта вывода не обнаружено."
        
        report = f"❌ Обнаружено {len(violations)} нарушений контракта вывода:\n\n"
        
        # Группируем по типам
        by_type: Dict[str, List[OutputContractViolation]] = {}
        for violation in violations:
            if violation.violation_type not in by_type:
                by_type[violation.violation_type] = []
            by_type[violation.violation_type].append(violation)
        
        for violation_type, type_violations in by_type.items():
            report += f"\n## {violation_type} ({len(type_violations)} нарушений)\n\n"
            for violation in type_violations:
                report += f"  - {violation}\n"
        
        return report


def check_output_contract(project_root: str = '.') -> Tuple[bool, str]:
    """
    Проверяет контракт вывода.
    
    Returns:
        (is_compliant, report) — соответствие и отчёт
    """
    guard = OutputContractGuard(project_root)
    violations = guard.check_project()
    report = guard.generate_report(violations)
    return len(violations) == 0, report


if __name__ == '__main__':
    is_compliant, report = check_output_contract()
    print(report)
    exit(0 if is_compliant else 1)

