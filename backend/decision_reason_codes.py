"""
Decision Reason Codes — ШАГ 7: Стратегическая память отказов

Каждое решение "НЕ УЧАСТВОВАТЬ" обязано иметь Reason Codes
для корпоративной памяти и управленческой статистики.
"""

from typing import List, Literal
from enum import Enum


class DecisionReasonCode(str, Enum):
    """
    Коды причин решения "НЕ УЧАСТВОВАТЬ".
    
    Это корпоративная память отказов, не ML и не оптимизация.
    """
    # DEAL_BREAKER причины
    UNBOUNDED_PENALTY = "unbounded_penalty"  # Неограниченная неустойка/штраф
    CONTRACTUAL_ASYMMETRY = "contractual_asymmetry"  # Асимметричная ответственность
    IRREVERSIBLE_OBLIGATION = "irreversible_obligation"  # Необратимое обязательство
    CRITICAL_UNCERTAINTY = "critical_uncertainty"  # Критическая неопределённость без контроля
    
    # Финансовые причины
    FINANCIAL_EXPOSURE_EXCEEDS_LIMIT = "financial_exposure_exceeds_limit"  # Финансовая экспозиция превышает лимит
    PAYMENT_TERMS_UNACCEPTABLE = "payment_terms_unacceptable"  # Неприемлемые условия оплаты
    GUARANTEE_REQUIREMENTS_EXCESSIVE = "guarantee_requirements_excessive"  # Чрезмерные требования к обеспечению
    
    # Процедурные причины
    DEADLINE_UNREALISTIC = "deadline_unrealistic"  # Нереалистичные сроки
    DOCUMENTATION_INCOMPLETE = "documentation_incomplete"  # Неполная документация
    CONTRADICTIONS_UNRESOLVABLE = "contradictions_unresolvable"  # Неразрешимые противоречия
    
    # Технические причины
    TECHNICAL_REQUIREMENTS_UNMET = "technical_requirements_unmet"  # Технические требования не выполнены
    LICENSES_MISSING = "licenses_missing"  # Отсутствуют необходимые лицензии
    
    # Стратегические причины
    STRATEGIC_MISMATCH = "strategic_mismatch"  # Стратегическое несоответствие
    MARKET_CONDITIONS_UNFAVORABLE = "market_conditions_unfavorable"  # Неблагоприятные рыночные условия
    
    # Низкая уверенность в данных
    LOW_EVIDENCE = "low_evidence"  # Недостаточно данных для управленческого решения


def extract_reason_codes_from_decision(
    decision: str,
    deal_breakers: List[dict],
    controlled_risks: List[dict],
    contradictions: List[dict],
    financial_exposure: dict,
    management_load: dict
) -> List[DecisionReasonCode]:
    """
    Извлекает Reason Codes из решения "НЕ УЧАСТВОВАТЬ".
    
    Это стратегическая память, не ML-классификация.
    """
    if decision != "DO_NOT_PARTICIPATE":
        return []
    
    reason_codes: List[DecisionReasonCode] = []
    
    # Проверяем DEAL_BREAKER причины
    for db in deal_breakers:
        db_title_lower = (db.get("title", "") or "").lower()
        db_description_lower = (db.get("description", "") or "").lower()
        
        if any(kw in db_title_lower or kw in db_description_lower for kw in ["неограничен", "без ограничений", "без верхнего предела"]):
            reason_codes.append(DecisionReasonCode.UNBOUNDED_PENALTY)
        
        if any(kw in db_title_lower or kw in db_description_lower for kw in ["асимметричн", "односторонн", "ответственность только"]):
            reason_codes.append(DecisionReasonCode.CONTRACTUAL_ASYMMETRY)
        
        if any(kw in db_title_lower or kw in db_description_lower for kw in ["необратим", "без права отказа", "не может быть отменено"]):
            reason_codes.append(DecisionReasonCode.IRREVERSIBLE_OBLIGATION)
        
        if any(kw in db_title_lower or kw in db_description_lower for kw in ["неопределён", "неясно", "требует уточнения"]) and "контроль" not in db_title_lower:
            reason_codes.append(DecisionReasonCode.CRITICAL_UNCERTAINTY)
    
    # Проверяем финансовые причины
    if financial_exposure:
        potential_costs = financial_exposure.get("potential_extra_costs_rub", 0) or 0
        if potential_costs > 10_000_000:  # 10 млн руб — примерный порог
            reason_codes.append(DecisionReasonCode.FINANCIAL_EXPOSURE_EXCEEDS_LIMIT)
        
        funds_blocking = financial_exposure.get("funds_blocking_percent", "0%")
        if funds_blocking and "%" in funds_blocking:
            try:
                blocking_pct = float(funds_blocking.replace("%", "").strip())
                if blocking_pct > 30:  # Блокировка более 30%
                    reason_codes.append(DecisionReasonCode.GUARANTEE_REQUIREMENTS_EXCESSIVE)
            except (ValueError, AttributeError):
                pass
    
    # Проверяем противоречия
    if contradictions and len(contradictions) > 2:
        reason_codes.append(DecisionReasonCode.CONTRADICTIONS_UNRESOLVABLE)
    
    # Проверяем управленческую нагрузку
    if management_load:
        load_value = management_load.get("value", 0) or 0
        if load_value > 85:
            reason_codes.append(DecisionReasonCode.CRITICAL_UNCERTAINTY)
    
    # Если нет конкретных причин, но решение "НЕ УЧАСТВОВАТЬ" — низкая уверенность
    if not reason_codes and deal_breakers:
        reason_codes.append(DecisionReasonCode.LOW_EVIDENCE)
    
    # Убираем дубликаты, сохраняя порядок
    seen = set()
    unique_codes = []
    for code in reason_codes:
        if code not in seen:
            seen.add(code)
            unique_codes.append(code)
    
    return unique_codes


def format_reason_codes_for_statistics(reason_codes: List[DecisionReasonCode]) -> dict:
    """
    Форматирует Reason Codes для управленческой статистики.
    
    Это корпоративная память отказов.
    """
    if not reason_codes:
        return {}
    
    # Группируем по категориям
    categories = {
        "deal_breaker": [],
        "financial": [],
        "procedural": [],
        "technical": [],
        "strategic": [],
        "uncertainty": [],
    }
    
    for code in reason_codes:
        if code in [
            DecisionReasonCode.UNBOUNDED_PENALTY,
            DecisionReasonCode.CONTRACTUAL_ASYMMETRY,
            DecisionReasonCode.IRREVERSIBLE_OBLIGATION,
        ]:
            categories["deal_breaker"].append(code.value)
        elif code in [
            DecisionReasonCode.FINANCIAL_EXPOSURE_EXCEEDS_LIMIT,
            DecisionReasonCode.PAYMENT_TERMS_UNACCEPTABLE,
            DecisionReasonCode.GUARANTEE_REQUIREMENTS_EXCESSIVE,
        ]:
            categories["financial"].append(code.value)
        elif code in [
            DecisionReasonCode.DEADLINE_UNREALISTIC,
            DecisionReasonCode.DOCUMENTATION_INCOMPLETE,
            DecisionReasonCode.CONTRADICTIONS_UNRESOLVABLE,
        ]:
            categories["procedural"].append(code.value)
        elif code in [
            DecisionReasonCode.TECHNICAL_REQUIREMENTS_UNMET,
            DecisionReasonCode.LICENSES_MISSING,
        ]:
            categories["technical"].append(code.value)
        elif code in [
            DecisionReasonCode.STRATEGIC_MISMATCH,
            DecisionReasonCode.MARKET_CONDITIONS_UNFAVORABLE,
        ]:
            categories["strategic"].append(code.value)
        elif code in [
            DecisionReasonCode.CRITICAL_UNCERTAINTY,
            DecisionReasonCode.LOW_EVIDENCE,
        ]:
            categories["uncertainty"].append(code.value)
    
    return {
        "reason_codes": [code.value for code in reason_codes],
        "categories": {k: v for k, v in categories.items() if v},
        "primary_reason": reason_codes[0].value if reason_codes else None,
    }































