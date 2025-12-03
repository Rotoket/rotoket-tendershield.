"""
Скрипт для запуска всех тестов
"""

import sys
import subprocess

def run_tests():
    """Запускает все тесты"""
    print("🧪 Запуск тестов...")
    print("=" * 60)
    
    # Запускаем pytest
    result = subprocess.run(
        ["pytest", "tests/", "-v", "--tb=short"],
        cwd=".",
        capture_output=False
    )
    
    if result.returncode == 0:
        print("\n✅ Все тесты пройдены успешно!")
        return 0
    else:
        print("\n❌ Некоторые тесты не прошли")
        return result.returncode

if __name__ == "__main__":
    sys.exit(run_tests())

