from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
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

# --- ПРОСТАЯ ЗАЩИТА ОТ МНОЖЕСТВЕННЫХ РЕГИСТРАЦИЙ С ОДНОГО IP ---
# Важно: это in-memory защита на уровне процесса. При перезапуске backend
# счётчики обнуляются. Для production-регламента можно будет перенести
# эти лимиты в БД / Redis.
IP_REGISTRATION_LOG: Dict[str, List[datetime]] = {}
MAX_TRIAL_ACCOUNTS_PER_IP = 2       # максимум 2 триала на IP
TRIAL_IP_WINDOW_DAYS = 30           # считаем за последние 30 дней

# --- КОНФИГУРАЦИЯ МОДЕЛЕЙ ДЛЯ FAILOVER ---
# Список моделей по приоритету: от быстрой к надежной
OLLAMA_MODELS = [
    "qwen2.5-coder:7b",      # Основная (установлена, хорошее качество)
    "mistral:7b-instruct-q4_K_M",  # Резерв 1 (установлена, надежная)
    "qwen2.5:0.5b",          # Резерв 2 (если установлена)
]

# --- ИМПОРТЫ ---
from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader
from langchain_ollama import ChatOllama

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
)
from rag_engine import get_law_snippets
from auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_optional_user,
    get_password_hash,
    get_user_by_email
)
import schemas
from schemas import UserCreate, UserResponse, UserLogin, Token, AnalysisResponse, CompanyProfile
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from fastapi import Depends, status
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
    
    usage_response = schemas.UsageResponse(
        analyses_count=analyses_count,
        packages_count=packages_count,
        analyses_limit=analyses_limit,
        package_limit=package_limit,
        analyses_remaining=max(0, analyses_limit - analyses_count) if analyses_limit > 0 else -1,
        packages_remaining=max(0, package_limit - packages_count) if package_limit > 0 else -1
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
    user = authenticate_user(db, form_data.email, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return schemas.Token(
        access_token=access_token,
        token_type="bearer"
    )


@app.get("/api/auth/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Получение информации о текущем пользователе"""
    return current_user


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
    """Находит цену, если ИИ ошибся"""
    matches = re.findall(r'(\d[\d\s]*[.,]?\d*)\s?(?:руб|₽|RUB)', text, re.IGNORECASE)
    if matches:
        try:
            prices = [float(m.replace(' ', '').replace(',', '.').strip()) for m in matches if m.strip()]
            if prices:
                return f"{max(prices):,.2f} ₽".replace(',', ' ').replace('.', ',')
        except Exception:
            pass
    return "Не найдено"


def extract_dates_regex(text):
    """Находит дедлайны"""
    matches = re.findall(r'\d{2}[./-]\d{2}[./-]\d{4}', text)
    return matches[-1] if matches else "См. документацию"


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
    - разные режимы закона (44-ФЗ / 223-ФЗ);
    - разные условия обеспечения;
    - наличие критичных рисков внутри отдельных документов.
    """

    issues: List[dict] = []

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
            issues.append(
                {
                    "title": "Несоответствие НМЦК между документами пакета",
                    "severity": severity,
                    "description": "В разных документах указаны разные значения НМЦК. "
                    "Проверьте ТЗ, проект договора и протоколы.",
                    "details": {
                        "documents": doc_list,
                        "min": min_v,
                        "max": max_v,
                    },
                }
            )

    # --- 2. Режим закона (44-ФЗ / 223-ФЗ) ---
    fz_map = {}
    for doc in documents:
        passport = doc.passport or {}
        fz_raw = str(passport.get("fz", "")).strip()
        if fz_raw:
            key = fz_raw.upper()
            fz_map.setdefault(key, []).append(doc.filename)

    if len(fz_map.keys()) > 1:
        issues.append(
            {
                "title": "Разные режимы закона в документах",
                "severity": "HIGH",
                "description": "В разных документах пакета указаны разные режимы (44-ФЗ/223-ФЗ и т.п.)."
                " Это может указывать на ошибку в документации.",
                "details": {k: v for k, v in fz_map.items()},
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
        issues.append(
            {
                "title": "Разные условия обеспечения в документах",
                "severity": "MEDIUM",
                "description": "Условия обеспечения заявки/контракта различаются между документами пакета.",
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
        issues.append(
            {
                "title": "Критичные риски внутри документов пакета",
                "severity": "HIGH",
                "description": "В одном или нескольких документах найдены риски уровня HIGH.",
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
    1. qwen2.5-coder:7b (основная, хорошее качество)
    2. mistral:7b-instruct-q4_K_M (резерв, надежная)
    3. qwen2.5:0.5b (резерв, если установлена)
    
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
                "timeout": 180,  # 3 минуты таймаут (уменьшено для быстрой обратной связи)
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

    # 1. Чтение (Всеядный ридер)
    text = ""
    loader = None
    try:
        ext = (os.path.splitext(str(filename or ""))[1] or "").lower()

        if ext == ".pdf":
            loader = PyMuPDFLoader(temp_path)
            docs = loader.load()
            text = "\n".join([d.page_content for d in docs])
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
            # Пробуем Docx2txt; при ошибке — читаем как простой текст
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
                from openpyxl import load_workbook
                wb = load_workbook(temp_path, data_only=True)
                chunks = []
                for ws in wb.worksheets:
                    chunks.append(f"Лист: {ws.title}")
                    row_count = 0
                    for row in ws.iter_rows(values_only=True):
                        row_count += 1
                        if row > 500:
                            chunks.append("... (дальнейшие строки опущены)")
                            break
                        cells = [str(v) for v in row if v not in (None, "")]
                        if cells:
                            chunks.append(" | ".join(cells))
                text = "\n".join(chunks)
            except Exception as e:
                logger.error(f"Ошибка чтения Excel-файла: {e}")
                raise HTTPException(status_code=400, detail="Файл Excel не читается")

        else:
            # Текстовые файлы и все прочие, которые можно открыть как текст
            with open(temp_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
    except Exception as e:
        logger.error(f"Ошибка чтения: {e}")
        if loader:
            try:
                del loader
            except Exception:
                pass
        raise HTTPException(status_code=400, detail="Файл не читается")

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

    # 3b. МЕГА-ПРОМПТ (Паспорт, Риски, Спецификация + RAG-контекст)
    prompt = f"""
    Ты — эксперт по тендерам. Проанализируй документ и ответь на вопросы. Пиши для директора, не для юриста.
    Специфика: {industry_context}
    
    {industry_checks}

    {("Выдержки из законов:\n" + law_context_block[:2000]) if law_context_block else ""}

    ОТВЕТЬ НА ВОПРОСЫ (если нет данных — "Не указано"):
    1. Заказчик (ИНН, ОГРН, адрес)
    2. Предмет закупки
    3. НМЦК (цена)
    4. Сроки подачи заявок
    5. Сроки исполнения
    6. Требования к участникам (лицензии, опыт)
    7. Обеспечения (заявка/контракт)
    8. Условия оплаты
    9. Критерии оценки
    10. Противоречия в документах
    11. Штрафы и санкции
    12. Гарантии и сервис
    13. Доп. требования (поставка, монтаж)
    14. Риски отмены/изменения
    15. Требования к документам
    16. Финансовые требования
    17. Конфиденциальность
    18. История заказчика (если есть)
    19. Ограничения по субподряду
    20. Конфликты интересов
    21. Признаки дискриминации
    22. Условия расторжения
    23. Уровень конкуренции
    24. Страхование
    25. Доп. риски участия

    ВЕРНИ JSON (только JSON, без комментариев):
    {{
        "summary": "Суть закупки (1-2 предложения)",
        "score": число_0_100,
        "passport": {{"nmck": "цена", "region": "место", "fz": "44-ФЗ/223-ФЗ", "deadlineApp": "дата", "bidSecurity": "обеспечение заявки", "contractSecurity": "обеспечение контракта"}},
        "issues": [{{"title": "риск", "severity": "HIGH/MEDIUM/LOW", "description": "почему опасно", "quote": "цитата", "lawReference": "статья"}}],
        "specs": [{{"name": "товар", "qty": "количество", "details": "характеристики"}}],
        "redFlags": [{{"code": "IT_BRAND_ONLY/TIME_UNREAL/OTHER", "title": "название", "severity": "HIGH/MEDIUM/LOW", "lawReference": "статья", "explanation": "что нарушено", "quote": "цитата"}}],
        "financialSummary": {{"nmck": "НМЦК", "advance": "аванс", "bidSecurity": "обеспечение заявки", "contractSecurity": "обеспечение контракта", "paymentTerms": "условия оплаты"}},
        "timelineSummary": {{"deadlineApp": "срок подачи", "deadlineExecution": "срок исполнения", "timelineRisk": "оценка сроков"}},
        "participantRequirements": {{"licenses": ["лицензии"], "experienceRequired": "требования к опыту", "overallBarrier": "HIGH/MEDIUM/LOW"}},
        "summaryBlocks": {{"money": {{"status": "GREEN/YELLOW/RED", "comment": "вывод"}}, "time": {{"status": "GREEN/YELLOW/RED", "comment": "вывод"}}, "barriers": {{"status": "GREEN/YELLOW/RED", "comment": "вывод"}}, "traps": {{"status": "GREEN/YELLOW/RED", "comment": "вывод"}}}},
        "actions": [{{"type": "ASK_CLARIFICATION/PARTICIPATE/SKIP", "priority": 1, "text": "действие"}}],
        "structuredAnswers": {{
            "customer": "ответ на вопрос 1",
            "subject": "ответ на вопрос 2",
            "nmck": "ответ на вопрос 3",
            "applicationDeadline": "ответ на вопрос 4",
            "executionDeadline": "ответ на вопрос 5",
            "participantRequirements": "ответ на вопрос 6",
            "securityAmounts": "ответ на вопрос 7",
            "paymentTerms": "ответ на вопрос 8",
            "evaluationCriteria": "ответ на вопрос 9",
            "contradictions": "ответ на вопрос 10",
            "penalties": "ответ на вопрос 11",
            "guarantees": "ответ на вопрос 12",
            "additionalRequirements": "ответ на вопрос 13",
            "tenderRisks": "ответ на вопрос 14",
            "documentationRequirements": "ответ на вопрос 15",
            "financialRequirements": "ответ на вопрос 16",
            "confidentiality": "ответ на вопрос 17",
            "customerHistory": "ответ на вопрос 18",
            "subcontractingLimits": "ответ на вопрос 19",
            "conflictsOfInterest": "ответ на вопрос 20",
            "discriminationSigns": "ответ на вопрос 21",
            "terminationConditions": "ответ на вопрос 22",
            "competitionLevel": "ответ на вопрос 23",
            "insuranceRequirements": "ответ на вопрос 24",
            "additionalRisks": "ответ на вопрос 25"
        }}
    }}

    Текст документа (первые 15000 символов):
    {text[:15000]}
    """

    logger.info(f"Отправка в Ollama с failover... (длина промпта: {len(prompt)} символов)")
    import time
    start_time = time.time()
    response_json = None
    try:
        # Используем безопасный вызов с переключением моделей
        response_json = _safe_ollama_invoke(prompt)
        elapsed = time.time() - start_time
        if not response_json:
            raise ValueError("Пустой ответ от Ollama")
        logger.info(f"✅ Получен ответ от Ollama за {elapsed:.1f}с (длина: {len(response_json)} символов)")
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
    regex_price = extract_price_regex(text[:5000])
    final_nmck = ai_data.get("passport", {}).get("nmck")
    if not final_nmck or "Ищи" in str(final_nmck):
        final_nmck = regex_price

    score = int(ai_data.get("score", 50) or 50)
    verdict = "STOP" if score < 40 else ("CAUTION" if score < 80 else "PARTICIPATE")

    # Финальный ответ
    issues: List[dict] = list(ai_data.get("issues", []))

    # Нормализация ключей law_reference -> lawReference для единообразия
    for issue in issues:
        if "law_reference" in issue and "lawReference" not in issue:
            issue["lawReference"] = issue.get("law_reference")

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

    # --- 5c. Deal Breakers (стоп-факторы) ---
    def extract_deal_breakers(
        issues_list: List[dict],
        red_flags_list: List[dict],
        participant_req: dict,
        score_value: int,
    ) -> List[dict]:
        """
        Формирует список dealBreakers на основе:
        - красных флагов HIGH-серьёзности,
        - экстремально низкого score,
        - барьеров участия.
        Формат элемента:
        {
            "title": str,
            "quote": str,
            "essence": str,
            "status": str,
            "lawReference": Optional[str],
            "action": {
                "type": "SKIP" | "FILE_FAS_COMPLAINT" | "ASK_CLARIFICATION",
                "buttonLabel": str,
                "justification": str,
            }
        }
        """
        deal_breakers: List[dict] = []

        # 1. Красные флаги высокой серьёзности
        for rf in red_flags_list:
            if str(rf.get("severity", "")).upper() == "HIGH":
                title = rf.get("title") or "Критический красный флаг"
                law_ref = rf.get("lawReference")
                quote = rf.get("quote") or ""
                explanation = rf.get("explanation") or ""
                status = f"Высокий правовой риск{f' ({law_ref})' if law_ref else ''}"
                action_type = "SKIP"
                button_label = "🟥 НЕ УЧАСТВОВАТЬ"
                justification = "Риск слишком высок по сравнению с потенциальной выгодой"
                deal_breakers.append(
                    {
                        "title": title,
                        "quote": quote,
                        "essence": explanation or "Критический риск, который может привести к серьёзным потерям.",
                        "status": status,
                        "lawReference": law_ref,
                        "action": {
                            "type": action_type,
                            "buttonLabel": button_label,
                            "justification": justification,
                        },
                    }
                )

        # 2. Очень низкий score (< 30) как общий стоп-фактор
        if score_value < 30:
            deal_breakers.append(
                {
                    "title": "Очень высокий суммарный риск по тендеру",
                    "quote": "",
                    "essence": "Индекс безопасности ниже 30 из 100. В документе много серьёзных рисков по деньгам, срокам и требованиям.",
                    "status": "STOP",
                    "lawReference": None,
                    "action": {
                        "type": "SKIP",
                        "buttonLabel": "🟥 НЕ УЧАСТВОВАТЬ",
                        "justification": "Слишком большое количество критических рисков по сравнению с потенциальной выгодой.",
                    },
                }
            )

        # 3. Барьеры участия (например, высокий overallBarrier)
        overall_barrier = str(participant_req.get("overallBarrier", "")).upper()
        if overall_barrier == "HIGH":
            deal_breakers.append(
                {
                    "title": "Высокие барьеры для участия",
                    "quote": "",
                    "essence": "Требуются лицензии, опыт или статус, которые трудно или невозможно быстро получить. Участие может быть формально невозможно или сильно рискованно.",
                    "status": "HIGH BARRIER",
                    "lawReference": None,
                    "action": {
                        "type": "ASK_CLARIFICATION",
                        "buttonLabel": "🔵 Запросить разъяснения",
                        "justification": "Нужно уточнить у заказчика, допускается ли участие без всех перечисленных требований.",
                    },
                }
            )

        # Ограничиваем список 5 элементами, чтобы не перегружать интерфейс
        if len(deal_breakers) > 5:
            deal_breakers = deal_breakers[:5]

        return deal_breakers

    red_flags_list = list(ai_data.get("redFlags", []))
    deal_breakers = extract_deal_breakers(issues, red_flags_list, participant_requirements, score)

    # --- 5d. Финансовый удар в рублях (расширение financialSummary) ---
    financial_summary = ai_data.get("financialSummary", {}) or {}
    try:
        # Пытаемся извлечь НМЦК как число из строки
        nmck_raw = str(final_nmck or "").replace(" ", "").replace("₽", "").replace(",", ".")
        nmck_value = None
        for token in nmck_raw.split():
            try:
                nmck_value = float(token)
                break
            except ValueError:
                continue

        # Простейшие эвристики: если в тексте есть штраф "0.1% в день" или похожие формулировки
        text_lower = text.lower()
        daily_penalty_percent = 0.0
        if "% в день" in text_lower or "%/день" in text_lower:
            # Ищем число перед "% в день"
            import re
            m = re.search(r"(\d+[.,]?\d*)\s*% ?в ?день", text_lower)
            if not m:
                m = re.search(r"(\d+[.,]?\d*)\s*%/?день", text_lower)
            if m:
                try:
                    daily_penalty_percent = float(m.group(1).replace(",", "."))
                except ValueError:
                    daily_penalty_percent = 0.0

        penalty_risk_rubles = None
        if nmck_value and daily_penalty_percent > 0:
            penalty_risk_rubles = nmck_value * daily_penalty_percent / 100.0

        # Кассовый разрыв — грубая эвристика: ищем упоминание 30/60 дней
        working_capital_needed = None
        if nmck_value:
            if "30 дней" in text_lower:
                working_capital_needed = nmck_value * 0.3
            elif "60 дней" in text_lower:
                working_capital_needed = nmck_value * 0.6

        guarantee_amount = None
        guarantee_text = str(financial_summary.get("contractSecurity") or ai_data.get("passport", {}).get("contractSecurity") or "")
        if "%" in guarantee_text and nmck_value:
            import re
            gm = re.search(r"(\d+[.,]?\d*)\s*%", guarantee_text)
            if gm:
                try:
                    perc = float(gm.group(1).replace(",", "."))
                    guarantee_amount = nmck_value * perc / 100.0
                except ValueError:
                    guarantee_amount = None

        # Формируем человеко-понятные строки
        def fmt_rub(v: float) -> str:
            return f"{int(v):,} ₽".replace(",", " ")

        if penalty_risk_rubles is not None:
            financial_summary["penaltyRiskRubles"] = fmt_rub(penalty_risk_rubles)
        if working_capital_needed is not None:
            financial_summary["workingCapitalNeeded"] = fmt_rub(working_capital_needed)
        if guarantee_amount is not None:
            financial_summary["guaranteeAmount"] = fmt_rub(guarantee_amount)
    except Exception as fin_err:
        logger.warning(f"Не удалось оценить финансовый удар в рублях: {fin_err}")

    result = {
        "score": score,
        "summary": ai_data.get("summary", "Нет описания"),
        "verdict": verdict,
        "passport": {
            "nmck": final_nmck,
            "region": ai_data.get("passport", {}).get("region", "РФ"),
            "fz": ai_data.get("passport", {}).get("fz", "44-ФЗ"),
            "deadlineApp": ai_data.get("passport", {}).get("deadlineApp", extract_dates_regex(text[:3000])),
            "guarantee": ai_data.get("passport", {}).get("guarantee", "Не указано"),
            "bidSecurity": ai_data.get("passport", {}).get("bidSecurity"),
            "contractSecurity": ai_data.get("passport", {}).get("contractSecurity"),
        },
        "issues": issues,
        "specs": ai_data.get("specs", []),  # <-- спецификация
        "redFlags": red_flags_list,
        "financialSummary": financial_summary,
        "timelineSummary": ai_data.get("timelineSummary", {}),
        "participantRequirements": participant_requirements,
        "summaryBlocks": summary_blocks,
        "actions": ai_data.get("actions", []),
        "dealBreakers": deal_breakers,
        "structuredAnswers": ai_data.get("structuredAnswers", {}),  # <-- структурированные ответы на 25 вопросов
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
    from utils.file_validator import validate_file, validate_file_size

    # --- Сначала определяем режим (авторизованный / демо) и проверяем лимиты ---
    # Это важно делать ДО тяжелых операций с файлом, чтобы при превышении лимита
    # сразу вернуть 429, как ожидают тесты и фронтенд.
    is_demo = False
    demo_session = None
    user_id = None
    session_id = None
    usage = None

    if current_user:
        # Авторизованный пользователь
        # Проверяем триал и автоматически переводим на Free если истек
        if current_user.plan_type == "trial" and not current_user.is_trial_active():
            # Триал истек - переводим на Free тариф
            free_tariff = db.query(Tariff).filter(Tariff.name == "Free").first()
            if free_tariff:
                current_user.plan_type = "free"
                current_user.tariff_id = free_tariff.id
                db.commit()
                logger.info(f"Триал истек для {current_user.email}, переведен на Free тариф")
        
        # Проверяем доступность анализа
        can_analyze, error_msg = check_user_can_analyze(current_user, db)
        if not can_analyze:
            raise HTTPException(status_code=429, detail=error_msg)
        
        user_id = current_user.id
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Получаем или создаем запись использования
        usage = db.query(Usage).filter(
            Usage.user_id == current_user.id,
            Usage.year == current_year,
            Usage.month == current_month
        ).first()
        
        if not usage:
            usage = Usage(
                user_id=current_user.id,
                year=current_year,
                month=current_month,
                analyses_count=0
            )
            db.add(usage)
            db.flush()
    else:
        # Демо-пользователь
        is_demo = True
        if request:
            demo_session = get_or_create_demo_session(request, db)
            if demo_session:
                can_analyze, reason = demo_session.can_analyze()
                if not can_analyze:
                    # КОНТЕКСТНЫЙ ТРИГГЕР: Демо лимит достигнут
                    raise HTTPException(
                        status_code=429,
                        detail=reason,
                        headers={
                            "X-Demo-Limit": "true",
                            "X-Suggest-Registration": "true"
                        }
                    )
                session_id = demo_session.id
                demo_session.increment_analyses()
                db.commit()
            else:
                raise HTTPException(status_code=500, detail="Не удалось создать демо-сессию")
        else:
            # Если нет request, но и нет пользователя - разрешаем один раз
            logger.warning("Демо-режим без request объекта")

    # --- После проверки лимитов переходим к работе с файлом ---
    # Валидация файла
    is_valid, error_msg = validate_file(file)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Используем tempfile для безопасного создания временного файла.
    # ВАЖНО: используем только расширение оригинального файла, без полного имени,
    # чтобы избежать проблем с не-ASCII путями (особенно на Windows).
    original_ext = os.path.splitext(file.filename or "")[1] or ""
    temp_fd, temp_path = tempfile.mkstemp(suffix=original_ext, prefix="tender_", dir=os.getcwd())
    file_content_bytes = b""

    try:
        # Закрываем файловый дескриптор сразу после создания, мы будем работать с путем
        os.close(temp_fd)
        
        # Проверка размера при сохранении
        file_size = 0
        MAX_SIZE = 50 * 1024 * 1024  # 50 МБ
        
        with open(temp_path, "wb") as buffer:
            while True:
                chunk = await file.read(8192)  # Читаем по 8 КБ
                if not chunk:
                    break
                file_size += len(chunk)
                if file_size > MAX_SIZE:
                    os.remove(temp_path)
                    raise HTTPException(
                        status_code=413,
                        detail=f"Файл слишком большой ({(file_size / 1024 / 1024):.2f} МБ). Максимальный размер: {MAX_SIZE / 1024 / 1024} МБ"
                    )
                buffer.write(chunk)
                file_content_bytes += chunk  # Сохраняем для кеширования
            buffer.flush()
            os.fsync(buffer.fileno())
        
        # Проверяем кеш перед анализом
        from cache_service import get_document_hash, get_cached_analysis, cache_analysis
        file_hash = get_document_hash(file_content_bytes, file.filename)
        cached_result = get_cached_analysis(file_hash, industry)
        
        if cached_result:
            logger.info(f"✅ Использован закешированный результат для {file.filename}")
            # Сохраняем в БД если пользователь авторизован
            if current_user:
                try:
                    analysis_record = Analysis(
                        user_id=current_user.id,
                        session_id=session_id,
                        is_demo=is_demo,
                        filename=file.filename,
                        industry=industry,
                        result_json=cached_result,
                        score=cached_result.get("score", 50),
                        verdict=cached_result.get("verdict", "CAUTION"),
                        summary=cached_result.get("summary", "")
                    )
                    db.add(analysis_record)
                    if current_user and usage:
                        usage.analyses_count += 1
                        usage.updated_at = datetime.utcnow()
                    db.commit()
                except Exception as db_err:
                    db.rollback()
                    logger.error(f"Ошибка сохранения кешированного анализа: {db_err}")
            
            return cached_result
        
        # Файл уже сохранен в temp_path, seek не нужен
        # await file.seek(0)  # Удалено - файл уже прочитан и сохранен
        result = await analyze_single_file(temp_path, file.filename, industry)
        logger.info(
            f"ANALYZE_SINGLE_DONE file={file.filename} industry={industry} score={result.get('score')} verdict={result.get('verdict')}"
        )
        
        # Сохраняем результат в кеш
        try:
            file_hash = get_document_hash(file_content_bytes, file.filename)
            cache_analysis(file_hash, result, industry, ttl=86400)  # 24 часа
            logger.info(f"✅ Результат анализа закеширован: {file.filename}")
        except Exception as cache_err:
            logger.warning(f"Не удалось закешировать результат: {cache_err}")

        # Сохраняем в БД
        try:
            analysis_record = Analysis(
                user_id=user_id,
                session_id=session_id,
                is_demo=is_demo,
                filename=file.filename,
                industry=industry,
                result_json=result,
                score=result.get("score", 50),
                verdict=result.get("verdict", "CAUTION"),
                summary=result.get("summary", "")
            )
            db.add(analysis_record)
            
            # Обновляем счетчик использования (для авторизованных)
            if current_user and usage:
                usage.analyses_count += 1
                usage.updated_at = datetime.utcnow()
            
            db.commit()
            
            if current_user:
                logger.info(f"✅ Анализ сохранен в БД для пользователя {current_user.email}")
            else:
                logger.info(f"✅ Анализ сохранен в БД для демо-сессии {session_id}")
            
            # КОНТЕКСТНЫЙ ТРИГГЕР #1: После первого анализа в демо-режиме
            if is_demo and demo_session and demo_session.analyses_count == 1:
                result['ui_suggestion'] = {
                    'type': 'register_after_analysis',
                    'title': '🎉 Анализ готов!',
                    'message': 'Сохраните результаты в личный кабинет',
                    'benefits': [
                        'Хранить все анализы',
                        'Экспортировать в PDF',
                        'Делиться с коллегами'
                    ]
                }
        except Exception as db_err:
            db.rollback()
            logger.error(f"Ошибка сохранения в БД: {db_err}")
        
        # Старая история (для обратной совместимости)
        if not current_user:
            # Для неавторизованных пользователей сохраняем в старую историю (обратная совместимость)
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

        # Сохраняем результат в кеш (если file_content_bytes доступен)
        try:
            from cache_service import get_document_hash, cache_analysis
            # Читаем файл для кеширования
            with open(temp_path, "rb") as f:
                file_content_bytes = f.read()
            file_hash = get_document_hash(file_content_bytes, file.filename)
            cache_analysis(file_hash, result, industry, ttl=86400)  # 24 часа
            logger.info(f"✅ Результат анализа закеширован: {file.filename}")
        except Exception as cache_err:
            logger.warning(f"Не удалось закешировать результат: {cache_err}")

        return result

    except HTTPException:
        # Пробрасываем HTTP исключения как есть
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"❌ Server Error в analyze_endpoint: {e}")
        logger.error(f"Детали ошибки:\n{error_trace}")
        raise HTTPException(
            status_code=500, 
            detail=f"Ошибка при анализе документа: {str(e)[:200]}"
        )
    finally:
        # Безопасное удаление файла с повторными попытками
        safe_remove_file(temp_path)

@app.post("/api/analyze-package")
async def analyze_package_endpoint(
    files: List[UploadFile] = File(...),
    industry: str = Form("UNIVERSAL"),
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PackageAnalysisResponse:
    from utils.file_validator import validate_file
    
    if not files:
        raise HTTPException(status_code=400, detail="Не переданы файлы для анализа")
    
    # Ограничение на количество файлов в пакете
    MAX_FILES_IN_PACKAGE = 10
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
                
                # Сбрасываем позицию файла
                await upload.seek(0)

                single_result = await analyze_single_file(temp_path, upload.filename, industry)

                document_results.append(
                    DocumentAnalysis(
                        filename=upload.filename,
                        score=single_result["score"],
                        summary=single_result["summary"],
                        verdict=single_result["verdict"],
                        passport=single_result["passport"],
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
            verdict=analysis.verdict
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
            verdict=package.verdict
        ))
    
    # Сортируем по дате
    items.sort(key=lambda x: x.createdAt, reverse=True)
    
    return HistoryResponse(items=items[:limit])


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)
