"""
Модуль для работы с базой данных PostgreSQL
Использует SQLAlchemy ORM для управления моделями и сессиями
"""

from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime, ForeignKey, Float, Boolean, Text, event
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import Optional
import os

Base = declarative_base()

# ФАЗА 5: Импортируем модели procurement для регистрации в Base.metadata
# Импорт выполняется в конце файла после определения Base


class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=True)  # Имя пользователя
    company = Column(String, nullable=True)  # Название компании
    tariff_id = Column(Integer, ForeignKey("tariffs.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Система триалов
    plan_type = Column(String, default="trial")  # "trial", "free", "pro", "enterprise"
    trial_start = Column(DateTime, nullable=True)
    trial_end = Column(DateTime, nullable=True)
    trial_extended = Column(Boolean, default=False)
    
    # Подписка
    subscription_start = Column(DateTime, nullable=True)
    subscription_end = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    tariff = relationship("Tariff", back_populates="users")
    analyses = relationship("Analysis", back_populates="user", cascade="all, delete-orphan")
    package_analyses = relationship("PackageAnalysis", back_populates="user", cascade="all, delete-orphan")
    usage_records = relationship("Usage", back_populates="user", cascade="all, delete-orphan")
    
    def is_trial_active(self) -> bool:
        """Проверяет, активен ли триал"""
        if self.plan_type != "trial":
            return False
        if not self.trial_end:
            return False
        return datetime.utcnow() <= self.trial_end
    
    def get_remaining_trial_days(self) -> int:
        """Возвращает количество оставшихся дней триала"""
        if not self.is_trial_active():
            return 0
        delta = self.trial_end - datetime.utcnow()
        return max(0, delta.days + 1)  # +1 чтобы показывать текущий день


class Tariff(Base):
    """Модель тарифного плана"""
    __tablename__ = "tariffs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # "Start", "Pro", "Enterprise"
    price = Column(Integer, nullable=False)  # Цена в рублях/месяц
    analyses_limit = Column(Integer, nullable=False)  # Лимит анализов в месяц
    package_limit = Column(Integer, nullable=False, default=5)  # Лимит документов в пакете
    features = Column(JSON, nullable=True)  # Список доступных функций
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    users = relationship("User", back_populates="tariff")


class DemoSession(Base):
    """Модель демо-сессии (анонимные пользователи)"""
    __tablename__ = "demo_sessions"
    
    id = Column(String, primary_key=True)  # session_id в браузере
    device_fingerprint = Column(String, nullable=True)  # для отслеживания устройства
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    last_analysis_at = Column(DateTime, nullable=True)
    analyses_count = Column(Integer, default=0)
    is_unlimited = Column(Boolean, default=False)  # Флаг безлимитного доступа
    
    def __init__(self, *args, **kwargs):
        """Гарантируем, что created_at выставлен даже до сохранения в БД.

        SQLAlchemy по умолчанию проставляет default только при INSERT,
        а в юнит-тестах мы часто работаем с несохранёнными объектами.
        """
        super().__init__(*args, **kwargs)
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def can_analyze(self) -> tuple:
        """Проверка: может ли пользователь анализировать? Returns: (can_analyze, reason)"""
        # Если установлен безлимит - всегда разрешаем
        if self.is_unlimited:
            return True, "OK"
        # Лимит: 3 анализа в сутки
        if self.analyses_count >= 3:
            if not self.last_analysis_at:
                return True, "OK"
            # Проверяем, прошли ли сутки с последнего анализа
            hours_passed = (datetime.utcnow() - self.last_analysis_at).total_seconds() / 3600
            if hours_passed < 24:
                remaining_hours = int(24 - hours_passed)
                return False, f"Лимит достигнут. Попробуйте через {remaining_hours} ч"
            else:
                # Сброс счетчика
                self.analyses_count = 0
                self.last_analysis_at = datetime.utcnow()
        return True, "OK"
    
    def increment_analyses(self):
        """Увеличить счетчик анализов"""
        self.analyses_count += 1
        self.last_analysis_at = datetime.utcnow()


class Analysis(Base):
    """Модель анализа одного документа"""
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Может быть NULL для демо
    session_id = Column(String, ForeignKey("demo_sessions.id"), nullable=True, index=True)  # Для демо-сессий
    is_demo = Column(Boolean, default=False)  # Флаг демо-анализа
    filename = Column(String, nullable=False)
    industry = Column(String, nullable=False, default="UNIVERSAL")  # IT, CONSTRUCTION, MEDICINE, UNIVERSAL
    result_json = Column(JSON, nullable=False)  # Весь результат анализа
    score = Column(Integer, nullable=False)
    verdict = Column(String, nullable=False)  # STOP, CAUTION, PARTICIPATE
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Решение пользователя (Decision Layer)
    user_decision = Column(JSON, nullable=True)  # {decision, comment, timestamp, dealBreakersCount, score, verdict}
    decision_at = Column(DateTime, nullable=True, index=True)  # Когда решение было зафиксировано
    
    # Связи
    user = relationship("User", back_populates="analyses")


class GeneratedDocument(Base):
    """Сгенерированный документ на основе анализа (обоснование, письмо и т.п.)."""
    __tablename__ = "generated_documents"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False, index=True)
    doc_type = Column(String, nullable=False)  # e.g. "OBJECTION_LETTER", "CLARIFICATION_LETTER"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class PackageAnalysis(Base):
    """Модель пакетного анализа"""
    __tablename__ = "package_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    package_id = Column(String, unique=True, nullable=False, index=True)  # UUID пакета
    summary_score = Column(Float, nullable=False)
    verdict = Column(String, nullable=False)
    documents_json = Column(JSON, nullable=False)  # Список DocumentAnalysis
    global_issues = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Решение пользователя (Decision Layer)
    user_decision = Column(JSON, nullable=True)  # {decision, comment, timestamp, dealBreakersCount, score, verdict}
    decision_at = Column(DateTime, nullable=True, index=True)  # Когда решение было зафиксировано
    
    # Связи
    user = relationship("User", back_populates="package_analyses")


class DecisionRecord(Base):
    """
    Decision Record v1.0 — Журнал управленческих решений.
    
    Каноническая запись с ТОЛЬКО 7 обязательными полями:
    1. Tender ID
    2. Объект (кратко)
    3. Принятое решение
    4. Основание решения (1–3 причины)
    5. Индекс управленческой нагрузки (одно число)
    6. Ответственный
    7. Дата фиксации
    """
    __tablename__ = "decision_records"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Канонические 7 полей
    tender_id = Column(String, nullable=False, index=True)  # 1. Tender ID
    tender_object = Column(Text, nullable=False)  # 2. Объект (кратко)
    decision = Column(String, nullable=False)  # 3. Принятое решение (PARTICIPATE, DO_NOT_PARTICIPATE, PARTICIPATE_WITH_CONDITIONS, POSTPONE)
    decision_reasons = Column(JSON, nullable=False)  # 4. Основание решения (1–3 причины, список строк)
    management_load_index = Column(Integer, nullable=False)  # 5. Индекс управленческой нагрузки (0-100)
    responsible_person = Column(String, nullable=False)  # 6. Ответственный
    fixed_at = Column(DateTime, nullable=False, index=True)  # 7. Дата фиксации
    
    # Служебные поля для связи с анализом
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=True, index=True)
    package_id = Column(String, nullable=True, index=True)  # Связь с PackageAnalysis.package_id (без FK для совместимости)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Связи
    user = relationship("User")
    analysis = relationship("Analysis")


class Usage(Base):
    """Модель для отслеживания использования (квоты)"""
    __tablename__ = "usage"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)  # 1-12
    analyses_count = Column(Integer, default=0)
    packages_count = Column(Integer, default=0)
    tokens_used = Column(Integer, default=0)  # Для будущего использования
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    user = relationship("User", back_populates="usage_records")
    
    # Уникальный индекс на user_id + year + month
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class PasswordResetToken(Base):
    """Модель для токенов сброса пароля"""
    __tablename__ = "password_reset_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    user = relationship("User")


class AnalysisJob(Base):
    """Модель для асинхронных задач анализа документов"""
    __tablename__ = "analysis_jobs"
    
    id = Column(String, primary_key=True, index=True)  # UUID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Может быть NULL для demo
    session_id = Column(String, ForeignKey("demo_sessions.id"), nullable=True, index=True)  # Для demo-сессий
    
    # Статус и прогресс
    status = Column(String, nullable=False, index=True, default="queued")  # queued | processing | done | error
    progress = Column(Integer, default=0)  # 0-100
    stage = Column(String, nullable=True)  # Текущий этап анализа (parsing_documents, legal_checks, etc.)
    
    # Метаданные задачи
    mode = Column(String, nullable=False)  # "single" | "package"
    filename = Column(String, nullable=True)  # Для single mode
    filenames = Column(JSON, nullable=True)  # Для package mode
    industry = Column(String, default="UNIVERSAL")
    
    # Результат
    result_json = Column(JSON, nullable=True)  # Результат анализа (AnalysisResult или PackageAnalysis)
    error_message = Column(Text, nullable=True)
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    
    # Связи
    user = relationship("User")
    session = relationship("DemoSession")


# Настройка подключения к БД
def get_database_url() -> str:
    """Получает URL подключения к БД из переменных окружения или config"""
    from config import settings
    from urllib.parse import quote_plus

    # Специальный упрощённый режим для разработки:
    # если в .env указать TENDER_DB_HOST=sqlite, то всегда используем локальную SQLite
    # и вообще не пытаемся подключаться к PostgreSQL (чтобы не блокировать работу,
    # если Postgres не настроен или недоступен).
    if str(settings.DB_HOST).lower() == "sqlite":
        return "sqlite:///./tender_shield.db"

    # URL-кодируем пароль для безопасности (защита от спецсимволов)
    # Убеждаемся, что пароль в UTF-8 перед кодированием
    password_str = str(settings.DB_PASSWORD)
    if isinstance(password_str, bytes):
        password_str = password_str.decode('utf-8', errors='replace')
    encoded_password = quote_plus(password_str, safe='')
    
    # Также кодируем имя пользователя и имя БД на случай спецсимволов
    encoded_user = quote_plus(str(settings.DB_USER), safe='')
    encoded_db = quote_plus(str(settings.DB_NAME), safe='')
    
    # Добавляем параметры кодировки прямо в URL для избежания проблем с кодировкой
    db_url = f"postgresql://{encoded_user}:{encoded_password}@{settings.DB_HOST}:{settings.DB_PORT}/{encoded_db}?client_encoding=utf8"
    
    return db_url


# Создание движка и сессии
try:
    db_url = get_database_url()
    # Убеждаемся, что URL в правильной кодировке
    if isinstance(db_url, bytes):
        db_url = db_url.decode('utf-8', errors='replace')
    
    # Для PostgreSQL добавляем параметры кодировки
    connect_args = {}
    if "postgresql" in db_url.lower():
        connect_args = {
            "client_encoding": "UTF8",
            "options": "-c client_encoding=UTF8 -c timezone=UTC"
        }
        # Используем connect_timeout для избежания зависаний
        try:
            import psycopg2
            # psycopg2 автоматически обрабатывает кодировку, но явно указываем
            connect_args["connect_timeout"] = 10
        except ImportError:
            pass
    
    engine = create_engine(
        db_url,
        pool_pre_ping=True,  # Проверка соединения перед использованием
        echo=False,  # Логирование SQL запросов (поставить True для отладки)
        connect_args=connect_args,
        # Явно указываем кодировку для connection pool
        poolclass=None,
    )
    
    # Устанавливаем кодировку для всех новых соединений
    if "postgresql" in db_url.lower():
        @event.listens_for(engine, "connect")
        def set_encoding(dbapi_conn, connection_record):
            """Устанавливает UTF8 кодировку при каждом подключении"""
            try:
                if hasattr(dbapi_conn, 'set_client_encoding'):
                    dbapi_conn.set_client_encoding('UTF8')
            except Exception:
                pass  # Игнорируем ошибки установки кодировки
except UnicodeDecodeError as e:
    # Специальная обработка ошибок кодировки
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"❌ Ошибка кодировки при подключении к БД: {e}")
    logger.warning("⚠️ Переключаемся на SQLite из-за проблемы с кодировкой PostgreSQL.")
    engine = create_engine(
        "sqlite:///./tender_shield.db",
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
        echo=False
    )
except Exception as e:
    # Fallback на SQLite если PostgreSQL недоступен
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠️ Не удалось подключиться к PostgreSQL: {e}. Используется SQLite.")
    engine = create_engine(
        "sqlite:///./tender_shield.db",
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency для получения сессии БД.

    ВАЖНО: здесь дополнительно проверяем первое подключение.
    Если при обращении к PostgreSQL возникает ошибка кодировки (UnicodeDecodeError),
    автоматически переключаемся на локальную SQLite, чтобы не падать 500‑ми.
    Это особенно полезно в Windows‑окружении при проблемах с env/кодировкой.
    """
    global engine, SessionLocal

    db = SessionLocal()
    try:
        # Пробуем простейший запрос, чтобы «пробить» подключение
        from sqlalchemy import text
        from sqlalchemy.exc import OperationalError
        try:
            db.execute(text("SELECT 1"))
        except UnicodeDecodeError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Ошибка кодировки при подключении к PostgreSQL в get_db: {e}")
            logger.warning("⚠️ Переключаемся на SQLite (tender_shield.db) для работы приложения.")

            # Переподключаем engine и SessionLocal на SQLite
            engine = create_engine(
                "sqlite:///./tender_shield.db",
                connect_args={"check_same_thread": False},
                pool_pre_ping=True,
                echo=False,
            )
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

            # Закрываем старую сессию и открываем новую уже на SQLite
            db.close()
            db = SessionLocal()
        except OperationalError as e:
            # Ошибка подключения к PostgreSQL (сервер недоступен, нет соединения и т.п.)
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Ошибка подключения к PostgreSQL в get_db: {e}")
            logger.warning("⚠️ PostgreSQL недоступен, переключаемся на SQLite (tender_shield.db).")

            engine = create_engine(
                "sqlite:///./tender_shield.db",
                connect_args={"check_same_thread": False},
                pool_pre_ping=True,
                echo=False,
            )
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

            db.close()
            db = SessionLocal()
        except Exception:
            # Любые другие ошибки подключения обрабатываются выше по стеку
            pass

        yield db
    finally:
        db.close()


def init_db():
    """Создает все таблицы в БД"""
    Base.metadata.create_all(bind=engine)


# ФАЗА 5: Новые таблицы для procurement-специфичных данных

class ProcurementKnowledgeBase(Base):
    """
    ФАЗА 5: Таблица для хранения ссылок на документы Knowledge Base,
    используемые в анализе закупок.
    """
    __tablename__ = "procurement_knowledge_base"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=True, index=True)
    package_id = Column(String, nullable=True, index=True)  # Для пакетных анализов
    
    # Информация о документе KB
    kb_path = Column(String, nullable=False)  # Относительный путь (например, "laws/fz-44-2013.md")
    kb_category = Column(String, nullable=True)  # laws, standards, templates, examples, risks, canon, utils
    kb_title = Column(String, nullable=True)  # Название документа
    
    # Контекст использования
    query_used = Column(Text, nullable=True)  # Запрос, который привел к этому документу
    relevance_score = Column(Float, nullable=True)  # Оценка релевантности (0-1)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Связи
    analysis = relationship("Analysis")


class ProcurementBlocker(Base):
    """
    ФАЗА 5: Таблица для хранения блокеров, выявленных в анализе закупок.
    """
    __tablename__ = "procurement_blockers"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False, index=True)
    
    # Информация о блокере
    sub_classification = Column(String, nullable=False)  # LOCATION_BLOCKER, CERTIFICATION_MISSING и т.д.
    description = Column(Text, nullable=False)
    legal_basis = Column(String, nullable=True)  # 44-ФЗ, 223-ФЗ, ТР ЕАЭС и т.д.
    
    # Митигация
    is_mitigable = Column(Boolean, default=False)
    mitigation_strategy = Column(Text, nullable=True)
    mitigation_cost = Column(Float, nullable=True)  # В рублях
    mitigation_time_days = Column(Integer, nullable=True)
    
    # Связи с evidence
    evidence_ids = Column(JSON, nullable=True)  # Список ID evidence объектов
    kb_reference = Column(String, nullable=True)  # Ссылка на документ KB
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Связи
    analysis = relationship("Analysis")


class AnalysisEvidenceExtended(Base):
    """
    ФАЗА 5: Расширенная таблица для хранения Evidence Objects с procurement-специфичными полями.
    """
    __tablename__ = "analysis_evidence_extended"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False, index=True)
    
    # Базовые поля из EvidenceObject
    evidence_id = Column(String, unique=True, nullable=False, index=True)  # E-XXXXXXXX
    source_file = Column(String, nullable=False)
    fact = Column(Text, nullable=False)
    classification = Column(String, nullable=False)  # DEAL_BREAKER, CONTROLLED_RISK, MARKET_NOISE
    confidence = Column(String, nullable=False)  # HIGH, MEDIUM, LOW
    
    # ФАЗА 2: Расширенные поля
    sub_classification = Column(String, nullable=True)  # LOCATION_BLOCKER, CERTIFICATION_MISSING и т.д.
    legal_basis = Column(String, nullable=True)  # 44-ФЗ, 223-ФЗ, ТР ЕАЭС и т.д.
    
    # Финансовые данные
    financial_impact_rub = Column(Float, nullable=True)
    
    # Митигация
    mitigation_strategy = Column(Text, nullable=True)
    mitigation_cost_rub = Column(Float, nullable=True)
    mitigation_time_days = Column(Integer, nullable=True)
    
    # Метаданные
    derived_from = Column(JSON, nullable=True)  # Список источников
    raw_extract = Column(Text, nullable=True)
    applicable_to_procurement_type = Column(JSON, nullable=True)  # ["44-ФЗ", "223-ФЗ"]
    reference_in_kb = Column(String, nullable=True)  # Ссылка на документ KB
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Связи
    analysis = relationship("Analysis")


class ProcurementDecisionExtended(Base):
    """
    ФАЗА 5: Расширенная таблица для хранения решений по закупкам с полной информацией.
    """
    __tablename__ = "procurement_decisions_extended"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False, index=True, unique=True)
    
    # Основные поля решения
    verdict = Column(String, nullable=False)  # PROCEED, PROCEED_WITH_CONDITIONS, DO_NOT_PARTICIPATE, POSTPONE
    iun = Column(Integer, nullable=False)  # Индекс управленческой нагрузки (0-100)
    decision_grounds = Column(Text, nullable=False)  # Обоснование решения
    
    # Критические параметры
    critical_parameters = Column(JSON, nullable=True)  # Список CriticalParameter
    
    # Финансовое влияние
    financial_impact = Column(JSON, nullable=True)  # FinancialImpact как JSON
    
    # Списки
    blockers = Column(JSON, nullable=True)  # Список BlockerInfo
    red_flags = Column(JSON, nullable=True)  # Список red flags
    checklist = Column(JSON, nullable=True)  # Список ChecklistItem
    
    # Ссылки на Knowledge Base
    kb_references = Column(JSON, nullable=True)  # Список путей к документам KB
    
    # Метаданные
    procurement_law = Column(String, nullable=True)  # 44-ФЗ или 223-ФЗ
    nmck = Column(Float, nullable=True)  # НМЦК
    deadline_days = Column(Integer, nullable=True)  # Дней до дедлайна
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    analysis = relationship("Analysis", backref="procurement_decision_extended")


def create_default_tariffs(db):
    """Создает тарифные планы по умолчанию"""
    from sqlalchemy.exc import IntegrityError
    
    default_tariffs = [
        {
            "name": "Free",
            "price": 0,
            "analyses_limit": 2,
            "package_limit": 1,
            "features": ["single_analysis", "history_30_days", "basic_support"]
        },
        {
            "name": "Start",
            "price": 2990,
            "analyses_limit": 50,
            "package_limit": 5,
            "features": ["single_analysis", "package_analysis", "history_30_days", "basic_support", "export_pdf"]
        },
        {
            "name": "Pro",
            "price": 9990,
            "analyses_limit": 200,
            "package_limit": 10,
            "features": ["single_analysis", "package_analysis", "history_90_days", "priority_support", "export_reports", "export_pdf", "export_excel"]
        },
        {
            "name": "Enterprise",
            "price": 0,  # По договору
            "analyses_limit": -1,  # -1 = безлимит
            "package_limit": 50,
            "features": ["single_analysis", "package_analysis", "unlimited_history", "24_7_support", "api_access", "custom_integrations", "export_pdf", "export_excel"]
        }
    ]
    
    for tariff_data in default_tariffs:
        existing = db.query(Tariff).filter(Tariff.name == tariff_data["name"]).first()
        if not existing:
            tariff = Tariff(**tariff_data)
            db.add(tariff)
    
    try:
        db.commit()
        print("✅ Тарифные планы созданы")
    except IntegrityError:
        db.rollback()
        print("ℹ️ Тарифные планы уже существуют")

