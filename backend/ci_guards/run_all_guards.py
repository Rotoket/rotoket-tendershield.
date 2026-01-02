"""
Run All CI Guards — ШАГ 11

Запускает все CI guardrails и генерирует сводный отчёт.
"""

import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent.parent))

from ci_guards.architecture_boundary_guard import check_architecture_boundaries
from ci_guards.decision_integrity_guard import check_decision_integrity
from ci_guards.prompt_abuse_guard import check_prompt_abuse
from ci_guards.output_contract_guard import check_output_contract
from ci_guards.red_team_replay import run_red_team_replay
from ci_guards.kill_switch_guard import check_kill_switch
from ci_guards.canon_guardrails import check_canon_guardrails


def main():
    """Запускает все CI guardrails."""
    import sys
    import io
    # Устанавливаем UTF-8 для вывода в Windows
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except (AttributeError, ValueError):
            # Если reconfigure недоступен, пробуем другой способ
            try:
                if hasattr(sys.stdout, 'buffer'):
                    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
                if hasattr(sys.stderr, 'buffer'):
                    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
            except (AttributeError, ValueError):
                pass  # Пропускаем, если не удалось настроить кодировку
    
    print("=" * 80)
    print("CI GUARDRAILS — Tender Shield Pro")
    print("=" * 80)
    print()
    
    all_passed = True
    reports = []
    
    # 1. Architecture Boundary Guard
    print("1. Проверка архитектурных границ...")
    passed, report = check_architecture_boundaries()
    reports.append(("Architecture Boundary Guard", passed, report))
    if not passed:
        all_passed = False
    print("   " + ("[PASSED]" if passed else "[FAILED]"))
    print()
    
    # 2. Decision Integrity Guard
    print("2. Проверка целостности решений...")
    passed, report = check_decision_integrity()
    reports.append(("Decision Integrity Guard", passed, report))
    if not passed:
        all_passed = False
    print("   " + ("[PASSED]" if passed else "[FAILED]"))
    print()
    
    # 3. Prompt Abuse Guard
    print("3. Проверка промптов на ослабление правил...")
    passed, report = check_prompt_abuse()
    reports.append(("Prompt Abuse Guard", passed, report))
    if not passed:
        all_passed = False
    print("   " + ("[PASSED]" if passed else "[FAILED]"))
    print()
    
    # 4. Output Contract Guard
    print("4. Проверка контракта вывода...")
    passed, report = check_output_contract()
    reports.append(("Output Contract Guard", passed, report))
    if not passed:
        all_passed = False
    print("   " + ("[PASSED]" if passed else "[FAILED]"))
    print()
    
    # 5. Red Team Replay
    print("5. Red Team Replay тесты...")
    passed, report = run_red_team_replay()
    reports.append(("Red Team Replay", passed, report))
    if not passed:
        all_passed = False
    print("   " + ("[PASSED]" if passed else "[FAILED]"))
    print()
    
    # 6. Kill Switch Guard
    print("6. Проверка Kill Switch...")
    # Передаем корень проекта (родительскую директорию backend/)
    project_root = str(Path(__file__).parent.parent.parent)
    passed, report = check_kill_switch(project_root=project_root)
    reports.append(("Kill Switch Guard", passed, report))
    if not passed:
        all_passed = False
    print("   " + ("[PASSED]" if passed else "[FAILED]"))
    print()
    
    # 7. Canon Guardrails (Language, Structural, Impact, Data Exhaustion)
    print("7. Проверка Canon Guardrails (Language, Structural, Impact, Data Exhaustion)...")
    project_root = str(Path(__file__).parent.parent.parent)
    passed, report = check_canon_guardrails(project_root=project_root)
    reports.append(("Canon Guardrails", passed, report))
    if not passed:
        all_passed = False
    print("   " + ("[PASSED]" if passed else "[FAILED]"))
    print()
    
    # Сводный отчёт
    print("=" * 80)
    print("СВОДНЫЙ ОТЧЁТ")
    print("=" * 80)
    print()
    
    for name, passed, report in reports:
        status = "[PASSED]" if passed else "[FAILED]"
        print(f"{name}: {status}")
        if not passed:
            print(report)
            print()
    
    print("=" * 80)
    if all_passed:
        print("[SUCCESS] ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ")
        return 0
    else:
        print("[FAILURE] ОБНАРУЖЕНЫ НАРУШЕНИЯ")
        print()
        print("CI FAILURE = АРХИТЕКТУРНОЕ СОБЫТИЕ")
        print("Нельзя 'быстро починить' или bypass.")
        print("Требуется указать, какой шаг нарушен, либо оформить осознанный форк Manifest.")
        return 1


if __name__ == '__main__':
    exit(main())

