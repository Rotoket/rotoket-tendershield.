from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import shutil
import os
import logging
import json
import re
import uuid
import tempfile
import time
from datetime import datetime

# --- НАСТРОЙКИ ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ШАГ 3: Preprocessing & Evidence Layer (импорт до использования)
try:
    from preprocessor import EvidencePreprocessor
    from evidence_adapter import evidence_objects_to_llm_prompt, evidence_objects_to_summary
    EVIDENCE_LAYER_ENABLED = True
except ImportError as e:
    logger.warning(f"Evidence Layer (ШАГ 3) недоступен: {e}. Используется fallback на сырой текст.")
    EVIDENCE_LAYER_ENABLED = False

# ШАГ 4: Reasoning & Decision Layer (импорт до использования)
try:
    from reasoning_layer import ReasoningEngine
    from reasoning_types import ReasoningResult, DecisionPreview
    REASONING_LAYER_ENABLED = True
except ImportError as e:
    logger.warning(f"Reasoning Layer (ШАГ 4) недоступен: {e}. Используется fallback на LLM reasoning.")
    REASONING_LAYER_ENABLED = False

# ШАГ 5: Decision Preview Formatter (импорт до использования)
try:
    from decision_preview_formatter import DecisionPreviewFormatter
    DECISION_PREVIEW_FORMATTER_ENABLED = True
except ImportError as e:
    logger.warning(f"Decision Preview Formatter (ШАГ 5) недоступен: {e}.")
    DECISION_PREVIEW_FORMATTER_ENABLED = False

# ШАГ 6: Audit Trail & Versioning (импорт до использования)
try:
    from audit_trail_manager import get_audit_trail_manager
    from audit_trail_types import DecisionFreshnessStatus
    AUDIT_TRAIL_ENABLED = True
except ImportError as e:
    logger.warning(f"Audit Trail Manager (ШАГ 6) недоступен: {e}.")
    AUDIT_TRAIL_ENABLED = False

# ШАГ 13: Kill Switch & Safe Mode (импорт до использования)
try:
    from kill_switch_manager import get_kill_switch_manager
    from safe_mode_handler import SafeModeHandler
    from kill_switch_types import SystemMode
    KILL_SWITCH_ENABLED = True
except ImportError as e:
    logger.warning(f"Kill Switch (ШАГ 13) недоступен: {e}.")
    KILL_SWITCH_ENABLED = False
    # Заглушки для совместимости
    def get_kill_switch_manager():
        return None
    class SafeModeHandler:
        def get_safe_mode_response(self, tender_id=None):
            return None
        def get_evidence_only_response(self, evidence_objects, document_snapshot_id=None):
            return None
    class SystemMode:
        NORMAL = "NORMAL"
        SAFE = "SAFE"
        LOCKDOWN = "LOCKDOWN"

# --- ПРОСТАЯ ЗАЩИТА ОТ МНОЖЕСТВЕННЫХ РЕГИСТРАЦИЙ С ОДНОГО IP ---
# Важно: это in-memory защита на уровне процесса. При перезапуске backend
# счётчики обнуляются. Для production-регламента можно будет перенести
# эти лимиты в БД / Redis.
IP_REGISTRATION_LOG: Dict[str, List[datetime]] = {}
MAX_TRIAL_ACCOUNTS_PER_IP = 2       # максимум 2 триала на IP
TRIAL_IP_WINDOW_DAYS = 30           # считаем за последние 30 дней

# --- КОНФИГУРАЦИЯ МОДЕЛЕЙ ДЛЯ FAILOVER ---
# Импортируем настройки до использования, чтобы не было NameError.
from config import settings

# Список моделей по приоритету:
# 1) основная модель из настроек (по умолчанию qwen2.5-coder:7b),
# 2) лёгкий fallback qwen2.5:0.5b.
OLLAMA_MODELS = [
    getattr(settings, "OLLAMA_MODEL", "qwen2.5-coder:7b"),
    "qwen2.5:0.5b",
]

# --- ИМПОРТЫ ---
from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader
from langchain_ollama import ChatOllama
from services.pandoc_service import docx_to_markdown, PandocServiceError

from config import settings
from llm_client import get_analysis_llm, get_chat_llm
from legal_data import LEGAL_SNIPPETS
from database import (
    get_db,
    init_db,
    create_default_tariffs,
    User,
    Analysis,
    PackageAnalysis,
    Usage,
    Tariff,
    engine,
    DemoSession,
    GeneratedDocument,
    DecisionRecord,
    PasswordResetToken,
    AnalysisJob,
)
from rag_engine import get_law_snippets
from mcp_client import get_mcp_client
from auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_current_user,
    get_optional_user,
    get_password_hash,
    get_user_by_email
)
import schemas
from schemas import (
    UserCreate, UserResponse, UserLogin, Token, AnalysisResponse, CompanyProfile,
    ForgotPasswordRequest, ResetPasswordRequest, LegalExplainRequest, LegalExplainResponse,
    AnalysisJobStartRequest, AnalysisJobStartResponse, AnalysisJobStatusResponse
)
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from fastapi import Depends, status, BackgroundTasks
from typing import Optional
from contextlib import asynccontextmanager


def _build_profile_response(current_user: User, db: Session) -> "schemas.ProfileResponse":
    """Формирует ответ профиля пользователя с учётом тарифа, использования и триала."""
    # Получаем тариф
    tariff = None
    if current_user.tariff_id:
        tariff = db.query(Tariff).filter(Tariff.id == current_user.tariff_id).first()
    
    # Получаем использование за текущий месяц
    now = datetime.utcnow()
    usage_record = db.query(Usage).filter(
        Usage.user_id == current_user.id,
        Usage.year == now.year,
        Usage.month == now.month
    ).first()
    
    # Если записи использования нет, создаем её
    if not usage_record:
        usage_record = Usage(
            user_id=current_user.id,
            year=now.year,
            month=now.month,
            analyses_count=0,
            packages_count=0
        )
        db.add(usage_record)
        db.commit()
        db.refresh(usage_record)
    
    # Формируем ответ по использованию
    analyses_count = usage_record.analyses_count
    packages_count = usage_record.packages_count
    analyses_limit = tariff.analyses_limit if tariff else 0
    package_limit = tariff.package_limit if tariff else 0
    
    # Для безлимитного тарифа (analyses_limit == -1) возвращаем -1 как индикатор безлимита
    analyses_remaining = -1 if analyses_limit == -1 else max(0, analyses_limit - analyses_count)
    packages_remaining = -1 if package_limit == -1 else max(0, package_limit - packages_count)
    
    usage_response = schemas.UsageResponse(
        analyses_count=analyses_count,
        packages_count=packages_count,
        analyses_limit=analyses_limit,
        package_limit=package_limit,
        analyses_remaining=analyses_remaining,
        packages_remaining=packages_remaining
    )
    
    # Информация о тарифе
    tariff_response = None
    if tariff:
        tariff_response = schemas.TariffResponse(
            id=tariff.id,
            name=tariff.name,
            price=tariff.price,
            analyses_limit=tariff.analyses_limit,
            package_limit=tariff.package_limit,
            features=tariff.features
        )
    
    # Информация о триале
    trial_info = None
    if current_user.plan_type == "trial":
        trial_info = schemas.TrialInfo(
            is_active=current_user.is_active and current_user.is_trial_active(),
            remaining_days=current_user.get_remaining_trial_days(),
            trial_start=current_user.trial_start,
            trial_end=current_user.trial_end
        )
    
    # Профиль компании (для персонализации анализа)
    company_profile = None
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('users')]
        has_profile_fields = any(col in columns for col in ['has_sro', 'has_fstek', 'has_fsb', 'has_mchs', 'experience_level', 'tax_system'])
        if has_profile_fields:
            company_profile = schemas.CompanyProfile(
                has_sro=getattr(current_user, 'has_sro', False),
                has_fstek=getattr(current_user, 'has_fstek', False),
                has_fsb=getattr(current_user, 'has_fsb', False),
                has_mchs=getattr(current_user, 'has_mchs', False),
                experience_level=getattr(current_user, 'experience_level', None),
                tax_system=getattr(current_user, 'tax_system', None),
            )
    except Exception as e:
        logger.warning(f"Не удалось получить профиль компании пользователя: {e}")
        company_profile = None
    
    return schemas.ProfileResponse(
        user=current_user,
        tariff=tariff_response,
        usage=usage_response,
        trial=trial_info,
        company_profile=company_profile,
    )

# Инициализация БД при старте
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        # Проверяем подключение к БД
        from sqlalchemy import text
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        
        # Создаем таблицы (если их нет)
        init_db()
        
        # Создаем тарифы
        db = next(get_db())
        create_default_tariffs(db)
        db.close()
        
        # Создаем индексы для оптимизации
        try:
            from database_indexes import create_indexes
            create_indexes()
        except Exception as idx_err:
            logger.warning(f"⚠️ Не удалось создать индексы: {idx_err}")
        
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        logger.info("💡 Для полной функциональности настройте PostgreSQL (см. DATABASE_SETUP.md)")
    
    yield
    
    # Shutdown (если нужно)
    pass

app = FastAPI(
    title="Tender Shield API",
    description="API для анализа тендерной документации",
    version="1.0.0",
    lifespan=lifespan
)

# Настройка Rate Limiting
try:
    from rate_limiter import setup_rate_limiting
    setup_rate_limiting(app)
except ImportError:
    logger.warning("slowapi не установлен, rate limiting отключен")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint для диагностики
@app.get("/api/health")
async def health_check():
    """Проверка работоспособности API"""
    return {
        "status": "ok",
        "message": "API работает",
        "timestamp": datetime.now().isoformat(),
        "cors_origins": settings.CORS_ORIGINS
    }

class ChatRequest(BaseModel):
    history: List[dict]
    message: str


class DocumentAnalysis(BaseModel):
    filename: str
    score: int
    summary: str
    verdict: str
    passport: dict
    passportValidation: Optional[dict] = None
    passportEvidence: Optional[dict] = None
    issues: list
    specs: list


class PackageAnalysisResponse(BaseModel):
    packageId: str
    summaryScore: float
    verdict: str
    documents: List[DocumentAnalysis]
    globalIssues: List[dict]


class HistoryItem(BaseModel):
    id: str
    createdAt: datetime
    kind: str  # "single" или "package"
    industry: str
    files: List[str]
    summaryScore: float
    verdict: str
    user_decision: Optional[Dict[str, Any]] = None  # Решение пользователя (Decision Layer)


class HistoryResponse(BaseModel):
    items: List[HistoryItem]


class LegalSnippet(BaseModel):
    id: str
    category: str
    lawReference: str
    title: str
    summary: str


class LegalSearchResponse(BaseModel):
    items: List[LegalSnippet]


class GeneratedDocumentResponse(BaseModel):
    id: int
    analysis_id: int
    type: str
    content: str
    created_at: datetime


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ТРИАЛОВ И ЛИМИТОВ ---
def check_user_can_analyze(user: User, db: Session) -> tuple:
    """Проверяет, может ли пользователь выполнить анализ"""
    from database import Tariff
    
    # Если триал активен - разрешаем без ограничений
    if user.plan_type == "trial" and user.is_trial_active():
        return True, ""
    
    # Получаем тариф
    tariff = None
    if user.tariff_id:
        tariff = db.query(Tariff).filter(Tariff.id == user.tariff_id).first()
    elif user.plan_type == "free":
        # Если Free тариф, но tariff_id не установлен - находим Free тариф
        tariff = db.query(Tariff).filter(Tariff.name == "Free").first()
    
    if not tariff:
        return False, "Тариф не найден. Обратитесь в поддержку."
    
    # Проверяем лимиты
    if tariff.analyses_limit == -1:  # Безлимит
        return True, ""
    
    # Получаем использование за текущий месяц
    now = datetime.utcnow()
    usage = db.query(Usage).filter(
        Usage.user_id == user.id,
        Usage.year == now.year,
        Usage.month == now.month
    ).first()
    
    analyses_count = usage.analyses_count if usage else 0
    
    if analyses_count >= tariff.analyses_limit:
        remaining_days = user.get_remaining_trial_days() if user.plan_type == "trial" else 0
        if remaining_days > 0:
            return False, f"Достигнут лимит анализов. Триал истекает через {remaining_days} дней. Обновите подписку."
        return False, f"Достигнут лимит анализов по тарифу ({tariff.analyses_limit}/мес). Обновите подписку."
    
    return True, ""


# Инициализация БД при старте (если нужно)
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        # Проверяем подключение к БД
        from sqlalchemy import text
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        
        # Создаем таблицы (если их нет)
        init_db()
        
        # Создаем тарифы
        db = next(get_db())
        create_default_tariffs(db)
        db.close()
        
        # Создаем индексы для оптимизации
        try:
            from database_indexes import create_indexes
            create_indexes()
        except Exception as idx_err:
            logger.warning(f"⚠️ Не удалось создать индексы: {idx_err}")
        
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        logger.info("💡 Для полной функциональности настройте PostgreSQL (см. DATABASE_SETUP.md)")
    
    yield
    
    # Shutdown (если нужно)
    pass

# Старый способ (deprecated) - оставляем для совместимости, но используем lifespan
@app.on_event("startup")
async def startup_event():
    """Инициализация БД и создание тарифов при первом запуске"""
    try:
        # Проверяем подключение к БД
        from sqlalchemy import text
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        
        # Создаем таблицы (если их нет)
        init_db()
        
        # Создаем тарифы
        db = next(get_db())
        create_default_tariffs(db)
        db.close()
        
        # Создаем индексы для оптимизации
        try:
            from database_indexes import create_indexes
            create_indexes()
        except Exception as idx_err:
            logger.warning(f"⚠️ Не удалось создать индексы: {idx_err}")
        
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.warning(f"⚠️ БД недоступна, работаем в режиме без БД: {e}")
        logger.info("💡 Для полной функциональности настройте PostgreSQL (см. DATABASE_SETUP.md)")

# Старая история (для обратной совместимости, будет удалена после миграции)
HISTORY: List[HistoryItem] = []
MAX_HISTORY_ITEMS = 200


# --- ЭНДПОИНТЫ АВТОРИЗАЦИИ ---
@app.post("/api/auth/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: schemas.UserCreate,
    request: Request,
    demo_session_id: Optional[str] = None,  # Опциональный ID демо-сессии для миграции
    db: Session = Depends(get_db)
):
    """Регистрация нового пользователя с автоматическим триалом на 7 дней.

    Простая защита: ограничиваем количество trial-аккаунтов,
    создаваемых с одного IP, чтобы избежать бесконечных регистраций.
    """
    try:
        # --- Ограничение по IP для trial-регистраций ---
        client_ip = request.client.host if request and request.client else "unknown"
        now = datetime.utcnow()
        window_start = now - timedelta(days=TRIAL_IP_WINDOW_DAYS)

        ip_events = IP_REGISTRATION_LOG.get(client_ip, [])
        # Оставляем только регистрации за последнее окно
        ip_events = [ts for ts in ip_events if ts >= window_start]

        if len(ip_events) >= MAX_TRIAL_ACCOUNTS_PER_IP:
            logger.warning(f"Trial registration limit reached for IP {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Лимит бесплатных регистраций с этого IP исчерпан. "
                       "Используйте уже созданный аккаунт или свяжитесь с поддержкой."
            )

        # Проверяем, существует ли пользователь с таким email
        existing_user = get_user_by_email(db, user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже зарегистрирован"
            )
        
        # Создаем нового пользователя с триалом
        # bcrypt поддерживает пароли до 72 байт, поэтому аккуратно обрезаем слишком длинные пароли
        raw_password = (user_in.password or "").strip()
        if len(raw_password.encode("utf-8")) > 72:
            logger.warning(
                "Пароль при регистрации длиннее 72 байт, выполняем безопасное усечение до допустимой длины"
            )
            # Усечение по байтам, а не по символам, чтобы не порвать UTF‑8
            raw_bytes = raw_password.encode("utf-8")[:72]
            try:
                raw_password = raw_bytes.decode("utf-8", errors="ignore")
            except Exception:
                # В маловероятном случае проблем с декодированием просто берём ASCII-часть
                raw_password = raw_bytes.decode("utf-8", errors="ignore")

        hashed_password = get_password_hash(raw_password)
        trial_end = now + timedelta(days=7)  # 7 дней триала
        
        # Проверяем, есть ли поля триалов в таблице (для обратной совместимости)
        from sqlalchemy import inspect
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('users')]
        has_trial_fields = all(col in columns for col in ['plan_type', 'trial_start', 'trial_end'])
        
        if has_trial_fields:
            # Создаем пользователя с полями триала
            new_user = User(
                email=user_in.email,
                hashed_password=hashed_password,
                name=user_in.name,
                company=user_in.company,
                is_active=True,
                plan_type="trial",
                trial_start=now,
                trial_end=trial_end,
            )
        else:
            # Создаем пользователя без полей триала (старая версия БД)
            logger.warning("Поля триалов не найдены в БД. Создаем пользователя без триала.")
            logger.warning("Выполните миграцию: python migrate_trial_fields.py")
            new_user = User(
                email=user_in.email,
                hashed_password=hashed_password,
                name=user_in.name,
                company=user_in.company,
                is_active=True,
            )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Регистрируем успешную trial-регистрацию для этого IP
        ip_events.append(now)
        IP_REGISTRATION_LOG[client_ip] = ip_events
        
        logger.info(f"✅ Новый пользователь зарегистрирован: {user_in.email}")
        if hasattr(new_user, 'trial_end') and new_user.trial_end:
            logger.info(f"   Триал до {new_user.trial_end.date()}")
        
        # Мигрируем демо-анализы, если есть demo_session_id
        if demo_session_id:
            try:
                from demo_migration import migrate_demo_analyses_to_user
                migrated_count = migrate_demo_analyses_to_user(demo_session_id, new_user.id, db)
                if migrated_count > 0:
                    logger.info(f"Мигрировано {migrated_count} демо-анализов при регистрации")
            except Exception as e:
                logger.warning(f"Не удалось мигрировать демо-анализы: {e}")
        
        # Отправляем приветственное письмо
        try:
            from email_service import EmailService
            EmailService.send_welcome_email(
                email=new_user.email,
                name=new_user.name,
                trial_days=7
            )
        except Exception as e:
            logger.warning(f"Не удалось отправить приветственное письмо: {e}")
        
        return new_user
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"❌ Ошибка регистрации: {e}")
        logger.error(f"Детали ошибки:\n{error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при регистрации пользователя: {str(e)}"
        )


@app.post("/api/auth/login", response_model=schemas.Token)
async def login_for_access_token(
    form_data: schemas.UserLogin,
    db: Session = Depends(get_db)
):
    """Вход в систему и получение JWT токена"""
    logger.info(f"Попытка входа: email={form_data.email}")
    
    # Проверяем, что email и password не пустые
    if not form_data.email or not form_data.password:
        logger.warning("Пустой email или пароль при попытке входа")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = authenticate_user(db, form_data.email, form_data.password)
    if not user:
        logger.warning(f"Неудачная попытка входа для email: {form_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # Нормализуем email для токена (lowercase для консистентности)
    email_for_token = user.email.lower().strip()
    access_token = create_access_token(
        data={"sub": email_for_token}, expires_delta=access_token_expires
    )
    logger.info(f"✅ Токен создан для пользователя {email_for_token}")
    
    return schemas.Token(
        access_token=access_token,
        token_type="bearer"
    )


@app.get("/api/auth/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Получение информации о текущем пользователе"""
    return current_user


@app.post("/api/auth/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    request_data: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Запрос на сброс пароля. Отправляет email со ссылкой для сброса пароля.
    Для безопасности всегда возвращает успех, даже если email не найден.
    """
    try:
        user = get_user_by_email(db, request_data.email)
        
        # Для безопасности всегда возвращаем успех, даже если пользователь не найден
        # Это предотвращает перебор email-адресов
        if not user:
            logger.info(f"Запрос сброса пароля для несуществующего email: {request_data.email}")
            return {"ok": True}
        
        # Генерируем уникальный токен
        import secrets
        reset_token = secrets.token_urlsafe(32)
        
        # Удаляем старые неиспользованные токены для этого пользователя
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == False,
            PasswordResetToken.expires_at > datetime.utcnow()
        ).delete()
        
        # Создаём новый токен (действителен 30 минут)
        expires_at = datetime.utcnow() + timedelta(minutes=30)
        reset_token_obj = PasswordResetToken(
            user_id=user.id,
            token=reset_token,
            expires_at=expires_at,
            used=False
        )
        db.add(reset_token_obj)
        db.commit()
        
        # Отправляем email в фоне (не блокируем ответ)
        try:
            from email_service import EmailService
            # Отправляем синхронно, но с таймаутом в email_service
            email_sent = EmailService.send_password_reset_email(
                email=user.email,
                name=user.name,
                reset_token=reset_token
            )
            if email_sent:
                logger.info(f"✅ Письмо для сброса пароля отправлено: {user.email}")
            else:
                logger.warning(f"⚠️ Не удалось отправить письмо для сброса пароля: {user.email}")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки письма для сброса пароля: {e}", exc_info=True)
            # Не возвращаем ошибку пользователю, чтобы не раскрывать информацию
        
        # Всегда возвращаем успех (для безопасности)
        return {"ok": True}
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Ошибка при запросе сброса пароля: {e}")
        # Всегда возвращаем успех для безопасности
        return {"ok": True}


@app.post("/api/auth/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request_data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Сброс пароля по токену из email.
    """
    try:
        # Находим токен
        reset_token_obj = db.query(PasswordResetToken).filter(
            PasswordResetToken.token == request_data.token,
            PasswordResetToken.used == False
        ).first()
        
        if not reset_token_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный или недействительный токен сброса пароля"
            )
        
        # Проверяем срок действия
        if datetime.utcnow() > reset_token_obj.expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Срок действия ссылки для сброса пароля истёк. Запросите новую ссылку."
            )
        
        # Получаем пользователя
        user = db.query(User).filter(User.id == reset_token_obj.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        # Проверяем длину пароля (bcrypt ограничение 72 байта)
        raw_password = (request_data.new_password or "").strip()
        if len(raw_password.encode("utf-8")) > 72:
            logger.warning("Пароль при сбросе длиннее 72 байт, выполняем безопасное усечение")
            raw_bytes = raw_password.encode("utf-8")[:72]
            raw_password = raw_bytes.decode("utf-8", errors="ignore")
        
        # Обновляем пароль
        user.hashed_password = get_password_hash(raw_password)
        
        # Помечаем токен как использованный
        reset_token_obj.used = True
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"✅ Пароль успешно сброшен для пользователя: {user.email}")
        
        return {"message": "Пароль успешно изменён. Теперь вы можете войти с новым паролем."}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Ошибка при сбросе пароля: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при сбросе пароля. Попробуйте позже или запросите новую ссылку."
        )


@app.get("/api/profile", response_model=schemas.ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получение полной информации о профиле пользователя (тариф, использование, триал, профиль компании)"""
    return _build_profile_response(current_user, db)


@app.put("/api/profile/company", response_model=schemas.ProfileResponse)
async def update_company_profile(
    profile_in: CompanyProfile,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Обновление профиля компании (лицензии, опыт, налоговый режим).
    Для обратной совместимости сначала проверяем наличие соответствующих полей в БД.
    """
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('users')]
        required_columns = ['has_sro', 'has_fstek', 'has_fsb', 'has_mchs', 'experience_level', 'tax_system']
        has_profile_fields = all(col in columns for col in required_columns)
        if not has_profile_fields:
            logger.warning("Поля профиля компании отсутствуют в таблице users. Запустите миграцию для добавления этих полей.")
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Поля профиля компании ещё не настроены. Обратитесь к администратору системы.",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка проверки структуры БД для профиля компании: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при сохранении профиля компании")

    # Обновляем поля пользователя
    current_user.has_sro = profile_in.has_sro
    current_user.has_fstek = profile_in.has_fstek
    current_user.has_fsb = profile_in.has_fsb
    current_user.has_mchs = profile_in.has_mchs
    current_user.experience_level = profile_in.experience_level
    current_user.tax_system = profile_in.tax_system

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return _build_profile_response(current_user, db)


@app.get("/api/tariffs", response_model=List[schemas.TariffResponse])
async def get_tariffs(db: Session = Depends(get_db)):
    """Получение списка доступных тарифов"""
    tariffs = db.query(Tariff).filter(Tariff.is_active == True).all()
    return [
        schemas.TariffResponse(
            id=t.id,
            name=t.name,
            price=t.price,
            analyses_limit=t.analyses_limit,
            package_limit=t.package_limit,
            features=t.features
        )
        for t in tariffs
    ]


# --- ЭНДПОИНТЫ ПЛАТЕЖНОЙ СИСТЕМЫ ---
@app.post("/api/payment/create")
async def create_payment_endpoint(
    tariff_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Создание платежа для подписки на тариф"""
    from payment import create_payment
    
    try:
        payment_info = create_payment(current_user.id, tariff_id, db)
        return payment_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка создания платежа: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания платежа")


@app.post("/api/payment/webhook")
async def payment_webhook(request: Request, db: Session = Depends(get_db)):
    """Webhook для обработки уведомлений от Yandex Kassa"""
    from payment import process_payment_webhook, verify_webhook_signature
    import json
    
    body = await request.body()
    signature = request.headers.get("X-YooMoney-Signature", "")
    
    try:
        webhook_data = json.loads(body.decode())
        
        # Проверяем подпись (в тестовом режиме пропускаем)
        if not verify_webhook_signature(body.decode(), signature):
            logger.warning("Неверная подпись webhook")
            # В тестовом режиме все равно обрабатываем
            if not getattr(settings, 'YOOKASSA_TEST_MODE', True):
                raise HTTPException(status_code=401, detail="Неверная подпись")
        
        success = process_payment_webhook(webhook_data, db)
        if success:
            return {"status": "ok"}
        else:
            return {"status": "ignored"}
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обработки webhook")


@app.get("/api/payment/mock-confirm")
async def mock_payment_confirm(
    payment_id: str,
    tariff_id: int = None,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Эмуляция подтверждения платежа (для тестирования)"""
    from payment import activate_subscription_mock
    from fastapi.responses import RedirectResponse
    
    if not current_user:
        return RedirectResponse(url="/login?error=not_authenticated")
    
    if not tariff_id:
        return RedirectResponse(url="/profile?error=no_tariff")
    
    try:
        success = activate_subscription_mock(current_user.id, tariff_id, db)
        if success:
            return RedirectResponse(url="/profile?payment=success")
        else:
            return RedirectResponse(url="/profile?payment=error")
    except Exception as e:
        logger.error(f"Ошибка активации подписки: {e}")
        return RedirectResponse(url="/profile?payment=error")


# --- УТИЛИТЫ (REGEX) ---
def extract_price_regex(text):
    """Находит цену, если ИИ ошибся. Улучшенная версия с поддержкой млн/тыс."""
    # Очищаем текст от лишних пробелов для лучшего поиска
    text_clean = re.sub(r'\s+', ' ', text)
    
    # Ищем НМЦК, начальную цену, цену контракта
    patterns = [
        r'нмцк[^\d]{0,200}?(\d[\d\s]*[.,]?\d*)\s*(?:млн|тыс|руб|₽|rur|rub)',
        r'нмцд[^\d]{0,200}?(\d[\d\s]*[.,]?\d*)\s*(?:млн|тыс|руб|₽|rur|rub)',
        r'начальн[ая]*\s*(?:максимальн[ая]*)?\s*цен[аи][^\d]{0,200}?(\d[\d\s]*[.,]?\d*)\s*(?:млн|тыс|руб|₽|rur|rub)',
        r'цен[аи]\s*контракт[а]?[^\d]{0,200}?(\d[\d\s]*[.,]?\d*)\s*(?:млн|тыс|руб|₽|rur|rub)',
        r'стоимость[^\d]{0,200}?(\d[\d\s]*[.,]?\d*)\s*(?:млн|тыс|руб|₽|rur|rub)',
        r'сумм[аи]\s*контракт[а]?[^\d]{0,200}?(\d[\d\s]*[.,]?\d*)\s*(?:млн|тыс|руб|₽|rur|rub)',
        r'общая\s+стоимость[^\d]{0,200}?(\d[\d\s]*[.,]?\d*)\s*(?:млн|тыс|руб|₽|rur|rub)',
        r'итого[^\d]{0,200}?(\d[\d\s]*[.,]?\d*)\s*(?:млн|тыс|руб|₽|rur|rub)',
        r'обоснован[ия]*\s*цен[ы]?[^\d]{0,200}?(\d[\d\s]*[.,]?\d*)\s*(?:млн|тыс|руб|₽|rur|rub)',
    ]
    
    all_prices = []
    for pattern in patterns:
        matches = re.finditer(pattern, text_clean, re.IGNORECASE)
        for match in matches:
            value_str = match.group(1).replace(' ', '').replace(',', '.').strip()
            context = text_clean[max(0, match.start()-50):match.end()+50].lower()
            
            try:
                value = float(value_str)
                # Проверяем множитель (млн, тыс)
                if 'млн' in context:
                    value *= 1_000_000
                elif 'тыс' in context:
                    value *= 1_000
                all_prices.append(value)
            except ValueError:
                continue
    
    # Также ищем простые паттерны с рублями (только большие суммы)
    simple_matches = re.findall(r'(\d[\d\s]{3,}[.,]?\d*)\s*(?:руб|₽|RUB|rur|rub)', text_clean, re.IGNORECASE)
    for m in simple_matches:
        try:
            price = float(m.replace(' ', '').replace(',', '.').strip())
            # Игнорируем слишком маленькие суммы (меньше 1000 руб) - это не НМЦК
            if price >= 1000:
                all_prices.append(price)
        except ValueError:
            continue
    
    # Ищем числа в таблицах и структурированных данных
    # Паттерн для чисел с пробелами как разделителями тысяч
    table_patterns = re.findall(r'(\d{1,3}(?:\s+\d{3})*(?:[.,]\d+)?)\s*(?:млн|тыс|руб|₽)', text_clean, re.IGNORECASE)
    for m in table_patterns:
        try:
            price_str = m.replace(' ', '').replace(',', '.').strip()
            price = float(price_str)
            # Проверяем контекст на множители
            context_idx = text_clean.lower().find(m.lower())
            if context_idx >= 0:
                context = text_clean[max(0, context_idx-50):context_idx+len(m)+50].lower()
                if 'млн' in context:
                    price *= 1_000_000
                elif 'тыс' in context:
                    price *= 1_000
            if price >= 1000:
                all_prices.append(price)
        except ValueError:
            continue
    
    if all_prices:
        # Берем максимальную цену (обычно это НМЦК)
        max_price = max(all_prices)
        if max_price >= 1_000_000:
            return f"{max_price/1_000_000:,.2f} млн ₽".replace(',', ' ').replace('.', ',')
        elif max_price >= 1_000:
            return f"{max_price/1_000:,.2f} тыс ₽".replace(',', ' ').replace('.', ',')
        else:
            return f"{max_price:,.2f} ₽".replace(',', ' ').replace('.', ',')
    
    return "Не найдено"


def extract_dates_regex(text):
    """Находит дедлайны. Улучшенная версия с контекстом."""
    # Ищем даты в контексте "срок подачи", "крайний срок", "до"
    deadline_patterns = [
        r'срок\s+подачи\s+заявк[и]?[^\d]{0,50}?(\d{2}[./-]\d{2}[./-]\d{4})',
        r'крайн[ий]*\s+срок[^\d]{0,50}?(\d{2}[./-]\d{2}[./-]\d{4})',
        r'до\s+(\d{2}[./-]\d{2}[./-]\d{4})',
        r'дата\s+окончания[^\d]{0,50}?(\d{2}[./-]\d{2}[./-]\d{4})',
        r'приём\s+заявок[^\d]{0,50}?(\d{2}[./-]\d{2}[./-]\d{4})',
    ]
    
    for pattern in deadline_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            # Нормализуем формат
            date_str = date_str.replace('/', '.').replace('-', '.')
            return date_str
    
    # Если не нашли в контексте, ищем любые даты
    matches = re.findall(r'\d{2}[./-]\d{2}[./-]\d{4}', text)
    if matches:
        # Берем последнюю (обычно это дедлайн)
        date_str = matches[-1].replace('/', '.').replace('-', '.')
        return date_str
    
    return "См. документацию"


def extract_onmck_summary(text: str) -> dict:
    """Извлекает НМЦК из обоснования НМЦК/НМЦД.
    
    Ищет НМЦК в различных форматах и контекстах. Агрессивный поиск.
    """
    summary: dict = {}
    # Очищаем текст от лишних пробелов
    text_clean = re.sub(r'\s+', ' ', text)
    tl = text_clean.lower()
    
    # Ищем НМЦК в разных контекстах (более агрессивные паттерны)
    nmck_patterns = [
        r'нмцк[^\d]{0,300}?(\d[\d\s]*[.,]?\d*)\s*(?:млн|тыс|руб|₽|rur|rub)',
        r'нмцд[^\d]{0,300}?(\d[\d\s]*[.,]?\d*)\s*(?:млн|тыс|руб|₽|rur|rub)',
        r'начальн[ая]*\s*(?:максимальн[ая]*)?\s*цен[аи]\s*контракт[а]?[^\d]{0,300}?(\d[\d\s]*[.,]?\d*)\s*(?:млн|тыс|руб|₽|rur|rub)',
        r'обоснован[ия]*\s*(?:нмцк|нмцд|цен[ы]?)[^\d]{0,300}?(\d[\d\s]*[.,]?\d*)\s*(?:млн|тыс|руб|₽|rur|rub)',
        r'итого[^\d]{0,300}?(\d[\d\s]*[.,]?\d*)\s*(?:млн|тыс|руб|₽|rur|rub)',
        r'общая\s+стоимость[^\d]{0,300}?(\d[\d\s]*[.,]?\d*)\s*(?:млн|тыс|руб|₽|rur|rub)',
        r'сумм[аи]\s*(?:контракт[а]?|закупк[и]?)[^\d]{0,300}?(\d[\d\s]*[.,]?\d*)\s*(?:млн|тыс|руб|₽|rur|rub)',
    ]
    
    all_prices = []
    for pattern in nmck_patterns:
        matches = re.finditer(pattern, text_clean, re.IGNORECASE)
        for match in matches:
            value_str = match.group(1).replace(' ', '').replace(',', '.').strip()
            context = text_clean[max(0, match.start()-100):match.end()+100].lower()
            
            try:
                value = float(value_str)
                # Проверяем множитель (млн, тыс)
                if 'млн' in context:
                    value *= 1_000_000
                elif 'тыс' in context:
                    value *= 1_000
                all_prices.append(value)
            except ValueError:
                continue
    
    if all_prices:
        # Берем максимальную цену (обычно это НМЦК)
        max_price = max(all_prices)
        if max_price >= 1_000_000:
            summary["nmck"] = f"{max_price/1_000_000:,.2f} млн ₽".replace(',', ' ').replace('.', ',')
        elif max_price >= 1_000:
            summary["nmck"] = f"{max_price/1_000:,.2f} тыс ₽".replace(',', ' ').replace('.', ',')
        else:
            summary["nmck"] = f"{max_price:,.2f} ₽".replace(',', ' ').replace('.', ',')
        summary["nmckNumeric"] = max_price
    
    return summary


def extract_tender_number_regex(text: str) -> Optional[str]:
    """Пытается извлечь номер закупки/тендера.

    Частый случай для ЕИС: 19-значный номер.
    """
    if not text:
        return None

    # ЕИС: 19 цифр подряд
    m = re.search(r"\b(\d{19})\b", text)
    if m:
        return m.group(1)

    # Общий случай: № <цифры>
    m = re.search(r"(?:закупк[аи]|извещени[ея]|тендер)[^\n]{0,60}?№\s*([0-9]{6,})", text, re.IGNORECASE)
    if m:
        return m.group(1)

    m = re.search(r"№\s*([0-9]{6,})", text)
    if m:
        return m.group(1)

    return None


def extract_customer_regex(text: str) -> Optional[str]:
    """Пытается извлечь наименование заказчика/организатора из текста."""
    if not text:
        return None

    # Ищем по строкам (в документах часто это отдельная строка)
    patterns = [
        r"^(?:государственный\s+)?заказчик\s*[:\-]\s*(.+)$",
        r"^наименование\s+заказчика\s*[:\-]\s*(.+)$",
        r"^организатор\s+закупк[аи]\s*[:\-]\s*(.+)$",
        r"^заказчик\s*[:\-]\s*(.+)$",
    ]

    for p in patterns:
        m = re.search(p, text, re.IGNORECASE | re.MULTILINE)
        if m:
            value = (m.group(1) or "").strip()
            # Обрезаем хвосты вроде "ИНН..." если попали в ту же строку
            value = re.split(r"\s{2,}|\s+ИНН\s*[:\-]", value, maxsplit=1)[0].strip()
            if 3 <= len(value) <= 200:
                return value

    # Fallback: в некоторых документах встречается "Заказчик: <...> (ИНН ...)"
    m = re.search(r"заказчик\s*[:\-]\s*([^\n]{3,200})", text, re.IGNORECASE)
    if m:
        value = (m.group(1) or "").strip()
        value = re.split(r"\s{2,}|\s+ИНН\s*[:\-]", value, maxsplit=1)[0].strip()
        if 3 <= len(value) <= 200:
            return value

    return None


def extract_deadline_execution_regex(text: str) -> Optional[str]:
    """Пытается извлечь срок исполнения/поставки.

    Это может быть дата или длительность (например, "в течение 30 дней").
    """
    if not text:
        return None

    patterns = [
        r"срок\s+(?:исполнения|оказания\s+услуг|поставки|выполнения\s+работ)[^\n\d]{0,80}?(\d{2}[./-]\d{2}[./-]\d{4})",
        r"срок\s+(?:исполнения|оказания\s+услуг|поставки|выполнения\s+работ)[^\n]{0,120}?(в\s+течение\s+\d{1,3}\s*(?:календарн(?:ых|ые)?|рабоч(?:их|ие)?)?\s*дн(?:ей|я)?)",
        r"(?:поставка|исполнение|оказание\s+услуг)[^\n]{0,80}?(до\s+\d{2}[./-]\d{2}[./-]\d{4})",
    ]

    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            value = (m.group(1) or "").strip()
            value = value.replace('/', '.').replace('-', '.')
            if value:
                return value

    return None


def extract_nmck_info(text: str) -> dict:
    """Возвращает {nmck: str, nmckNumeric: float|None} на основе детерминированных правил."""
    if not text:
        return {"nmck": "Не найдено", "nmckNumeric": None}

    # 1) агрессивно для обоснования
    onmck = extract_onmck_summary(text)
    if onmck.get("nmck") and onmck.get("nmckNumeric"):
        return {"nmck": onmck["nmck"], "nmckNumeric": onmck["nmckNumeric"]}

    # 2) общий regex
    nmck_str = extract_price_regex(text)
    nmck_num = _parse_amount(nmck_str) if nmck_str else None

    return {"nmck": nmck_str or "Не найдено", "nmckNumeric": nmck_num}


def build_passport_validation(passport: dict) -> dict:
    """Неблокирующая валидация ключевых паспортных полей."""
    missing_fields: List[str] = []

    tender_number = str(passport.get("tenderNumber") or "").strip()
    customer = str(passport.get("customer") or "").strip()
    nmck_numeric = passport.get("nmckNumeric")
    deadline_app = str(passport.get("deadlineApp") or "").strip()
    deadline_execution = str(passport.get("deadlineExecution") or "").strip()

    if not tender_number or tender_number in {"Не найдено", "—"}:
        missing_fields.append("tenderNumber")

    if not customer or customer in {"Не найдено", "Не указан", "—"}:
        missing_fields.append("customer")

    try:
        nmck_val = float(nmck_numeric) if nmck_numeric is not None else 0.0
    except Exception:
        nmck_val = 0.0

    if nmck_val <= 0:
        missing_fields.append("nmck")

    if not deadline_app or deadline_app in {"См. документацию", "Не найдено", "Не указано", "—"}:
        missing_fields.append("deadlineApp")

    if not deadline_execution or deadline_execution in {"Не найдено", "Не указано", "—"}:
        missing_fields.append("deadlineExecution")

    warnings: List[str] = []
    if missing_fields:
        warnings.append("Паспорт тендера заполнен не полностью. Данные не найдены — возможен скрытый риск.")

    return {
        "is_complete": len(missing_fields) == 0,
        "missing_fields": missing_fields,
        "warnings": warnings,
    }


def build_llm_context_excerpt(text: str, max_chars: int = 24000) -> str:
    """Собирает "умные" выдержки для LLM вместо первых N символов.

    Идея: давать модели начало + конец + фрагменты вокруг ключевых маркеров (НМЦК/сроки/заказчик).
    """
    if not text:
        return ""

    if len(text) <= max_chars:
        return text

    head = text[: min(8000, len(text))]
    tail = text[max(0, len(text) - 8000) :]

    markers = [
        "нмцк",
        "нмцд",
        "начальная (максимальная) цена",
        "цена контракта",
        "заказчик",
        "организатор",
        "срок подачи",
        "окончания подачи",
        "срок исполнения",
        "срок поставки",
    ]

    windows: List[str] = []
    lowered = text.lower()
    for mk in markers:
        idx = lowered.find(mk)
        if idx == -1:
            continue
        start = max(0, idx - 1200)
        end = min(len(text), idx + 2000)
        windows.append(text[start:end])
        if len(windows) >= 6:
            break

    body = "\n\n".join(windows)

    # Собираем с ограничением
    combined = "\n\n".join(
        [
            "=== НАЧАЛО ДОКУМЕНТА ===\n" + head,
            "=== КЛЮЧЕВЫЕ ФРАГМЕНТЫ ===\n" + body,
            "=== КОНЕЦ ДОКУМЕНТА ===\n" + tail,
        ]
    )

    return combined[:max_chars]


# --- Evidence helpers (P1: источники для паспорта/рисков) ---

def _normalize_for_search(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


def _extract_section_reference(quote: str) -> Optional[str]:
    if not quote:
        return None
    q = quote
    patterns = [
        r"(п\.?\s*\d+(?:\.\d+)*)",
        r"(раздел\s+[IVXLC\d]+)",
        r"(ст\.?\s*\d+(?:\.\d+)*)",
    ]
    for p in patterns:
        m = re.search(p, q, re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def _find_page_for_snippet(page_texts: Optional[List[str]], snippet: str) -> Optional[str]:
    """Пытается найти страницу, где встречается snippet.

    Важно: quote обычно содержит лишний контекст (окно вокруг совпадения), поэтому
    полное совпадение часто не срабатывает. Используем несколько "якорей":
    - полный нормализованный snippet
    - начало/конец
    - набор первых/последних токенов
    """
    if not page_texts or not snippet:
        return None

    sn = _normalize_for_search(snippet)
    if not sn:
        return None

    candidates: List[str] = []
    candidates.append(sn)

    if len(sn) > 220:
        candidates.append(sn[:220].strip())
        candidates.append(sn[-220:].strip())

    tokens = re.findall(r"[0-9a-zа-я]{4,}", sn, re.IGNORECASE)
    if tokens:
        candidates.append(" ".join(tokens[:10]))
        candidates.append(" ".join(tokens[-10:]))

    # убираем слишком короткие/дубликаты
    seen = set()
    final_candidates: List[str] = []
    for c in candidates:
        c = (c or "").strip()
        if len(c) < 20:
            continue
        if c in seen:
            continue
        seen.add(c)
        final_candidates.append(c)

    for i, page_text in enumerate(page_texts):
        pt = _normalize_for_search(page_text)
        for cand in final_candidates:
            if cand and cand in pt:
                return str(i + 1)

    return None


def _build_evidence_item(
    filename: str,
    quote: str,
    page_texts: Optional[List[str]] = None,
) -> dict:
    quote = (quote or "").strip()
    page_ref = _find_page_for_snippet(page_texts, quote)
    section_ref = _extract_section_reference(quote)
    return {
        "document_name": filename,
        "page_reference": page_ref,
        "section_reference": section_ref,
        "quote": quote,
    }


def _build_quote_window(text: str, start: int, end: int, window: int = 220) -> str:
    if not text:
        return ""
    s = max(0, start - window)
    e = min(len(text), end + window)
    return re.sub(r"\s+", " ", text[s:e]).strip()


def build_passport_evidence(
    text: str,
    filename: str,
    passport: dict,
    page_texts: Optional[List[str]] = None,
) -> dict:
    """Пытается дать источники для ключевых паспортных полей.

    Возвращает dict: { fieldKey: [ {document_name,page_reference,section_reference,quote} ] }
    """
    if not text or not filename or not isinstance(passport, dict):
        return {}

    evidence: Dict[str, List[dict]] = {}

    def add(field: str, quote: str):
        q = (quote or "").strip()
        if not q:
            return
        evidence[field] = [_build_evidence_item(filename, q, page_texts=page_texts)]

    # tenderNumber
    tender_number = str(passport.get("tenderNumber") or "").strip()
    if tender_number and tender_number not in {"Не найдено", "—"}:
        m = re.search(rf"(№\s*{re.escape(tender_number)}|\b{re.escape(tender_number)}\b)", text)
        if m:
            add("tenderNumber", _build_quote_window(text, m.start(), m.end()))

    # customer
    customer = str(passport.get("customer") or "").strip()
    if customer and customer not in {"Не найдено", "Не указан", "—"}:
        m = re.search(rf"(заказчик\s*[:\-].{{0,200}}?{re.escape(customer)})", text, re.IGNORECASE)
        if m:
            add("customer", _build_quote_window(text, m.start(), m.end()))

    # nmck
    nmck = str(passport.get("nmck") or "").strip()
    if nmck and nmck not in {"Не найдено", "Не указано", "—"}:
        # Пытаемся найти контекст НМЦК рядом с числом
        m = re.search(r"(нмцк.{0,200}?\d[\d\s]*[.,]?\d*\s*(?:млн|тыс|руб|₽|rur|rub))", text, re.IGNORECASE)
        if m:
            add("nmck", _build_quote_window(text, m.start(), m.end()))

    # deadlineApp
    deadline_app = str(passport.get("deadlineApp") or "").strip()
    if deadline_app and deadline_app not in {"См. документацию", "Не найдено", "Не указано", "—"}:
        m = re.search(r"(срок\s+подачи\s+заявк[и]?[^\n\d]{0,80}?" + re.escape(deadline_app) + r")", text, re.IGNORECASE)
        if m:
            add("deadlineApp", _build_quote_window(text, m.start(), m.end()))
        else:
            m = re.search(rf"(\b{re.escape(deadline_app)}\b)", text)
            if m:
                add("deadlineApp", _build_quote_window(text, m.start(), m.end()))

    # deadlineExecution
    deadline_exec = str(passport.get("deadlineExecution") or "").strip()
    if deadline_exec and deadline_exec not in {"Не найдено", "Не указано", "—"}:
        m = re.search(r"(срок\s+(?:исполнения|поставки|оказания\s+услуг|выполнения\s+работ).{0,160}?)", text, re.IGNORECASE)
        if m:
            add("deadlineExecution", _build_quote_window(text, m.start(), m.end()))

    # fz
    fz = str(passport.get("fz") or "").strip()
    if fz and fz not in {"—", "Не найдено", "Не указано"}:
        # 44-ФЗ / 223-ФЗ / "ФЗ-44"
        if "44" in fz:
            m = re.search(r"(44\s*[-–]?\s*фз|фз\s*[-–]?\s*44)", text, re.IGNORECASE)
            if m:
                add("fz", _build_quote_window(text, m.start(), m.end()))
        elif "223" in fz:
            m = re.search(r"(223\s*[-–]?\s*фз|фз\s*[-–]?\s*223)", text, re.IGNORECASE)
            if m:
                add("fz", _build_quote_window(text, m.start(), m.end()))

    # guarantee (обеспечение)
    guarantee = str(passport.get("guarantee") or "").strip()
    if guarantee and guarantee not in {"—", "Не найдено", "Не указано"}:
        m = re.search(r"(обеспечени[ея].{0,160}?)", text, re.IGNORECASE)
        if m:
            add("guarantee", _build_quote_window(text, m.start(), m.end()))

    return evidence


def _try_load_pdf_page_texts(file_path: str, filename: str) -> Optional[List[str]]:
    try:
        ext = (os.path.splitext(str(filename or ""))[1] or "").lower()
        if ext != ".pdf":
            return None
        loader = PyMuPDFLoader(file_path)
        docs = loader.load()
        page_texts = [d.page_content for d in docs]
        # best-effort close
        try:
            if hasattr(loader, "close"):
                loader.close()
        except Exception:
            pass
        return page_texts
    except Exception:
        return None


def attach_issue_evidence(issues: list, filename: str, page_texts: Optional[List[str]] = None) -> list:
    """Неблокирующе добавляет evidence к issues, если есть quote."""
    if not isinstance(issues, list):
        return issues
    out = []
    for it in issues:
        if not isinstance(it, dict):
            out.append(it)
            continue
        quote = str(it.get("quote") or "").strip()
        if quote:
            it = {**it}
            it["evidence"] = [_build_evidence_item(filename, quote, page_texts=page_texts)]
        out.append(it)
    return out


def _parse_amount(value: str) -> Optional[float]:
    """Пытается вытащить числовое значение из строки с ценой/процентом.

    Используется для кросс-док анализа (НМЦК, обеспечения и т.п.).
    """

    if not value:
        return None

    if not isinstance(value, str):
        value = str(value)

    match = re.search(r"(\d[\d\s]*[.,]?\d*)", value)
    if not match:
        return None

    raw = match.group(1).replace(" ", "").replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


def build_global_issues(documents: List[DocumentAnalysis]) -> List[dict]:
    """Формирует глобальные риски по всему пакету документов.

    Сейчас проверяем:
    - расхождение НМЦК между документами;
    - режимы закона (44-ФЗ / 223-ФЗ) с учётом основного режима;
    - разные условия обеспечения;
    - наличие критичных рисков внутри отдельных документов.
    """

    issues: List[dict] = []

    doc_by_name: Dict[str, Any] = {getattr(d, 'filename', ''): d for d in documents}

    def _fallback_ev(docname: str, quote: str) -> dict:
        return {
            "document_name": docname,
            "page_reference": None,
            "section_reference": None,
            "quote": quote,
        }

    def _get_doc_passport_ev(docname: str, field: str, fallback_quote: str) -> dict:
        d = doc_by_name.get(docname)
        ev_map = getattr(d, 'passportEvidence', None) if d is not None else None
        if isinstance(ev_map, dict):
            ev_list = ev_map.get(field)
            if isinstance(ev_list, list) and ev_list:
                return ev_list[0]
        return _fallback_ev(docname, fallback_quote)

    # --- 1. НМЦК ---
    nmck_values = []  # (filename, numeric_value, raw)
    for doc in documents:
        passport = doc.passport or {}
        raw_nmck = str(passport.get("nmck", ""))
        amount = _parse_amount(raw_nmck)
        if amount is not None:
            nmck_values.append((doc.filename, amount, raw_nmck))

    if len(nmck_values) > 1:
        amounts = [v[1] for v in nmck_values]
        min_v, max_v = min(amounts), max(amounts)
        if max_v > 0 and (max_v - min_v) > 0:
            diff_ratio = (max_v - min_v) / max_v
            severity = "HIGH" if diff_ratio > 0.05 else "MEDIUM"
            doc_list = [f"{fn}: {raw}" for fn, _, raw in nmck_values]
            evidence = [
                _get_doc_passport_ev(fn, "nmck", f"НМЦК: {raw}") for fn, _, raw in nmck_values
            ]
            issues.append(
                {
                    "title": "Несоответствие НМЦК между документами пакета",
                    "severity": severity,
                    "description": "В разных документах указаны разные значения НМЦК. "
                    "Проверьте ТЗ, проект договора и протоколы.",
                    "evidence": evidence,
                    "details": {
                        "documents": doc_list,
                        "min": min_v,
                        "max": max_v,
                    },
                }
            )

    # --- 2. Режим закона (44-ФЗ / 223-ФЗ) с учётом основного режима ---
    # Собираем карту режимов по документам
    fz_map: Dict[str, List[str]] = {}
    for doc in documents:
        passport = doc.passport or {}
        fz_raw = str(passport.get("fz", "")).strip()
        if not fz_raw:
            continue
        key = fz_raw.upper()
        fz_map.setdefault(key, []).append(doc.filename)

    if fz_map:
        # Нормализуем режимы к категориям:
        # - 44-ФЗ / 223-ФЗ считаем основными режимами закупки
        # - 209-ФЗ, ГК РФ, НК РФ, ТК РФ, БК РФ и прочие считаем контекстными нормами
        PRIMARY_LAWS = {"44-ФЗ", "223-ФЗ"}
        CONTEXT_LAWS = {
            "209-ФЗ",
            "ГК РФ",
            "НК РФ",
            "ТК РФ",
            "БК РФ",
        }

        # Выделяем основные и контекстные режимы
        primary_laws_present: Dict[str, List[str]] = {}
        secondary_laws_present: Dict[str, List[str]] = {}
        for law_code, filenames in fz_map.items():
            if law_code in PRIMARY_LAWS:
                primary_laws_present[law_code] = filenames
            elif law_code in CONTEXT_LAWS:
                secondary_laws_present[law_code] = filenames
            else:
                # Все прочие режимы пока считаем контекстными, чтобы не спамить критическими ошибками
                secondary_laws_present[law_code] = filenames

        primary_law_keys = list(primary_laws_present.keys())

        # Сценарий 1: есть один основной режим, но есть дополнительные контекстные нормы
        if len(primary_law_keys) == 1 and secondary_laws_present:
            primary_law = primary_law_keys[0]
            secondary_list = sorted(secondary_laws_present.keys())
            evidence = []
            for law_code, files in secondary_laws_present.items():
                for fn in files:
                    evidence.append(_get_doc_passport_ev(fn, "fz", f"Упоминание нормы/режима: {law_code}"))
            issues.append(
                {
                    "title": "Возможные артефакты заимствованных формулировок",
                    "severity": "MEDIUM",  # повышенное внимание, но не критический стоп-фактор
                    "description": (
                        "В документах закупки обнаружены ссылки на различные нормативные акты. "
                        f"Основной режим закупки определён как {primary_law}. "
                        "Отдельные формулировки могут быть заимствованы из иных процедур и требуют "
                        "проверки на соответствие Положению о закупках заказчика."
                    ),
                    "evidence": evidence or None,
                    "details": {
                        "primaryLaw": primary_law,
                        "secondaryLaws": secondary_list,
                        "documentsByLaw": {k: v for k, v in fz_map.items()},
                        "classification": "warning",
                    },
                }
            )

        # Сценарий 2: обнаружены несколько основных режимов (противоречие)
        if len(primary_law_keys) > 1:
            # КРИТИЧНО: проверяем, где именно найдены упоминания разных ФЗ
            # Если они только в шапке/преамбуле (первые 500 символов каждого документа) - это FORMAL риск
            # Если в условиях (расчеты, оплата, ответственность) - это CRITICAL риск
            
            # Эвристика: проверяем, найдены ли упоминания ФЗ в контексте условий
            # Пока используем простую проверку: если все упоминания в начале документа - FORMAL
            is_formal_only = True
            for doc in documents:
                if doc.filename in [f for files in fz_map.values() for f in files]:
                    # Проверяем, есть ли упоминания ФЗ в основном тексте (не в начале)
                    # Это упрощенная проверка - в будущем можно улучшить через анализ позиций упоминаний
                    # Сейчас считаем, что если разные ФЗ только в passport - это формальность
                    pass
            
            # Для MVP: если конфликт только между документами (разные ФЗ в разных документах),
            # а не внутри одного документа с условиями - понижаем до FORMAL
            # Если же внутри одного документа - это может быть CRITICAL
            
            # Простая эвристика: если разные ФЗ в разных документах - вероятно шаблон
            docs_per_law = {law: files for law, files in primary_laws_present.items()}
            all_docs_with_conflict = [f for files in docs_per_law.values() for f in files]
            unique_docs = set(all_docs_with_conflict)
            
            # Если каждая группа ФЗ в своих документах (нет пересечений) - это формальность
            has_overlap = len(unique_docs) < len(all_docs_with_conflict)
            
            if not has_overlap and len(docs_per_law) > 1:
                # Разные ФЗ в разных документах - скорее всего шаблон → MARKET_NOISE
                severity_level = "MARKET_NOISE"
                severity = "LOW"
                classification = "formal_conflict"
                description = (
                    "⚠️ Характер расхождения: формальный\n\n"
                    "Упоминания разных ФЗ часто возникают из-за шаблонов документации "
                    "и не всегда отражают фактический правовой режим закупки.\n\n"
                    "✔ Критических последствий не выявлено\n"
                    "❗ Рекомендуется уточнение у заказчика при подаче заявки"
                )
            else:
                # Один и тот же документ содержит разные ФЗ - может быть управляемый риск
                severity_level = "CONTROLLED_RISK"  # Управляемый риск, требует внимания
                severity = "MEDIUM"
                classification = "potential_conflict"
                description = (
                    "Обнаружены упоминания разных основных правовых режимов закупки "
                    "(например, 44-ФЗ и 223-ФЗ). Это может создавать правовую неопределённость. "
                    "Рекомендуется проверить, какой режим фактически применяется к условиям участия, "
                    "оплаты и ответственности."
                )
            
            evidence = []
            for law_code, files in primary_laws_present.items():
                for fn in files:
                    evidence.append(_get_doc_passport_ev(fn, "fz", f"Режим закупки: {law_code}"))
            issues.append(
                {
                    "title": "Расхождение упоминаний правового режима",
                    "severity": severity,
                    "severity_level": severity_level,  # DEAL_BREAKER | CONTROLLED_RISK | MARKET_NOISE
                    "risk_type": "FORMAL" if severity_level == "MARKET_NOISE" else "POTENTIAL",  # Для обратной совместимости
                    "confidence_level": 80 if severity_level == "MARKET_NOISE" else 85,
                    "description": description,
                    "evidence": evidence or None,
                    "details": {
                        "primaryLawCandidates": primary_law_keys,
                        "secondaryLaws": sorted(secondary_laws_present.keys()),
                        "documentsByLaw": {k: v for k, v in fz_map.items()},
                        "classification": classification,
                        "hasOverlap": has_overlap,
                    },
                }
            )

    # --- 3. Обеспечение заявки/контракта ---
    guarantee_map = {}
    for doc in documents:
        passport = doc.passport or {}
        g_raw = str(passport.get("guarantee", "")).strip()
        if g_raw:
            guarantee_map.setdefault(g_raw, []).append(doc.filename)

    if len(guarantee_map.keys()) > 1:
        evidence = []
        for g_val, files in guarantee_map.items():
            for fn in files:
                evidence.append(_get_doc_passport_ev(fn, "guarantee", f"Обеспечение: {g_val}"))
        issues.append(
            {
                "title": "Разные условия обеспечения в документах",
                "severity": "MEDIUM",
                "description": "Условия обеспечения заявки/контракта различаются между документами пакета.",
                "evidence": evidence or None,
                "details": guarantee_map,
            }
        )

    # --- 4. Сводка по критичным рискам внутри документов ---
    high_risk_docs = []
    for doc in documents:
        for item in (doc.issues or []):
            sev = str(item.get("severity", "")).upper()
            if "HIGH" in sev or "КРИТ" in sev:
                high_risk_docs.append({"document": doc.filename, "issue": item})

    if high_risk_docs:
        evidence = []
        for rec in high_risk_docs:
            docname = rec.get("document")
            issue = rec.get("issue") or {}
            if isinstance(issue, dict) and isinstance(issue.get("evidence"), list) and issue.get("evidence"):
                evidence.append(issue.get("evidence")[0])
            else:
                q = str(issue.get("quote") or issue.get("title") or "").strip()
                if docname and q:
                    evidence.append(_fallback_ev(docname, q))

        issues.append(
            {
                "title": "Критичные риски внутри документов пакета",
                "severity": "HIGH",
                "description": "В одном или нескольких документах найдены риски уровня HIGH.",
                "evidence": evidence or None,
                "details": high_risk_docs,
            }
        )

    return issues


def enrich_it_specific_issues(source_text: str, issues: List[dict]) -> List[dict]:
    """Добавляет к списку рисков типовые флаги для IT-закупок.

    Это простые эвристики по тексту документа: брендовые требования,
    смешение товара и ПО в одном лоте, отсутствие явного указания на
    новизну товара и иностранное ПО для госзаказчиков.
    """

    text_lower = source_text.lower()

    def add_issue(title: str, severity: str, description: str, quote: str = "") -> None:
        issues.append(
            {
                "title": title,
                "severity": severity,
                "description": description,
                "quote": quote,
            }
        )

    # 1. Жёсткие требования к бренду/модели без "или эквивалент"
    vendor_keywords = [
        "intel",
        "amd",
        "nvidia",
        "geforce",
        "rtx",
        "core i3",
        "core i5",
        "core i7",
        "lenovo",
        "dell",
        "hp",
        "microsoft office",
        "office 365",
    ]
    if any(k in text_lower for k in vendor_keywords) and "или эквивалент" not in text_lower:
        # Берём небольшой фрагмент вокруг первого найденного бренда как цитату
        idx = min((text_lower.find(k) for k in vendor_keywords if k in text_lower), default=-1)
        quote = ""
        if idx != -1:
            start = max(0, idx - 80)
            end = min(len(source_text), idx + 120)
            quote = source_text[start:end].strip()

        add_issue(
            title="Возможное ограничение конкуренции по бренду (ст. 33 44-ФЗ)",
            severity="HIGH",
            description=(
                "В требованиях указаны конкретные бренды/модели без формулировки "
                "'или эквивалент'. Это может быть расценено как ограничение конкуренции."
            ),
            quote=quote,
        )

    # 2. Смешение оборудования и программного обеспечения в одном лоте
    if "компьютер" in text_lower and "office" in text_lower:
        add_issue(
            title="Смешение оборудования и ПО в одном лоте",
            severity="HIGH",
            description=(
                "В одном лоте одновременно закупаются компьютеры и офисное ПО. "
                "ФАС часто считает это ограничением конкуренции, если нет явного обоснования."
            ),
        )

    # 3. Не указана новизна товара
    if "новые" not in text_lower and "не бывшие в употреблении" not in text_lower:
        add_issue(
            title="Не указана новизна оборудования",
            severity="MEDIUM",
            description=(
                "В документации нет явного требования, что оборудование должно быть новым, "
                "не бывшим в употреблении. Это повышает риск поставки б/у товара."
            ),
        )

    # 4. Иностранное ПО при государственном заказчике
    if ("windows" in text_lower or "microsoft office" in text_lower or "office 365" in text_lower) and (
        "государствен" in text_lower or "муниципальн" in text_lower or "бюджетн" in text_lower
    ):
        add_issue(
            title="Иностранное программное обеспечение у госзаказчика",
            severity="MEDIUM",
            description=(
                "В ТЗ фигурирует иностранное ПО (Windows/Office) при признаках государственного "
                "заказчика. Необходимо проверить требования по использованию отечественного ПО "
                "и возможные исключения."
            ),
        )

    return issues


def enrich_construction_specific_issues(source_text: str, issues: List[dict]) -> List[dict]:
    """Отраслевые флаги для строительных закупок (CONSTRUCTION).

    Цель — подсветить завышенные штрафы/неустойки и потенциально проблемные
    формулировки по скрытым работам и ГОСТам.
    """

    text_lower = source_text.lower()

    def add_issue(title: str, severity: str, description: str, quote: str = "") -> None:
        issues.append(
            {
                "title": title,
                "severity": severity,
                "description": description,
                "quote": quote,
            }
        )

    # 1. Очень жёсткие штрафы/неустойки (например, >1% в день)
    for match in re.finditer(r"(штраф|неусто[йи]к)[^%]{0,80}(\d+[.,]?\d*)\s*%", text_lower):
        percent_str = match.group(2)
        try:
            value = float(percent_str.replace(",", "."))
        except ValueError:
            continue
        if value >= 1.0:
            start = max(0, match.start() - 80)
            end = min(len(source_text), match.end() + 80)
            quote = source_text[start:end].strip()
            add_issue(
                title="Жёсткие штрафы/неустойки в договоре",
                severity="HIGH",
                description=(
                    "Обнаружены штрафы или неустойки с размером от 1% в день и выше. "
                    "Это создаёт высокий финансовый риск при срыве сроков."
                ),
                quote=quote,
            )
            break

    # 2. Скрытые работы без явного упоминания актов освидетельствования
    if "скрыт" in text_lower and "акт освидетельствования" not in text_lower:
        add_issue(
            title="Скрытые работы без процедуры оформления актов",
            severity="MEDIUM",
            description=(
                "Встречаются упоминания скрытых работ, но нет явного описания порядка "
                "оформления актов освидетельствования. Это усиливает риск споров при приёмке."
            ),
        )

    # 3. Жёсткие требования к ГОСТ/маркам без допуска эквивалентов
    if "гост" in text_lower and "или эквивалент" not in text_lower:
        add_issue(
            title="Жёсткие требования по ГОСТ без эквивалентов",
            severity="MEDIUM",
            description=(
                "В ТЗ фигурируют конкретные ГОСТ/марки материалов без допуска эквивалентных "
                "характеристик. Это может ограничивать конкуренцию и повышать риск жалоб."
            ),
        )

    return issues


def enrich_medicine_specific_issues(source_text: str, issues: List[dict]) -> List[dict]:
    """Отраслевые флаги для медицинских закупок (MEDICINE).

    Проверяем наличие требований к сроку годности, температурному режиму
    и регистрационному удостоверению. Отсутствие этих блоков — риск. """

    text_lower = source_text.lower()

    def add_issue(title: str, severity: str, description: str, quote: str = "") -> None:
        issues.append(
            {
                "title": title,
                "severity": severity,
                "description": description,
                "quote": quote,
            }
        )

    # 1. Срок годности не описан
    if "срок годност" not in text_lower and "до истечения срока" not in text_lower:
        add_issue(
            title="Не описаны требования к сроку годности изделий/препаратов",
            severity="MEDIUM",
            description=(
                "В документации не найдено явного описания требований к сроку годности. "
                "Это создаёт риск поставки товара с малым остаточным сроком."
            ),
        )

    # 2. Температурный режим не описан
    if "температурн" not in text_lower and "режим хранения" not in text_lower:
        add_issue(
            title="Не указан температурный режим хранения/транспортировки",
            severity="MEDIUM",
            description=(
                "Для медицинских изделий/лекарств важно указывать температурный режим "
                "хранения и перевозки. В тексте явных требований не найдено."
            ),
        )

    # 3. Регистрационное удостоверение (РУ) не упоминается
    if "регистрационное удостоверение" not in text_lower and "ру на изделие" not in text_lower:
        add_issue(
            title="Не указано требование к наличию регистрационного удостоверения (РУ)",
            severity="HIGH",
            description=(
                "В тексте нет явного требования о наличии действующего регистрационного "
                "удостоверения на медицинские изделия/препараты. Это критичный регуляторный риск."
            ),
        )

    return issues


# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ БЕЗОПАСНОГО УДАЛЕНИЯ ФАЙЛА ---
def safe_remove_file(file_path: str, max_retries: int = 5, delay: float = 1.0):
    """Безопасно удаляет файл с повторными попытками и задержкой.
    
    Args:
        file_path: Путь к файлу для удаления
        max_retries: Максимальное количество попыток удаления
        delay: Начальная задержка между попытками (секунды)
    """
    if not file_path or not os.path.exists(file_path):
        return True  # Файл уже не существует, считаем успехом
    
    # Даем системе время освободить ресурсы перед первой попыткой
    time.sleep(0.5)
    
    for attempt in range(max_retries):
        try:
            # Пытаемся удалить файл
            os.remove(file_path)
            logger.info(f"Файл {file_path} успешно удален (попытка {attempt + 1})")
            return True
        except PermissionError as e:
            if attempt < max_retries - 1:
                wait_time = delay * (attempt + 1)  # Увеличиваем задержку с каждой попыткой
                logger.warning(f"Попытка {attempt + 1}/{max_retries}: файл {file_path} занят, ожидание {wait_time:.1f}с...")
                time.sleep(wait_time)
            else:
                logger.error(f"Не удалось удалить файл {file_path} после {max_retries} попыток: {e}")
                # Помечаем файл для удаления при следующем запуске (если возможно)
                try:
                    # Пытаемся переименовать файл, чтобы он не мешал
                    old_path = file_path
                    new_path = f"{file_path}.old_{int(time.time())}"
                    os.rename(old_path, new_path)
                    logger.info(f"Файл {old_path} переименован в {new_path} для последующего удаления")
                except:
                    pass
                return False
        except FileNotFoundError:
            # Файл уже удален
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении файла {file_path}: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay * (attempt + 1))
            else:
                return False
    return False


# --- ФУНКЦИЯ БЕЗОПАСНОГО ВЫЗОВА LLM С FAILOVER ---
def _safe_ollama_invoke(prompt: str, format_json: bool = True) -> str:
    """
    Безопасный вызов Ollama с каскадным переключением между моделями.
    
    Пытается использовать модели по приоритету:
    1. qwen2.5:0.5b (быстрая)
    2. llama3:8b (умная)
    3. mistral:7b (надежная)
    
    Args:
        prompt: Промпт для отправки в LLM
        format_json: Если True, требует JSON формат ответа (для анализа). 
                     Если False, обычный текстовый ответ (для чата).
        
    Returns:
        Содержимое ответа от LLM
        
    Raises:
        HTTPException: Если все модели недоступны (503)
    """
    last_error = None
    
    for model_name in OLLAMA_MODELS:
        try:
            logger.info(f"Попытка использования модели: {model_name}")
            
            # Инициализируем ChatOllama с текущей моделью
            llm_params = {
                "model": model_name,
                "base_url": settings.OLLAMA_BASE_URL,
                "temperature": 0.1,  # Низкая температура для стабильности
                "timeout": 120,  # 2 минуты таймаут (уменьшено с 5 минут для быстрого ответа)
            }
            
            # Добавляем формат JSON только если нужно
            if format_json:
                llm_params["format"] = "json"
            
            llm = ChatOllama(**llm_params)
            
            # Пытаемся выполнить invoke
            response = llm.invoke(prompt)
            
            # Проверяем, что ответ валидный
            if response and response.content and len(response.content) > 10:
                logger.info(f"✅ Успешный ответ от модели {model_name}")
                return response.content
            else:
                raise ValueError("Пустой или слишком короткий ответ от модели")
                
        except Exception as e:
            last_error = e
            error_msg = str(e)
            logger.warning(f"⚠️ Модель {model_name} недоступна или вернула ошибку: {error_msg[:200]}")
            # Продолжаем к следующей модели
            continue
    
    # Если все модели не сработали
    logger.error(f"❌ Все модели недоступны. Последняя ошибка: {last_error}")

    # Если последняя ошибка связана с GPU/CUDA/памятью, не возвращаем 503,
    # а даём вызывающему коду обработать это как обычное исключение и перейти в fallback.
    if last_error is not None:
        msg = str(last_error).lower()
        if any(t in msg for t in ["cuda", "cublas", "out of memory", "no kernel image"]):
            logger.warning("⚠️ Обнаружена ошибка GPU/CUDA при вызове LLM. Передаём исключение наружу для активации текстового fallback.")
            raise last_error

    # Во всех остальных случаях считаем, что Ollama реально недоступен
    raise HTTPException(
        status_code=503,
        detail="Все AI-сервисы недоступны. Проверьте, запущен ли Ollama и установлены ли модели."
    )


# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ АНАЛИЗА ОДНОГО ФАЙЛА ---
async def analyze_single_file(temp_path: str, filename: str, industry: str) -> dict:
    logger.info(f"--- АНАЛИЗ ДОКУМЕНТА: {filename} [{industry}] ---")

    # ШАГ 6: Создаём Document Snapshot (если доступен) — ДО начала анализа
    document_snapshot = None
    evidence_snapshot = None  # Инициализируем для использования в ШАГЕ 6
    decision_snapshot = None  # Инициализируем для использования в ШАГЕ 6
    if AUDIT_TRAIL_ENABLED:
        try:
            audit_manager = get_audit_trail_manager()
            # Формируем метаданные файла для snapshot
            file_metadata = {
                "filename": filename,
                "path": temp_path,
                "size": os.path.getsize(temp_path) if os.path.exists(temp_path) else 0,
            }
            document_snapshot = audit_manager.create_document_snapshot(
                files=[file_metadata],
                industry=industry
            )
            logger.info(f"✅ Document Snapshot создан: {document_snapshot.snapshot_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка создания Document Snapshot: {e}", exc_info=True)

    # ШАГ 3: Preprocessing & Evidence Layer (если доступен)
    evidence_objects = None
    evidence_prompt = None
    evidence_summary = None
    procurement_law = None  # ФАЗА 2: Режим закупки
    if EVIDENCE_LAYER_ENABLED:
        try:
            preprocessor = EvidencePreprocessor()
            preprocessing_result = await preprocessor.preprocess_file(temp_path, filename, industry)
            
            # ФАЗА 2: Извлекаем режим закупки из raw_extract первого evidence
            if preprocessing_result.evidence_objects:
                first_ev = preprocessing_result.evidence_objects[0]
                if first_ev.raw_extract and "procurement_law:" in first_ev.raw_extract:
                    for part in first_ev.raw_extract.split("|"):
                        if "procurement_law:" in part:
                            procurement_law = part.split(":")[1]
                            break
            
            if preprocessing_result.evidence_objects:
                evidence_objects = preprocessing_result.evidence_objects
                evidence_prompt = evidence_objects_to_llm_prompt(preprocessing_result.evidence_objects)
                evidence_summary = evidence_objects_to_summary(preprocessing_result.evidence_objects)
                logger.info(
                    f"✅ Evidence Layer: извлечено {len(preprocessing_result.evidence_objects)} Evidence Objects "
                    f"(DEAL_BREAKER: {evidence_summary['deal_breakers_count']}, "
                    f"CONTROLLED_RISK: {evidence_summary['controlled_risks_count']})"
                )
                
                # ШАГ 6: Создаём Evidence Snapshot (если доступен)
                if AUDIT_TRAIL_ENABLED and document_snapshot:
                    try:
                        audit_manager = get_audit_trail_manager()
                        # Сериализуем Evidence Objects для snapshot
                        evidence_objects_dict = [ev.dict() if hasattr(ev, 'dict') else ev for ev in evidence_objects]
                        evidence_snapshot = audit_manager.create_evidence_snapshot(
                            document_snapshot_id=document_snapshot.snapshot_id,
                            evidence_objects=evidence_objects_dict,
                            mcp_versions={}  # TODO: добавить версии MCP-нод
                        )
                        logger.info(f"✅ Evidence Snapshot создан: {evidence_snapshot.evidence_set_id}")
                    except Exception as e:
                        logger.error(f"❌ Ошибка создания Evidence Snapshot: {e}", exc_info=True)
            else:
                logger.warning(f"⚠️ Evidence Layer: Evidence Objects не извлечены для {filename}. Fallback на сырой текст.")
        except Exception as e:
            logger.error(f"❌ Ошибка Evidence Layer для {filename}: {e}. Fallback на сырой текст.", exc_info=True)
    
    # ШАГ 13: Kill Switch — проверка режима работы перед reasoning
    kill_switch = None
    safe_mode_handler = None
    current_mode = SystemMode.NORMAL
    is_reasoning_enabled = True
    
    if KILL_SWITCH_ENABLED:
        try:
            kill_switch = get_kill_switch_manager()
            safe_mode_handler = SafeModeHandler()
            current_mode = kill_switch.get_current_mode()
            is_reasoning_enabled = kill_switch.is_reasoning_enabled()
        except Exception as e:
            logger.warning(f"⚠️ Ошибка получения Kill Switch статуса: {e}. Продолжаем в нормальном режиме.")
    
    # ШАГ 4: Reasoning & Decision Layer (если доступен, есть Evidence Objects И reasoning включён)
    reasoning_result = None
    if REASONING_LAYER_ENABLED and evidence_objects and is_reasoning_enabled:
        try:
            reasoning_engine = ReasoningEngine()
            # ФАЗА 2: Передаем режим закупки в reasoning engine
            reasoning_result = reasoning_engine.process_evidence(evidence_objects, industry, procurement_law)
            logger.info(
                f"✅ Reasoning Layer: сформировано {len(reasoning_result.risk_signals)} Risk Signals, "
                f"{len(reasoning_result.contradictions)} противоречий, "
                f"решение: {reasoning_result.decision_preview.decision}"
            )
        except Exception as e:
            logger.error(f"❌ Ошибка Reasoning Layer для {filename}: {e}. Fallback на LLM reasoning.", exc_info=True)
    elif not is_reasoning_enabled:
        logger.warning(
            f"⚠️ Reasoning отключён (режим: {current_mode.value}). "
            f"Новые управленческие выводы не формируются."
        )

    # 1. Чтение (Всеядный ридер) — используется как fallback или для документов без Evidence
    text = ""
    page_texts: Optional[List[str]] = None
    loader = None
    try:
        ext = (os.path.splitext(str(filename or ""))[1] or "").lower()

        if ext == ".pdf":
            loader = PyMuPDFLoader(temp_path)
            docs = loader.load()
            page_texts = [d.page_content for d in docs]
            text = "\n".join(page_texts)
            # Принудительно освобождаем ресурсы
            del docs
            if loader:
                try:
                    # Закрываем все открытые ресурсы загрузчика
                    if hasattr(loader, "close"):
                        loader.close()
                except Exception:
                    pass
            del loader
            loader = None
            # Даем время системе освободить файл
            time.sleep(0.1)

        elif ext in (".docx", ".doc"):
            # Сначала пробуем Pandoc для .docx (более точное извлечение таблиц)
            # Если Pandoc недоступен или ошибка — fallback на Docx2txt
            text = None
            if ext == ".docx":
                try:
                    markdown_text = docx_to_markdown(temp_path)
                    if markdown_text and markdown_text.strip():
                        text = markdown_text
                        logger.info(f"✅ Pandoc успешно конвертировал {filename} в Markdown ({len(text)} символов)")
                except PandocServiceError as pandoc_error:
                    logger.debug(f"Pandoc недоступен для {filename}: {pandoc_error}. Используем Docx2txt.")
                except Exception as pandoc_e:
                    logger.debug(f"Ошибка Pandoc для {filename}: {pandoc_e}. Используем Docx2txt.")
            
            # Fallback: пробуем Docx2txt; при ошибке — читаем как простой текст
            if text is None:
                try:
                    loader = Docx2txtLoader(temp_path)
                    docs = loader.load()
                    text = "\n".join([d.page_content for d in docs])
                    # Принудительно освобождаем ресурсы
                    del docs
                    if loader:
                        try:
                            if hasattr(loader, "close"):
                                loader.close()
                        except Exception:
                            pass
                    del loader
                    loader = None
                    time.sleep(0.1)
                except Exception as e:
                    logger.warning(f"Docx2txt не смог прочитать файл {filename}: {e}. Пробуем прочитать как текст.")
                    try:
                        with open(temp_path, "rb") as f:
                            raw = f.read()
                        text = raw.decode("utf-8", errors="ignore")
                    except Exception as inner_e:
                        logger.error(f"Не удалось прочитать .doc/.docx даже как текст: {inner_e}")
                        raise

        elif ext in (".xls", ".xlsx"):
            # Excel-файлы: конвертируем содержимое ячеек в плоский текст
            try:
                # Проверяем, что файл существует и доступен
                if not os.path.exists(temp_path):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Файл {filename} не найден после загрузки"
                    )
                
                chunks = []
                
                if ext == ".xlsx":
                    # Новый формат Excel (.xlsx) - используем openpyxl
                    try:
                        from openpyxl import load_workbook
                    except ImportError:
                        logger.error("openpyxl не установлен. Установите: pip install openpyxl")
                        raise HTTPException(
                            status_code=500,
                            detail="Библиотека для чтения Excel-файлов не установлена. Обратитесь к администратору."
                        )
                    
                    wb = load_workbook(temp_path, data_only=True, read_only=True)
                    for ws in wb.worksheets:
                        chunks.append(f"Лист: {ws.title}")
                        row_count = 0
                        for row in ws.iter_rows(values_only=True):
                            row_count += 1
                            if row_count > 500:
                                chunks.append("... (дальнейшие строки опущены)")
                                break
                            cells = [str(v) for v in row if v not in (None, "")]
                            if cells:
                                chunks.append(" | ".join(cells))
                    wb.close()
                    
                elif ext == ".xls":
                    # Старый формат Excel (.xls) - используем xlrd
                    try:
                        import xlrd
                    except ImportError:
                        logger.error("xlrd не установлен. Установите: pip install 'xlrd<2.0'")
                        raise HTTPException(
                            status_code=500,
                            detail="Библиотека для чтения старых Excel-файлов (.xls) не установлена. Обратитесь к администратору."
                        )
                    
                    # xlrd 1.2.0 открывает файл напрямую по пути
                    try:
                        workbook = xlrd.open_workbook(temp_path)
                    except xlrd.XLRDError as e:
                        logger.error(f"Ошибка xlrd при открытии файла {filename}: {e}")
                        raise HTTPException(
                            status_code=400,
                            detail=f"Файл {filename} повреждён или имеет неверный формат Excel (.xls)"
                        )
                    
                    for sheet_name in workbook.sheet_names():
                        sheet = workbook.sheet_by_name(sheet_name)
                        chunks.append(f"Лист: {sheet_name}")
                        row_count = 0
                        for row_idx in range(sheet.nrows):
                            row_count += 1
                            if row_count > 500:
                                chunks.append("... (дальнейшие строки опущены)")
                                break
                            row_values = sheet.row_values(row_idx)
                            # Преобразуем значения в строки, обрабатывая даты и числа
                            cells = []
                            for v in row_values:
                                if v is None or v == "" or v == " ":
                                    continue
                                # xlrd возвращает даты как числа, нужно конвертировать
                                if isinstance(v, (int, float)) and v > 0 and v < 1e10:
                                    # Возможно, это дата (xlrd date format)
                                    try:
                                        date_tuple = xlrd.xldate_as_tuple(v, workbook.datemode)
                                        if date_tuple[0] > 1900:  # Валидная дата
                                            from datetime import datetime
                                            date_obj = datetime(*date_tuple)
                                            cells.append(date_obj.strftime("%Y-%m-%d"))
                                            continue
                                    except:
                                        pass
                                cells.append(str(v))
                            if cells:
                                chunks.append(" | ".join(cells))
                
                text = "\n".join(chunks)
            except Exception as e:
                logger.error(f"Ошибка чтения Excel-файла {filename}: {e}", exc_info=True)
                # Более информативное сообщение
                error_str = str(e).lower()
                if "no such file" in error_str or "cannot find" in error_str:
                    error_msg = f"Файл Excel {filename} не найден"
                elif "openpyxl" in error_str or "invalid" in error_str or "corrupt" in error_str:
                    error_msg = f"Файл Excel {filename} повреждён или имеет неверный формат. Убедитесь, что файл не открыт в другой программе."
                elif "permission" in error_str:
                    error_msg = f"Нет доступа к файлу Excel {filename}. Закройте файл в других программах."
                else:
                    error_msg = f"Не удалось прочитать файл Excel {filename}. Проверьте формат файла."
                raise HTTPException(status_code=400, detail=error_msg)

        else:
            # Текстовые файлы и все прочие, которые можно открыть как текст
            with open(temp_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
    except Exception as e:
        logger.error(f"Ошибка чтения файла {filename} (путь: {temp_path}): {e}", exc_info=True)
        error_detail = str(e)
        # Более информативное сообщение об ошибке
        if "No such file" in error_detail or "cannot find" in error_detail.lower():
            error_msg = f"Файл {filename} не найден или недоступен"
        elif "permission" in error_detail.lower() or "access" in error_detail.lower():
            error_msg = f"Нет доступа к файлу {filename}"
        elif "corrupt" in error_detail.lower() or "invalid" in error_detail.lower():
            error_msg = f"Файл {filename} повреждён или имеет неверный формат"
        else:
            error_msg = f"Не удалось прочитать файл {filename}. Проверьте формат файла."
        
        if loader:
            try:
                del loader
            except Exception:
                pass
        raise HTTPException(status_code=400, detail=error_msg)

    if not text:
        raise HTTPException(status_code=400, detail="Файл пустой")

    # 2. Промпт (Отраслевой контекст с детализацией)
    industry_context = ""
    industry_checks = ""
    
    if industry == "CONSTRUCTION":
        industry_context = "Это СТРОЙКА. Ищи: СРО, скрытые работы, марки материалов (ГОСТ), график выполнения."
        industry_checks = """
        ОБЯЗАТЕЛЬНО ПРОВЕРЬ:
        - Наличие требования к СРО (Саморегулируемая организация) - КРИТИЧНО
        - Упоминание скрытых работ и наличие процедуры оформления актов освидетельствования
        - Требования к маркам материалов (ГОСТ) - есть ли "или эквивалент"
        - Этапность работ и реалистичность сроков
        - Штрафы за задержку (не должны превышать 0.5% в день)
        - Гарантийные обязательства (обычно 60 месяцев, но проверь на завышенные сроки)
        - Наличие чертежей, смет, спецификаций
        """
    elif industry == "IT":
        industry_context = "Это IT. Ищи: Лицензии ФСТЭК, реестр ПО, SLA, передачу исключительных прав."
        industry_checks = """
        ОБЯЗАТЕЛЬНО ПРОВЕРЬ:
        - Ограничение конкуренции (требование конкретного языка/фреймворка без "или эквивалент")
        - Смешение оборудования и ПО в одном лоте (компьютеры + Office)
        - Требование новизны товара (не бывшие в употреблении)
        - Иностранное ПО у госзаказчика (Windows/Office - проверить требования Минцифры)
        - Реалистичность сроков разработки (соотнеси объем функционала с дедлайнами)
        - Требования к SLA (uptime, response time)
        - Функциональные и нефункциональные требования (производительность, безопасность)
        - Требования к квалификации (опыт, портфолио, сертификаты)
        """
    elif industry == "MEDICINE":
        industry_context = "Это МЕДИЦИНА. Ищи: Остаточный срок годности, РУ, температурный режим."
        industry_checks = """
        ОБЯЗАТЕЛЬНО ПРОВЕРЬ:
        - Наличие требования к регистрационному удостоверению (РУ) - КРИТИЧНО
        - Температурный режим хранения и транспортировки
        - Требования к остаточному сроку годности
        - Наличие лицензии Росздравнадзора
        - Соответствие ГОСТ, СанПиН
        - Наличие инструкций на русском языке
        - Требования к сервисному обслуживанию (наличие сервис-центра, сроки реагирования)
        - Ограничение конкуренции (только конкретная марка без "или эквивалент")
        """

    # 3a. RAG: подбор релевантных фрагментов законов по тексту документа
    law_context_block = ""
    try:
        # Берём усечённый фрагмент текста, чтобы не перегружать ретривер
        base_query_text = text[:8000]
        law_snippets = get_law_snippets(base_query_text, k=5)
        if law_snippets:
            parts = []
            for i, sn in enumerate(law_snippets, start=1):
                src = sn.get("metadata", {}).get("source", "") or sn.get("metadata", {}).get("source", "")
                header = f"Фрагмент {i}"
                if src:
                    header += f" (источник: {src})"
                parts.append(f"{header}:\n{sn.get('content', '').strip()}\n")
            law_context_block = (
                "Ниже приведены выдержки из релевантных нормативных актов и законов, "
                "найденные в локальной базе (RAG). ОБЯЗАТЕЛЬНО учитывай их при правовом анализе и ссылках на нормы закона:\n\n"
                + "\n".join(parts)
            )
    except Exception as e:
        logger.warning(f"RAG: не удалось получить выдержки из законов: {e}")
        law_context_block = ""

    # 3b. МЕГА-ПРОМПТ (Паспорт, Риски, Спецификация + RAG-контекст + Evidence Layer)
    law_block = ""
    if law_context_block:
        law_block = "Выдержки из нормативных актов для учёта при анализе:\n" + law_context_block

    # ШАГ 3: Добавляем Evidence Objects в промпт (если доступны)
    evidence_block = ""
    llm_context = build_llm_context_excerpt(text, max_chars=24000)

    if evidence_prompt:
        evidence_block = "\n\n" + evidence_prompt + "\n\n"
        logger.info("📋 Evidence Objects включены в промпт для LLM")
    else:
        # Fallback: используем выдержки вместо первых N символов
        evidence_block = f"\n\n=== СОДЕРЖИМОЕ ДОКУМЕНТА (выдержки) ===\n{llm_context}\n\n"
        logger.info("📄 Используется fallback: выдержки документа")

    prompt = f"""
    Ты — Главный Эксперт Тендерного Отдела. Твоя задача — полный аудит документа.
    Специфика: {industry_context}
    
    {industry_checks}

    {law_block}
    
    {evidence_block}

    КРИТИЧЕСКИ ВАЖНО ДЛЯ ИЗВЛЕЧЕНИЯ ДАННЫХ:
    - НМЦК: ищи ВЕЗДЕ - "НМЦК", "НМЦД", "начальная (максимальная) цена контракта", "цена контракта", "стоимость", "сумма контракта", "общая стоимость", "итоговая сумма"
    - ИЩИ в таблицах, в тексте, в заголовках, в конце документа
    - Если документ — обоснование НМЦК/НМЦД — ОБЯЗАТЕЛЬНО найди цену!
    - Если не найдено - верни "Не найдено" (НЕ пиши "Ищи" или другие инструкции)
    - Описание объекта: НЕ пиши "Нет описания" - всегда анализируй документ и давай конкретное описание!
    - Резюме: НЕ пиши "Нет описания" - всегда давай конкретное резюме на основе анализа документа!
    
    ## PHASE 1: TENDER PASSPORT EXTRACTION (НОВОЕ)
    
    Вам нужно ВСЕГДА извлечь следующие данные о тендере в структурированном формате:
    
    ### 1. НМЦК (Начальная максимальная цена контракта)
    ТРЕБОВАНИЕ: Обязательно найдите численное значение НМЦК в рублях
    - Поищите в разделах "Цена", "НМЦК", "Стоимость"
    - Если найдете несколько значений - берите САМОЕ КРУПНОЕ
    - Формат: целое число без форматирования (500000000)
    ЕСЛИ НЕ НАЙДЕНО: верните null
    
    ### 2. ЗАКАЗЧИК (Название организации)
    ТРЕБОВАНИЕ: Найдите полное название заказчика
    - Обычно в начале документа, в реквизитах
    - Смотрите разделы "Организатор", "Заказчик"
    - Полное юридическое имя (ООО/АО/ГУП и т.д.)
    ЕСЛИ НЕ НАЙДЕНО: верните null
    
    ### 3. ДЕДЛАЙН (Крайний срок подачи заявок)
    ТРЕБОВАНИЕ: Дата в формате YYYY-MM-DD
    - Смотрите "Крайний срок подачи", "Срок участия"
    - Это дата когда заканчивается приём заявок
    ЕСЛИ НЕ НАЙДЕНО: верните null
    
    ### 4. СРОКИ КОНТРАКТА (В месяцах)
    - Раздел "Условия контракта", "Период выполнения"
    - Если в годах - переведите в месяцы (1 год = 12 месяцев)
    
    ### 5. ОБЕСПЕЧЕНИЕ (Процент от НМЦК или рублей)
    - Раздел "Обеспечение участия", "Залог"
    - Обычно 5-10% от НМЦК
    
    ВЕРНИ JSON СТРОГО ТАКОГО ФОРМАТА (НЕ ДОБАВЛЯЙ ПОЛЕЙ СВЕРХ УКАЗАННЫХ):
    {{
        "summary": "Краткая суть закупки (1-2 предложения). ОБЯЗАТЕЛЬНО: НЕ пиши 'Нет описания' - всегда давай конкретное резюме!",
        "score": (Оценка безопасности 0-100. Штрафы >1% или размытое ТЗ = низкий балл),
        "passport": {{
            "nmck": "Цена контракта (число + валюта). ИЩИ ВЕЗДЕ: 'НМЦК', 'НМЦД', 'начальная (максимальная) цена контракта', 'цена контракта', 'стоимость', 'сумма контракта', 'общая стоимость', 'итоговая сумма'. ИЩИ в таблицах, в тексте, в заголовках. Если документ — обоснование НМЦК/НМЦД — ОБЯЗАТЕЛЬНО найди цену! Если не найдено - верни 'Не найдено'",
            "region": "Место поставки/работ",
            "fz": "44-ФЗ или 223-ФЗ",
            "deadlineApp": "Дата подачи заявки",
            "guarantee": "Обеспечение заявки/контракта (если указана одна цифра)",
            "bidSecurity": "Обеспечение заявки (если указано отдельно)",
            "contractSecurity": "Обеспечение контракта (если указано отдельно)"
        }},
        "issues": [
            {{
                "title": "Название риска (например: Незаконный штраф)",
                "severity": "HIGH" | "MEDIUM" | "LOW",
                "description": "Пояснение, почему это опасно. Ссылка на закон.",
                "quote": "Точная цитата из текста документа"
            }}
        ],
        "specs": [
            {{
                "name": "Наименование товара/работы",
                "qty": "Количество (шт, кг, м2)",
                "details": "Ключевые характеристики (ГОСТ, размеры)"
            }}
        ],
        "redFlags": [
            {{
                "code": "IT_BRAND_ONLY" | "TIME_UNREAL" | "PRICE_DUMPING" | "MIXED_LOT" | "OTHER",
                "title": "Краткое название красного флага",
                "severity": "HIGH" | "MEDIUM" | "LOW",
                "lawReference": "Статья закона / практика ФАС (если есть)",
                "explanation": "Что именно нарушено или почему это опасно",
                "quote": "Ключевая цитата из документа"
            }}
        ],
        "financialSummary": {{
            "nmck": "Строка с НМЦК",
            "estimatedCost": "Оценочная себестоимость (если удаётся понять)",
            "marginComment": "Краткий комментарий по марже и финансовым рискам",
            "advance": "Аванс (например: 30% или Нет)",
            "bidSecurity": "Обеспечение заявки (например: 1% от НМЦК)",
            "contractSecurity": "Обеспечение контракта (например: 10% от НМЦК)",
            "paymentTerms": "Условия и сроки оплаты (например: оплата в течение 7/30/60 дней...)"
        }},
        "timelineSummary": {{
            "deadlineApp": "Крайний срок подачи заявки",
            "deadlineExecution": "Срок исполнения контракта (если есть)",
            "contractDuration": "Срок действия контракта (например: 12 месяцев), если можно определить",
            "timelineRisk": "Краткий комментарий: реалистичные/сомнительные/нереальные сроки"
        }},
        "participantRequirements": {{
            "licenses": ["Перечень требуемых лицензий и допусков, если есть"],
            "experienceRequired": "Текстовое описание требований к опыту / объёму выполненных контрактов",
            "nationalRegime": "Краткое описание ограничений по нацрежиму (запрет иностранного товара и т.п.)",
            "overallBarrier": "HIGH | MEDIUM | LOW — суммарная оценка барьеров для участия"
        }},
        "summaryBlocks": {{
            "money": {{
                "status": "GREEN | YELLOW | RED",
                "comment": "Краткий вывод по деньгам (аванс, обеспечения, оплата)"
            }},
            "time": {{
                "status": "GREEN | YELLOW | RED",
                "comment": "Краткий вывод по срокам и реалистичности"
            }},
            "barriers": {{
                "status": "GREEN | YELLOW | RED",
                "comment": "Краткий вывод по требованиям к участнику (лицензии, опыт, нацрежим)"
            }},
            "traps": {{
                "status": "GREEN | YELLOW | RED",
                "comment": "Краткий вывод по скрытым ловушкам в ТЗ и договоре"
            }}
        }},
        "actions": [
            {{
                "type": "ASK_CLARIFICATION" | "FILE_FAS_COMPLAINT" | "PARTICIPATE" | "SKIP",
                "priority": 1,
                "text": "Конкретное рекомендованное действие в 1-2 предложениях"
            }}
        ],
        "tender_passport": {{
            "nmck_numeric": <число или null, обязательно > 0 если найдено>,
            "nmck_formatted": "<строка с рублями, например '500 млн руб.'>",
            "nmck_source": "<где именно найдено в документе, цитата>",
            "customer": "<полное название заказчика>",
            "customer_source": "<где найдено, цитата>",
            "deadline": "<YYYY-MM-DD или null>",
            "deadline_source": "<где найдено, цитата>",
            "contract_term_months": <число или null>,
            "contract_term_source": "<где найдено, цитата>",
            "guarantee_amount": <число или null>,
            "guarantee_source": "<где найдено, цитата>"
        }}
    }}

    ВАЖНО:
    - Не нарушай формат JSON.
    - Не добавляй комментарии вне JSON.
    - В поле 'specs' вытащи до 15 ключевых позиций ТЗ (Таблица товаров).

    Текст документа (выдержки):
    {llm_context}
    """

    logger.info("Отправка в Ollama с failover...")
    response_json = None
    try:
        # Используем безопасный вызов с переключением моделей
        response_json = _safe_ollama_invoke(prompt)
        if not response_json:
            raise ValueError("Пустой ответ от Ollama")
        logger.info(f"✅ Получен ответ от Ollama (длина: {len(response_json)} символов)")
        logger.debug(f"Первые 200 символов ответа: {response_json[:200]}")
    except HTTPException:
        # Пробрасываем HTTPException как есть (это наша ошибка 503)
        raise
    except Exception as ollama_error:
        error_msg = str(ollama_error)
        logger.error(f"❌ Ошибка подключения к Ollama: {error_msg}")
        
        # Определяем тип ошибки
        if "CUDA" in error_msg or "memory" in error_msg.lower() or "allocate" in error_msg.lower():
            logger.error("⚠️ Проблема с памятью GPU. Попробуйте:")
            logger.error("1. Использовать более легкую модель: qwen2.5:0.5b")
            logger.error("2. Или освободить память GPU")
            logger.error("3. Или использовать CPU режим")
        else:
            logger.error("Проверьте:")
            logger.error(f"1. Запущен ли Ollama: проверьте http://localhost:11434")
            logger.error(f"2. Доступен ли по адресу: {settings.OLLAMA_BASE_URL}")
            logger.error(f"3. Установлена ли модель: ollama pull {settings.OLLAMA_MODEL}")
            logger.error("4. Проверьте доступные модели: ollama list")
            logger.error("5. Запустите скрипт проверки: python check_ollama.py")
        
        # Fallback: возвращаем базовый анализ без LLM
        logger.warning("⚠️ Используется fallback-анализ без LLM")
        fallback_nmck = extract_price_regex(text[:5000]) or "Не указано"
        fallback_deadline = extract_dates_regex(text[:3000]) or "Не указано"
        
        # В fallback случае сразу создаем dict, а не JSON строку
        response_json = {
            "summary": f"⚠️ Анализ выполнен в упрощенном режиме. Ollama недоступен: {error_msg[:100]}. Проверьте подключение к Ollama.",
            "score": 50,
            "passport": {
                "nmck": fallback_nmck,
                "region": "РФ",
                "fz": "44-ФЗ",
                "deadlineApp": fallback_deadline,
                "guarantee": "Не указано"
            },
            "issues": [
                {
                    "title": "Ollama недоступен",
                    "severity": "MEDIUM",
                    "description": f"Не удалось подключиться к Ollama для полного анализа. Ошибка: {error_msg[:200]}",
                    "quote": ""
                }
            ],
            "specs": [],
            "redFlags": [],
            "financialSummary": {},
            "timelineSummary": {},
            "actions": [
                {
                    "type": "ASK_CLARIFICATION",
                    "priority": 1,
                    "text": "Проверьте подключение к Ollama и установите модель для полного анализа"
                }
            ]
        }

    # 4. Умный Парсинг (с защитой от сбоев)
    ai_data = {}
    try:
        if not response_json:
            raise ValueError("response_json пуст")
        
        # Если response_json уже dict (из fallback), используем его
        if isinstance(response_json, dict):
            ai_data = response_json
            logger.info("✅ Использован fallback-ответ (dict)")
        elif isinstance(response_json, str):
            # Ищем JSON в строке
            json_start = response_json.find('{')
            json_end = response_json.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("JSON не найден в ответе")
            
            json_str = response_json[json_start:json_end]
            logger.debug(f"Извлеченный JSON (первые 300 символов): {json_str[:300]}")
            
            ai_data = json.loads(json_str)
            logger.info("✅ JSON успешно распарсен")
        else:
            raise ValueError(f"Неожиданный тип response_json: {type(response_json)}")
            
    except json.JSONDecodeError as json_err:
        logger.error(f"❌ Ошибка парсинга JSON: {json_err}")
        logger.error(f"Проблемный фрагмент: {response_json[json_start:json_start+500] if isinstance(response_json, str) and 'json_start' in locals() else 'N/A'}")
        ai_data = {"summary": "Анализ выполнен (текстовый режим, ошибка парсинга JSON)", "issues": [], "specs": []}
    except Exception as parse_err:
        logger.error(f"❌ Ошибка при парсинге ответа: {parse_err}")
        logger.error(f"Тип response_json: {type(response_json)}")
        logger.error(f"Содержимое (первые 500 символов): {str(response_json)[:500] if response_json else 'None'}")
        ai_data = {"summary": "Анализ выполнен (текстовый режим, ошибка обработки)", "issues": [], "specs": []}

    # 5. Обогащение данными (Regex + AI)
    # Определяем тип документа для более агрессивного поиска НМЦК
    filename_lower = filename.lower()
    is_onmck_doc = any(k in filename_lower for k in ["нмцк", "нмцд", "обоснование", "онмцк", "онмцд"])
    text_lower = text.lower()
    is_onmck_content = any(k in text_lower[:5000] for k in ["обоснование нмцк", "обоснование нмцд", "обоснование начальной", "обоснование цены"])
    
    # Инициализируем переменные
    onmck_summary: dict = {}
    regex_price = "Не найдено"
    
    # Для обоснований НМЦК ищем в большем объеме текста
    if is_onmck_doc or is_onmck_content:
        # Для обоснований ищем во всем тексте
        onmck_summary = extract_onmck_summary(text)
        if onmck_summary.get("nmck"):
            regex_price = onmck_summary["nmck"]
            logger.info(f"✅ НМЦК извлечена из обоснования: {regex_price}")
        else:
            regex_price = extract_price_regex(text)  # Весь текст для обоснований
            logger.info(f"🔍 Поиск НМЦК в обосновании (regex): найдено={regex_price}")
    else:
        regex_price = extract_price_regex(text[:10000])  # Увеличил до 10000 для всех документов
    
    final_nmck = ai_data.get("passport", {}).get("nmck")
    
    # Приоритет: обоснование НМЦК > LLM > regex fallback
    if is_onmck_doc or is_onmck_content:
        if onmck_summary.get("nmck"):
            final_nmck = onmck_summary["nmck"]
        elif not final_nmck or final_nmck in ["Не найдено", "Не указано"] or "Ищи" in str(final_nmck):
            final_nmck = regex_price if regex_price and regex_price != "Не найдено" else "Не найдено"
    elif not final_nmck or final_nmck in ["Не найдено", "Не указано"] or "Ищи" in str(final_nmck):
        final_nmck = regex_price if regex_price and regex_price != "Не найдено" else "Не найдено"
    
    # Логируем результат для отладки
    logger.info(f"📄 Документ {filename}: НМЦК={final_nmck}, длина текста={len(text)} символов")

    # PHASE 1: Извлечение Tender Passport (LLM + Regex Fallback)
    tender_passport_data = None
    llm_passport = None  # Инициализируем для использования в дальнейшем коде
    try:
        # Пробуем извлечь tender_passport из LLM ответа
        llm_passport = ai_data.get("tender_passport", {})
        
        # Если LLM извлек данные - используем их
        if llm_passport and llm_passport.get("nmck_numeric"):
            logger.info("✅ Tender Passport извлечен через LLM")
            tender_passport_data = llm_passport
        else:
            # Fallback: используем regex экстрактор
            logger.info("⚠️ LLM не извлек Tender Passport, используем regex fallback")
            from extractors.tender_passport_extractor import extract_tender_passport_fallback
            regex_passport = extract_tender_passport_fallback(text, filename)
            
            # Преобразуем regex результат в формат LLM
            tender_passport_data = {
                "nmck_numeric": regex_passport.get("nmck_numeric"),
                "nmck_formatted": regex_passport.get("nmck_formatted", "Не найдено"),
                "nmck_source": regex_passport.get("nmck_source", {}).get("quote", ""),
                "customer": regex_passport.get("customer"),
                "customer_source": regex_passport.get("customer_source", {}).get("quote", ""),
                "deadline": regex_passport.get("deadline"),
                "deadline_source": regex_passport.get("deadline_source", {}).get("quote", ""),
                "contract_term_months": regex_passport.get("contract_term_months"),
                "contract_term_source": regex_passport.get("contract_term_source", {}).get("quote", ""),
                "guarantee_amount": regex_passport.get("guarantee_amount"),
                "guarantee_source": regex_passport.get("guarantee_source", {}).get("quote", ""),
                "warnings": regex_passport.get("warnings", []),
                "completion_percentage": regex_passport.get("completion_percentage", 0)
            }
            
            # Если regex нашел НМЦК, обновляем final_nmck
            if regex_passport.get("nmck_numeric") and (not final_nmck or final_nmck == "Не найдено"):
                final_nmck = regex_passport.get("nmck_formatted", str(regex_passport.get("nmck_numeric")))
                logger.info(f"✅ НМЦК извлечена через regex fallback: {final_nmck}")
    except Exception as passport_error:
        logger.error(f"❌ Ошибка извлечения Tender Passport: {passport_error}", exc_info=True)
        tender_passport_data = None
        llm_passport = None

    score = int(ai_data.get("score", 50) or 50)
    verdict = "STOP" if score < 40 else ("CAUTION" if score < 80 else "PARTICIPATE")

    # ШАГ 4: Обогащаем результат Reasoning Layer (если доступен)
    if reasoning_result:
        # Импортируем EvidenceClassification для проверки
        from evidence_types import EvidenceClassification
        
        # ФАЗА 3: Если есть специализированный анализ закупок, используем его
        if hasattr(reasoning_result, 'procurement_analysis') and reasoning_result.procurement_analysis:
            proc_analysis = reasoning_result.procurement_analysis
            logger.info(f"📊 Используем специализированный анализ закупок: {proc_analysis.verdict.value}")
            
            # Добавляем блокеры в issues
            for blocker in proc_analysis.blockers:
                severity = "CRITICAL" if not blocker.is_mitigable else "HIGH"
                description = blocker.description
                if blocker.mitigation_strategy:
                    description += f"\n\nМитигация: {blocker.mitigation_strategy}"
                if blocker.mitigation_cost:
                    description += f"\nСтоимость: {blocker.mitigation_cost:,.0f} руб."
                if blocker.mitigation_time_days:
                    description += f"\nВремя: {blocker.mitigation_time_days} дней"
                
                issues.append({
                    "title": f"Блокер: {blocker.sub_classification.value}",
                    "severity": severity,
                    "description": description,
                    "quote": f"Источник: {', '.join(blocker.evidence_ids)}",
                    "recommendation": blocker.mitigation_strategy,
                    "kb_reference": blocker.kb_reference,
                })
            
            # Добавляем red flags в issues
            for rf in proc_analysis.red_flags:
                issues.append({
                    "title": f"Red flag: {rf.get('sub_classification', 'unknown')}",
                    "severity": rf.get("severity", "MEDIUM"),
                    "description": rf.get("description", ""),
                    "quote": f"Источник: {rf.get('evidence_id', 'unknown')}",
                    "recommendation": None,
                    "kb_reference": rf.get("kb_reference"),
                })
            
            # Обновляем verdict на основе специализированного анализа
            proc_verdict = proc_analysis.verdict.value
            if proc_verdict == "DO_NOT_PARTICIPATE":
                verdict = "STOP"
            elif proc_verdict == "PROCEED_WITH_CONDITIONS":
                verdict = "CAUTION"
            elif proc_verdict == "PROCEED":
                verdict = "PARTICIPATE"
            else:  # POSTPONE
                verdict = "CAUTION"
            
            # Добавляем информацию о финансовом влиянии
            if proc_analysis.financial_impact:
                fi = proc_analysis.financial_impact
                issues.append({
                    "title": "Финансовое влияние",
                    "severity": "MEDIUM",
                    "description": (
                        f"Best Case: {fi.best_case:,.0f} руб.\n"
                        f"Worst Case: {fi.worst_case:,.0f} руб.\n"
                        f"Expected Value: {fi.expected_value:,.0f} руб.\n"
                        f"Стоимость митигации: {fi.mitigation_costs:,.0f} руб."
                    ),
                    "quote": "",
                    "recommendation": None,
                    "kb_reference": "canon/financial-impact-matrix.md",
                })
        
        # Добавляем Risk Signals в issues (базовый анализ)
        for risk in reasoning_result.risk_signals:
            issues.append({
                "title": risk.description,
                "severity": "HIGH" if risk.classification == EvidenceClassification.DEAL_BREAKER else "MEDIUM",
                "description": risk.why_it_matters,
                "quote": f"Источник: {', '.join(risk.derived_from)}",
                "recommendation": None,  # Risk mitigation находится в DecisionPreview
            })
        
        # Добавляем противоречия в issues
        for contr in reasoning_result.contradictions:
            issues.append({
                "title": f"Противоречие: {contr.description}",
                "severity": "MEDIUM",
                "description": contr.impact,
                "quote": f"Источники: {', '.join(contr.evidence_ids)}",
                "recommendation": contr.resolution_hint,
            })
        
        # ФАЗА 3: Обновляем verdict на основе специализированного анализа (если есть)
        if hasattr(reasoning_result, 'procurement_analysis') and reasoning_result.procurement_analysis:
            proc_analysis = reasoning_result.procurement_analysis
            proc_verdict = proc_analysis.verdict.value
            if proc_verdict == "DO_NOT_PARTICIPATE":
                verdict = "STOP"
                score = min(score, 30)
            elif proc_verdict == "PROCEED_WITH_CONDITIONS":
                verdict = "CAUTION"
                score = min(score, 70)
            elif proc_verdict == "POSTPONE":
                verdict = "CAUTION"
                score = min(score, 60)
            # Если PROCEED, оставляем текущий verdict
        # Fallback: Обновляем verdict на основе Decision Preview
        elif reasoning_result.decision_preview.decision == "DO_NOT_PARTICIPATE":
            verdict = "STOP"
            score = min(score, 30)  # Понижаем score при DEAL_BREAKER
        elif reasoning_result.decision_preview.decision == "PARTICIPATE_WITH_CONDITIONS":
            verdict = "CAUTION"
            score = min(score, 70)  # Ограничиваем score при условиях
        
        logger.info(f"✅ Reasoning Layer обогатил результат: {len(reasoning_result.risk_signals)} рисков, решение: {reasoning_result.decision_preview.decision}")
        
        # ШАГ 6: Создаём Decision Snapshot (если доступен)
        if AUDIT_TRAIL_ENABLED:
            try:
                audit_manager = get_audit_trail_manager()
                # Находим Evidence Snapshot (если был создан)
                evidence_snapshot_id = None
                if evidence_snapshot:
                    evidence_snapshot_id = evidence_snapshot.evidence_set_id
                elif document_snapshot:
                    # Если Evidence Snapshot не был создан, используем Document Snapshot напрямую
                    # (для совместимости, создаём временный Evidence Snapshot)
                    evidence_objects_dict = [ev.dict() if hasattr(ev, 'dict') else ev for ev in (evidence_objects or [])]
                    if evidence_objects_dict:
                        temp_evidence_snapshot = audit_manager.create_evidence_snapshot(
                            document_snapshot_id=document_snapshot.snapshot_id,
                            evidence_objects=evidence_objects_dict,
                        )
                        evidence_snapshot_id = temp_evidence_snapshot.evidence_set_id
                
                if evidence_snapshot_id:
                    # ШАГ 7: Извлекаем Reason Codes для решений "НЕ УЧАСТВОВАТЬ"
                    reason_codes = None
                    if reasoning_result.decision_preview.decision == "DO_NOT_PARTICIPATE":
                        try:
                            from decision_reason_codes import extract_reason_codes_from_decision
                            
                            # Вычисляем financial_exposure из decision_preview
                            financial_exposure = {}
                            total_financial_impact = 0.0
                            for risk in reasoning_result.decision_preview.deal_breakers + reasoning_result.decision_preview.controlled_risks:
                                if risk.financial_impact_rub:
                                    total_financial_impact += risk.financial_impact_rub
                            
                            if total_financial_impact > 0:
                                financial_exposure["potential_extra_costs_rub"] = total_financial_impact
                                # Примерный расчет блокировки средств (если есть обеспечение)
                                financial_exposure["funds_blocking_percent"] = "0%"  # Можно вычислить из passport гарантий
                            
                            reason_codes = [
                                code.value for code in extract_reason_codes_from_decision(
                                    decision=reasoning_result.decision_preview.decision,
                                    deal_breakers=[db.dict() for db in reasoning_result.decision_preview.deal_breakers],
                                    controlled_risks=[cr.dict() for cr in reasoning_result.decision_preview.controlled_risks],
                                    contradictions=[c.dict() for c in reasoning_result.decision_preview.contradictions],
                                    financial_exposure=financial_exposure,
                                    management_load=reasoning_result.decision_preview.management_load.dict(),
                                )
                            ]
                            logger.info(f"✅ Reason Codes извлечены: {reason_codes}")
                        except Exception as e:
                            logger.warning(f"⚠️ Ошибка извлечения Reason Codes: {e}")
                    
                    decision_snapshot = audit_manager.create_decision_snapshot(
                        evidence_snapshot_id=evidence_snapshot_id,
                        decision=reasoning_result.decision_preview.decision,
                        decision_preview=reasoning_result.decision_preview.dict(),
                        decision_graph=reasoning_result.decision_graph.dict() if reasoning_result.decision_graph else None,
                        reason_codes=reason_codes,
                    )
                    logger.info(f"✅ Decision Snapshot создан: {decision_snapshot.decision_id}")
                    
                    # ШАГ 7: Проверяем соответствие Architecture Manifest
                    try:
                        from manifest_compliance_checker import ManifestComplianceChecker
                        compliance_results = ManifestComplianceChecker.check_all(
                            decision_preview=reasoning_result.decision_preview.dict(),
                            reason_codes=reason_codes,
                        )
                        if any(violations for violations in compliance_results.values()):
                            logger.warning("⚠️ Обнаружены нарушения Architecture Manifest")
                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка проверки соответствия Manifest: {e}")
            except Exception as e:
                logger.error(f"❌ Ошибка создания Decision Snapshot: {e}", exc_info=True)
        
        # ШАГ 5: Форматируем Decision Preview в board-ready формат
        formatted_decision_preview = None
        if DECISION_PREVIEW_FORMATTER_ENABLED:
            try:
                formatter = DecisionPreviewFormatter()
                formatted_decision_preview = formatter.format_preview(reasoning_result.decision_preview)
                
                # Валидируем Decision Preview
                validation_errors = formatter.validate_preview(reasoning_result.decision_preview)
                if validation_errors:
                    logger.warning(f"⚠️ Decision Preview validation errors: {validation_errors}")
                
                logger.info(f"✅ Decision Preview отформатирован для board-ready вывода")
            except Exception as e:
                logger.error(f"❌ Ошибка форматирования Decision Preview: {e}", exc_info=True)

    # Финальный ответ
    issues: List[dict] = list(ai_data.get("issues", []))

    # Отраслевые эвристики: усиливаем список рисков для конкретных сфер
    if industry == "IT":
        issues = enrich_it_specific_issues(text, issues)
    elif industry == "CONSTRUCTION":
        issues = enrich_construction_specific_issues(text, issues)
    elif industry == "MEDICINE":
        issues = enrich_medicine_specific_issues(text, issues)
    
    # Используем специализированные анализаторы (из TenderShield-Consolidated-Analysis)
    try:
        from specialized_analyzers import analyze_with_specialized_analyzers, LegalRiskAnalyzer, FinancialAnalyzer, RedFlagsDetector
        
        specialized_results = analyze_with_specialized_analyzers(text, industry)
        
        # Добавляем правовые риски
        if specialized_results.get("legal_risks"):
            issues.extend(specialized_results["legal_risks"])
        
        # Обновляем финансовый анализ
        financial_analysis = specialized_results.get("financial_analysis", {})
        if financial_analysis.get("nmck") and not final_nmck:
            final_nmck = financial_analysis["nmck"]
        if financial_analysis.get("risks"):
            issues.extend(financial_analysis["risks"])
        
        # Добавляем красные флаги из детектора
        if specialized_results.get("red_flags"):
            red_flags_from_detector = specialized_results["red_flags"]
            # Объединяем с красными флагами от LLM
            existing_red_flags = ai_data.get("redFlags", [])
            existing_codes = {rf.get("code") for rf in existing_red_flags}
            for rf in red_flags_from_detector:
                if rf.get("code") not in existing_codes:
                    existing_red_flags.append(rf)
            ai_data["redFlags"] = existing_red_flags
        
        # Проверка реестров (Registry Checker)
        try:
            from registry_checker import RegistryChecker
            registry_results = RegistryChecker.check_all_registries(text)
            if registry_results.get("warnings"):
                # Добавляем предупреждения о заблокированных/санкционированных поставщиках
                for warning in registry_results["warnings"]:
                    issues.append({
                        "title": warning.get("message", "Проблема с поставщиком"),
                        "severity": warning.get("severity", "HIGH"),
                        "description": "Обнаружено в реестрах блокировок/санкций",
                        "quote": ""
                    })
        except Exception as reg_error:
            logger.warning(f"Ошибка проверки реестров: {reg_error}")
    except ImportError as e:
        logger.warning(f"Специализированные анализаторы недоступны: {e}")
    except Exception as spec_error:
        logger.error(f"Ошибка специализированных анализаторов: {spec_error}")

    # 5b. Summary-блоки: если LLM их не вернул, формируем упрощённую версию на основе score
    default_block_status = "GREEN"
    if score < 40:
        default_block_status = "RED"
    elif score < 80:
        default_block_status = "YELLOW"

    summary_blocks = ai_data.get("summaryBlocks") or {
        "money": {
            "status": default_block_status,
            "comment": "Общая оценка финансовых условий по документу",
        },
        "time": {
            "status": default_block_status,
            "comment": "Общая оценка сроков и дедлайнов по документу",
        },
        "barriers": {
            "status": default_block_status,
            "comment": "Общая оценка требований к участнику (лицензии, опыт, нацрежим)",
        },
        "traps": {
            "status": default_block_status,
            "comment": "Общая оценка скрытых ловушек и рисков в ТЗ и договоре",
        },
    }

    participant_requirements = ai_data.get("participantRequirements", {})

    # Инициализируем переменные для ШАГОВ 4-5 (если они были выполнены)
    formatted_decision_preview = None
    decision_graph_data = None
    if reasoning_result:
        # ШАГ 5: Форматируем Decision Preview в board-ready формат
        if DECISION_PREVIEW_FORMATTER_ENABLED:
            try:
                formatter = DecisionPreviewFormatter()
                formatted_decision_preview = formatter.format_preview(reasoning_result.decision_preview)
                
                # Валидируем Decision Preview
                validation_errors = formatter.validate_preview(reasoning_result.decision_preview)
                if validation_errors:
                    logger.warning(f"⚠️ Decision Preview validation errors: {validation_errors}")
                
                logger.info(f"✅ Decision Preview отформатирован для board-ready вывода")
            except Exception as e:
                logger.error(f"❌ Ошибка форматирования Decision Preview: {e}", exc_info=True)
        
        # Сохраняем Decision Graph для audit trail
        if reasoning_result.decision_graph:
            try:
                decision_graph_data = reasoning_result.decision_graph.dict()
            except Exception as e:
                logger.warning(f"⚠️ Ошибка сериализации Decision Graph: {e}")

    # ШАГ 13: Добавляем информацию о режиме работы системы
    kill_switch_status = None
    safe_mode_response = None
    if KILL_SWITCH_ENABLED and kill_switch and safe_mode_handler:
        if not is_reasoning_enabled:
            # Если reasoning отключён, возвращаем Safe Mode ответ
            safe_mode_response = safe_mode_handler.get_safe_mode_response()
            # Если есть Evidence Objects, возвращаем их без reasoning
            if evidence_objects and current_mode == SystemMode.SAFE:
                safe_mode_response = safe_mode_handler.get_evidence_only_response(
                    evidence_objects=[ev.dict() if hasattr(ev, 'dict') else ev for ev in evidence_objects],
                    document_snapshot_id=document_snapshot.snapshot_id if document_snapshot else None,
                )
        else:
            # В нормальном режиме просто добавляем статус
            kill_switch_status = {
                "mode": current_mode.value,
                "reasoning_enabled": True,
            }
    
    # --- Паспорт (объединение AI + детерминированное извлечение) ---
    nmck_info = extract_nmck_info(text)
    extracted_passport = {
        "tenderNumber": extract_tender_number_regex(text) or "Не найдено",
        "customer": extract_customer_regex(text) or "Не найдено",
        "nmck": final_nmck or nmck_info.get("nmck") or "Не найдено",
        "nmckNumeric": nmck_info.get("nmckNumeric"),
        "deadlineApp": ai_data.get("passport", {}).get("deadlineApp") or extract_dates_regex(text) or "См. документацию",
        "deadlineExecution": extract_deadline_execution_regex(text) or ai_data.get("timelineSummary", {}).get("deadlineExecution") or "Не указано",
        "region": ai_data.get("passport", {}).get("region", "РФ"),
        "fz": ai_data.get("passport", {}).get("fz", "44-ФЗ"),
        "guarantee": ai_data.get("passport", {}).get("guarantee", "Не указано"),
        "bidSecurity": ai_data.get("passport", {}).get("bidSecurity"),
        "contractSecurity": ai_data.get("passport", {}).get("contractSecurity"),
    }

    # PHASE 1: Преобразуем tender_passport_data в формат TenderPassport схемы (если есть данные)
    tender_passport_schema = None
    if tender_passport_data and tender_passport_data.get("nmck_numeric") and tender_passport_data.get("customer"):
        try:
            from schemas import TenderSource, TenderPassport
            from datetime import datetime as dt
            
            # Преобразуем deadline из строки в date если нужно
            deadline_date = None
            if tender_passport_data.get("deadline"):
                if isinstance(tender_passport_data["deadline"], str):
                    try:
                        deadline_date = dt.fromisoformat(tender_passport_data["deadline"]).date()
                    except:
                        try:
                            deadline_date = dt.strptime(tender_passport_data["deadline"], "%Y-%m-%d").date()
                        except:
                            deadline_date = None
                else:
                    deadline_date = tender_passport_data["deadline"]
            
            # Создаем TenderSource объекты
            nmck_quote = tender_passport_data.get("nmck_source", "") or ""
            nmck_source_obj = TenderSource(
                document_name=filename,
                quote=nmck_quote[:500] if nmck_quote else "Извлечено из документа",
                extraction_method="llm" if llm_passport and llm_passport.get("nmck_numeric") else "regex",
                confidence=0.9 if llm_passport else 0.8
            )
            
            customer_quote = tender_passport_data.get("customer_source", "") or ""
            customer_source_obj = TenderSource(
                document_name=filename,
                quote=customer_quote[:500] if customer_quote else "Извлечено из документа",
                extraction_method="llm" if llm_passport and llm_passport.get("customer") else "regex",
                confidence=0.85 if llm_passport else 0.75
            )
            
            deadline_source_obj = None
            if deadline_date and tender_passport_data.get("deadline_source"):
                deadline_quote = tender_passport_data.get("deadline_source", "") or ""
                deadline_source_obj = TenderSource(
                    document_name=filename,
                    quote=deadline_quote[:500] if deadline_quote else "Извлечено из документа",
                    extraction_method="llm" if llm_passport and llm_passport.get("deadline") else "regex",
                    confidence=0.85
                )
            
            contract_term_source_obj = None
            if tender_passport_data.get("contract_term_months") and tender_passport_data.get("contract_term_source"):
                term_quote = tender_passport_data.get("contract_term_source", "") or ""
                contract_term_source_obj = TenderSource(
                    document_name=filename,
                    quote=term_quote[:500] if term_quote else "Извлечено из документа",
                    extraction_method="llm" if llm_passport and llm_passport.get("contract_term_months") else "regex",
                    confidence=0.8
                )
            
            guarantee_source_obj = None
            if tender_passport_data.get("guarantee_amount") and tender_passport_data.get("guarantee_source"):
                guarantee_quote = tender_passport_data.get("guarantee_source", "") or ""
                guarantee_source_obj = TenderSource(
                    document_name=filename,
                    quote=guarantee_quote[:500] if guarantee_quote else "Извлечено из документа",
                    extraction_method="llm" if llm_passport and llm_passport.get("guarantee_amount") else "regex",
                    confidence=0.7
                )
            
            # Создаем TenderPassport объект
            tender_passport_schema = TenderPassport(
                nmck_numeric=float(tender_passport_data["nmck_numeric"]),
                nmck_formatted=tender_passport_data.get("nmck_formatted", f"{tender_passport_data['nmck_numeric']:,.0f} руб."),
                nmck_source=nmck_source_obj,
                customer=tender_passport_data["customer"],
                customer_source=customer_source_obj,
                deadline=deadline_date,
                deadline_source=deadline_source_obj,
                contract_term_months=tender_passport_data.get("contract_term_months"),
                contract_term_source=contract_term_source_obj,
                guarantee_amount=tender_passport_data.get("guarantee_amount"),
                guarantee_source=guarantee_source_obj,
                completion_percentage=tender_passport_data.get("completion_percentage", 0),
                warnings=tender_passport_data.get("warnings", [])
            )
            logger.info(f"✅ Tender Passport создан: НМЦК={tender_passport_schema.nmck_numeric}, Заказчик={tender_passport_schema.customer}")
        except Exception as schema_error:
            logger.error(f"❌ Ошибка создания TenderPassport схемы: {schema_error}")
            tender_passport_schema = None

    # ФАЗА 3: Подготавливаем данные procurement_analysis для response
    procurement_analysis_data = None
    procurement_analysis_obj = None  # Сохраняем оригинальный объект для БД
    if reasoning_result and hasattr(reasoning_result, 'procurement_analysis') and reasoning_result.procurement_analysis:
        proc_analysis = reasoning_result.procurement_analysis
        procurement_analysis_obj = proc_analysis  # Сохраняем оригинальный объект
        try:
            # Сериализуем ProcurementAnalysis в dict
            procurement_analysis_data = {
                "verdict": proc_analysis.verdict.value,
                "iun": proc_analysis.iun,
                "decision_grounds": proc_analysis.decision_grounds,
                "critical_parameters": [
                    {
                        "name": p.name,
                        "value": p.value,
                        "source": p.source,
                        "confidence": p.confidence,
                        "impact": p.impact,
                    }
                    for p in proc_analysis.critical_parameters
                ],
                "blockers": [
                    {
                        "sub_classification": b.sub_classification.value,
                        "description": b.description,
                        "legal_basis": b.legal_basis.value if b.legal_basis else None,
                        "mitigation_strategy": b.mitigation_strategy,
                        "mitigation_cost": b.mitigation_cost,
                        "mitigation_time_days": b.mitigation_time_days,
                        "is_mitigable": b.is_mitigable,
                        "evidence_ids": b.evidence_ids,
                        "kb_reference": b.kb_reference,
                    }
                    for b in proc_analysis.blockers
                ],
                "red_flags": proc_analysis.red_flags,
                "financial_impact": {
                    "best_case": proc_analysis.financial_impact.best_case,
                    "worst_case": proc_analysis.financial_impact.worst_case,
                    "expected_value": proc_analysis.financial_impact.expected_value,
                    "worst_case_probability": proc_analysis.financial_impact.worst_case_probability,
                    "mitigation_costs": proc_analysis.financial_impact.mitigation_costs,
                    "penalty_risks": proc_analysis.financial_impact.penalty_risks,
                },
                "checklist": proc_analysis.checklist,
                "kb_references": proc_analysis.kb_references,
            }
        except Exception as e:
            logger.warning(f"⚠️ Ошибка сериализации procurement_analysis: {e}")

    result = {
        "score": score,
        "summary": ai_data.get("summary", "Нет описания"),
        "verdict": verdict,
        "passport": extracted_passport,
        "passportValidation": build_passport_validation(extracted_passport),
        "passportEvidence": build_passport_evidence(text, filename, extracted_passport, page_texts=page_texts),
        "issues": attach_issue_evidence(issues, filename, page_texts=page_texts),
        "specs": ai_data.get("specs", []),  # <-- спецификация
        "redFlags": ai_data.get("redFlags", []),
        "financialSummary": ai_data.get("financialSummary", {}),
        "timelineSummary": ai_data.get("timelineSummary", {}),
        "participantRequirements": participant_requirements,
        "summaryBlocks": summary_blocks,
        "actions": ai_data.get("actions", []),
        # PHASE 1: Добавляем Tender Passport (структурированные данные)
        "tender_passport": tender_passport_schema.dict() if tender_passport_schema else None,
        # ШАГ 5: Добавляем отформатированный Decision Preview (если доступен)
        "decision_preview_step5": formatted_decision_preview,
        # ШАГ 4: Добавляем Decision Graph для audit trail (если доступен)
        "decision_graph": decision_graph_data,
        # ФАЗА 3: Добавляем специализированный анализ закупок
        "procurement_analysis": procurement_analysis_data,
        # ФАЗА 5: Сохраняем ссылку на оригинальный объект для сохранения в БД
        "_procurement_analysis_obj": procurement_analysis_obj,  # Внутреннее поле, не для API
        # ФАЗА 5: Сохраняем evidence_objects для сохранения в БД
        "_evidence_objects": evidence_objects if evidence_objects else None,  # Внутреннее поле, не для API
        # ШАГ 6: Добавляем Audit Trail snapshots (если доступны)
        "audit_trail": {
            "document_snapshot_id": document_snapshot.snapshot_id if document_snapshot else None,
            "evidence_snapshot_id": evidence_snapshot.evidence_set_id if evidence_snapshot else None,
            "decision_snapshot_id": decision_snapshot.decision_id if decision_snapshot else None,
            "freshness_status": decision_snapshot.freshness_status.value if decision_snapshot else None,
        } if (document_snapshot or decision_snapshot) else None,
        # ШАГ 13: Kill Switch статус
        "kill_switch_status": kill_switch_status,
        "safe_mode_response": safe_mode_response,
    }

    logger.info(
        f"Успех по документу {filename}! Найдено {len(result['specs'])} позиций и {len(result['issues'])} рисков."
    )
    return result


# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ДЕМО-СЕССИЙ ---
def get_or_create_demo_session(request: Request, db: Session) -> Optional[DemoSession]:
    """Получить или создать демо-сессию для текущего браузера"""
    # Получаем session_id из cookies или заголовков
    session_id = None
    if hasattr(request, 'cookies') and request.cookies.get("demo_session_id"):
        session_id = request.cookies.get("demo_session_id")
    elif hasattr(request, 'headers') and request.headers.get("X-Demo-Session-Id"):
        session_id = request.headers.get("X-Demo-Session-Id")
    
    if not session_id:
        # Создаем новую сессию
        session_id = str(uuid.uuid4())
    
    # Ищем в БД
    demo = db.query(DemoSession).filter(DemoSession.id == session_id).first()
    
    if not demo:
        # Создаем новую
        device_fingerprint = f"{request.client.host if hasattr(request, 'client') else 'unknown'}"
        demo = DemoSession(
            id=session_id,
            device_fingerprint=device_fingerprint
        )
        db.add(demo)
        db.commit()
        db.refresh(demo)
    
    return demo


# --- ГЛАВНЫЙ АНАЛИЗАТОР ОДНОГО ДОКУМЕНТА ---
# Rate limiting для анализа (опционально)
try:
    from rate_limiter import limit_analysis_requests
    _analyze_decorator = limit_analysis_requests
except ImportError:
    # Если rate limiter недоступен, просто возвращаем функцию как есть
    def _analyze_decorator(func):
        return func

@app.post("/api/analyze")
@_analyze_decorator
async def analyze_endpoint(
    request: Request,
    file: UploadFile = File(...),
    industry: str = Form("UNIVERSAL"),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """
    Новый двухступенчатый конвейер анализа (Chain of Thought):
    1) Сбор фактов из документа (финансы, сроки, обязанности, пробелы).
    2) "Злой аудитор" принимает решение и формирует JSON результата.
    """
    from utils.file_validator import validate_file, validate_file_size

    class Stage1Facts(BaseModel):
        nmck: Optional[str] = None
        advance: Optional[str] = None
        bid_security: Optional[str] = None
        contract_security: Optional[str] = None
        payment_terms: Optional[str] = None
        deadlines: Optional[str] = None
        obligations_customer: Optional[str] = None
        obligations_supplier: Optional[str] = None
        missing_items: Optional[str] = None
        risks: Optional[str] = None

    class Issue(BaseModel):
        title: str
        severity: str
        description: str
        quote: str
        recommendation: Optional[str] = None

    class AnalysisResult(BaseModel):
        summary: str
        score: int
        verdict: str
        passport: Dict[str, str]
        issues: List[Dict] = []
        specs: List[Dict] = []
        executive_summary: Optional[str] = None
        financial_analysis: Optional[Dict[str, Any]] = None
        deal_breakers: List[str] = []
        smart_questions: List[str] = []

    def _call_llm(prompt: str, format_json: bool = True) -> str:
        """Локальный безопасный вызов LLM с приоритетом qwen2.5-coder:7b -> llama3 -> fallback список."""
        preferred_models = ["qwen2.5-coder:7b", "llama3"] + OLLAMA_MODELS
        last_error = None
        for model_name in preferred_models:
            try:
                params = {
                    "model": model_name,
                    "base_url": settings.OLLAMA_BASE_URL,
                    "temperature": 0.1,
                    "timeout": 120,  # 2 минуты таймаут (уменьшено с 5 минут)
                }
                if format_json:
                    params["format"] = "json"
                llm = ChatOllama(**params)
                resp = llm.invoke(prompt)
                if resp and resp.content and len(resp.content) > 10:
                    return resp.content
                last_error = ValueError("Пустой ответ LLM")
            except Exception as e:
                last_error = e
                logger.warning(f"LLM {model_name} ошибка: {e}")
                continue
        logger.error(f"Все модели недоступны: {last_error}")
        raise HTTPException(status_code=503, detail="LLM недоступен для анализа")

    def _extract_text(temp_path: str, filename: str) -> str:
        """Умный парсинг с unstructured, затем fallback к PyMuPDF/Docx2txt."""
        ext = (os.path.splitext(str(filename or ""))[1] or "").lower()
        # 1) unstructured, если доступна
        try:
            from unstructured.partition.auto import partition

            elements = partition(filename=temp_path)
            joined = "\n".join([el.text for el in elements if getattr(el, "text", "")])
            if joined.strip():
                return joined
        except Exception as e:
            logger.info(f"unstructured не сработал: {e}")

        # 2) fallback
        try:
            if ext == ".pdf":
                docs = PyMuPDFLoader(temp_path).load()
                return "\n".join([d.page_content for d in docs])
            if ext in (".docx", ".doc"):
                # Сначала пробуем Pandoc для .docx
                if ext == ".docx":
                    try:
                        markdown_text = docx_to_markdown(temp_path)
                        if markdown_text and markdown_text.strip():
                            return markdown_text
                    except (PandocServiceError, Exception):
                        pass  # Fallback на Docx2txt
                # Fallback: Docx2txt
                docs = Docx2txtLoader(temp_path).load()
                return "\n".join([d.page_content for d in docs])
            if ext in (".xls", ".xlsx"):
                # Excel-файлы: конвертируем содержимое ячеек в плоский текст
                try:
                    from openpyxl import load_workbook
                    wb = load_workbook(temp_path, data_only=True, read_only=True)
                    text_parts = []
                    for sheet_name in wb.sheetnames:
                        sheet = wb[sheet_name]
                        text_parts.append(f"=== Лист: {sheet_name} ===")
                        for row in sheet.iter_rows(values_only=True):
                            row_text = " | ".join([str(cell) if cell is not None else "" for cell in row])
                            if row_text.strip():
                                text_parts.append(row_text)
                    wb.close()
                    result = "\n".join(text_parts)
                    if result.strip():
                        return result
                    else:
                        logger.warning(f"Excel файл {filename} пуст или не содержит данных")
                        return f"[Excel файл {filename} не содержит читаемых данных]"
                except ImportError:
                    logger.error("openpyxl не установлен. Установите: pip install openpyxl")
                    raise HTTPException(status_code=500, detail="Библиотека для чтения Excel не установлена")
                except Exception as excel_err:
                    logger.error(f"Ошибка чтения Excel-файла {filename}: {excel_err}")
                    # Пробуем альтернативный способ для старых .xls через xlrd (если доступен)
                    if ext == ".xls":
                        try:
                            import xlrd
                            book = xlrd.open_workbook(temp_path)
                            text_parts = []
                            for sheet in book.sheets():
                                text_parts.append(f"=== Лист: {sheet.name} ===")
                                for row_idx in range(sheet.nrows):
                                    row = sheet.row_values(row_idx)
                                    row_text = " | ".join([str(cell) if cell else "" for cell in row])
                                    if row_text.strip():
                                        text_parts.append(row_text)
                            result = "\n".join(text_parts)
                            if result.strip():
                                return result
                        except ImportError:
                            logger.warning("xlrd не установлен для чтения старых .xls файлов")
                        except Exception as xls_err:
                            logger.error(f"Ошибка чтения .xls через xlrd: {xls_err}")
                    raise HTTPException(status_code=400, detail=f"Файл Excel не читается: {str(excel_err)[:100]}")
            # текст по умолчанию
            with open(temp_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка чтения файла {filename}: {e}")
            raise HTTPException(status_code=400, detail=f"Файл не читается: {str(e)[:100]}")

    # --- 1. Проверяем лимиты/режим ---
    is_demo = False
    demo_session = None
    user_id = None
    session_id = None
    usage = None

    if current_user:
        if current_user.plan_type == "trial" and not current_user.is_trial_active():
            free_tariff = db.query(Tariff).filter(Tariff.name == "Free").first()
            if free_tariff:
                current_user.plan_type = "free"
                current_user.tariff_id = free_tariff.id
                db.commit()
                logger.info(f"Триал истек для {current_user.email}, переведен на Free тариф")

        can_analyze, error_msg = check_user_can_analyze(current_user, db)
        if not can_analyze:
            raise HTTPException(status_code=429, detail=error_msg)

        user_id = current_user.id
        now = datetime.now()
        usage = db.query(Usage).filter(
            Usage.user_id == current_user.id, Usage.year == now.year, Usage.month == now.month
        ).first()
        if not usage:
            usage = Usage(user_id=current_user.id, year=now.year, month=now.month, analyses_count=0)
            db.add(usage)
            db.flush()
    else:
        is_demo = True
        if request:
            demo_session = get_or_create_demo_session(request, db)
            if demo_session:
                can_analyze, reason = demo_session.can_analyze()
                if not can_analyze:
                    raise HTTPException(
                        status_code=429,
                        detail=reason,
                        headers={"X-Demo-Limit": "true", "X-Suggest-Registration": "true"},
                    )
                session_id = demo_session.id
                demo_session.increment_analyses()
                db.commit()
        else:
            logger.warning("Демо-режим без request объекта")

    # --- 2. Сохраняем файл и проверяем кеш ---
    is_valid, error_msg = validate_file(file)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    original_ext = os.path.splitext(file.filename or "")[1] or ""
    temp_fd, temp_path = tempfile.mkstemp(suffix=original_ext, prefix="tender_", dir=os.getcwd())
    file_content_bytes = b""

    try:
        os.close(temp_fd)
        file_size = 0
        MAX_SIZE = 50 * 1024 * 1024
        with open(temp_path, "wb") as buffer:
            while True:
                chunk = await file.read(8192)
                if not chunk:
                    break
                file_size += len(chunk)
                if file_size > MAX_SIZE:
                    os.remove(temp_path)
                    raise HTTPException(
                        status_code=413,
                        detail=f"Файл слишком большой ({(file_size / 1024 / 1024):.2f} МБ). Максимальный размер: {MAX_SIZE / 1024 / 1024} МБ",
                    )
                buffer.write(chunk)
                file_content_bytes += chunk
            buffer.flush()
            os.fsync(buffer.fileno())

        from cache_service import get_document_hash, get_cached_analysis, cache_analysis

        file_hash = get_document_hash(file_content_bytes, file.filename)
        cached_result = get_cached_analysis(file_hash, industry)
        if cached_result:
            logger.info(f"✅ Использован закешированный результат для {file.filename}")
            if current_user:
                try:
                    db.add(
                        Analysis(
                            user_id=current_user.id,
                            session_id=session_id,
                            is_demo=is_demo,
                            filename=file.filename,
                            industry=industry,
                            result_json=cached_result,
                            score=cached_result.get("score", 50),
                            verdict=cached_result.get("verdict", "CAUTION"),
                            summary=cached_result.get("summary", ""),
                        )
                    )
                    if usage:
                        usage.analyses_count += 1
                        usage.updated_at = datetime.utcnow()
                    db.commit()
                except Exception as db_err:
                    db.rollback()
                    logger.error(f"Ошибка сохранения кешированного анализа: {db_err}")
            return cached_result

        # --- 3. Чтение текста ---
        text = _extract_text(temp_path, file.filename)
        if not text.strip():
            raise HTTPException(status_code=400, detail="Файл пустой")

        # --- 4. Stage 1: факты ---
        llm_context = build_llm_context_excerpt(text, max_chars=24000)

        stage1_prompt = f"""
        Ты — быстрый факт-экстрактор для тендерного анализа. Верни JSON без комментариев:
        {{
          "nmck": "...",
          "advance": "...",
          "bid_security": "...",
          "contract_security": "...",
          "payment_terms": "сроки и условия оплаты",
          "deadlines": "сроки подачи/исполнения",
          "obligations_customer": "главные обязанности заказчика",
          "obligations_supplier": "главные обязанности поставщика",
          "missing_items": "чего явно не хватает",
          "risks": "кратко потенциальные риски"
        }}
        Текст:
        {llm_context}
        """
        facts_raw = _call_llm(stage1_prompt, format_json=True)
        try:
            facts_dict = json.loads(facts_raw) if isinstance(facts_raw, str) else facts_raw
            facts = Stage1Facts(**facts_dict)
        except Exception as e:
            logger.warning(f"Stage1 парсинг не удался: {e}")
            facts = Stage1Facts()

        # --- 5. Stage 2: Злой аудитор ---
        system_prompt = (
            "Ты — опытный тендерный специалист с 30-летним стажем. "
            "Говоришь живым, понятным языком, как коллега коллеге. "
            "Не используй канцеляризмы, формальные обороты и бюрократический жаргон. "
            "Объясняй простыми словами, как будто предупреждаешь друга-бизнесмена о подвохах. "
            "Твоя задача — найти реальные проблемы и объяснить их так, чтобы было понятно любому предпринимателю. "
            "Всегда ищи: (1) Асимметрию (жесткие требования к исполнителю vs слабые штрафы заказчика), "
            "(2) Отсутствие ключевых требований (опыт, квалификация, SLA, контроль качества), "
            "(3) Экономику: цена/единица, маржинальность, риск кассового разрыва при отсрочке платежей. "
            "Начинай ответы с 'Привет!' или 'Слушай, тут проблема...' - говори естественно."
        )
        verdict_prompt = f"""
        Инструкция:
        Сформируй глубокий анализ и верни JSON по структуре Советника:
        {{
          "summary": "1 предложение с вердиктом",  // дублирует executive_summary в сжатом виде
          "executive_summary": "Начни с 'Привет! Я изучил этот контракт.' Затем простыми словами объясни главную проблему в 3-5 строк. "
                              "Говори как опытный коллега, который предупреждает о подвохах. "
                              "Пример: 'Привет! Я изучил этот контракт. Честно говоря, он выглядит как ловушка для новичка. "
                              "Заказчик хочет Мерседес по цене Жигулей - цена занижена на 25%. "
                              "Более того, аванса нет, а оплата через 60 дней. Вы будете кредитовать заказчика своими деньгами.'",
          "score": 0-100,  // 0=полный стоп, 100=чисто
          "verdict": "STOP"|"CAUTION"|"PARTICIPATE",
          "passport": {{
              "nmck": "{facts.nmck or ''}",
              "deadlineApp": "{facts.deadlines or ''}",
              "guarantee": "{facts.contract_security or facts.bid_security or ''}",
              "advance": "{facts.advance or '0%'}",
              "payment_terms": "{facts.payment_terms or ''}"
          }},
          "financial_analysis": {{
              "margin_risk": "High|Medium|Low",
              "cash_gap_risk": "Yes|No",
              "reasoning": "Объясни простыми словами, почему такой риск. Пример: 'Цена занижена на 25% от рыночной. "
                          "При таких условиях даже при идеальном выполнении вы уйдете в минус. Плюс нет аванса - придется кредитовать заказчика.'"
          }},
          "deal_breakers": [
              "Простыми словами опиши критический стоп-фактор. Пример: 'Аванс 0%, оплата через 60 дней - вы кредитуете заказчика'",
              "Еще один критический фактор простыми словами"
          ],
          "smart_questions": [
              "Вопрос для заказчика простыми словами. Пример: 'Прошу разъяснить экономическое обоснование цены 300 руб/час, учитывая среднерыночную ставку 800 руб/час?'",
              "Еще один вопрос простыми словами",
              "Еще один вопрос простыми словами"
          ],
          "issues": [  // заполни на основе deal_breakers/рисков, чтобы совместимость с UI не ломать
              {{
                  "title": "краткий риск",
                  "severity": "high|medium|low",
                  "description": "объясни простыми словами, почему это плохо для бизнеса. Пример: 'Заказчик требует реакции за 60 минут, но сам может проверять работу неделями. Штрафы только для вас.'",
                  "quote": "цитата из документа",
                  "recommendation": "что сделать простыми словами. Пример: 'Запросить зеркальные штрафы через Протокол разногласий'"
              }}
          ],
          "specs": []
        }}

        Логика анализа (используй факты Stage1 + текст):
        - Асимметрия: жесткие обязанности исполнителя vs слабые штрафы заказчика.
        - Отсутствие: нет опыта/квалификации/SLA/контроля качества/ограничения объема — это риск демпинга.
        - Экономика: цена за единицу vs рынок; маржа; риск кассового разрыва, если отсрочка > 15 дней или аванс < 10%.
        - Если обеспечение > 15% -> укажи заморозку оборотных средств.
        - Если объем "без ограничений" при фиксированной цене -> это deal_breaker или high risk.
        - Вердикт: STOP (криминал/невыполнимо/нет экономики), CAUTION (нужны деньги/юристы/переговоры), PARTICIPATE (чисто).
        - Smart questions: 3-5 острых вопросов, раскрывающих подвох (объем, платежи, штрафы, опыт).

        Stage1 факты:
        {facts.model_dump()}

        Текст (выдержки):
        {llm_context}
        """
        final_prompt = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": verdict_prompt},
        ]

        final_raw = None
        try:
            # ChatOllama принимает messages, но _call_llm ожидает prompt. Объединяем.
            prompt_str = "\n".join([f"{m['role']}: {m['content']}" for m in final_prompt])
            final_raw = _call_llm(prompt_str, format_json=True)
            final_dict = json.loads(final_raw) if isinstance(final_raw, str) else final_raw
            result_model = AnalysisResult(**final_dict)
            result = result_model.model_dump()
        except Exception as e:
            logger.error(f"Stage2 парсинг не удался: {e}")
            # fallback минимальный
            result = {
                "summary": "⚠️ Упрощенный анализ: не удалось получить полный ответ LLM",
                "score": 45,
                "verdict": "CAUTION",
                "passport": {
                    "nmck": facts.nmck or "Не найдено",
                    "deadlineApp": facts.deadlines or "Не найдено",
                    "guarantee": facts.contract_security or facts.bid_security or "Не найдено",
                    "advance": facts.advance or "0%",
                },
                "executive_summary": "Не удалось получить полный ответ LLM. Требуется ручная проверка.",
                "financial_analysis": {
                    "margin_risk": "High",
                    "cash_gap_risk": "Yes",
                    "reasoning": "Резервный ответ: модель недоступна, экономический анализ не выполнен."
                },
                "deal_breakers": ["Модель не ответила, требуется повторный анализ"],
                "smart_questions": [
                    "Подтвердите ключевые риски вручную",
                    "Перезапустите анализ после восстановления LLM"
                ],
                "issues": [
                    {
                        "title": "Нет данных LLM",
                        "severity": "medium",
                        "description": "Модель не ответила, требуется ручная проверка.",
                        "quote": "",
                        "recommendation": "Перезапустить анализ после восстановления LLM",
                    }
                ],
                "specs": [],
            }

        # --- 6. Кеш/БД/ответ ---
        try:
            cache_analysis(file_hash, result, industry, ttl=86400)
        except Exception as cache_err:
            logger.warning(f"Не удалось закешировать результат: {cache_err}")

        try:
            analysis_obj = Analysis(
                user_id=user_id,
                session_id=session_id,
                is_demo=is_demo,
                filename=file.filename,
                industry=industry,
                result_json=result,
                score=result.get("score", 50),
                verdict=result.get("verdict", "CAUTION"),
                summary=result.get("summary", ""),
            )
            db.add(analysis_obj)
            if current_user and usage:
                usage.analyses_count += 1
                usage.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(analysis_obj)
            
            # ФАЗА 5: Сохраняем procurement анализ в БД (если доступен)
            # Примечание: procurement анализ уже выполнен в analyze_single_file через reasoning_layer
            # Здесь мы сохраняем его в БД, используя оригинальный объект из результата
            if analysis_obj and EVIDENCE_LAYER_ENABLED and isinstance(result, dict):
                try:
                    from services.procurement_analysis_service import ProcurementAnalysisService
                    
                    # Получаем оригинальный объект procurement_analysis (не dict)
                    procurement_analysis_obj = result.get("_procurement_analysis_obj")
                    
                    if procurement_analysis_obj:
                        # Получаем evidence_objects из результата (если они там есть)
                        evidence_list = None
                        if result.get("_evidence_objects"):
                            evidence_list = result["_evidence_objects"]
                        
                        # Сохраняем через сервис
                        service = ProcurementAnalysisService(db)
                        service.save_procurement_analysis(
                            analysis_id=analysis_obj.id,
                            procurement_analysis=procurement_analysis_obj,
                            evidence_list=evidence_list
                        )
                        logger.info(f"✅ Procurement анализ сохранен для analysis_id={analysis_obj.id}")
                        result["procurement_analysis_id"] = analysis_obj.id
                        
                        # Удаляем внутренние поля из результата перед отправкой клиенту
                        result.pop("_procurement_analysis_obj", None)
                        result.pop("_evidence_objects", None)
                    
                except ImportError as import_err:
                    logger.warning(f"Procurement анализ недоступен: {import_err}")
                except Exception as proc_err:
                    logger.error(f"Ошибка сохранения procurement анализа: {proc_err}", exc_info=True)
                    # Не блокируем основной анализ из-за ошибки сохранения
                    # Удаляем внутренние поля в любом случае
                    result.pop("_procurement_analysis_obj", None)
                    result.pop("_evidence_objects", None)
            
            if is_demo and demo_session and demo_session.analyses_count == 1:
                result["ui_suggestion"] = {
                    "type": "register_after_analysis",
                    "title": "🎉 Анализ готов!",
                    "message": "Сохраните результаты в личный кабинет",
                    "benefits": ["Хранить все анализы", "Экспортировать в PDF", "Делиться с коллегами"],
                }
        except Exception as db_err:
            db.rollback()
            logger.error(f"Ошибка сохранения в БД: {db_err}")

        if not current_user:
            try:
                item = HistoryItem(
                    id=str(uuid.uuid4()),
                    createdAt=datetime.utcnow(),
                    kind="single",
                    industry=industry,
                    files=[file.filename],
                    summaryScore=float(result.get("score", 0) or 0.0),
                    verdict=str(result.get("verdict", "")),
                )
                HISTORY.append(item)
                if len(HISTORY) > MAX_HISTORY_ITEMS:
                    del HISTORY[0 : len(HISTORY) - MAX_HISTORY_ITEMS]
            except Exception as hist_err:
                logger.error(f"History append error (single): {hist_err}")

        # --- 7. Стабилизация паспорта и неблокирующая валидация ---
        try:
            nmck_info = extract_nmck_info(text)
            extracted_passport = {
                "tenderNumber": extract_tender_number_regex(text) or "Не найдено",
                "customer": extract_customer_regex(text) or "Не найдено",
                "nmck": nmck_info.get("nmck") or "Не найдено",
                "nmckNumeric": nmck_info.get("nmckNumeric"),
                "deadlineApp": extract_dates_regex(text) or "См. документацию",
                "deadlineExecution": extract_deadline_execution_regex(text) or "Не указано",
            }

            # Объединяем с тем, что вернул LLM (приоритет LLM, кроме nmckNumeric)
            result_passport = result.get("passport") if isinstance(result, dict) else None
            if isinstance(result_passport, dict):
                merged = {**extracted_passport, **result_passport}
                # Гарантируем, что nmckNumeric не затёрт строкой
                if "nmckNumeric" not in merged or merged.get("nmckNumeric") is None:
                    merged["nmckNumeric"] = extracted_passport.get("nmckNumeric")
                result["passport"] = merged
            else:
                result["passport"] = extracted_passport

            result["passportValidation"] = build_passport_validation(result.get("passport") or {})
            filename = file.filename
            page_texts = _try_load_pdf_page_texts(temp_path, filename)
            result["passportEvidence"] = build_passport_evidence(text, filename, result.get("passport") or {}, page_texts=page_texts)
            result["issues"] = attach_issue_evidence(result.get("issues") or [], filename, page_texts=page_texts)
        except Exception as e:
            logger.warning(f"⚠️ Ошибка стабилизации паспорта/валидации: {e}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        import traceback

        error_trace = traceback.format_exc()
        logger.error(f"❌ Server Error в analyze_endpoint: {e}")
        logger.error(f"Детали ошибки:\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"Ошибка при анализе документа: {str(e)[:200]}")
    finally:
        safe_remove_file(temp_path)

@app.post("/api/analyze-package")
async def analyze_package_endpoint(
    request: Request,
    files: List[UploadFile] = File(...),
    industry: str = Form("UNIVERSAL"),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> PackageAnalysisResponse:
    from utils.file_validator import validate_file
    
    # Проверяем DEMO-режим (если пользователь не авторизован)
    is_demo = current_user is None
    demo_session = None
    
    if is_demo:
        demo_session = get_or_create_demo_session(request, db)
        if demo_session:
            can_analyze, reason = demo_session.can_analyze()
            if not can_analyze:
                raise HTTPException(
                    status_code=429,
                    detail=reason,
                    headers={"X-Demo-Limit": "true", "X-Suggest-Registration": "true"},
                )
            logger.info(f"✅ DEMO-анализ пакета: session_id={demo_session.id}, analyses_count={demo_session.analyses_count}")
            demo_session.increment_analyses()
            db.commit()
        else:
            logger.warning("⚠️ DEMO-режим: не удалось создать demo-сессию, продолжаем без неё")
    
    if not files:
        raise HTTPException(status_code=400, detail="Не переданы файлы для анализа")
    
    # Ограничение на количество файлов в пакете (режим «ключевых документов»)
    # Рекомендуется анализировать 3–5 ключевых файлов; жёсткий предел — 5 документов в пакете
    MAX_FILES_IN_PACKAGE = 5
    if len(files) > MAX_FILES_IN_PACKAGE:
        raise HTTPException(
            status_code=400,
            detail=f"Слишком много файлов ({len(files)}). Максимум: {MAX_FILES_IN_PACKAGE}"
        )
    
    # Валидация всех файлов перед обработкой
    for upload in files:
        is_valid, error_msg = validate_file(upload)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Ошибка валидации файла {upload.filename}: {error_msg}")

    package_id = str(uuid.uuid4())
    document_results: List[DocumentAnalysis] = []

    try:
        for upload in files:
            # Используем tempfile для безопасного создания временного файла.
            # Используем только расширение файла, чтобы избежать проблем с
            # не-ASCII символами в путях.
            original_ext = os.path.splitext(upload.filename or "")[1] or ""
            temp_fd, temp_path = tempfile.mkstemp(suffix=original_ext, prefix="tender_", dir=os.getcwd())
            try:
                os.close(temp_fd)  # Закрываем дескриптор, работаем с путем
                
                # Проверка размера при сохранении
                file_size = 0
                MAX_SIZE = 50 * 1024 * 1024  # 50 МБ
                
                with open(temp_path, "wb") as buffer:
                    while True:
                        chunk = await upload.read(8192)  # Читаем по 8 КБ
                        if not chunk:
                            break
                        file_size += len(chunk)
                        if file_size > MAX_SIZE:
                            os.remove(temp_path)
                            raise HTTPException(
                                status_code=413,
                                detail=f"Файл {upload.filename} слишком большой ({(file_size / 1024 / 1024):.2f} МБ). Максимальный размер: {MAX_SIZE / 1024 / 1024} МБ"
                            )
                        buffer.write(chunk)
                    buffer.flush()
                    os.fsync(buffer.fileno())
                
                # Проверяем, что файл действительно записан
                if not os.path.exists(temp_path):
                    raise HTTPException(
                        status_code=500,
                        detail=f"Не удалось сохранить файл {upload.filename} на сервере"
                    )
                
                # Проверяем размер файла
                file_size_on_disk = os.path.getsize(temp_path)
                if file_size_on_disk == 0:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Файл {upload.filename} пустой или не был сохранён корректно"
                    )
                
                logger.info(f"Файл {upload.filename} сохранён на диск: {temp_path}, размер: {file_size_on_disk} байт")

                single_result = await analyze_single_file(temp_path, upload.filename, industry)

                # Гарантируем, что summary всегда строка (иногда LLM может вернуть dict)
                raw_summary = single_result.get("summary", "")
                if isinstance(raw_summary, dict):
                    summary_value = (
                        raw_summary.get("description")
                        or raw_summary.get("text")
                        or str(raw_summary)
                    )
                else:
                    summary_value = str(raw_summary)
                
                document_results.append(
                    DocumentAnalysis(
                        filename=upload.filename,
                        score=single_result["score"],
                        summary=summary_value,
                        verdict=single_result["verdict"],
                        passport=single_result["passport"],
                        passportValidation=single_result.get("passportValidation"),
                        passportEvidence=single_result.get("passportEvidence"),
                        issues=single_result["issues"],
                        specs=single_result["specs"],
                    )
                )
            finally:
                # Безопасное удаление файла с повторными попытками
                safe_remove_file(temp_path)

        # Итоговая оценка пакета
        scores = [doc.score for doc in document_results]
        summary_score = sum(scores) / len(scores)

        # Вердикт пакета по худшему документу
        verdict_order = {"STOP": 2, "CAUTION": 1, "PARTICIPATE": 0}
        worst_doc = max(document_results, key=lambda d: verdict_order.get(d.verdict, 0))
        package_verdict = worst_doc.verdict

        # Глобальные риски по всему пакету
        global_issues: List[dict] = build_global_issues(document_results)

        logger.info(
            "ANALYZE_PACKAGE_DONE packageId=%s industry=%s files=%s summaryScore=%.1f verdict=%s",
            package_id,
            industry,
            [d.filename for d in document_results],
            summary_score,
            package_verdict,
        )

        # Сохраняем в БД (если пользователь авторизован)
        if current_user:
            try:
                package_record = PackageAnalysis(
                    user_id=current_user.id,
                    package_id=package_id,
                    summary_score=summary_score,
                    verdict=package_verdict,
                    documents_json=[doc.dict() for doc in document_results],
                    global_issues=global_issues
                )
                db.add(package_record)
                db.commit()
                logger.info(f"✅ Пакетный анализ сохранен в БД для пользователя {current_user.email}")
            except Exception as db_err:
                db.rollback()
                logger.error(f"Ошибка сохранения пакета в БД: {db_err}")
        else:
            # Для неавторизованных пользователей сохраняем в старую историю
            try:
                item = HistoryItem(
                    id=package_id,
                    createdAt=datetime.utcnow(),
                    kind="package",
                    industry=industry,
                    files=[d.filename for d in document_results],
                    summaryScore=float(summary_score),
                    verdict=str(package_verdict),
                )
                HISTORY.append(item)
                if len(HISTORY) > MAX_HISTORY_ITEMS:
                    del HISTORY[0 : len(HISTORY) - MAX_HISTORY_ITEMS]
            except Exception as hist_err:
                logger.error(f"History append error (package): {hist_err}")

        return PackageAnalysisResponse(
            packageId=package_id,
            summaryScore=summary_score,
            verdict=package_verdict,
            documents=document_results,
            globalIssues=global_issues,
        )

    except Exception as e:
        logger.error(f"Package analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history", response_model=HistoryResponse)
async def get_history(
    limit: int = 50,
    search: Optional[str] = None,  # Поиск по названию файла или содержимому
    industry: Optional[str] = None,  # Фильтр по отрасли
    verdict: Optional[str] = None,  # Фильтр по вердикту (STOP, CAUTION, PARTICIPATE)
    min_score: Optional[int] = None,  # Минимальный score
    max_score: Optional[int] = None,  # Максимальный score
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Возвращает недавнюю историю анализов пользователя из БД с поиском и фильтрацией"""
    
    # Если пользователь не авторизован, возвращаем пустую историю
    # (для обратной совместимости можно вернуть старую in-memory историю)
    if not current_user:
        ordered = sorted(HISTORY, key=lambda h: h.createdAt, reverse=True)
        # Простая фильтрация для in-memory истории
        filtered = ordered
        if industry:
            filtered = [h for h in filtered if h.industry == industry]
        if verdict:
            filtered = [h for h in filtered if h.verdict == verdict]
        if search:
            search_lower = search.lower()
            filtered = [h for h in filtered if any(search_lower in f.lower() for f in h.files)]
        return HistoryResponse(items=filtered[:limit])
    
    # Получаем анализы пользователя с фильтрацией
    query = db.query(Analysis).filter(Analysis.user_id == current_user.id)
    
    # Фильтр по отрасли
    if industry:
        query = query.filter(Analysis.industry == industry)
    
    # Фильтр по вердикту
    if verdict:
        query = query.filter(Analysis.verdict == verdict)
    
    # Фильтр по score
    if min_score is not None:
        query = query.filter(Analysis.score >= min_score)
    if max_score is not None:
        query = query.filter(Analysis.score <= max_score)
    
    # Поиск по названию файла или содержимому
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Analysis.filename.ilike(search_pattern)) |
            (Analysis.summary.ilike(search_pattern))
        )
    
    analyses = query.order_by(Analysis.created_at.desc()).limit(limit).all()
    
    # Получаем пакетные анализы с фильтрацией
    package_query = db.query(PackageAnalysis).filter(
        PackageAnalysis.user_id == current_user.id
    )
    
    # Применяем фильтры к пакетным анализам (если нужно)
    if verdict:
        package_query = package_query.filter(PackageAnalysis.verdict == verdict)
    
    packages = package_query.order_by(PackageAnalysis.created_at.desc()).limit(limit).all()
    
    # Преобразуем в формат HistoryItem
    items = []
    
    for analysis in analyses:
        items.append(HistoryItem(
            id=str(analysis.id),
            createdAt=analysis.created_at,
            kind="single",
            industry=analysis.industry,
            files=[analysis.filename],
            summaryScore=float(analysis.score),
            verdict=analysis.verdict,
            user_decision=analysis.user_decision
        ))
    
    for package in packages:
        files = [doc.get("filename", "unknown") for doc in package.documents_json]
        items.append(HistoryItem(
            id=package.package_id,
            createdAt=package.created_at,
            kind="package",
            industry="UNIVERSAL",
            files=files,
            summaryScore=package.summary_score,
            verdict=package.verdict,
            user_decision=package.user_decision
        ))
    
    # Сортируем по дате
    items.sort(key=lambda x: x.createdAt, reverse=True)
    
    # Обновляем items с user_decision из БД
    for item in items:
        if item.kind == "single":
            analysis = db.query(Analysis).filter(Analysis.id == int(item.id)).first()
            if analysis and analysis.user_decision:
                item.user_decision = analysis.user_decision
        elif item.kind == "package":
            package = db.query(PackageAnalysis).filter(PackageAnalysis.package_id == item.id).first()
            if package and package.user_decision:
                item.user_decision = package.user_decision
    
    return HistoryResponse(items=items[:limit])


@app.put("/api/analysis/{analysis_id}/decision")
async def save_analysis_decision(
    analysis_id: int,
    decision_data: Dict[str, Any],
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Сохраняет решение пользователя по анализу (Decision Layer) и создает Decision Record (ШАГ 11)"""
    try:
        analysis = db.query(Analysis).filter(
            Analysis.id == analysis_id,
            Analysis.user_id == current_user.id
        ).first()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Анализ не найден")
        
        # Сохраняем решение
        fixed_at = datetime.utcnow()
        analysis.user_decision = decision_data
        analysis.decision_at = fixed_at
        db.commit()
        
        # ШАГ 11: Создаем Decision Record из Decision Preview (если доступен)
        if DECISION_RECORD_ENABLED:
            try:
                result_json = analysis.result_json
                decision_preview_data = result_json.get("decision_preview_step5") or result_json.get("decision_preview")
                
                if decision_preview_data:
                    # Парсим Decision Preview из JSON
                    try:
                        decision_preview = DecisionPreview(**decision_preview_data)
                    except Exception as parse_err:
                        logger.warning(f"⚠️ Не удалось распарсить Decision Preview для создания Record: {parse_err}")
                        decision_preview = None
                    
                    if decision_preview:
                        # Извлекаем данные для Decision Record
                        tender_id = extract_tender_id_from_analysis(result_json)
                        tender_object = extract_tender_object_from_analysis(result_json)
                        responsible_person = current_user.name or current_user.email or "Директор"
                        
                        # Преобразуем decision из user_decision в формат Decision Preview
                        user_decision_str = decision_data.get("decision", "").upper()
                        if user_decision_str == "PARTICIPATE":
                            decision_preview.decision = "PARTICIPATE"
                        elif user_decision_str == "DO_NOT_PARTICIPATE":
                            decision_preview.decision = "DO_NOT_PARTICIPATE"
                        elif user_decision_str == "PARTICIPATE_WITH_CONDITIONS":
                            decision_preview.decision = "PARTICIPATE_WITH_CONDITIONS"
                        elif user_decision_str == "POSTPONE":
                            decision_preview.decision = "PARTICIPATE_WITH_CONDITIONS"  # POSTPONE нет в DecisionPreview, используем CONDITIONS
                        
                        # Создаем Decision Record
                        decision_record = convert_preview_to_record(
                            decision_preview=decision_preview,
                            tender_id=tender_id,
                            tender_object=tender_object,
                            responsible_person=responsible_person,
                            fixed_at=fixed_at,
                            analysis_id=analysis_id,
                            user_id=current_user.id,
                        )
                        
                        # Сохраняем в БД
                        db_record = DecisionRecord(
                            tender_id=decision_record.tender_id,
                            tender_object=decision_record.tender_object,
                            decision=decision_record.decision,
                            decision_reasons=decision_record.decision_reasons,
                            management_load_index=decision_record.management_load_index,
                            responsible_person=decision_record.responsible_person,
                            fixed_at=decision_record.fixed_at,
                            analysis_id=decision_record.analysis_id,
                            user_id=decision_record.user_id,
                        )
                        db.add(db_record)
                        db.commit()
                        logger.info(f"✅ Decision Record создан для анализа {analysis_id}")
                    else:
                        logger.warning(f"⚠️ Decision Preview недоступен для анализа {analysis_id}, Record не создан")
                else:
                    logger.warning(f"⚠️ Decision Preview не найден в результате анализа {analysis_id}, Record не создан")
            except Exception as record_err:
                logger.error(f"❌ Ошибка создания Decision Record: {record_err}", exc_info=True)
                # Не прерываем сохранение решения, только логируем ошибку
        
        logger.info(f"✅ Решение сохранено для анализа {analysis_id} пользователя {current_user.email}")
        return {"success": True, "message": "Решение сохранено"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка сохранения решения: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/package/{package_id}/decision")
async def save_package_decision(
    package_id: str,
    decision_data: Dict[str, Any],
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Сохраняет решение пользователя по пакетному анализу (Decision Layer) и создает Decision Record (ШАГ 11)"""
    try:
        package = db.query(PackageAnalysis).filter(
            PackageAnalysis.package_id == package_id,
            PackageAnalysis.user_id == current_user.id
        ).first()
        
        if not package:
            raise HTTPException(status_code=404, detail="Пакетный анализ не найден")
        
        # Сохраняем решение
        fixed_at = datetime.utcnow()
        package.user_decision = decision_data
        package.decision_at = fixed_at
        db.commit()
        
        # ШАГ 11: Создаем Decision Record из Decision Preview (если доступен)
        if DECISION_RECORD_ENABLED:
            try:
                # В пакетном анализе Decision Preview может быть в documents_json[0] или в глобальном результате
                documents_json = package.documents_json or []
                decision_preview_data = None
                
                # Ищем Decision Preview в первом документе пакета
                if documents_json and len(documents_json) > 0:
                    first_doc = documents_json[0]
                    if isinstance(first_doc, dict):
                        result_json = first_doc.get("result") or first_doc
                        decision_preview_data = result_json.get("decision_preview_step5") or result_json.get("decision_preview")
                
                if decision_preview_data:
                    # Парсим Decision Preview из JSON
                    try:
                        decision_preview = DecisionPreview(**decision_preview_data)
                    except Exception as parse_err:
                        logger.warning(f"⚠️ Не удалось распарсить Decision Preview для пакета: {parse_err}")
                        decision_preview = None
                    
                    if decision_preview:
                        # Извлекаем данные для Decision Record (из первого документа)
                        first_doc_result = documents_json[0].get("result") if documents_json else {}
                        tender_id = extract_tender_id_from_analysis(first_doc_result or {})
                        tender_object = extract_tender_object_from_analysis(first_doc_result or {})
                        responsible_person = current_user.name or current_user.email or "Директор"
                        
                        # Преобразуем decision из user_decision в формат Decision Preview
                        user_decision_str = decision_data.get("decision", "").upper()
                        if user_decision_str == "PARTICIPATE":
                            decision_preview.decision = "PARTICIPATE"
                        elif user_decision_str == "DO_NOT_PARTICIPATE":
                            decision_preview.decision = "DO_NOT_PARTICIPATE"
                        elif user_decision_str == "PARTICIPATE_WITH_CONDITIONS":
                            decision_preview.decision = "PARTICIPATE_WITH_CONDITIONS"
                        elif user_decision_str == "POSTPONE":
                            decision_preview.decision = "PARTICIPATE_WITH_CONDITIONS"  # POSTPONE нет в DecisionPreview
                        
                        # Создаем Decision Record
                        decision_record = convert_preview_to_record(
                            decision_preview=decision_preview,
                            tender_id=tender_id,
                            tender_object=tender_object,
                            responsible_person=responsible_person,
                            fixed_at=fixed_at,
                            package_id=package_id,
                            user_id=current_user.id,
                        )
                        
                        # Сохраняем в БД
                        db_record = DecisionRecord(
                            tender_id=decision_record.tender_id,
                            tender_object=decision_record.tender_object,
                            decision=decision_record.decision,
                            decision_reasons=decision_record.decision_reasons,
                            management_load_index=decision_record.management_load_index,
                            responsible_person=decision_record.responsible_person,
                            fixed_at=decision_record.fixed_at,
                            package_id=decision_record.package_id,
                            user_id=decision_record.user_id,
                        )
                        db.add(db_record)
                        db.commit()
                        logger.info(f"✅ Decision Record создан для пакета {package_id}")
                    else:
                        logger.warning(f"⚠️ Decision Preview недоступен для пакета {package_id}, Record не создан")
                else:
                    logger.warning(f"⚠️ Decision Preview не найден в пакете {package_id}, Record не создан")
            except Exception as record_err:
                logger.error(f"❌ Ошибка создания Decision Record для пакета: {record_err}", exc_info=True)
                # Не прерываем сохранение решения, только логируем ошибку
        
        logger.info(f"✅ Решение сохранено для пакета {package_id} пользователя {current_user.email}")
        return {"success": True, "message": "Решение сохранено"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка сохранения решения: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/decision-records")
async def get_decision_records(
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 100,
    offset: int = 0,
):
    """
    Возвращает список Decision Records (Журнал управленческих решений) для текущего пользователя.
    
    ШАГ 11: Канонический список записей с ТОЛЬКО 7 полями.
    """
    try:
        # Получаем Decision Records пользователя
        records = db.query(DecisionRecord).filter(
            DecisionRecord.user_id == current_user.id
        ).order_by(
            DecisionRecord.fixed_at.desc()
        ).limit(limit).offset(offset).all()
        
        # Преобразуем в JSON формат
        records_list = []
        for record in records:
            records_list.append({
                "id": record.id,
                "tender_id": record.tender_id,
                "tender_object": record.tender_object,
                "decision": record.decision,
                "decision_reasons": record.decision_reasons,
                "management_load_index": record.management_load_index,
                "responsible_person": record.responsible_person,
                "fixed_at": record.fixed_at.isoformat() if record.fixed_at else None,
                "analysis_id": record.analysis_id,
                "package_id": record.package_id,
            })
        
        return {
            "records": records_list,
            "total": len(records_list),
            "limit": limit,
            "offset": offset,
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения Decision Records: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/board-pack/{record_id}")
async def export_board_pack(
    record_id: int,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Экспорт Decision Record в Board Pack (PDF).
    
    ШАГ 12: Генерирует канонический Board Pack с 7 секциями:
    1. Executive Summary
    2. Tender Context
    3. Decision
    4. Decision Grounds
    5. Financial Snapshot
    6. Next Steps
    7. Audit Note
    """
    from board_pack_generator import generate_board_pack
    from fastapi.responses import Response
    
    try:
        # Получаем Decision Record
        record = db.query(DecisionRecord).filter(
            DecisionRecord.id == record_id,
            DecisionRecord.user_id == current_user.id
        ).first()
        
        if not record:
            raise HTTPException(status_code=404, detail="Decision Record не найден")
        
        # Преобразуем record в словарь
        record_dict = {
            "id": record.id,
            "tender_id": record.tender_id,
            "tender_object": record.tender_object,
            "decision": record.decision,
            "decision_reasons": record.decision_reasons,
            "management_load_index": record.management_load_index,
            "responsible_person": record.responsible_person,
            "fixed_at": record.fixed_at.isoformat() if record.fixed_at else datetime.now().isoformat(),
        }
        
        # Получаем данные анализа для Financial Snapshot и Tender Context (если доступны)
        analysis_data = None
        if record.analysis_id:
            analysis = db.query(Analysis).filter(Analysis.id == record.analysis_id).first()
            if analysis and analysis.result_json:
                analysis_data = analysis.result_json
        elif record.package_id:
            package = db.query(PackageAnalysis).filter(PackageAnalysis.package_id == record.package_id).first()
            if package and package.documents_json:
                # Берем данные из первого документа пакета
                first_doc = package.documents_json[0] if package.documents_json else {}
                analysis_data = first_doc.get("result") or first_doc
        
        # Генерируем Board Pack
        pdf_buffer = generate_board_pack(record_dict, analysis_data)
        
        filename = f"board_pack_{record.tender_id}_{record.fixed_at.strftime('%Y%m%d')}.pdf"
        return Response(
            content=pdf_buffer.read(),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
        
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail="Board Pack генерация недоступна. Установите reportlab: pip install reportlab"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка генерации Board Pack: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка генерации Board Pack: {str(e)}")


# ФАЗА 5: API endpoints для procurement анализа
@app.get("/api/analysis/{analysis_id}/procurement")
async def get_procurement_analysis(
    analysis_id: int,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получает детальный procurement анализ для указанного анализа.
    
    Возвращает:
    - ProcurementDecisionExtended с вердиктом, ИУН, обоснованием
    - Список блокеров
    - Extended evidence
    - Ссылки на Knowledge Base
    """
    from services.procurement_analysis_service import ProcurementAnalysisService
    
    try:
        # Проверяем доступ к анализу
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            raise HTTPException(status_code=404, detail="Анализ не найден")
        
        if current_user and analysis.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Нет доступа к этому анализу")
        
        # Получаем procurement данные
        service = ProcurementAnalysisService(db)
        procurement_decision = service.get_procurement_analysis(analysis_id)
        
        if not procurement_decision:
            raise HTTPException(status_code=404, detail="Procurement анализ не найден для этого анализа")
        
        blockers = service.get_blockers_for_analysis(analysis_id)
        evidence_extended = service.get_evidence_extended_for_analysis(analysis_id)
        kb_references = service.get_kb_references_for_analysis(analysis_id)
        
        return {
            "decision": {
                "verdict": procurement_decision.verdict,
                "iun": procurement_decision.iun,
                "decision_grounds": procurement_decision.decision_grounds,
                "critical_parameters": procurement_decision.critical_parameters,
                "financial_impact": procurement_decision.financial_impact,
                "blockers": procurement_decision.blockers,
                "red_flags": procurement_decision.red_flags,
                "checklist": procurement_decision.checklist,
                "procurement_law": procurement_decision.procurement_law,
                "nmck": procurement_decision.nmck,
                "deadline_days": procurement_decision.deadline_days,
            },
            "blockers": [
                {
                    "id": b.id,
                    "sub_classification": b.sub_classification,
                    "description": b.description,
                    "legal_basis": b.legal_basis,
                    "is_mitigable": b.is_mitigable,
                    "mitigation_strategy": b.mitigation_strategy,
                    "mitigation_cost": b.mitigation_cost,
                    "mitigation_time_days": b.mitigation_time_days,
                }
                for b in blockers
            ],
            "evidence_extended": [
                {
                    "id": e.id,
                    "evidence_id": e.evidence_id,
                    "source_file": e.source_file,
                    "fact": e.fact,
                    "classification": e.classification,
                    "confidence": e.confidence,
                    "sub_classification": e.sub_classification,
                    "legal_basis": e.legal_basis,
                    "financial_impact_rub": e.financial_impact_rub,
                }
                for e in evidence_extended
            ],
            "kb_references": [
                {
                    "id": kb.id,
                    "kb_path": kb.kb_path,
                    "kb_category": kb.kb_category,
                    "kb_title": kb.kb_title,
                    "relevance_score": kb.relevance_score,
                }
                for kb in kb_references
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения procurement анализа: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/legal/search", response_model=LegalSearchResponse)
async def legal_search(query: str, limit: int = 10):
    """Простейший поиск по заготовленной правовой базе.

    В реальной системе здесь должен быть полнотекстовый поиск/RAG по законам и практике ФАС.
    """

    q = query.lower()
    results: List[LegalSnippet] = []
    for item in LEGAL_SNIPPETS:
        haystack = " ".join(
            [
                item.get("title", ""),
                item.get("summary", ""),
                item.get("lawReference", ""),
                " ".join(item.get("keywords", [])),
            ]
        ).lower()
        if q in haystack:
            results.append(
                LegalSnippet(
                    id=item["id"],
                    category=item["category"],
                    lawReference=item["lawReference"],
                    title=item["title"],
                    summary=item["summary"],
                )
            )
        if len(results) >= limit:
            break

    return LegalSearchResponse(items=results)


# ШАГ 13: Kill Switch endpoints
@app.get("/api/kill-switch/status")
async def get_kill_switch_status():
    """Возвращает текущий статус Kill Switch."""
    if not KILL_SWITCH_ENABLED:
        return {"mode": "NORMAL", "is_active": False, "kill_switch_enabled": False}
    
    try:
        kill_switch = get_kill_switch_manager()
        status = kill_switch.get_status()
        return {
            "mode": status.current_mode.value,
            "is_active": status.is_active,
            "last_activation": status.last_activation.dict() if status.last_activation else None,
            "kill_switch_enabled": True,
        }
    except Exception as e:
        logger.error(f"Ошибка получения статуса Kill Switch: {e}")
        return {"mode": "NORMAL", "is_active": False, "error": str(e)}


@app.post("/api/kill-switch/activate")
async def activate_kill_switch(
    trigger: str,
    reason: str,
    target_mode: str = "SAFE",
    current_user: Optional[User] = Depends(get_current_user),
):
    """Активирует Kill Switch (только для администраторов)."""
    if not KILL_SWITCH_ENABLED:
        raise HTTPException(status_code=503, detail="Kill Switch недоступен")
    
    # Проверка прав администратора (по email)
    if not current_user or current_user.email != "admin@tendershield.pro":
        raise HTTPException(status_code=403, detail="Требуются права администратора")
    
    try:
        from kill_switch_types import KillSwitchTrigger, SystemMode
        
        trigger_enum = KillSwitchTrigger(trigger)
        mode_enum = SystemMode(target_mode)
        
        kill_switch = get_kill_switch_manager()
        activation = kill_switch.activate(
            trigger=trigger_enum,
            reason=reason,
            target_mode=mode_enum,
            activated_by=str(current_user.id) if current_user else None,
        )
        
        return {"success": True, "activation": activation.dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка активации Kill Switch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/kill-switch/deactivate")
async def deactivate_kill_switch(
    reason: str,
    current_user: Optional[User] = Depends(get_current_active_user),
):
    """Деактивирует Kill Switch (только для администраторов)."""
    if not KILL_SWITCH_ENABLED:
        raise HTTPException(status_code=503, detail="Kill Switch недоступен")
    
    # Проверка прав администратора (по email)
    if not current_user or current_user.email != "admin@tendershield.pro":
        raise HTTPException(status_code=403, detail="Требуются права администратора")
    
    try:
        kill_switch = get_kill_switch_manager()
        activation = kill_switch.deactivate(
            reason=reason,
            deactivated_by=str(current_user.id) if current_user else None,
        )
        
        return {"success": True, "activation": activation.dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка деактивации Kill Switch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/legal/explain", response_model=LegalExplainResponse)
async def legal_explain(
    request: LegalExplainRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """
    Объяснение правового вопроса на основе MCP-контента.
    
    ВАЖНО: Этот эндпоинт предоставляет только справочную информацию.
    Он НЕ влияет на Decision Engine, scoring, deal breakers или решения.
    
    Используется для блоков "Что это значит?" в UI.
    """
    try:
        user_id = current_user.id if current_user else None
        
        # Получаем MCP-клиент
        mcp_client = get_mcp_client()
        
        # Вызываем объяснение
        result = await mcp_client.explain_legal(
            question=request.question,
            context=request.context,
            user_id=user_id,
            analysis_id=None  # Можно добавить позже, если нужно
        )
        
        return LegalExplainResponse(
            explanation=result["explanation"],
            sources=result["sources"],
            disclaimer=result["disclaimer"]
        )
    
    except Exception as e:
        logger.error(f"❌ Ошибка в /api/legal/explain: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении объяснения. Попробуйте позже."
        )


@app.post("/api/documents/objection/{analysis_id}", response_model=GeneratedDocumentResponse)
async def generate_objection_letter(
    analysis_id: int,
    extra_context: Optional[str] = Form(None),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """Генерация документа 'Обоснованное несогласие' по результатам анализа.

    Использует failover-LLM. При падении LLM возвращает шаблон на основе issues.
    """
    # 1. Находим анализ
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Анализ не найден")

    # 2. Базовая проверка доступа: если анализ привязан к пользователю и есть current_user — он должен совпадать
    if current_user and analysis.user_id and analysis.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    data = analysis.result_json or {}
    issues = data.get("issues", [])
    red_flags = data.get("redFlags", [])
    passport = data.get("passport", {})

    # 3. Строим промпт для LLM
    issues_text_parts = []
    for idx, issue in enumerate(issues[:10], start=1):
        issues_text_parts.append(
            f"{idx}. {issue.get('title', '')} "
            f"(severity={issue.get('severity', '')}) — {issue.get('description', '')} "
            f"Цитата: {issue.get('quote', '')}"
        )
    issues_text = "\n".join(issues_text_parts) if issues_text_parts else "Нет явных нарушений, но требуется общее обоснование."

    red_flags_parts = []
    for idx, rf in enumerate(red_flags[:10], start=1):
        red_flags_parts.append(
            f"{idx}. [{rf.get('code', '')}] {rf.get('title', '')} "
            f"(severity={rf.get('severity', '')}) — {rf.get('explanation', '')}"
        )
    red_flags_text = "\n".join(red_flags_parts) if red_flags_parts else "Красных флагов не зафиксировано."

    summary = data.get("summary", "")
    nmck = passport.get("nmck", "")
    fz = passport.get("fz", "")
    region = passport.get("region", "")

    user_context = extra_context or ""

    prompt = f"""
Ты — опытный юрист по закупкам. Сгенерируй проект документа "Обоснованное несогласие"
по результатам анализа тендерной документации.

Формат: официальное письмо в адрес заказчика с ссылками на нормативные акты и
конкретные формулировки документации.

Данные по закупке:
- Краткое описание: {summary}
- НМЦК: {nmck}
- Регион: {region}
- Режим закона: {fz}

Нарушения и риски (issues):
{issues_text}

Красные флаги:
{red_flags_text}

Дополнительный контекст от пользователя (если есть):
{user_context}

Требования к результату:
- Строгий деловой стиль.
- Структура: шапка, вводная, перечисление нарушений по пунктам, ссылки на нормы закона,
  формулировка требований (исправить ТЗ / продлить сроки / изменить условия обеспечения и т.п.),
  заключительная часть.
- Не используй маркдаун и JSON, только чистый текст письма.
"""

    doc_content: str
    try:
        # Используем безопасный вызов LLM без JSON-формата
        doc_content = _safe_ollama_invoke(prompt, format_json=False)
        if not doc_content or len(doc_content.strip()) < 50:
            raise ValueError("Слишком короткий ответ от LLM")
    except HTTPException:
        # Пробрасываем 503 и т.п. как есть
        raise
    except Exception as e:
        # Fallback: формируем шаблон на основе issues без LLM
        logger.error(f"Ошибка генерации 'Обоснованного несогласия' через LLM: {e}")
        lines = []
        lines.append("Обоснованное несогласие с условиями тендерной документации")
        lines.append("")
        lines.append(f"По результатам анализа документации по закупке ({summary}) выявлены следующие потенциальные нарушения и риски:")
        lines.append("")
        if issues_text_parts:
            lines.extend(issues_text_parts)
        else:
            lines.append("- Существенных формальных нарушений не выявлено, однако просим уточнить отдельные положения документации.")
        lines.append("")
        lines.append("Просим заказчика рассмотреть изложенные замечания, при необходимости скорректировать документацию и дать официальный ответ в установленные сроки.")
        doc_content = "\n".join(lines)

    # 4. Сохраняем документ в БД
    generated = GeneratedDocument(
        analysis_id=analysis.id,
        doc_type="OBJECTION_LETTER",
        content=doc_content,
    )
    db.add(generated)
    db.commit()
    db.refresh(generated)

    return GeneratedDocumentResponse(
        id=generated.id,
        analysis_id=generated.analysis_id,
        type=generated.doc_type,
        content=generated.content,
        created_at=generated.created_at,
    )

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        # Используем безопасный вызов с переключением моделей (без JSON формата для чата)
        response = _safe_ollama_invoke(req.message, format_json=False)
        return {"response": response}
    except HTTPException:
        # Пробрасываем HTTPException как есть (это наша ошибка 503)
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {"response": "Ошибка чата."}


# --- ЭНДПОИНТЫ ЭКСПОРТА ---
@app.get("/api/export/pdf/{analysis_id}")
async def export_analysis_pdf(
    analysis_id: int,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Экспорт анализа в PDF"""
    from pdf_export import export_analysis_to_pdf
    from fastapi.responses import Response
    
    # Проверяем, что анализ существует
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Анализ не найден")
    
    # КОНТЕКСТНЫЙ ТРИГГЕР #3: Если демо-пользователь пытается экспортировать
    # Для демо-анализов блокируем экспорт как для полностью неавторизованного пользователя,
    # так и для временного тестового пользователя (user_id может быть None).
    if analysis.is_demo and (not current_user or analysis.user_id is None):
        raise HTTPException(
            status_code=403,
            detail="PDF export available after registration",
            headers={"X-Suggest-Registration": "true"}
        )
    
    # Проверяем, что анализ принадлежит пользователю (если авторизован)
    if current_user and analysis.user_id and analysis.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    try:
        pdf_buffer = export_analysis_to_pdf(analysis_id, db)
        if not pdf_buffer:
            raise HTTPException(status_code=500, detail="Ошибка генерации PDF")
        
        filename = f"analysis_{analysis_id}_{analysis.filename}.pdf"
        return Response(
            content=pdf_buffer.read(),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail="Экспорт в PDF недоступен. Установите reportlab: pip install reportlab"
        )
    except Exception as e:
        logger.error(f"Ошибка экспорта в PDF: {e}")
        raise HTTPException(status_code=500, detail="Ошибка генерации PDF")


@app.post("/api/export/pdf")
async def export_analysis_pdf_direct(
    analysis_data: dict,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Экспорт анализа в PDF из переданных данных (для неавторизованных пользователей)"""
    from pdf_export import generate_pdf_report
    from fastapi.responses import Response
    
    try:
        pdf_buffer = generate_pdf_report(analysis_data)
        filename = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        return Response(
            content=pdf_buffer.read(),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail="Экспорт в PDF недоступен. Установите reportlab: pip install reportlab"
        )
    except Exception as e:
        logger.error(f"Ошибка экспорта в PDF: {e}")
        raise HTTPException(status_code=500, detail="Ошибка генерации PDF")


@app.get("/api/export/excel/{analysis_id}")
async def export_analysis_excel(
    analysis_id: int,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Экспорт анализа в Excel"""
    from excel_export import generate_excel_report
    from fastapi.responses import Response
    
    # Проверяем, что анализ существует
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Анализ не найден")
    
    # КОНТЕКСТНЫЙ ТРИГГЕР #3: Если демо-пользователь пытается экспортировать
    if analysis.is_demo and not current_user:
        raise HTTPException(
            status_code=403,
            detail="Excel export available after registration",
            headers={"X-Suggest-Registration": "true"}
        )
    
    # Проверяем, что анализ принадлежит пользователю (если авторизован)
    if current_user and analysis.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    try:
        # Подготавливаем данные для экспорта
        analysis_data = analysis.result_json.copy()
        analysis_data["filename"] = analysis.filename
        analysis_data["industry"] = analysis.industry
        analysis_data["created_at"] = analysis.created_at
        
        excel_buffer = generate_excel_report(analysis_data)
        filename = f"analysis_{analysis_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return Response(
            content=excel_buffer.read(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail="Экспорт в Excel недоступен. Установите openpyxl: pip install openpyxl"
        )
    except Exception as e:
        logger.error(f"Ошибка экспорта в Excel: {e}")
        raise HTTPException(status_code=500, detail="Ошибка генерации Excel")


@app.post("/api/export/excel")
async def export_analysis_excel_direct(
    analysis_data: dict,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Экспорт анализа в Excel из переданных данных"""
    from excel_export import generate_excel_report
    from fastapi.responses import Response
    
    try:
        excel_buffer = generate_excel_report(analysis_data)
        filename = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return Response(
            content=excel_buffer.read(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail="Экспорт в Excel недоступен. Установите openpyxl: pip install openpyxl"
        )
    except Exception as e:
        logger.error(f"Ошибка экспорта в Excel: {e}")
        raise HTTPException(status_code=500, detail="Ошибка генерации Excel")


# --- АНАЛИТИКА И МЕТРИКИ ---

@app.get("/api/analytics/user/{user_id}")
async def get_user_analytics(
    user_id: int,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить аналитику для пользователя"""
    from analytics import AnalyticsService
    
    # Проверяем доступ (только свой профиль или админ)
    if current_user.id != user_id and current_user.email != "admin@tendershield.pro":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    analytics = AnalyticsService(db)
    return analytics.get_user_stats(user_id)


@app.get("/api/analytics/system")
async def get_system_analytics(
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить системную аналитику (только для админов)"""
    from analytics import AnalyticsService
    
    # Проверяем что пользователь админ
    if not current_user or current_user.email != "admin@tendershield.pro":
        raise HTTPException(status_code=403, detail="Требуются права администратора")
    
    analytics = AnalyticsService(db)
    return analytics.get_system_stats()


@app.get("/api/analytics/timeline")
async def get_analytics_timeline(
    days: int = 30,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить временную линию анализов"""
    from analytics import AnalyticsService
    
    user_id = current_user.id if current_user else None
    analytics = AnalyticsService(db)
    return analytics.get_analyses_timeline(user_id, days)


@app.get("/api/analytics/popular-industries")
async def get_popular_industries(
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """Получить популярные отрасли (публичный эндпоинт)"""
    from analytics import AnalyticsService
    
    analytics = AnalyticsService(db)
    return analytics.get_popular_industries(limit)


@app.get("/api/analytics/average-scores")
async def get_average_scores(
    db: Session = Depends(get_db)
):
    """Получить средние оценки по отраслям (публичный эндпоинт)"""
    from analytics import AnalyticsService
    
    analytics = AnalyticsService(db)
    return analytics.get_average_scores()


# --- УВЕДОМЛЕНИЯ ---

@app.get("/api/notifications")
async def get_notifications(
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить уведомления для текущего пользователя"""
    from notifications import NotificationService
    
    if not current_user:
        return []
    
    notification_service = NotificationService(db)
    return notification_service.get_all_notifications(current_user.id)


@app.get("/api/analytics/export/csv")
async def export_analytics_csv(
    days: int = 30,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Экспорт аналитики в CSV"""
    from analytics import AnalyticsService
    from analytics_export import export_analytics_to_csv
    from fastapi.responses import Response
    
    user_id = current_user.id if current_user else None
    analytics = AnalyticsService(db)
    
    try:
        csv_buffer = export_analytics_to_csv(analytics, user_id, days)
        filename = f"analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return Response(
            content=csv_buffer.read(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        logger.error(f"Ошибка экспорта в CSV: {e}")
        raise HTTPException(status_code=500, detail="Ошибка генерации CSV")


@app.get("/api/analytics/export/excel")
async def export_analytics_excel(
    days: int = 30,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Экспорт аналитики в Excel"""
    from analytics import AnalyticsService
    from analytics_export import export_analytics_to_excel
    from fastapi.responses import Response
    
    user_id = current_user.id if current_user else None
    analytics = AnalyticsService(db)
    
    try:
        excel_buffer = export_analytics_to_excel(analytics, user_id, days)
        filename = f"analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return Response(
            content=excel_buffer.read(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Экспорт в Excel недоступен. Установите openpyxl: pip install openpyxl"
        )
    except Exception as e:
        logger.error(f"Ошибка экспорта в Excel: {e}")
        raise HTTPException(status_code=500, detail="Ошибка генерации Excel")


# --- ЭНДПОИНТЫ ДЛЯ ДЕМО-РЕЖИМА ---
@app.get("/api/demo/session/{session_id}")
async def get_demo_session(session_id: str, db: Session = Depends(get_db)):
    """Получение информации о демо-сессии"""
    demo = db.query(DemoSession).filter(DemoSession.id == session_id).first()
    
    if not demo:
        # Создаем новую сессию
        demo = DemoSession(
            id=session_id,
            device_fingerprint="unknown"
        )
        db.add(demo)
        db.commit()
        db.refresh(demo)
    
    # Вычисляем оставшиеся часы
    remaining_hours = 24
    if demo.last_analysis_at:
        hours_passed = (datetime.utcnow() - demo.last_analysis_at).total_seconds() / 3600
        if hours_passed < 24:
            remaining_hours = int(24 - hours_passed)
        else:
            # Сброс счетчика
            demo.analyses_count = 0
            db.commit()
    
    return {
        "id": demo.id,
        "analyses_count": demo.analyses_count,
        "remaining_analyses": max(0, 3 - demo.analyses_count),
        "remaining_hours": remaining_hours,
        "last_analysis_at": demo.last_analysis_at.isoformat() if demo.last_analysis_at else None,
        "created_at": demo.created_at.isoformat()
    }


# --- АСИНХРОННЫЙ АНАЛИЗ ---

# Директория для временного хранения файлов анализа
ANALYSIS_JOBS_DIR = os.path.join(os.getcwd(), "analysis_jobs")
os.makedirs(ANALYSIS_JOBS_DIR, exist_ok=True)


@app.post("/api/analysis/start", response_model=AnalysisJobStartResponse, status_code=status.HTTP_201_CREATED)
async def start_analysis(
    request: Request,
    file: Optional[UploadFile] = File(None),
    files: Optional[List[UploadFile]] = File(None),
    industry: str = Form("UNIVERSAL"),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Запускает асинхронный анализ документов.
    Возвращает analysis_id сразу, анализ выполняется в фоне.
    """
    from utils.file_validator import validate_file, validate_file_size
    
    # Определяем режим (single или package)
    if file and files:
        raise HTTPException(status_code=400, detail="Укажите либо один файл, либо несколько файлов")
    
    if not file and not files:
        raise HTTPException(status_code=400, detail="Не переданы файлы для анализа")
    
    mode = "single" if file else "package"
    upload_files = [file] if file else (files or [])
    
    # Проверяем DEMO-режим
    is_demo = current_user is None
    demo_session = None
    
    if is_demo:
        demo_session = get_or_create_demo_session(request, db)
        if demo_session:
            can_analyze, reason = demo_session.can_analyze()
            if not can_analyze:
                raise HTTPException(
                    status_code=429,
                    detail=reason,
                    headers={"X-Demo-Limit": "true", "X-Suggest-Registration": "true"},
                )
            demo_session.increment_analyses()
            db.commit()
    
    # Валидация файлов
    for upload in upload_files:
        is_valid, error_msg = validate_file(upload)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Ошибка валидации файла {upload.filename}: {error_msg}")
        
        # Проверка размера
        file_size_ok, size_error = validate_file_size(upload)
        if not file_size_ok:
            raise HTTPException(status_code=400, detail=size_error)
    
    # Создаём задачу анализа
    analysis_id = str(uuid.uuid4())
    job = AnalysisJob(
        id=analysis_id,
        user_id=current_user.id if current_user else None,
        session_id=demo_session.id if demo_session else None,
        status="queued",
        progress=0,
        stage="queued",
        mode=mode,
        filename=upload_files[0].filename if mode == "single" else None,
        filenames=[f.filename for f in upload_files] if mode == "package" else None,
        industry=industry,
    )
    db.add(job)
    db.commit()
    
    # Сохраняем файлы во временное хранилище
    job_dir = os.path.join(ANALYSIS_JOBS_DIR, analysis_id)
    os.makedirs(job_dir, exist_ok=True)
    
    saved_files = []
    for idx, upload in enumerate(upload_files):
        file_path = os.path.join(job_dir, upload.filename or f"file_{idx}")
        with open(file_path, "wb") as f:
            content = await upload.read()
            f.write(content)
        saved_files.append(file_path)
        # Сбрасываем позицию для возможного повторного чтения
        await upload.seek(0)
    
    # Запускаем анализ в фоне
    background_tasks.add_task(process_analysis_job, analysis_id, saved_files, mode, industry, db)
    
    logger.info(f"✅ Задача анализа создана: {analysis_id}, режим: {mode}, файлов: {len(upload_files)}")
    
    return AnalysisJobStartResponse(
        analysis_id=analysis_id,
        status="queued",
        message="Анализ запущен. Используйте GET /api/analysis/status/:id для получения статуса."
    )


@app.get("/api/analysis/status/{analysis_id}", response_model=AnalysisJobStatusResponse)
async def get_analysis_status(
    request: Request,
    analysis_id: str,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """
    Получает статус задачи анализа.
    """
    job = db.query(AnalysisJob).filter(AnalysisJob.id == analysis_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Задача анализа не найдена")
    
    # Проверяем доступ (пользователь может видеть только свои задачи или demo-задачи)
    if current_user:
        if job.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Нет доступа к этой задаче")
    else:
        # Для demo проверяем session_id через request
        demo_session = get_or_create_demo_session(request, db)
        if demo_session and job.session_id != demo_session.id:
            raise HTTPException(status_code=403, detail="Нет доступа к этой задаче")
    
    return AnalysisJobStatusResponse(
        analysis_id=job.id,
        status=job.status,
        progress=job.progress,
        stage=job.stage,
        result=job.result_json if job.status == "done" else None,
        error_message=job.error_message if job.status == "error" else None,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)
