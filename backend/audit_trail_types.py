"""
Audit Trail Types — ШАГ 6: Audit Trail, Versioning & Decision Freshness

Этот модуль определяет типы для версионирования и контроля актуальности решений.
"""

from typing import Literal, List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class DecisionFreshnessStatus(str, Enum):
    """Статус актуальности решения."""
    ACTUAL = "ACTUAL"
    STALE = "STALE"
    INVALIDATED = "INVALIDATED"


class DocumentSnapshot(BaseModel):
    """
    Document Snapshot — снимок документов на момент анализа.
    
    ОБЯЗАТЕЛЬНЫЙ АРТЕФАКТ ШАГА 6.
    """
    snapshot_id: str = Field(..., description="Уникальный идентификатор снимка (DS-XXXX)")
    files: List[Dict[str, Any]] = Field(..., description="Список файлов с метаданными")
    hash: str = Field(..., description="SHA256 хеш набора документов")
    created_at: str = Field(..., description="ISO timestamp создания снимка")
    industry: Optional[str] = Field(None, description="Отрасль анализа")


class EvidenceSnapshot(BaseModel):
    """
    Evidence Snapshot — снимок Evidence Objects на момент reasoning.
    
    ОБЯЗАТЕЛЬНЫЙ АРТЕФАКТ ШАГА 6.
    """
    evidence_set_id: str = Field(..., description="Уникальный идентификатор набора Evidence (ES-XXXX)")
    derived_from: str = Field(..., description="ID Document Snapshot, из которого извлечены Evidence")
    evidence_objects: List[Dict[str, Any]] = Field(..., description="Массив Evidence Objects (сериализованных)")
    mcp_versions: Dict[str, str] = Field(default_factory=dict, description="Версии MCP-нод, использованных для извлечения")
    created_at: str = Field(..., description="ISO timestamp создания снимка")
    evidence_hash: str = Field(..., description="SHA256 хеш набора Evidence Objects")


class DecisionSnapshot(BaseModel):
    """
    Decision Snapshot — снимок решения на момент фиксации.
    
    ОБЯЗАТЕЛЬНЫЙ АРТЕФАКТ ШАГА 6.
    """
    decision_id: str = Field(..., description="Уникальный идентификатор решения (D-XXXX)")
    derived_from: str = Field(..., description="ID Evidence Snapshot, из которого сформировано решение")
    decision: Literal["PARTICIPATE", "DO_NOT_PARTICIPATE", "PARTICIPATE_WITH_CONDITIONS"] = Field(
        ..., description="Итоговое решение"
    )
    decision_preview: Dict[str, Any] = Field(..., description="Decision Preview (сериализованный)")
    decision_graph: Optional[Dict[str, Any]] = Field(None, description="Decision Graph (сериализованный)")
    created_at: str = Field(..., description="ISO timestamp создания решения")
    created_by: Optional[str] = Field(None, description="ID пользователя, принявшего решение")
    comment: Optional[str] = Field(None, description="Комментарий директора")
    freshness_status: DecisionFreshnessStatus = Field(
        default=DecisionFreshnessStatus.ACTUAL,
        description="Статус актуальности решения"
    )
    freshness_reason: Optional[str] = Field(None, description="Причина устаревания (если применимо)")
    # ШАГ 7: Reason Codes для решений "НЕ УЧАСТВОВАТЬ" (стратегическая память)
    reason_codes: List[str] = Field(default_factory=list, description="Коды причин решения (для корпоративной памяти)")


class AuditTrailChain(BaseModel):
    """
    Audit Trail Chain — структурированная цепочка версий.
    
    Document Version → Evidence Objects → Risk Signals → Decision Graph → Decision Preview
    """
    chain_id: str = Field(..., description="Уникальный идентификатор цепочки")
    document_snapshot: DocumentSnapshot
    evidence_snapshot: Optional[EvidenceSnapshot] = None
    decision_snapshot: Optional[DecisionSnapshot] = None
    created_at: str = Field(..., description="ISO timestamp создания цепочки")
    updated_at: str = Field(..., description="ISO timestamp последнего обновления")


class FreshnessCheckResult(BaseModel):
    """
    Результат проверки актуальности решения.
    """
    status: DecisionFreshnessStatus
    reason: Optional[str] = None
    invalidated_by: Optional[str] = Field(None, description="ID нового snapshot, который инвалидировал решение")
    check_timestamp: str = Field(..., description="ISO timestamp проверки")

