#!/usr/bin/env python3
"""
Скрипт для деактивации Kill Switch и возврата системы в NORMAL режим.

Использование:
    python deactivate_kill_switch.py
"""

import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent))

from kill_switch_manager import get_kill_switch_manager

def main():
    """Деактивирует Kill Switch и возвращает систему в NORMAL режим."""
    try:
        kill_switch = get_kill_switch_manager()
        
        # Получаем текущий статус
        status = kill_switch.get_status()
        print(f"Текущий режим: {status.current_mode.value}")
        print(f"Активен: {status.is_active}")
        
        if status.current_mode.value == "NORMAL":
            print("[OK] Система уже в нормальном режиме. Ничего не требуется.")
            return 0
        
        # Деактивируем Kill Switch
        activation = kill_switch.deactivate(
            reason="Деактивация для возврата в нормальный режим работы",
            deactivated_by="admin_script"
        )
        
        print("[OK] Kill Switch деактивирован")
        print(f"Предыдущий режим: {activation.previous_mode.value}")
        print(f"Новый режим: {activation.new_mode.value}")
        print(f"Активация ID: {activation.activation_id}")
        print(f"Время: {activation.timestamp}")
        
        # Проверяем результат
        new_status = kill_switch.get_status()
        if new_status.current_mode.value == "NORMAL" and not new_status.is_active:
            print("\n[OK] Система успешно переведена в NORMAL режим")
            return 0
        else:
            print(f"\n[WARNING] Предупреждение: режим не изменился. Текущий режим: {new_status.current_mode.value}")
            return 1
            
    except Exception as e:
        print(f"[ERROR] Ошибка деактивации Kill Switch: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

