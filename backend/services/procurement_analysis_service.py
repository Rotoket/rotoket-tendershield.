"""
ФАЗА 5: Сервисный слой для работы с procurement анализами.

Обеспечивает сохранение и загрузку procurement-специфичных данных в БД.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from database import (
    ProcurementKnowledgeBase,
    ProcurementBlocker,
    AnalysisEvidenceExtended,
    ProcurementDecisionExtended,
    Analysis,
)
from core.procurement_reasoner import ProcurementAnalysis, BlockerInfo, CriticalParameter, FinancialImpact, ChecklistItem
from core.evidence_types_extended import EvidenceExtendedModel

logger = logging.getLogger(__name__)


class ProcurementAnalysisService:
    """
    Сервис для работы с procurement анализами в БД.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def save_procurement_analysis(
        self,
        analysis_id: int,
        procurement_analysis: ProcurementAnalysis,
        evidence_list: Optional[List[EvidenceExtendedModel]] = None
    ) -> ProcurementDecisionExtended:
        """
        Сохраняет результат procurement анализа в БД.
        
        Args:
            analysis_id: ID анализа
            procurement_analysis: Результат анализа от ProcurementReasoningEngine
            evidence_list: Список evidence объектов (опционально)
        
        Returns:
            ProcurementDecisionExtended объект
        """
        try:
            # Проверяем, существует ли уже запись
            existing = self.db.query(ProcurementDecisionExtended).filter(
                ProcurementDecisionExtended.analysis_id == analysis_id
            ).first()
            
            if existing:
                # Обновляем существующую запись
                decision = existing
            else:
                # Создаем новую запись
                decision = ProcurementDecisionExtended(analysis_id=analysis_id)
                self.db.add(decision)
            
            # Заполняем поля
            decision.verdict = procurement_analysis.verdict.value
            decision.iun = procurement_analysis.iun
            decision.decision_grounds = procurement_analysis.decision_grounds
            
            # Сохраняем critical_parameters как JSON
            if procurement_analysis.critical_parameters:
                decision.critical_parameters = [
                    {
                        "name": p.name,
                        "value": p.value,
                        "source": p.source,
                        "confidence": p.confidence,
                        "impact": p.impact
                    }
                    for p in procurement_analysis.critical_parameters
                ]
            
            # Сохраняем financial_impact как JSON
            if procurement_analysis.financial_impact:
                fi = procurement_analysis.financial_impact
                decision.financial_impact = {
                    "best_case": fi.best_case,
                    "worst_case": fi.worst_case,
                    "expected_value": fi.expected_value,
                    "mitigation_costs": fi.mitigation_costs,
                    "penalty_risks": getattr(fi, "penalty_risks", 0.0),
                    "worst_case_probability": getattr(fi, "worst_case_probability", 0.20),
                }
            
            # Сохраняем blockers как JSON
            if procurement_analysis.blockers:
                decision.blockers = [
                    {
                        "sub_classification": b.sub_classification.value,
                        "description": b.description,
                        "is_mitigable": b.is_mitigable,
                        "mitigation_strategy": b.mitigation_strategy,
                        "mitigation_cost": b.mitigation_cost,
                        "mitigation_time_days": b.mitigation_time_days,
                        "evidence_ids": b.evidence_ids,
                        "kb_reference": b.kb_reference,
                    }
                    for b in procurement_analysis.blockers
                ]
            
            # Сохраняем red_flags как JSON
            if procurement_analysis.red_flags:
                decision.red_flags = procurement_analysis.red_flags
            
            # Сохраняем checklist как JSON
            if procurement_analysis.checklist:
                decision.checklist = [
                    {
                        "item": c.item if isinstance(c, ChecklistItem) else c.get("item"),
                        "priority": c.priority if isinstance(c, ChecklistItem) else c.get("priority"),
                        "deadline_days": c.deadline_days if isinstance(c, ChecklistItem) else c.get("deadline_days"),
                        "cost_estimate": c.cost_estimate if isinstance(c, ChecklistItem) else c.get("cost_estimate"),
                        "related_blocker": c.related_blocker if isinstance(c, ChecklistItem) else c.get("related_blocker"),
                        "kb_reference": c.kb_reference if isinstance(c, ChecklistItem) else c.get("kb_reference"),
                    }
                    for c in procurement_analysis.checklist
                ]
            
            # Сохраняем kb_references
            if procurement_analysis.kb_references:
                decision.kb_references = procurement_analysis.kb_references
            
            # Извлекаем procurement_law, nmck, deadline_days из critical_parameters
            if procurement_analysis.critical_parameters:
                for param in procurement_analysis.critical_parameters:
                    if param.name == "НМЦК" and isinstance(param.value, (int, float)):
                        decision.nmck = float(param.value)
                        break
            
            # Сохраняем blockers в отдельную таблицу
            if procurement_analysis.blockers:
                # Удаляем старые блокеры для этого анализа
                self.db.query(ProcurementBlocker).filter(
                    ProcurementBlocker.analysis_id == analysis_id
                ).delete()
                
                # Сохраняем новые блокеры
                for blocker in procurement_analysis.blockers:
                    blocker_db = ProcurementBlocker(
                        analysis_id=analysis_id,
                        sub_classification=blocker.sub_classification.value,
                        description=blocker.description,
                        legal_basis=blocker.legal_basis.value if blocker.legal_basis else None,
                        is_mitigable=blocker.is_mitigable,
                        mitigation_strategy=blocker.mitigation_strategy,
                        mitigation_cost=blocker.mitigation_cost,
                        mitigation_time_days=blocker.mitigation_time_days,
                        evidence_ids=blocker.evidence_ids,
                        kb_reference=blocker.kb_reference,
                    )
                    self.db.add(blocker_db)
            
            # Сохраняем extended evidence (если предоставлены)
            if evidence_list:
                # Удаляем старые evidence для этого анализа
                self.db.query(AnalysisEvidenceExtended).filter(
                    AnalysisEvidenceExtended.analysis_id == analysis_id
                ).delete()
                
                # Сохраняем новые evidence
                for ev in evidence_list:
                    ev_db = AnalysisEvidenceExtended(
                        analysis_id=analysis_id,
                        evidence_id=ev.evidence_id,
                        source_file=ev.source_file,
                        fact=ev.fact,
                        classification=ev.classification.value,
                        confidence=ev.confidence.value,
                        sub_classification=ev.sub_classification.value if ev.sub_classification else None,
                        legal_basis=ev.legal_basis.value if ev.legal_basis else None,
                        financial_impact_rub=ev.financial_impact_rub,
                        mitigation_strategy=ev.mitigation_strategy,
                        mitigation_cost_rub=ev.mitigation_cost_rub,
                        mitigation_time_days=ev.mitigation_time_days,
                        derived_from=ev.derived_from,
                        raw_extract=ev.raw_extract,
                        applicable_to_procurement_type=ev.applicable_to_procurement_type,
                        reference_in_kb=ev.reference_in_kb,
                    )
                    self.db.add(ev_db)
            
            # Сохраняем ссылки на Knowledge Base
            if procurement_analysis.kb_references:
                # Удаляем старые ссылки
                self.db.query(ProcurementKnowledgeBase).filter(
                    ProcurementKnowledgeBase.analysis_id == analysis_id
                ).delete()
                
                # Сохраняем новые ссылки
                for kb_ref in procurement_analysis.kb_references:
                    # Парсим путь к документу KB
                    parts = kb_ref.split("/")
                    category = parts[0] if len(parts) > 0 else None
                    filename = parts[-1] if len(parts) > 1 else kb_ref
                    
                    kb_db = ProcurementKnowledgeBase(
                        analysis_id=analysis_id,
                        kb_path=kb_ref,
                        kb_category=category,
                        kb_title=filename.replace(".md", "").replace("-", " ").replace("_", " "),
                    )
                    self.db.add(kb_db)
            
            self.db.commit()
            logger.info(f"✅ Procurement анализ сохранен для analysis_id={analysis_id}")
            
            return decision
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Ошибка сохранения procurement анализа: {e}", exc_info=True)
            raise
    
    def get_procurement_analysis(self, analysis_id: int) -> Optional[ProcurementDecisionExtended]:
        """
        Получает сохраненный procurement анализ из БД.
        
        Args:
            analysis_id: ID анализа
        
        Returns:
            ProcurementDecisionExtended или None
        """
        return self.db.query(ProcurementDecisionExtended).filter(
            ProcurementDecisionExtended.analysis_id == analysis_id
        ).first()
    
    def get_blockers_for_analysis(self, analysis_id: int) -> List[ProcurementBlocker]:
        """
        Получает список блокеров для анализа.
        
        Args:
            analysis_id: ID анализа
        
        Returns:
            Список ProcurementBlocker
        """
        return self.db.query(ProcurementBlocker).filter(
            ProcurementBlocker.analysis_id == analysis_id
        ).all()
    
    def get_evidence_extended_for_analysis(self, analysis_id: int) -> List[AnalysisEvidenceExtended]:
        """
        Получает список extended evidence для анализа.
        
        Args:
            analysis_id: ID анализа
        
        Returns:
            Список AnalysisEvidenceExtended
        """
        return self.db.query(AnalysisEvidenceExtended).filter(
            AnalysisEvidenceExtended.analysis_id == analysis_id
        ).all()
    
    def get_kb_references_for_analysis(self, analysis_id: int) -> List[ProcurementKnowledgeBase]:
        """
        Получает список ссылок на Knowledge Base для анализа.
        
        Args:
            analysis_id: ID анализа
        
        Returns:
            Список ProcurementKnowledgeBase
        """
        return self.db.query(ProcurementKnowledgeBase).filter(
            ProcurementKnowledgeBase.analysis_id == analysis_id
        ).all()

