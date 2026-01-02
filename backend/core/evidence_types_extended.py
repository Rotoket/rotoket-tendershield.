"""
Evidence Types Extended — ФАЗА 2: Расширение классификации Evidence для закупок

Расширяет базовые типы из evidence_types.py специализированными классификациями
для анализа закупок 44-ФЗ и 223-ФЗ.
"""

from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field

# Импортируем базовые типы
from evidence_types import (
    EvidenceObject,
    EvidenceClassification,
    EvidenceConfidence,
)


class EvidenceSubClassification(str, Enum):
    """Подклассификация evidence в контексте закупок"""
    
    # DEALBREAKER subcategories
    LOCATION_BLOCKER = "location_blocker"          # ЗАТО, спецрежим
    CERTIFICATION_MISSING = "cert_missing"         # ТР ЕАЭС, СанПиН
    EXPERIENCE_INSUFFICIENT = "exp_insufficient"   # Опыт < 20% цены
    LOGISTICS_IMPOSSIBLE = "logistics_impossible"  # Нельзя доставить
    LEGAL_PROHIBITION = "legal_prohibition"        # Нарушает закон 44-ФЗ
    
    # CONTROLLED RISK subcategories
    DEADLINE_TIGHT = "deadline_tight"              # Короткий срок подачи
    PRICE_BELOW_MARKET = "price_below_market"      # Цена подозрительно низкая
    VENDOR_NEW = "vendor_new"                      # Новый поставщик без истории
    COMPLEX_REQUIREMENTS = "complex_reqs"          # Сложные требования
    PARTIAL_CERTIFICATION = "partial_cert"        # Часть сертификатов есть
    PENALTY_RISK = "penalty_risk"                 # Риск штрафов (10% цены)
    QUALITY_VARIANCE = "quality_variance"          # Вариативность качества
    LOGISTICS_COMPLEX = "logistics_complex"        # Сложная логистика
    
    # MARKET NOISE subcategories
    REDUNDANT_REQUIREMENT = "redundant_req"       # Требование дублирует норму
    VAGUE_SPECIFICATION = "vague_spec"            # Неясная спецификация
    STANDARD_PROCEDURE = "std_procedure"          # Стандартная процедура


class EvidenceLegalBasis(str, Enum):
    """На каком законе/стандарте основано evidence"""
    FZ_44 = "44-ФЗ"                               # Федеральный закон 44-ФЗ
    FZ_223 = "223-ФЗ"                             # Закон 223-ФЗ
    FZ_135 = "135-ФЗ"                             # Закон о защите конкуренции
    FZ_152 = "152-ФЗ"                             # Закон о персональных данных
    TR_EAES_040 = "ТР ЕАЭС 040/2016"             # Техрегламент (рыба)
    SANPIN = "СанПиН 2.3/2.4.3590-20"            # Санитарные нормы
    GOST = "ГОСТ"                                # Государственный стандарт
    CUSTOM = "custom"                             # Специфичное требование заказчика


class EvidenceExtendedModel(EvidenceObject):
    """
    Расширенная модель Evidence для закупок.
    
    Наследует все поля из EvidenceObject и добавляет специализированные поля
    для анализа закупок 44-ФЗ и 223-ФЗ.
    """
    
    # НОВЫЕ поля для закупок
    sub_classification: Optional[EvidenceSubClassification] = Field(
        None,
        description="Подклассификация evidence (location_blocker, cert_missing и т.д.)"
    )
    
    legal_basis: Optional[EvidenceLegalBasis] = Field(
        None,
        description="На каком законе/стандарте основано evidence (44-ФЗ, ТР ЕАЭС и т.д.)"
    )
    
    applies_to_44fz: Optional[bool] = Field(
        None,
        description="Применимо ли к закупкам 44-ФЗ"
    )
    
    applies_to_223fz: Optional[bool] = Field(
        None,
        description="Применимо ли к закупкам 223-ФЗ"
    )
    
    mitigation_strategy: Optional[str] = Field(
        None,
        description="Как это можно решить (стратегия митигации)"
    )
    
    legal_consequences: Optional[str] = Field(
        None,
        description="Последствия нарушения (штрафы, отмена закупки и т.д.)"
    )
    
    reference_in_kb: Optional[str] = Field(
        None,
        description="Ссылка на документ Knowledge Base (например: 'risks/blockers-44fz.md')"
    )
    
    # Метаданные для расчета ИУН
    iun_contribution: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="Вклад этого evidence в ИУН (0-100)"
    )
    
    # Метаданные для финансового влияния
    mitigation_cost_estimate: Optional[float] = Field(
        None,
        ge=0,
        description="Ориентировочная стоимость митигации (руб.)"
    )
    
    mitigation_time_days: Optional[int] = Field(
        None,
        ge=0,
        description="Ориентировочное время на митигацию (дни)"
    )


def classify_evidence_for_procurement(
    evidence: EvidenceObject,
    procurement_law: str = "44-ФЗ"
) -> EvidenceExtendedModel:
    """
    Классифицирует базовый EvidenceObject для закупок.
    
    Автоматически определяет sub_classification, legal_basis и другие поля
    на основе содержимого evidence.
    
    Args:
        evidence: Базовый EvidenceObject
        procurement_law: "44-ФЗ" или "223-ФЗ"
    
    Returns:
        EvidenceExtendedModel с заполненными полями
    """
    fact_lower = evidence.fact.lower()
    source_lower = evidence.source_file.lower()
    
    # Определяем sub_classification
    sub_classification = None
    legal_basis = None
    applies_to_44fz = procurement_law == "44-ФЗ"
    applies_to_223fz = procurement_law == "223-ФЗ"
    mitigation_strategy = None
    legal_consequences = None
    reference_in_kb = None
    iun_contribution = None
    mitigation_cost_estimate = None
    mitigation_time_days = None
    
    # Определяем LOCATION_BLOCKER
    if any(keyword in fact_lower for keyword in ["зато", "закрытое", "пропуск", "спецрежим"]):
        sub_classification = EvidenceSubClassification.LOCATION_BLOCKER
        legal_basis = EvidenceLegalBasis.FZ_44 if applies_to_44fz else EvidenceLegalBasis.FZ_223
        mitigation_strategy = "Получить пропуск в ЗАТО (2-4 недели, 50K-100K руб.)"
        legal_consequences = "Без пропуска невозможно доставить товар"
        reference_in_kb = "risks/location-risks.md"
        iun_contribution = 25
        mitigation_cost_estimate = 75000.0  # Среднее значение
        mitigation_time_days = 21  # 3 недели
    
    # Определяем CERTIFICATION_MISSING
    elif any(keyword in fact_lower for keyword in ["сертификат", "требуется", "отсутствует", "тр еаэс", "санпин"]):
        if evidence.classification == EvidenceClassification.DEAL_BREAKER:
            sub_classification = EvidenceSubClassification.CERTIFICATION_MISSING
            if "тр еаэс" in fact_lower or "040" in fact_lower:
                legal_basis = EvidenceLegalBasis.TR_EAES_040
                reference_in_kb = "standards/tr-eaes-040-2016.md"
            elif "санпин" in fact_lower:
                legal_basis = EvidenceLegalBasis.SANPIN
                reference_in_kb = "standards/sanpin-2-3-2-4-3590-20.md"
            else:
                legal_basis = EvidenceLegalBasis.GOST
            mitigation_strategy = "Получить сертификат (2-4 недели, 50K-200K руб.)"
            legal_consequences = "Без сертификата заявка будет отклонена"
            iun_contribution = 20
            mitigation_cost_estimate = 125000.0  # Среднее значение
            mitigation_time_days = 21  # 3 недели
        else:
            sub_classification = EvidenceSubClassification.PARTIAL_CERTIFICATION
            iun_contribution = 10
    
    # Определяем EXPERIENCE_INSUFFICIENT
    elif any(keyword in fact_lower for keyword in ["опыт", "недостаточно", "менее 20%", "аналогичных контрактов"]):
        sub_classification = EvidenceSubClassification.EXPERIENCE_INSUFFICIENT
        legal_basis = EvidenceLegalBasis.FZ_44 if applies_to_44fz else EvidenceLegalBasis.FZ_223
        mitigation_strategy = "Не митигируемо (опыт нельзя 'купить')"
        legal_consequences = "Заявка будет отклонена без требуемого опыта"
        reference_in_kb = "risks/blockers-44fz.md"
        iun_contribution = 30
        mitigation_cost_estimate = None  # Не митигируемо
        mitigation_time_days = None
    
    # Определяем LOGISTICS_IMPOSSIBLE
    elif any(keyword in fact_lower for keyword in ["невозможно доставить", "логистика", "доставка", "транспортировка"]):
        if evidence.classification == EvidenceClassification.DEAL_BREAKER:
            sub_classification = EvidenceSubClassification.LOGISTICS_IMPOSSIBLE
        else:
            sub_classification = EvidenceSubClassification.LOGISTICS_COMPLEX
        legal_basis = EvidenceLegalBasis.FZ_44 if applies_to_44fz else EvidenceLegalBasis.FZ_223
        mitigation_strategy = "Организовать специализированную логистику (1-2 недели, 100K-1M руб.)"
        legal_consequences = "Нарушение срока доставки → штраф 10% от цены"
        reference_in_kb = "risks/logistics-risks.md"
        iun_contribution = 15 if sub_classification == EvidenceSubClassification.LOGISTICS_COMPLEX else 30
        mitigation_cost_estimate = 300000.0 if sub_classification == EvidenceSubClassification.LOGISTICS_COMPLEX else None
        mitigation_time_days = 10 if sub_classification == EvidenceSubClassification.LOGISTICS_COMPLEX else None
    
    # Определяем LEGAL_PROHIBITION
    elif any(keyword in fact_lower for keyword in ["нарушение", "44-фз", "223-фз", "135-фз", "запрещено", "товарный знак"]):
        sub_classification = EvidenceSubClassification.LEGAL_PROHIBITION
        if "44-фз" in fact_lower:
            legal_basis = EvidenceLegalBasis.FZ_44
        elif "223-фз" in fact_lower:
            legal_basis = EvidenceLegalBasis.FZ_223
        elif "135-фз" in fact_lower:
            legal_basis = EvidenceLegalBasis.FZ_135
        else:
            legal_basis = EvidenceLegalBasis.FZ_44
        mitigation_strategy = "Не митигируемо (нарушение закона нельзя исправить участнику)"
        legal_consequences = "Закупка может быть отменена или оспорена в ФАС"
        reference_in_kb = "laws/fz-44-2013.md"
        iun_contribution = 30
        mitigation_cost_estimate = None  # Не митигируемо
        mitigation_time_days = None
    
    # Определяем DEADLINE_TIGHT
    elif any(keyword in fact_lower for keyword in ["срок", "дедлайн", "короткий", "недостаточно времени"]):
        if evidence.classification == EvidenceClassification.CONTROLLED_RISK:
            sub_classification = EvidenceSubClassification.DEADLINE_TIGHT
            iun_contribution = 10
            mitigation_strategy = "Организовать быструю подготовку заявки"
            mitigation_time_days = 0  # Только время на подготовку
    
    # Определяем PENALTY_RISK
    elif any(keyword in fact_lower for keyword in ["штраф", "неустойка", "10%", "пеня"]):
        if evidence.classification == EvidenceClassification.CONTROLLED_RISK:
            sub_classification = EvidenceSubClassification.PENALTY_RISK
            legal_basis = EvidenceLegalBasis.FZ_44 if applies_to_44fz else EvidenceLegalBasis.FZ_223
            reference_in_kb = "risks/financial-risks.md"
            iun_contribution = 5
            mitigation_strategy = "Строгий контроль сроков поставки"
            legal_consequences = "Штраф 10% от цены контракта при нарушении срока (44-ФЗ, ст. 99)"
    
    # Определяем MARKET NOISE
    elif evidence.classification == EvidenceClassification.MARKET_NOISE:
        if any(keyword in fact_lower for keyword in ["дублирует", "повторяет", "стандарт"]):
            sub_classification = EvidenceSubClassification.REDUNDANT_REQUIREMENT
        elif any(keyword in fact_lower for keyword in ["неясно", "неопределенно", "расплывчато"]):
            sub_classification = EvidenceSubClassification.VAGUE_SPECIFICATION
        else:
            sub_classification = EvidenceSubClassification.STANDARD_PROCEDURE
    
    # Создаем расширенный объект
    extended = EvidenceExtendedModel(
        # Базовые поля из EvidenceObject
        evidence_id=evidence.evidence_id,
        source_file=evidence.source_file,
        fact=evidence.fact,
        classification=evidence.classification,
        financial_impact_rub=evidence.financial_impact_rub,
        confidence=evidence.confidence,
        derived_from=evidence.derived_from,
        page_reference=evidence.page_reference,
        section_reference=evidence.section_reference,
        raw_extract=evidence.raw_extract,
        
        # Новые поля
        sub_classification=sub_classification,
        legal_basis=legal_basis,
        applies_to_44fz=applies_to_44fz,
        applies_to_223fz=applies_to_223fz,
        mitigation_strategy=mitigation_strategy,
        legal_consequences=legal_consequences,
        reference_in_kb=reference_in_kb,
        iun_contribution=iun_contribution,
        mitigation_cost_estimate=mitigation_cost_estimate,
        mitigation_time_days=mitigation_time_days,
    )
    
    return extended


def convert_to_extended(
    evidence_list: List[EvidenceObject],
    procurement_law: str = "44-ФЗ"
) -> List[EvidenceExtendedModel]:
    """
    Конвертирует список базовых EvidenceObject в EvidenceExtendedModel.
    
    Args:
        evidence_list: Список базовых EvidenceObject
        procurement_law: "44-ФЗ" или "223-ФЗ"
    
    Returns:
        Список EvidenceExtendedModel
    """
    return [
        classify_evidence_for_procurement(evidence, procurement_law)
        for evidence in evidence_list
    ]


