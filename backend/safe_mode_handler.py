"""
Safe Mode Handler — ШАГ 13

Обработка запросов в Safe Mode (без reasoning).
"""

from typing import Dict, Any, Optional, List
from kill_switch_manager import get_kill_switch_manager
from kill_switch_types import SystemMode, SafeModeLimits
from audit_trail_manager import AuditTrailManager
from audit_trail_types import DecisionSnapshot


class SafeModeHandler:
    """
    Обработчик запросов в Safe Mode.
    
    В Safe Mode система НЕ ИМЕЕТ ПРАВА:
    - интерпретировать риски
    - формировать новые Decision Graph
    - менять классификации
    
    Разрешено:
    - показывать последнее актуальное решение
    - показывать Evidence Objects
    - показывать Audit Trail
    - явно сообщать об ограничениях
    """
    
    def __init__(self):
        self.kill_switch = get_kill_switch_manager()
        self.audit_trail = AuditTrailManager() if AuditTrailManager else None
    
    def get_safe_mode_response(self, tender_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Возвращает ответ системы в Safe Mode.
        
        Args:
            tender_id: ID тендера (опционально, для получения последнего решения)
        
        Returns:
            Словарь с ограниченным ответом системы
        """
        mode = self.kill_switch.get_current_mode()
        limits = self.kill_switch.get_safe_mode_limits()
        last_activation = self.kill_switch.get_status().last_activation
        
        response = {
            "mode": mode.value,
            "reasoning_enabled": limits.reasoning_enabled,
            "new_decisions_allowed": limits.new_decisions_allowed,
            "message": self._get_mode_message(mode),
            "last_activation": {
                "id": last_activation.activation_id if last_activation else None,
                "timestamp": last_activation.timestamp if last_activation else None,
                "reason": last_activation.reason if last_activation else None,
            } if last_activation else None,
        }
        
        # Если есть tender_id, пытаемся получить последнее решение
        if tender_id and limits.last_decision_access:
            last_decision = self._get_last_decision(tender_id)
            if last_decision:
                response["last_decision"] = {
                    "decision_id": last_decision.decision_id,
                    "decision": last_decision.decision,
                    "created_at": last_decision.created_at,
                    "freshness_status": last_decision.freshness_status.value,
                    "note": "Это решение было сформировано до активации Safe Mode. "
                           "Новые решения не формируются в текущем режиме.",
                }
        
        return response
    
    def _get_mode_message(self, mode: SystemMode) -> str:
        """Возвращает сообщение для режима."""
        if mode == SystemMode.SAFE:
            return (
                "Reasoning временно отключён. "
                "Система работает в безопасном режиме. "
                "Новые управленческие выводы не формируются."
            )
        elif mode == SystemMode.LOCKDOWN:
            return (
                "Система в режиме блокировки. "
                "Новые анализы и решения запрещены. "
                "Доступен только просмотр истории (Audit Trail)."
            )
        else:
            return "Система работает в нормальном режиме."
    
    def _get_last_decision(self, tender_id: str) -> Optional[DecisionSnapshot]:
        """Получает последнее решение для тендера."""
        # TODO: Реализовать получение последнего решения из Audit Trail
        # Пока возвращаем None
        return None
    
    def can_process_new_analysis(self) -> bool:
        """Проверяет, можно ли обрабатывать новый анализ."""
        limits = self.kill_switch.get_safe_mode_limits()
        return limits.new_decisions_allowed and limits.reasoning_enabled
    
    def get_evidence_only_response(
        self,
        evidence_objects: List[Dict[str, Any]],
        document_snapshot_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Возвращает ответ только с Evidence Objects (без reasoning).
        
        Используется в Safe Mode, когда reasoning отключён.
        """
        mode = self.kill_switch.get_current_mode()
        limits = self.kill_switch.get_safe_mode_limits()
        
        if not limits.evidence_access:
            return {
                "error": "Доступ к Evidence Objects запрещён в текущем режиме.",
                "mode": mode.value,
            }
        
        return {
            "mode": mode.value,
            "reasoning_enabled": False,
            "evidence_objects": evidence_objects,
            "document_snapshot_id": document_snapshot_id,
            "message": (
                "Evidence Objects извлечены, но reasoning отключён. "
                "Управленческие выводы не формируются."
            ),
            "safe_mode_limits": limits.dict(),
        }

