"""
Kill Switch Types — ШАГ 13

Типы и константы для Kill Switch механизма.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class SystemMode(str, Enum):
    """Режимы работы системы."""
    NORMAL = "NORMAL"  # Reasoning включён, все шаги активны
    SAFE = "SAFE"  # Reasoning отключён, Evidence доступен, Decision ограничен
    LOCKDOWN = "LOCKDOWN"  # Reasoning отключён, новые решения запрещены, только Audit Trail


class KillSwitchTrigger(str, Enum):
    """Триггеры активации Kill Switch."""
    # Автоматические
    CI_GUARDRAIL_FAIL = "ci_guardrail_fail"
    RED_TEAM_VIOLATION = "red_team_violation"
    SNAPSHOT_MISMATCH = "snapshot_mismatch"
    UNPREDICTABLE_MODEL_OUTPUT = "unpredictable_model_output"
    MCP_VALIDATION_FAIL = "mcp_validation_fail"
    
    # Ручные
    SECURITY_COMMAND = "security_command"
    COMPLIANCE_REQUIREMENT = "compliance_requirement"
    ENTERPRISE_CLIENT = "enterprise_client"
    ON_PREM_OFFLINE = "on_prem_offline"
    MANUAL_ADMIN = "manual_admin"


class KillSwitchActivation(BaseModel):
    """Активация Kill Switch."""
    activation_id: str = Field(default_factory=lambda: f"KS-{uuid.uuid4().hex[:8].upper()}")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    trigger: KillSwitchTrigger = Field(..., description="Триггер активации")
    reason: str = Field(..., description="Причина активации")
    previous_mode: SystemMode = Field(..., description="Предыдущий режим")
    new_mode: SystemMode = Field(..., description="Новый режим")
    activated_by: Optional[str] = Field(None, description="ID пользователя/системы, активировавшего")
    system_version: Optional[str] = Field(None, description="Версия системы при активации")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Дополнительные метаданные")


class KillSwitchStatus(BaseModel):
    """Текущий статус Kill Switch."""
    current_mode: SystemMode = Field(default=SystemMode.NORMAL)
    is_active: bool = Field(default=False, description="Активен ли Kill Switch")
    last_activation: Optional[KillSwitchActivation] = Field(None, description="Последняя активация")
    activation_history: List[KillSwitchActivation] = Field(default_factory=list, description="История активаций")


class SafeModeLimits(BaseModel):
    """Ограничения в Safe Mode."""
    reasoning_enabled: bool = Field(default=False, description="Reasoning отключён")
    new_decisions_allowed: bool = Field(default=False, description="Новые решения запрещены")
    evidence_access: bool = Field(default=True, description="Evidence доступен")
    audit_trail_access: bool = Field(default=True, description="Audit Trail доступен")
    last_decision_access: bool = Field(default=True, description="Доступ к последнему решению")































