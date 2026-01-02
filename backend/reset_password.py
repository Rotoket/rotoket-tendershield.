"""
Скрипт для сброса пароля пользователя
Использование: python reset_password.py <email> <новый_пароль>
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db, User
from auth import get_password_hash

def reset_password(email: str, new_password: str):
    """Сбрасывает пароль для пользователя"""
    db = next(get_db())
    
    try:
        user = db.query(User).filter(User.email.ilike(email)).first()
        
        if not user:
            print(f"[ERROR] Пользователь с email {email} не найден")
            return False
        
        # Хешируем новый пароль
        hashed_password = get_password_hash(new_password)
        
        # Обновляем пароль
        user.hashed_password = hashed_password
        
        db.commit()
        
        print(f"[OK] Пароль успешно изменен для {email}")
        print(f"     Новый пароль: {new_password}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Ошибка при сбросе пароля: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Использование: python reset_password.py <email> <новый_пароль>")
        sys.exit(1)
    
    email = sys.argv[1].lower().strip()
    new_password = sys.argv[2]
    
    reset_password(email, new_password)




































