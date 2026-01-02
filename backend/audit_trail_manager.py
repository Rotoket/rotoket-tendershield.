"""
Audit Trail Manager — ШАГ 6: Управление версионированием и актуальностью

КЛЮЧЕВОЙ ПРИНЦИП:
РЕШЕНИЕ БЕЗ ИСТОРИИ = НЕДЕЙСТВИТЕЛЬНОЕ РЕШЕНИЕ
"""

import logging
import hashlib
import json
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from audit_trail_types import (
    DocumentSnapshot,
    EvidenceSnapshot,
    DecisionSnapshot,
    AuditTrailChain,
    DecisionFreshnessStatus,
    FreshnessCheckResult,
)

logger = logging.getLogger(__name__)


class AuditTrailManager:
    """
    Менеджер Audit Trail и версионирования.
    
    ШАГ 6 НЕ АНАЛИЗИРУЕТ
    ШАГ 6 НЕ ПРИНИМАЕТ РЕШЕНИЙ
    ШАГ 6 НЕ МЕНЯЕТ ВЫВОД
    
    Он ФИКСИРУЕТ И КОНТРОЛИРУЕТ.
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Инициализация менеджера.
        
        Args:
            storage_path: Путь для хранения snapshots (если None, используется in-memory)
        """
        self.storage_path = storage_path or Path("audit_trail_storage")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory хранилище (для production можно заменить на БД)
        self._document_snapshots: Dict[str, DocumentSnapshot] = {}
        self._evidence_snapshots: Dict[str, EvidenceSnapshot] = {}
        self._decision_snapshots: Dict[str, DecisionSnapshot] = {}
        self._audit_chains: Dict[str, AuditTrailChain] = {}
    
    def create_document_snapshot(
        self,
        files: List[Dict[str, Any]],
        industry: Optional[str] = None
    ) -> DocumentSnapshot:
        """
        Создаёт Document Snapshot.
        
        Любое изменение документов → новая версия.
        """
        # Вычисляем хеш набора документов
        files_data = json.dumps(files, sort_keys=True, ensure_ascii=False)
        files_hash = hashlib.sha256(files_data.encode('utf-8')).hexdigest()
        
        snapshot_id = f"DS-{uuid.uuid4().hex[:8].upper()}"
        
        snapshot = DocumentSnapshot(
            snapshot_id=snapshot_id,
            files=files,
            hash=files_hash,
            created_at=datetime.utcnow().isoformat(),
            industry=industry,
        )
        
        self._document_snapshots[snapshot_id] = snapshot
        self._save_snapshot(snapshot, "document")
        
        logger.info(f"✅ Document Snapshot создан: {snapshot_id} (hash: {files_hash[:16]}...)")
        return snapshot
    
    def create_evidence_snapshot(
        self,
        document_snapshot_id: str,
        evidence_objects: List[Dict[str, Any]],
        mcp_versions: Optional[Dict[str, str]] = None
    ) -> EvidenceSnapshot:
        """
        Создаёт Evidence Snapshot.
        
        Любое изменение Evidence → новая версия.
        """
        # Вычисляем хеш набора Evidence Objects
        evidence_data = json.dumps(evidence_objects, sort_keys=True, ensure_ascii=False)
        evidence_hash = hashlib.sha256(evidence_data.encode('utf-8')).hexdigest()
        
        evidence_set_id = f"ES-{uuid.uuid4().hex[:8].upper()}"
        
        snapshot = EvidenceSnapshot(
            evidence_set_id=evidence_set_id,
            derived_from=document_snapshot_id,
            evidence_objects=evidence_objects,
            mcp_versions=mcp_versions or {},
            created_at=datetime.utcnow().isoformat(),
            evidence_hash=evidence_hash,
        )
        
        self._evidence_snapshots[evidence_set_id] = snapshot
        self._save_snapshot(snapshot, "evidence")
        
        logger.info(f"✅ Evidence Snapshot создан: {evidence_set_id} (derived from: {document_snapshot_id})")
        return snapshot
    
    def create_decision_snapshot(
        self,
        evidence_snapshot_id: str,
        decision: str,
        decision_preview: Dict[str, Any],
        decision_graph: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None,
        comment: Optional[str] = None,
        reason_codes: Optional[List[str]] = None
    ) -> DecisionSnapshot:
        """
        Создаёт Decision Snapshot.
        
        Любое изменение решения → новая версия.
        """
        decision_id = f"D-{uuid.uuid4().hex[:8].upper()}"
        
        snapshot = DecisionSnapshot(
            decision_id=decision_id,
            derived_from=evidence_snapshot_id,
            decision=decision,
            decision_preview=decision_preview,
            decision_graph=decision_graph,
            created_at=datetime.utcnow().isoformat(),
            created_by=created_by,
            comment=comment,
            freshness_status=DecisionFreshnessStatus.ACTUAL,
            reason_codes=reason_codes or [],
        )
        
        self._decision_snapshots[decision_id] = snapshot
        self._save_snapshot(snapshot, "decision")
        
        logger.info(f"✅ Decision Snapshot создан: {decision_id} (decision: {decision})")
        return snapshot
    
    def create_audit_chain(
        self,
        document_snapshot: DocumentSnapshot,
        evidence_snapshot: Optional[EvidenceSnapshot] = None,
        decision_snapshot: Optional[DecisionSnapshot] = None
    ) -> AuditTrailChain:
        """
        Создаёт Audit Trail Chain — структурированную цепочку версий.
        """
        chain_id = f"CHAIN-{uuid.uuid4().hex[:8].upper()}"
        
        chain = AuditTrailChain(
            chain_id=chain_id,
            document_snapshot=document_snapshot,
            evidence_snapshot=evidence_snapshot,
            decision_snapshot=decision_snapshot,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        )
        
        self._audit_chains[chain_id] = chain
        self._save_snapshot(chain, "chain")
        
        logger.info(f"✅ Audit Trail Chain создан: {chain_id}")
        return chain
    
    def check_decision_freshness(
        self,
        decision_id: str,
        current_document_snapshot_id: Optional[str] = None
    ) -> FreshnessCheckResult:
        """
        Проверяет актуальность решения (Decision Freshness Guard).
        
        ШАГ 6 НЕ ПЕРЕСЧИТЫВАЕТ РЕШЕНИЕ,
        он ТОЛЬКО СИГНАЛИЗИРУЕТ, что решение больше нельзя считать актуальным.
        """
        decision_snapshot = self._decision_snapshots.get(decision_id)
        if not decision_snapshot:
            return FreshnessCheckResult(
                status=DecisionFreshnessStatus.INVALIDATED,
                reason="Decision Snapshot не найден",
                check_timestamp=datetime.utcnow().isoformat(),
            )
        
        # Если решение уже помечено как устаревшее
        if decision_snapshot.freshness_status != DecisionFreshnessStatus.ACTUAL:
            return FreshnessCheckResult(
                status=decision_snapshot.freshness_status,
                reason=decision_snapshot.freshness_reason,
                check_timestamp=datetime.utcnow().isoformat(),
            )
        
        # Проверяем, изменился ли Document Snapshot
        if current_document_snapshot_id:
            evidence_snapshot = self._evidence_snapshots.get(decision_snapshot.derived_from)
            if evidence_snapshot:
                document_snapshot = self._document_snapshots.get(evidence_snapshot.derived_from)
                if document_snapshot and document_snapshot.snapshot_id != current_document_snapshot_id:
                    # Документы изменились → решение устарело
                    decision_snapshot.freshness_status = DecisionFreshnessStatus.STALE
                    decision_snapshot.freshness_reason = f"Документы изменились (новый snapshot: {current_document_snapshot_id})"
                    self._save_snapshot(decision_snapshot, "decision")
                    
                    return FreshnessCheckResult(
                        status=DecisionFreshnessStatus.STALE,
                        reason=decision_snapshot.freshness_reason,
                        invalidated_by=current_document_snapshot_id,
                        check_timestamp=datetime.utcnow().isoformat(),
                    )
        
        # Решение актуально
        return FreshnessCheckResult(
            status=DecisionFreshnessStatus.ACTUAL,
            check_timestamp=datetime.utcnow().isoformat(),
        )
    
    def invalidate_decision(
        self,
        decision_id: str,
        reason: str
    ) -> None:
        """
        Помечает решение как INVALIDATED.
        
        Используется при явной инвалидации (например, обнаружена ошибка).
        """
        decision_snapshot = self._decision_snapshots.get(decision_id)
        if decision_snapshot:
            decision_snapshot.freshness_status = DecisionFreshnessStatus.INVALIDATED
            decision_snapshot.freshness_reason = reason
            self._save_snapshot(decision_snapshot, "decision")
            logger.info(f"⚠️ Decision {decision_id} помечен как INVALIDATED: {reason}")
    
    def get_audit_chain(self, chain_id: str) -> Optional[AuditTrailChain]:
        """Получает Audit Trail Chain по ID."""
        return self._audit_chains.get(chain_id)
    
    def get_decision_snapshot(self, decision_id: str) -> Optional[DecisionSnapshot]:
        """Получает Decision Snapshot по ID."""
        return self._decision_snapshots.get(decision_id)
    
    def _save_snapshot(self, snapshot, snapshot_type: str) -> None:
        """Сохраняет snapshot в файл (для персистентности)."""
        try:
            snapshot_file = self.storage_path / f"{snapshot_type}_{snapshot.snapshot_id if hasattr(snapshot, 'snapshot_id') else snapshot.chain_id if hasattr(snapshot, 'chain_id') else 'unknown'}.json"
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(snapshot.dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения snapshot: {e}", exc_info=True)


# Глобальный экземпляр менеджера
_audit_trail_manager: Optional[AuditTrailManager] = None


def get_audit_trail_manager() -> AuditTrailManager:
    """Получить глобальный экземпляр Audit Trail Manager."""
    global _audit_trail_manager
    if _audit_trail_manager is None:
        _audit_trail_manager = AuditTrailManager()
    return _audit_trail_manager

