"""
Модуль для авторизации и аутентификации пользователей
Использует JWT токены и bcrypt для хеширования паролей
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db, User
from config import settings
import logging

logger = logging.getLogger(__name__)

# Настройка хеширования паролей
# Используем pbkdf2_sha256, чтобы избежать платформенных ограничений bcrypt (72 байта и привязка к C-библиотекам),
# при этом остаётся надёжный алгоритм с растяжкой ключа.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# OAuth2 схема для получения токена из заголовка
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет пароль"""
    try:
        result = pwd_context.verify(plain_password, hashed_password)
        if not result:
            logger.debug(f"Пароль не совпадает для хеша: {hashed_password[:20]}...")
        return result
    except Exception as e:
        logger.error(f"Ошибка при проверке пароля: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Хеширует пароль с учётом ограничения bcrypt по длине (72 байта)."""
    # bcrypt обрабатывает только первые 72 байта пароля. Чтобы избежать ошибок и
    # неожиданных обрезаний на стороне библиотеки, аккуратно укорачиваем пароль сами.
    raw_password = (password or "").strip()
    try:
        encoded = raw_password.encode("utf-8")
    except Exception:
        # На всякий случай приводим к str и пробуем ещё раз
        raw_password = str(password or "").strip()
        encoded = raw_password.encode("utf-8", errors="ignore")

    # Если больше 72 байт — обрезаем по байтам
    if len(encoded) > 72:
        logger.warning(
            "Пароль длиннее 72 байт, выполняем безопасное усечение до допустимой длины для bcrypt"
        )
        trimmed_bytes = encoded[:72]
        raw_password = trimmed_bytes.decode("utf-8", errors="ignore")

    # На некоторых конфигурациях passlib/bcrypt всё равно может кидать ValueError
    # "password cannot be longer than 72 bytes" — подстрахуемся и повторно обрежем.
    try:
        return pwd_context.hash(raw_password)
    except ValueError as e:
        logger.warning(f"Повторное усечение пароля из-за ошибки bcrypt: {e}")
        safe_bytes = raw_password.encode("utf-8", errors="ignore")[:72]
        safe_password = safe_bytes.decode("utf-8", errors="ignore")
        return pwd_context.hash(safe_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создает JWT токен"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Получает пользователя по email (case-insensitive)"""
    # Email должен быть case-insensitive для удобства пользователей
    return db.query(User).filter(User.email.ilike(email)).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Аутентифицирует пользователя"""
    user = get_user_by_email(db, email)
    if not user:
        logger.debug(f"Пользователь с email {email} не найден")
        return None
    
    logger.debug(f"Проверка пароля для пользователя {email}, хеш: {user.hashed_password[:30]}...")
    
    if not verify_password(password, user.hashed_password):
        logger.warning(f"Неверный пароль для пользователя {email}")
        return None
    
    if not user.is_active:
        logger.warning(f"Пользователь {email} неактивен")
        return None
    
    logger.info(f"✅ Успешная аутентификация пользователя {email}")
    return user


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Получает текущего пользователя из JWT токена"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен доступа не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            logger.warning("JWT payload не содержит 'sub' (email)")
            raise credentials_exception
        logger.debug(f"JWT декодирован, email из токена: {email}")
    except JWTError as e:
        logger.warning(f"Ошибка декодирования JWT: {e}")
        raise credentials_exception
    
    # Нормализуем email (lowercase) для поиска
    email_normalized = email.lower().strip()
    user = get_user_by_email(db, email=email_normalized)
    if user is None:
        logger.warning(f"Пользователь с email {email_normalized} не найден в БД")
        raise credentials_exception
    
    logger.debug(f"✅ Пользователь найден: {user.email}")
    
    return user


async def get_current_active_user(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """Проверяет, что пользователь активен"""
    if not current_user or not current_user.is_active:
        raise HTTPException(status_code=400, detail="Неактивный пользователь")
    return current_user


async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Получает пользователя из токена, если он есть (опциональная авторизация)"""
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email:
            user = get_user_by_email(db, email=email)
            if user and user.is_active:
                return user
    except (JWTError, Exception):
        pass
    
    return None

