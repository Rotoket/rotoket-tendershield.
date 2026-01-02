"""
Reasoning Types — ШАГ 4: Reasoning & Decision Layer

Этот модуль определяет типы для преобразования Evidence Objects
в управленческие выводы и решения.
"""

from typing import Literal, List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from evidence_types import EvidenceObject, EvidenceClassification, EvidenceConfidence


class RiskType(str, Enum):
    """Тип риска по управленческому воздействию."""
    FINANCIAL = "FINANCIAL"
    LEGAL = "LEGAL"
    OPERATIONAL = "OPERATIONAL"
    TECHNICAL = "TECHNICAL"


class RiskSignal(BaseModel):
    """
    Risk Signal — управленческое следствие из Evidence Objects.
    
    Один Evidence ≠ один Risk.
    Риск может возникать только из связки Evidence.
    """
    risk_id: str = Field(..., description="Уникальный идентификатор риска (R-XXX)")
    derived_from: List[str] = Field(..., description="Список evidence_id, из которых выведен риск")
    risk_type: RiskType = Field(..., description="Тип риска")
    classification: EvidenceClassification = Field(..., description="Классификация по управленческому воздействию")
    description: str = Field(..., description="Описание риска (управленческое следствие)")
    why_it_matters: str = Field(..., description="Почему это важно для директора")
    financial_impact_rub: Optional[float] = Field(None, description="Финансовое воздействие в рублях")
    confidence: EvidenceConfidence = Field(..., description="Уровень уверенности в риске")


class Contradiction(BaseModel):
    """
    Противоречие между Evidence Objects.
    
    Противоречие = рост управленческой нагрузки.
    """
    contradiction_id: str = Field(..., description="Уникальный идентификатор противоречия (C-XXX)")
    evidence_ids: List[str] = Field(..., description="Список evidence_id, которые противоречат друг другу")
    description: str = Field(..., description="Описание противоречия")
    impact: str = Field(..., description="Управленческое воздействие противоречия")
    resolution_hint: Optional[str] = Field(None, description="Подсказка по разрешению (если применимо)")


class DecisionNode(BaseModel):
    """
    Узел Decision Graph.
    
    Каждое решение должно быть восстановимо как граф:
    Evidence → Risk → Contradiction → Load → Decision
    """
    node_id: str
    node_type: Literal["evidence", "risk", "contradiction", "load_factor", "decision"]
    content: Dict[str, Any]
    connections: List[str] = Field(default_factory=list, description="ID связанных узлов")


class DecisionGraph(BaseModel):
    """
    Decision Graph — audit-ready структура решения.
    
    Это не текст, а структурированный граф для восстановления логики.
    """
    graph_id: str
    nodes: List[DecisionNode] = Field(default_factory=list)
    root_decision: Optional[str] = Field(None, description="ID финального узла решения")


class ManagementLoadExplanation(BaseModel):
    """
    Объяснение управленческой нагрузки (не числовой ИУН).
    
    ШАГ 4 НЕ считает ИУН численно, но обязан объяснять источники нагрузки.
    """
    sources: List[str] = Field(default_factory=list, description="Источники роста нагрузки")
    contradictions_count: int = Field(0, description="Количество противоречий")
    low_confidence_evidence_count: int = Field(0, description="Количество Evidence с низкой уверенностью")
    non_standard_conditions: List[str] = Field(default_factory=list, description="Нестандартные условия")
    manual_verification_required: List[str] = Field(default_factory=list, description="Требует ручной верификации")


class DecisionPreview(BaseModel):
    """
    Decision Preview — формат для директора (board-ready).
    
    Обязательные поля для управленческого вывода.
    """
    decision: Literal["PARTICIPATE", "DO_NOT_PARTICIPATE", "PARTICIPATE_WITH_CONDITIONS"] = Field(
        ..., description="Итоговое решение"
    )
    why: List[str] = Field(..., min_items=2, max_items=4, description="2-4 ключевых причины решения")
    main_risk: Optional[str] = Field(None, description="Главный риск (если есть DEAL_BREAKER — он здесь)")
    management_load: ManagementLoadExplanation = Field(..., description="Объяснение управленческой нагрузки")
    risk_mitigation: Optional[List[str]] = Field(None, description="Что нужно для снятия риска (если применимо)")
    
    # Структурированные данные для UI
    deal_breakers: List[RiskSignal] = Field(default_factory=list)
    controlled_risks: List[RiskSignal] = Field(default_factory=list)
    contradictions: List[Contradiction] = Field(default_factory=list)
    decision_graph: Optional[DecisionGraph] = Field(None, description="Decision Graph для audit trail")


class ReasoningResult(BaseModel):
    """
    Результат Reasoning Layer (ШАГ 4).
    
    Содержит все преобразования: Evidence → Risk → Contradiction → Decision.
    
    ФАЗА 3: Добавлено поле procurement_analysis для специализированного анализа закупок.
    """
    risk_signals: List[RiskSignal] = Field(default_factory=list)
    contradictions: List[Contradiction] = Field(default_factory=list)
    decision_preview: DecisionPreview
    decision_graph: DecisionGraph
    reasoning_errors: List[str] = Field(default_factory=list, description="Ошибки reasoning (если были)")
    procurement_analysis: Optional[Any] = Field(None, description="ФАЗА 3: Специализированный анализ закупок (ProcurementAnalysis)")





























