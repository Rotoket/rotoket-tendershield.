"""
Pydantic схемы для валидации данных API
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


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


class ProfileResponse(BaseModel):
    user: UserResponse
    tariff: Optional[TariffResponse] = None
    usage: Optional[UsageResponse] = None
    trial: Optional[TrialInfo] = None


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
    
    class Config:
        from_attributes = True

