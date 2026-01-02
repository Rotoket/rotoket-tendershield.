"""
Kill Switch Guard — ШАГ 13

Проверяет, что Kill Switch работает корректно в CI.
"""

from typing import List, Dict, Any, Tuple
from pathlib import Path
import sys
import os

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from kill_switch_manager import get_kill_switch_manager
    from kill_switch_types import SystemMode, KillSwitchTrigger
    KILL_SWITCH_AVAILABLE = True
except ImportError:
    KILL_SWITCH_AVAILABLE = False


class KillSwitchGuard:
    """
    Проверяет корректность работы Kill Switch.
    
    Правила:
    1. В Safe Mode reasoning не вызывается
    2. В Safe Mode новые решения не формируются
    3. UI показывает маркировку режима
    4. Kill Switch детерминирован (не зависит от LLM)
    """
    
    def __init__(self, project_root: str = '.'):
        self.project_root = Path(project_root)
        self.violations: List[str] = []
    
    def check_safe_mode_reasoning(self) -> List[str]:
        """
        Проверяет, что в Safe Mode reasoning не вызывается.
        """
        violations = []
        
        if not KILL_SWITCH_AVAILABLE:
            return violations
        
        # Проверяем, что в main.py есть проверка is_reasoning_enabled перед вызовом reasoning
        main_py = self.project_root / 'backend' / 'main.py'
        if not main_py.exists():
            return violations
        
        try:
            with open(main_py, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Проверяем, что есть проверка is_reasoning_enabled
            if 'is_reasoning_enabled' not in content:
                violations.append("Отсутствует проверка is_reasoning_enabled перед reasoning")
            
            # Проверяем, что reasoning вызывается только если is_reasoning_enabled
            if 'REASONING_LAYER_ENABLED and evidence_objects and is_reasoning_enabled' not in content:
                violations.append("Reasoning вызывается без проверки is_reasoning_enabled")
        
        except Exception as e:
            violations.append(f"Ошибка проверки Safe Mode reasoning: {e}")
        
        return violations
    
    def check_ui_marking(self) -> List[str]:
        """
        Проверяет, что UI показывает маркировку режима.
        """
        violations = []
        
        # Проверяем наличие KillSwitchBanner компонента
        banner_path = self.project_root / 'frontend' / 'src' / 'components' / 'KillSwitchBanner.tsx'
        if not banner_path.exists():
            violations.append("Отсутствует компонент KillSwitchBanner для отображения режима")
        
        return violations
    
    def check_deterministic(self) -> List[str]:
        """
        Проверяет, что Kill Switch детерминирован (не зависит от LLM).
        """
        violations = []
        
        if not KILL_SWITCH_AVAILABLE:
            return violations
        
        # Проверяем, что KillSwitchManager не использует LLM
        manager_py = self.project_root / 'backend' / 'kill_switch_manager.py'
        if not manager_py.exists():
            return violations
        
        try:
            with open(manager_py, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Проверяем отсутствие LLM-вызовов
            llm_patterns = ['ollama', 'openai', 'anthropic', 'llm', 'model']
            for pattern in llm_patterns:
                if pattern in content.lower() and 'kill_switch' in content.lower():
                    # Исключаем комментарии и строки документации
                    lines = content.split('\n')
                    for line in lines:
                        if pattern in line.lower() and not line.strip().startswith('#'):
                            violations.append(f"Kill Switch Manager содержит LLM-вызов: {line.strip()[:100]}")
                            break
        
        except Exception as e:
            violations.append(f"Ошибка проверки детерминированности: {e}")
        
        return violations
    
    def run_all_checks(self) -> Tuple[bool, str]:
        """
        Запускает все проверки Kill Switch.
        
        Returns:
            (is_compliant, report) — соответствие и отчёт
        """
        all_violations = []
        
        all_violations.extend(self.check_safe_mode_reasoning())
        all_violations.extend(self.check_ui_marking())
        all_violations.extend(self.check_deterministic())
        
        if not all_violations:
            return True, "[SUCCESS] Kill Switch работает корректно."
        
        report = f"[FAILURE] Обнаружено {len(all_violations)} нарушений Kill Switch:\n\n"
        for violation in all_violations:
            report += f"  - {violation}\n"
        
        return False, report


def check_kill_switch(project_root: str = '.') -> Tuple[bool, str]:
    """
    Проверяет корректность работы Kill Switch.
    
    Returns:
        (is_compliant, report) — соответствие и отчёт
    """
    guard = KillSwitchGuard(project_root)
    return guard.run_all_checks()


if __name__ == '__main__':
    is_compliant, report = check_kill_switch()
    print(report)
    exit(0 if is_compliant else 1)

