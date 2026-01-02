"""
Evidence Adapter — преобразование Evidence Objects в формат для LLM.

Этот модуль адаптирует структурированные Evidence Objects для передачи в LLM.
LLM получает только готовые Evidence, не сырой текст.
"""

import logging
from typing import List, Dict, Any
from evidence_types import EvidenceObject, EvidenceClassification, EvidenceConfidence

logger = logging.getLogger(__name__)


def evidence_objects_to_llm_prompt(evidence_objects: List[EvidenceObject]) -> str:
    """
    Преобразует массив Evidence Objects в текстовый промпт для LLM.
    
    LLM работает только с этим форматом, не с сырым текстом.
    """
    if not evidence_objects:
        return "Evidence Objects не извлечены. Анализ невозможен без структурированных фактов."
    
    lines = [
        "=== EVIDENCE OBJECTS (структурированные факты из документов) ===",
        "",
        "ВАЖНО: Эти факты извлечены детерминированно через препроцессинг.",
        "Твоя задача — reasoning на основе этих фактов, не извлечение новых.",
        "",
    ]
    
    # Группируем по классификации
    deal_breakers = [e for e in evidence_objects if e.classification == EvidenceClassification.DEAL_BREAKER]
    controlled_risks = [e for e in evidence_objects if e.classification == EvidenceClassification.CONTROLLED_RISK]
    market_noise = [e for e in evidence_objects if e.classification == EvidenceClassification.MARKET_NOISE]
    
    # DEAL BREAKERS
    if deal_breakers:
        lines.append("--- КРИТИЧЕСКИЕ СТОП-ФАКТОРЫ (DEAL_BREAKER) ---")
        for i, ev in enumerate(deal_breakers, 1):
            lines.append(f"{i}. {ev.fact}")
            lines.append(f"   Источник: {ev.source_file}")
            if ev.section_reference:
                lines.append(f"   Раздел/пункт: {ev.section_reference}")
            if ev.page_reference:
                lines.append(f"   Страница/лист: {ev.page_reference}")
            if ev.financial_impact_rub:
                lines.append(f"   Финансовое воздействие: {ev.financial_impact_rub} руб.")
            lines.append(f"   Уверенность: {ev.confidence.value}")
            if ev.raw_extract:
                lines.append(f"   Сырой фрагмент: {ev.raw_extract[:200]}")
            lines.append("")
    
    # CONTROLLED RISKS
    if controlled_risks:
        lines.append("--- УПРАВЛЯЕМЫЕ РИСКИ (CONTROLLED_RISK) ---")
        for i, ev in enumerate(controlled_risks, 1):
            lines.append(f"{i}. {ev.fact}")
            lines.append(f"   Источник: {ev.source_file}")
            if ev.section_reference:
                lines.append(f"   Раздел/пункт: {ev.section_reference}")
            if ev.page_reference:
                lines.append(f"   Страница/лист: {ev.page_reference}")
            if ev.financial_impact_rub:
                lines.append(f"   Финансовое воздействие: {ev.financial_impact_rub} руб.")
            lines.append(f"   Уверенность: {ev.confidence.value}")
            if ev.confidence == EvidenceConfidence.LOW:
                lines.append("   ⚠️ НИЗКАЯ УВЕРЕННОСТЬ: факт требует дополнительной проверки")
            if ev.raw_extract:
                lines.append(f"   Сырой фрагмент: {ev.raw_extract[:200]}")
            lines.append("")
    
    # MARKET NOISE
    if market_noise:
        lines.append("--- РЫНОЧНЫЕ ФАКТОРЫ (MARKET_NOISE) ---")
        for i, ev in enumerate(market_noise, 1):
            lines.append(f"{i}. {ev.fact}")
            lines.append(f"   Источник: {ev.source_file}")
            lines.append("")
    
    lines.append("=== КОНЕЦ EVIDENCE OBJECTS ===")
    lines.append("")
    lines.append("ИНСТРУКЦИЯ ДЛЯ LLM:")
    lines.append("- Используй ТОЛЬКО эти факты для reasoning")
    lines.append("- НЕ пытайся извлекать новые факты из сырого текста")
    lines.append("- Если уверенность LOW — явно укажи это в выводе")
    lines.append("- Финансовые воздействия используй для расчёта ИУН")
    
    return "\n".join(lines)


def evidence_objects_to_summary(evidence_objects: List[EvidenceObject]) -> Dict[str, Any]:
    """
    Формирует краткую сводку по Evidence Objects для логирования.
    """
    deal_breakers_count = sum(1 for e in evidence_objects if e.classification == EvidenceClassification.DEAL_BREAKER)
    controlled_risks_count = sum(1 for e in evidence_objects if e.classification == EvidenceClassification.CONTROLLED_RISK)
    market_noise_count = sum(1 for e in evidence_objects if e.classification == EvidenceClassification.MARKET_NOISE)
    
    high_confidence = sum(1 for e in evidence_objects if e.confidence == EvidenceConfidence.HIGH)
    medium_confidence = sum(1 for e in evidence_objects if e.confidence == EvidenceConfidence.MEDIUM)
    low_confidence = sum(1 for e in evidence_objects if e.confidence == EvidenceConfidence.LOW)
    
    total_financial_impact = sum(
        e.financial_impact_rub for e in evidence_objects
        if e.financial_impact_rub is not None
    )
    
    return {
        "total_evidence_count": len(evidence_objects),
        "deal_breakers_count": deal_breakers_count,
        "controlled_risks_count": controlled_risks_count,
        "market_noise_count": market_noise_count,
        "confidence_distribution": {
            "high": high_confidence,
            "medium": medium_confidence,
            "low": low_confidence,
        },
        "total_financial_impact_rub": total_financial_impact if total_financial_impact > 0 else None,
    }































