"""
Decision Integrity Guard — ШАГ 11

Проверяет целостность решений (ШАГИ 4-7).
"""

from typing import List, Dict, Any, Tuple, Optional
import json
import re
from pathlib import Path


class DecisionIntegrityViolation:
    """Нарушение целостности решения."""
    
    def __init__(self, file_path: str, line: int, violation_type: str, message: str, step: str):
        self.file_path = file_path
        self.line = line
        self.violation_type = violation_type
        self.message = message
        self.step = step
    
    def __str__(self):
        return f"{self.file_path}:{self.line} [{self.step}] {self.violation_type}: {self.message}"


class DecisionIntegrityGuard:
    """
    Проверяет целостность решений.
    
    Правила:
    1. DEAL_BREAKER → решение ≠ УЧАСТВОВАТЬ
    2. Отсутствие компенсации рисков
    3. Наличие Reason Codes при «НЕ УЧАСТВОВАТЬ»
    4. Разделение Risk vs Expert Opinion
    """
    
    def __init__(self, project_root: str = '.'):
        self.project_root = Path(project_root)
        self.violations: List[DecisionIntegrityViolation] = []
    
    def check_deal_breaker_rule(self, file_path: str, content: str) -> List[DecisionIntegrityViolation]:
        """
        Проверяет правило: DEAL_BREAKER → решение ≠ УЧАСТВОВАТЬ
        """
        violations = []
        lines = content.split('\n')
        
        # Ищем места, где есть DEAL_BREAKER и решение УЧАСТВОВАТЬ
        deal_breaker_pattern = r'DEAL_BREAKER|deal_breaker|"DEAL_BREAKER"'
        participate_pattern = r'PARTICIPATE|participate|"PARTICIPATE"|"УЧАСТВОВАТЬ"'
        
        in_deal_breaker_context = False
        in_decision_context = False
        
        for line_num, line in enumerate(lines, 1):
            # Проверяем контекст DEAL_BREAKER
            if re.search(deal_breaker_pattern, line, re.IGNORECASE):
                in_deal_breaker_context = True
            
            # Проверяем решение УЧАСТВОВАТЬ в контексте DEAL_BREAKER
            if in_deal_breaker_context and re.search(participate_pattern, line, re.IGNORECASE):
                # Проверяем, что это не просто упоминание, а реальное нарушение
                if 'decision' in line.lower() or 'решение' in line.lower():
                    violations.append(DecisionIntegrityViolation(
                        file_path, line_num,
                        'DEAL_BREAKER_VIOLATION',
                        'DEAL_BREAKER обнаружен, но решение = УЧАСТВОВАТЬ',
                        'ШАГ 4'
                    ))
                    in_deal_breaker_context = False
        
        return violations
    
    def check_reason_codes(self, file_path: str, content: str) -> List[DecisionIntegrityViolation]:
        """
        Проверяет наличие Reason Codes при «НЕ УЧАСТВОВАТЬ»
        """
        violations = []
        lines = content.split('\n')
        
        # Ищем решение "НЕ УЧАСТВОВАТЬ"
        do_not_participate_pattern = r'DO_NOT_PARTICIPATE|do_not_participate|"НЕ УЧАСТВОВАТЬ"|"НЕ_УЧАСТВОВАТЬ"'
        reason_codes_pattern = r'reason_codes|reasonCodes|reason.*code'
        
        found_do_not_participate = False
        found_reason_codes = False
        
        for line_num, line in enumerate(lines, 1):
            if re.search(do_not_participate_pattern, line, re.IGNORECASE):
                found_do_not_participate = True
                # Проверяем наличие reason_codes в следующих 20 строках
                lookahead = '\n'.join(lines[line_num:line_num+20])
                if re.search(reason_codes_pattern, lookahead, re.IGNORECASE):
                    found_reason_codes = True
                    break
        
        if found_do_not_participate and not found_reason_codes:
            violations.append(DecisionIntegrityViolation(
                file_path, 0,
                'MISSING_REASON_CODES',
                'Решение "НЕ УЧАСТВОВАТЬ" без Reason Codes',
                'ШАГ 7'
            ))
        
        return violations
    
    def check_expert_opinion_separation(self, file_path: str, content: str) -> List[DecisionIntegrityViolation]:
        """
        Проверяет разделение Risk vs Expert Opinion
        """
        violations = []
        lines = content.split('\n')
        
        # Ищем места, где Expert Opinion влияет на решение
        expert_opinion_pattern = r'expert.*opinion|ExpertOpinion|expert_opinion'
        affects_decision_pattern = r'affects.*decision|influence.*decision|change.*decision'
        
        for line_num, line in enumerate(lines, 1):
            if re.search(expert_opinion_pattern, line, re.IGNORECASE):
                # Проверяем следующие строки на влияние на решение
                lookahead = '\n'.join(lines[line_num:line_num+10])
                if re.search(affects_decision_pattern, lookahead, re.IGNORECASE):
                    # Проверяем, что это не просто комментарий о том, что НЕ влияет
                    # Исключаем строки с описаниями правил
                    if ('false' not in lookahead.lower() and 'не влияет' not in lookahead.lower() and
                        'affects_decision' not in lookahead.lower() and 'всегда false' not in lookahead.lower()):
                        violations.append(DecisionIntegrityViolation(
                            file_path, line_num,
                            'EXPERT_OPINION_VIOLATION',
                            'Expert Opinion влияет на решение',
                            'ШАГ 2'
                        ))
        
        return violations
    
    def check_file(self, file_path: str) -> List[DecisionIntegrityViolation]:
        """Проверяет один файл на нарушение целостности решений."""
        violations = []
        
        # Проверяем только файлы, связанные с решениями
        # Исключаем ci_guards (сами guards)
        if 'ci_guards' in file_path.lower():
            return violations
        
        if 'reasoning' not in file_path.lower() and 'decision' not in file_path.lower():
            return violations
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            violations.extend(self.check_deal_breaker_rule(file_path, content))
            violations.extend(self.check_reason_codes(file_path, content))
            violations.extend(self.check_expert_opinion_separation(file_path, content))
        
        except Exception as e:
            violations.append(DecisionIntegrityViolation(
                file_path, 0,
                'ERROR',
                f'Ошибка при проверке: {str(e)}',
                'UNKNOWN'
            ))
        
        return violations
    
    def check_project(self, directories: List[str] = None) -> List[DecisionIntegrityViolation]:
        """Проверяет весь проект."""
        if directories is None:
            directories = ['backend']
        
        all_violations = []
        
        for directory in directories:
            dir_path = self.project_root / directory
            if not dir_path.exists():
                continue
            
            for file_path in dir_path.rglob('*.py'):
                if '__pycache__' in str(file_path):
                    continue
                all_violations.extend(self.check_file(str(file_path)))
        
        return all_violations
    
    def generate_report(self, violations: List[DecisionIntegrityViolation]) -> str:
        """Генерирует отчёт о нарушениях."""
        if not violations:
            return "✅ Нарушений целостности решений не обнаружено."
        
        report = f"❌ Обнаружено {len(violations)} нарушений целостности решений:\n\n"
        
        # Группируем по типам
        by_type: Dict[str, List[DecisionIntegrityViolation]] = {}
        for violation in violations:
            if violation.violation_type not in by_type:
                by_type[violation.violation_type] = []
            by_type[violation.violation_type].append(violation)
        
        for violation_type, type_violations in by_type.items():
            report += f"\n## {violation_type} ({len(type_violations)} нарушений)\n\n"
            for violation in type_violations:
                report += f"  - {violation}\n"
        
        return report


def check_decision_integrity(project_root: str = '.') -> Tuple[bool, str]:
    """
    Проверяет целостность решений.
    
    Returns:
        (is_compliant, report) — соответствие и отчёт
    """
    guard = DecisionIntegrityGuard(project_root)
    violations = guard.check_project()
    report = guard.generate_report(violations)
    return len(violations) == 0, report


if __name__ == '__main__':
    is_compliant, report = check_decision_integrity()
    print(report)
    exit(0 if is_compliant else 1)

