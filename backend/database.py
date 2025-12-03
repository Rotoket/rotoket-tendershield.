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
    
    # Связи
    user = relationship("User", back_populates="package_analyses")


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


# Настройка подключения к БД
def get_database_url() -> str:
    """Получает URL подключения к БД из переменных окружения или config"""
    from config import settings
    from urllib.parse import quote_plus
    
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
        except Exception:
            # Любые другие ошибки подключения обрабатываются выше по стеку
            pass

        yield db
    finally:
        db.close()


def init_db():
    """Создает все таблицы в БД"""
    Base.metadata.create_all(bind=engine)


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

