"""
Prompt & LLM Abuse Guard — ШАГ 11

Проверяет промпты на ослабление правил (ШАГИ 7-10).
"""

from typing import List, Dict, Any, Tuple
import re
from pathlib import Path


class PromptAbuseViolation:
    """Нарушение правил промптов."""
    
    def __init__(self, file_path: str, line: int, violation_type: str, message: str):
        self.file_path = file_path
        self.line = line
        self.violation_type = violation_type
        self.message = message
    
    def __str__(self):
        return f"{self.file_path}:{self.line} {self.violation_type}: {self.message}"


class PromptAbuseGuard:
    """
    Проверяет промпты на ослабление правил.
    
    Правила:
    1. System prompts не ослаблены
    2. Нет фраз типа "можешь смягчить", "представь что ты юрист", "временно игнорируй"
    3. Нет обхода Red Team правил
    """
    
    # Запрещённые фразы в промптах
    FORBIDDEN_PHRASES = [
        (r'можешь смягчить|can you soften|you can soften', 'Ослабление формулировок'),
        (r'представь что ты юрист|imagine you are a lawyer|pretend to be', 'Ролевая путаница'),
        (r'временно игнорируй|temporarily ignore|skip for now', 'Временное игнорирование правил'),
        (r'можно исключить|can skip|optional', 'Исключение обязательных правил'),
        (r'на твоё усмотрение|at your discretion|your choice', 'Передача ответственности системе'),
        (r'если нужно|if needed|when appropriate', 'Условное применение правил'),
        (r'TODO.*later|FIXME.*later|hack|workaround', 'Отложенные исправления'),
        (r'bypass|обход|обойти', 'Обход правил'),
        (r'ignore.*rule|игнорируй.*правило', 'Игнорирование правил'),
        (r'relax.*requirement|ослабь.*требование', 'Ослабление требований'),
    ]
    
    # Запрещённые паттерны в комментариях
    FORBIDDEN_COMMENTS = [
        (r'TODO.*fix.*later|FIXME.*later', 'Отложенные исправления'),
        (r'hack|workaround|temporary', 'Временные решения'),
        (r'quick fix|быстро.*починить', 'Быстрые исправления'),
    ]
    
    def __init__(self, project_root: str = '.'):
        self.project_root = Path(project_root)
        self.violations: List[PromptAbuseViolation] = []
    
    def check_file(self, file_path: str) -> List[PromptAbuseViolation]:
        """Проверяет один файл на нарушение правил промптов."""
        violations = []
        
        # Проверяем только файлы с промптами или конфигурацией
        # Исключаем ci_guards (сами guards), docs (документация), prompts (описания правил)
        if 'ci_guards' in file_path.lower() or 'docs' in file_path.lower() or 'prompts' in file_path.lower():
            return violations
        
        if not any(keyword in file_path.lower() for keyword in ['prompt', 'system', 'config', 'manifest', '.md']):
            return violations
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Проверяем запрещённые фразы
            for line_num, line in enumerate(lines, 1):
                # Пропускаем комментарии и строки с описаниями правил
                if line.strip().startswith('#') or 'FORBIDDEN_PHRASE' in line or 'FORBIDDEN_COMMENT' in line:
                    continue
                
                # Пропускаем строки в документации, которые описывают правила
                if 'ШАГ' in line or 'правило' in line.lower() or 'rule' in line.lower():
                    continue
                
                for pattern, message in self.FORBIDDEN_PHRASES:
                    if re.search(pattern, line, re.IGNORECASE):
                        violations.append(PromptAbuseViolation(
                            file_path, line_num,
                            'FORBIDDEN_PHRASE',
                            f'{message}: "{line.strip()}"'
                        ))
                
                # Проверяем запрещённые комментарии
                for pattern, message in self.FORBIDDEN_COMMENTS:
                    if re.search(pattern, line, re.IGNORECASE):
                        violations.append(PromptAbuseViolation(
                            file_path, line_num,
                            'FORBIDDEN_COMMENT',
                            f'{message}: "{line.strip()}"'
                        ))
        
        except Exception as e:
            violations.append(PromptAbuseViolation(
                file_path, 0,
                'ERROR',
                f'Ошибка при проверке: {str(e)}'
            ))
        
        return violations
    
    def check_project(self, directories: List[str] = None) -> List[PromptAbuseViolation]:
        """Проверяет весь проект."""
        if directories is None:
            directories = ['backend', 'docs', 'mcp']
        
        all_violations = []
        
        for directory in directories:
            dir_path = self.project_root / directory
            if not dir_path.exists():
                continue
            
            # Проверяем Python файлы
            for file_path in dir_path.rglob('*.py'):
                if '__pycache__' in str(file_path) or 'venv' in str(file_path) or 'node_modules' in str(file_path):
                    continue
                all_violations.extend(self.check_file(str(file_path)))
            
            # Проверяем Markdown файлы (документация, промпты)
            for file_path in dir_path.rglob('*.md'):
                if 'venv' in str(file_path) or 'node_modules' in str(file_path):
                    continue
                all_violations.extend(self.check_file(str(file_path)))
            
            # Проверяем конфигурационные файлы
            for file_path in dir_path.rglob('*.txt'):
                all_violations.extend(self.check_file(str(file_path)))
        
        return all_violations
    
    def generate_report(self, violations: List[PromptAbuseViolation]) -> str:
        """Генерирует отчёт о нарушениях."""
        if not violations:
            return "✅ Нарушений правил промптов не обнаружено."
        
        report = f"❌ Обнаружено {len(violations)} нарушений правил промптов:\n\n"
        
        # Группируем по типам
        by_type: Dict[str, List[PromptAbuseViolation]] = {}
        for violation in violations:
            if violation.violation_type not in by_type:
                by_type[violation.violation_type] = []
            by_type[violation.violation_type].append(violation)
        
        for violation_type, type_violations in by_type.items():
            report += f"\n## {violation_type} ({len(type_violations)} нарушений)\n\n"
            for violation in type_violations:
                report += f"  - {violation}\n"
        
        return report


def check_prompt_abuse(project_root: str = '.') -> Tuple[bool, str]:
    """
    Проверяет промпты на ослабление правил.
    
    Returns:
        (is_compliant, report) — соответствие и отчёт
    """
    guard = PromptAbuseGuard(project_root)
    violations = guard.check_project()
    report = guard.generate_report(violations)
    return len(violations) == 0, report


if __name__ == '__main__':
    is_compliant, report = check_prompt_abuse()
    print(report)
    exit(0 if is_compliant else 1)

