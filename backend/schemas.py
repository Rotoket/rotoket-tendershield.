"""
Pydantic схемы для валидации данных API
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date


# Схемы для пользователей
class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    company: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    tariff_id: Optional[int] = None
    plan_type: Optional[str] = None
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


# Схемы для тарифов
class TariffResponse(BaseModel):
    id: int
    name: str
    price: int
    analyses_limit: int
    package_limit: int
    features: Optional[dict] = None
    
    class Config:
        from_attributes = True


# Схемы для использования
class UsageResponse(BaseModel):
    analyses_count: int
    packages_count: int
    analyses_limit: int
    package_limit: int
    analyses_remaining: int
    packages_remaining: int
    
    class Config:
        from_attributes = True


# Схема для полной информации профиля
class TrialInfo(BaseModel):
    """Информация о триале"""
    is_active: bool
    remaining_days: int
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None


class CompanyProfile(BaseModel):
    """Профиль компании для персонализации анализа"""
    has_sro: bool = False
    has_fstek: bool = False
    has_fsb: bool = False
    has_mchs: bool = False
    experience_level: Optional[str] = None  # e.g. "none" | "up_to_10m" | "10_50m" | "50m_plus"
    tax_system: Optional[str] = None       # e.g. "OSN" | "USN" | "PATENT"


class ProfileResponse(BaseModel):
    user: UserResponse
    tariff: Optional[TariffResponse] = None
    usage: Optional[UsageResponse] = None
    trial: Optional[TrialInfo] = None
    company_profile: Optional[CompanyProfile] = None


# ============================================
# PHASE 1: TENDER PASSPORT SCHEMAS (должны быть определены ДО AnalysisResponse)
# ============================================

class TenderSource(BaseModel):
    """Источник данных для конкретного поля"""
    document_name: str = Field(..., description="Название документа (например: tender_doc.pdf)")
    page_number: Optional[int] = Field(None, description="Номер страницы в документе")
    section: Optional[str] = Field(None, description="Раздел документа (например: 'II. Цена')")
    quote: str = Field(..., description="Точная цитата из документа")
    extraction_method: str = Field(..., description="Метод извлечения: 'llm' | 'regex' | 'manual'")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Уверенность в данных (0.0 - 1.0)")


class GovernmentData(BaseModel):
    """Данные из ГосЗакупок API"""
    customer_id: Optional[str] = Field(None, description="ID заказчика в zakupki.gov.ru")
    previous_tenders_count: int = Field(0, description="Количество предыдущих тендеров заказчика")
    avg_discount_percent: Optional[float] = Field(None, description="Средняя скидка победителей (%)")
    avg_competitor_count: Optional[int] = Field(None, description="Среднее количество участников")
    avg_payment_delay_days: Optional[int] = Field(None, description="Средняя задержка оплаты (дни)")
    data_source: str = Field("zakupki.gov.ru", description="Источник данных")
    data_freshness: str = Field(..., description="Свежесть данных (например: 'days_old: 3' или 'real_time')")
    confidence_level: str = Field("medium", description="Уровень уверенности: 'low' | 'medium' | 'high'")


class TenderPassport(BaseModel):
    """Основные параметры тендера (Tender Passport)"""
    # ОБЯЗАТЕЛЬНЫЕ поля (всегда должны быть заполнены)
    nmck_numeric: float = Field(..., gt=0, description="НМЦК в числовом формате (руб.)")
    nmck_formatted: str = Field(..., description="НМЦК с форматированием (например: '500 млн руб.')")
    nmck_source: TenderSource = Field(..., description="Источник данных НМЦК")
    
    customer: str = Field(..., min_length=1, description="Название заказчика")
    customer_source: TenderSource = Field(..., description="Источник данных заказчика")
    
    deadline: Optional[date] = Field(None, description="Дедлайн подачи заявок")
    deadline_source: Optional[TenderSource] = Field(None, description="Источник данных дедлайна")
    
    # ОПЦИОНАЛЬНЫЕ поля
    contract_term_months: Optional[int] = Field(None, description="Длительность контракта в месяцах")
    contract_term_source: Optional[TenderSource] = Field(None, description="Источник данных срока контракта")
    
    guarantee_amount: Optional[float] = Field(None, description="Обеспечение участия (руб.)")
    guarantee_source: Optional[TenderSource] = Field(None, description="Источник данных обеспечения")
    
    penalty_percent: Optional[float] = Field(None, description="Процент штрафа за нарушение")
    penalty_source: Optional[TenderSource] = Field(None, description="Источник данных штрафа")
    
    # МЕТАДАННЫЕ
    completion_percentage: int = Field(0, ge=0, le=100, description="Процент заполненности данных (0-100)")
    warnings: List[str] = Field(default_factory=list, description="Предупреждения валидации")
    government_data: Optional[GovernmentData] = Field(None, description="Данные из ГосЗакупок API")


# Схемы для анализов
class AnalysisCreate(BaseModel):
    filename: str
    industry: str = "UNIVERSAL"


class AnalysisResponse(BaseModel):
    id: int
    filename: str
    industry: str
    score: int
    verdict: str
    summary: Optional[str] = None
    created_at: datetime
    # PHASE 1: Добавляем Tender Passport
    tender_passport: Optional[TenderPassport] = Field(None, description="Паспорт тендера с основными параметрами")
    
    class Config:
        from_attributes = True


# Схемы для MCP (справочный слой)
class LegalExplainRequest(BaseModel):
    """Запрос на объяснение правового вопроса."""
    question: str
    context: Optional[Dict[str, Any]] = None  # lawCode, pattern, term и т.д.


class LegalExplainResponse(BaseModel):
    """Ответ с объяснением и источниками."""
    explanation: str
    sources: List[str]
    disclaimer: str


# Схемы для асинхронного анализа
class AnalysisJobStartRequest(BaseModel):
    mode: str  # "single" | "package"
    filename: Optional[str] = None  # Для single mode
    filenames: Optional[List[str]] = None  # Для package mode
    industry: str = "UNIVERSAL"


class AnalysisJobStartResponse(BaseModel):
    analysis_id: str
    status: str
    message: str


class AnalysisJobStatusResponse(BaseModel):
    analysis_id: str
    status: str  # queued | processing | done | error
    progress: int  # 0-100
    stage: Optional[str] = None  # Текущий этап анализа
    result: Optional[Dict[str, Any]] = None  # Результат анализа (если status == "done")
    error_message: Optional[str] = None  # Сообщение об ошибке (если status == "error")
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None



