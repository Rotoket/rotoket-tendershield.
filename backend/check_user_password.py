"""
Скрипт для проверки пользователя и сброса пароля
ВАЖНО: Пароли хранятся в хешированном виде и не могут быть восстановлены.
Можно только установить новый пароль.
"""

import sys
from database import SessionLocal, User
from auth import get_password_hash, verify_password

def check_user(email: str):
    """Проверяет наличие пользователя и показывает информацию (без пароля)"""
    db = SessionLocal()
    try:
        # Ищем без учета регистра
        from sqlalchemy import func
        user = db.query(User).filter(func.lower(User.email) == email.lower()).first()
        
        if not user:
            print(f"[ERROR] Пользователь с email {email} не найден в базе данных")
            return None
        
        print(f"[OK] Пользователь найден:")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Имя: {user.name or 'Не указано'}")
        print(f"   Компания: {user.company or 'Не указано'}")
        print(f"   Активен: {'Да' if user.is_active else 'Нет'}")
        print(f"   Тип плана: {user.plan_type}")
        print(f"   Пароль: [ХЕШИРОВАН - не может быть показан]")
        print(f"   Хеш пароля (первые 20 символов): {user.hashed_password[:20]}...")
        
        return user
    finally:
        db.close()

def reset_user_password(email: str, new_password: str):
    """Устанавливает новый пароль для пользователя"""
    db = SessionLocal()
    try:
        # Ищем без учета регистра
        from sqlalchemy import func
        user = db.query(User).filter(func.lower(User.email) == email.lower()).first()
        
        if not user:
            print(f"[ERROR] Пользователь с email {email} не найден")
            return False
        
        # Хешируем новый пароль
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        
        print(f"[OK] Пароль успешно изменён для пользователя {email}")
        print(f"   Новый пароль установлен (хеширован)")
        return True
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Ошибка при сбросе пароля: {e}")
        return False
    finally:
        db.close()

def verify_user_password(email: str, password: str):
    """Проверяет, правильный ли пароль у пользователя"""
    db = SessionLocal()
    try:
        # Ищем без учета регистра
        from sqlalchemy import func
        user = db.query(User).filter(func.lower(User.email) == email.lower()).first()
        
        if not user:
            print(f"[ERROR] Пользователь с email {email} не найден")
            return False
        
        if verify_password(password, user.hashed_password):
            print(f"[OK] Пароль правильный!")
            return True
        else:
            print(f"[ERROR] Пароль неверный")
            return False
    finally:
        db.close()

def list_all_users():
    """Показывает всех пользователей в базе"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"\nВсего пользователей в базе: {len(users)}")
        print("-" * 60)
        for u in users:
            print(f"ID: {u.id}, Email: {u.email}, Имя: {u.name or 'Нет'}, Активен: {u.is_active}")
        print("-" * 60)
        return users
    finally:
        db.close()

if __name__ == "__main__":
    email = "Rotoket@mail.ru"
    
    print("=" * 60)
    print("Проверка пользователя в базе данных")
    print("=" * 60)
    print()
    
    # Сначала показываем всех пользователей
    print("Список всех пользователей в базе:")
    list_all_users()
    print()
    
    # Проверяем пользователя
    user = check_user(email)
    
    if user:
        print()
        print("=" * 60)
        print("ВАЖНО: Пароли хранятся в хешированном виде (bcrypt)")
        print("Восстановить оригинальный пароль невозможно.")
        print()
        print("Варианты действий:")
        print("1. Использовать функцию 'Забыли пароль?' на сайте")
        print("2. Установить новый пароль через этот скрипт")
        print("=" * 60)
        
        # Спрашиваем, нужно ли сбросить пароль
        if len(sys.argv) > 1:
            if sys.argv[1] == "--reset":
                if len(sys.argv) > 2:
                    new_password = sys.argv[2]
                    print()
                    print("Сброс пароля...")
                    reset_user_password(email, new_password)
                else:
                    print()
                    print("[ERROR] Укажите новый пароль: python check_user_password.py --reset <новый_пароль>")
        else:
            print()
            print("Для сброса пароля используйте:")
            print(f"  python check_user_password.py --reset <новый_пароль>")

