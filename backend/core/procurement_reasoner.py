"""
Procurement Reasoning Engine — ФАЗА 3: Специализированный анализатор закупок

Использует Knowledge Base и extended evidence для глубокого анализа закупок 44-ФЗ и 223-ФЗ.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from core.evidence_types_extended import (
    EvidenceExtendedModel,
    EvidenceSubClassification,
    EvidenceLegalBasis,
)
from evidence_types import EvidenceClassification

# Импортируем RAG engine для поиска в Knowledge Base
try:
    from rag_engine import get_law_snippets
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("RAG engine недоступен, поиск в Knowledge Base будет отключен")
    def get_law_snippets(query: str, k: int = 5) -> List[Dict[str, Any]]:
        return []

logger = logging.getLogger(__name__)

# Путь к Knowledge Base
KNOWLEDGE_BASE_ROOT = Path(__file__).resolve().parent.parent.parent / "knowledge"


class ProcurementVerdict(str, Enum):
    """Вердикт по закупке"""
    PROCEED = "PROCEED"
    PROCEED_WITH_CONDITIONS = "PROCEED_WITH_CONDITIONS"
    DO_NOT_PARTICIPATE = "DO_NOT_PARTICIPATE"
    POSTPONE = "POSTPONE"


@dataclass
class CriticalParameter:
    """Критический параметр закупки"""
    name: str
    value: Any
    source: str  # Откуда извлечен (evidence_id или документ)
    confidence: str  # "high", "medium", "low"
    impact: str  # Описание влияния на решение


@dataclass
class BlockerInfo:
    """Информация о блокере"""
    sub_classification: EvidenceSubClassification
    description: str
    legal_basis: Optional[EvidenceLegalBasis]
    mitigation_strategy: Optional[str]
    mitigation_cost: Optional[float]
    mitigation_time_days: Optional[int]
    is_mitigable: bool
    evidence_ids: List[str]
    kb_reference: Optional[str]


@dataclass
class FinancialImpact:
    """Финансовое влияние"""
    best_case: float
    worst_case: float
    expected_value: float
    worst_case_probability: float  # 0.0 - 1.0
    mitigation_costs: float
    penalty_risks: float


@dataclass
class ProcurementAnalysis:
    """Результат анализа закупки"""
    verdict: ProcurementVerdict
    iun: int  # Индекс управленческой нагрузки (0-100)
    critical_parameters: List[CriticalParameter]
    blockers: List[BlockerInfo]
    red_flags: List[Dict[str, Any]]
    financial_impact: FinancialImpact
    checklist: List[Dict[str, Any]]
    decision_grounds: str  # Обоснование решения
    kb_references: List[str]  # Ссылки на документы Knowledge Base


class ProcurementReasoningEngine:
    """
    Специализированный анализатор закупок 44-ФЗ и 223-ФЗ.
    
    Использует:
    - Knowledge Base для поиска релевантных документов
    - Extended evidence для детальной классификации
    - Decision frameworks из canon/ для принятия решений
    - Sequential-thinking MCP для глубокого анализа
    """
    
    def __init__(self):
        self.knowledge_base_root = KNOWLEDGE_BASE_ROOT
    
    def analyze_procurement_viability(
        self,
        evidence_list: List[EvidenceExtendedModel],
        procurement_law: str = "44-ФЗ",
        nmck: Optional[float] = None,
        deadline_days: Optional[int] = None
    ) -> ProcurementAnalysis:
        """
        Анализирует жизнеспособность закупки.
        
        ФАЗА 3: Использует Sequential-thinking MCP для глубокого анализа.
        
        Args:
            evidence_list: Список extended evidence
            procurement_law: "44-ФЗ" или "223-ФЗ"
            nmck: Начальная максимальная цена контракта (если известна)
            deadline_days: Количество дней до дедлайна подачи заявки
        
        Returns:
            ProcurementAnalysis с вердиктом и обоснованием
        """
        logger.info(f"🔍 Анализ жизнеспособности закупки ({procurement_law})")
        
        # ФАЗА 4: Используем Sequential-thinking MCP для глубокого анализа (если доступен)
        sequential_analysis = None
        try:
            from services.mcp_integration import get_sequential_thinking_mcp
            
            # Формируем проблему для анализа
            problem_description = (
                f"Проанализировать жизнеспособность закупки по {procurement_law}. "
                f"Найдено {len(evidence_list)} evidence объектов. "
                f"НМЦК: {nmck or 'неизвестна'}. "
                f"Дедлайн: {deadline_days or 'неизвестен'} дней."
            )
            
            context = {
                "procurement_law": procurement_law,
                "evidence_count": len(evidence_list),
                "nmck": nmck,
                "deadline_days": deadline_days,
            }
            
            sequential_mcp = get_sequential_thinking_mcp()
            sequential_analysis = sequential_mcp.analyze_step_by_step(
                problem=problem_description,
                context=context,
                max_steps=7
            )
            
            if sequential_analysis.get("success"):
                logger.info(f"🧠 Sequential-thinking анализ выполнен: {len(sequential_analysis.get('steps', []))} шагов")
        except ImportError:
            logger.warning("Sequential-thinking MCP недоступен, используем стандартный анализ")
        except Exception as e:
            logger.warning(f"Ошибка Sequential-thinking MCP: {e}. Используем стандартный анализ")
        
        # 1. Извлекаем критические параметры
        critical_params = self.extract_critical_parameters(evidence_list, procurement_law)
        logger.info(f"✅ Извлечено критических параметров: {len(critical_params)}")
        
        # 2. Идентифицируем блокеры и red flags
        blockers, red_flags = self.identify_blockers_and_red_flags(evidence_list, procurement_law)
        logger.info(f"🔴 Найдено блокеров: {len(blockers)}, red flags: {len(red_flags)}")
        
        # 3. Рассчитываем финансовое влияние
        financial_impact = self.calculate_financial_impact(
            evidence_list,
            nmck or self._extract_nmck_from_evidence(evidence_list),
            procurement_law
        )
        logger.info(f"💰 Financial Impact: Best={financial_impact.best_case:,.0f}, Worst={financial_impact.worst_case:,.0f}")
        
        # 4. Генерируем чеклист
        checklist = self.generate_evidence_based_checklist(evidence_list, blockers, procurement_law)
        logger.info(f"✅ Сгенерирован чеклист: {len(checklist)} пунктов")
        
        # 5. Принимаем решение на основе decision framework
        verdict, iun, decision_grounds, kb_refs = self._make_decision(
            blockers,
            red_flags,
            financial_impact,
            evidence_list,
            procurement_law,
            deadline_days,
            critical_parameters
        )
        
        # ФАЗА 4: Сохраняем контекст анализа через Context7 MCP (если доступен)
        try:
            from services.mcp_integration import get_context7_mcp
            import uuid
            
            context7_mcp = get_context7_mcp()
            analysis_id = f"procurement_{uuid.uuid4().hex[:8]}"
            
            context_to_save = {
                "procurement_law": procurement_law,
                "verdict": verdict.value,
                "iun": iun,
                "blockers_count": len(blockers),
                "red_flags_count": len(red_flags),
                "nmck": nmck,
                "deadline_days": deadline_days,
                "critical_parameters": [p.name for p in critical_params],
            }
            
            metadata = {
                "timestamp": str(Path(__file__).stat().st_mtime),  # Упрощенно
                "source": "ProcurementReasoningEngine",
            }
            
            context7_mcp.save_context(analysis_id, context_to_save, metadata)
            logger.info(f"💾 Контекст анализа сохранен: {analysis_id}")
        except ImportError:
            logger.warning("Context7 MCP недоступен, контекст не сохранен")
        except Exception as e:
            logger.warning(f"Ошибка сохранения контекста: {e}")
        
        return ProcurementAnalysis(
            verdict=verdict,
            iun=iun,
            critical_parameters=critical_params,
            blockers=blockers,
            red_flags=red_flags,
            financial_impact=financial_impact,
            checklist=checklist,
            decision_grounds=decision_grounds,
            kb_references=kb_refs,
        )
    
    def extract_critical_parameters(
        self,
        evidence_list: List[EvidenceExtendedModel],
        procurement_law: str
    ) -> List[CriticalParameter]:
        """
        Извлекает критические параметры закупки из evidence.
        
        Критические параметры:
        - НМЦК
        - Сроки оплаты
        - Обеспечение контракта
        - Штрафы
        - География (ЗАТО, отдаленность)
        - Требования к сертификатам
        """
        params = []
        
        for ev in evidence_list:
            fact_lower = ev.fact.lower()
            
            # НМЦК
            if "нмцк" in fact_lower or "начальная максимальная" in fact_lower:
                nmck_value = self._extract_number_from_fact(ev.fact)
                if nmck_value:
                    params.append(CriticalParameter(
                        name="НМЦК",
                        value=nmck_value,
                        source=ev.evidence_id,
                        confidence="high" if ev.confidence.value == "high" else "medium",
                        impact="Базовая цена контракта для расчета финансового влияния"
                    ))
            
            # Сроки оплаты
            if "оплата" in fact_lower and ("день" in fact_lower or "дней" in fact_lower):
                payment_days = self._extract_number_from_fact(ev.fact)
                if payment_days:
                    params.append(CriticalParameter(
                        name="Срок оплаты",
                        value=f"{payment_days} дней",
                        source=ev.evidence_id,
                        confidence=ev.confidence.value,
                        impact="Влияет на кассовый разрыв и финансовое планирование"
                    ))
            
            # Обеспечение
            if "обеспечение" in fact_lower and ("%" in ev.fact or "процент" in fact_lower):
                guarantee_pct = self._extract_number_from_fact(ev.fact)
                if guarantee_pct:
                    params.append(CriticalParameter(
                        name="Обеспечение контракта",
                        value=f"{guarantee_pct}%",
                        source=ev.evidence_id,
                        confidence=ev.confidence.value,
                        impact="Финансовая нагрузка на обеспечение"
                    ))
            
            # Штрафы
            if ev.sub_classification == EvidenceSubClassification.PENALTY_RISK:
                penalty_pct = self._extract_number_from_fact(ev.fact)
                params.append(CriticalParameter(
                    name="Штраф за нарушение срока",
                    value=f"{penalty_pct}%" if penalty_pct else "10% (по умолчанию для 44-ФЗ)",
                    source=ev.evidence_id,
                    confidence=ev.confidence.value,
                    impact="Критичный финансовый риск при нарушении сроков"
                ))
            
            # География (ЗАТО)
            if ev.sub_classification == EvidenceSubClassification.LOCATION_BLOCKER:
                params.append(CriticalParameter(
                    name="География",
                    value="ЗАТО или спецрегион",
                    source=ev.evidence_id,
                    confidence=ev.confidence.value,
                    impact="Требуется пропуск, влияет на решение"
                ))
        
        return params
    
    def identify_blockers_and_red_flags(
        self,
        evidence_list: List[EvidenceExtendedModel],
        procurement_law: str
    ) -> Tuple[List[BlockerInfo], List[Dict[str, Any]]]:
        """
        Идентифицирует блокеры и red flags из evidence.
        
        Returns:
            Tuple[blockers, red_flags]
        """
        blockers = []
        red_flags = []
        
        # Группируем DEALBREAKER evidence
        dealbreaker_evidence = [
            ev for ev in evidence_list
            if ev.classification == EvidenceClassification.DEAL_BREAKER
        ]
        
        for ev in dealbreaker_evidence:
            if ev.sub_classification:
                # Проверяем митигируемость
                is_mitigable = (
                    ev.mitigation_strategy is not None
                    and ev.mitigation_cost_estimate is not None
                    and ev.mitigation_time_days is not None
                )
                
                # ФАЗА 4: Ищем релевантные документы в Knowledge Base для блокера
                kb_ref = ev.reference_in_kb
                if not kb_ref and ev.sub_classification:
                    # Пробуем найти релевантный документ через поиск
                    try:
                        kb_results = self.search_knowledge_base(
                            query=f"{ev.sub_classification.value} {procurement_law}",
                            k=1,
                            doc_type="risks"
                        )
                        if kb_results:
                            kb_ref = kb_results[0].get("metadata", {}).get("source", "")
                    except Exception:
                        pass
                
                blockers.append(BlockerInfo(
                    sub_classification=ev.sub_classification,
                    description=ev.fact,
                    legal_basis=ev.legal_basis,
                    mitigation_strategy=ev.mitigation_strategy,
                    mitigation_cost=ev.mitigation_cost_estimate,
                    mitigation_time_days=ev.mitigation_time_days,
                    is_mitigable=is_mitigable,
                    evidence_ids=[ev.evidence_id],
                    kb_reference=kb_ref,
                ))
        
        # Группируем CONTROLLED RISK как red flags
        controlled_risk_evidence = [
            ev for ev in evidence_list
            if ev.classification == EvidenceClassification.CONTROLLED_RISK
        ]
        
        for ev in controlled_risk_evidence:
            if ev.sub_classification:
                # ФАЗА 4: Ищем релевантные документы в Knowledge Base для red flag
                kb_ref = ev.reference_in_kb
                if not kb_ref:
                    try:
                        kb_results = self.search_knowledge_base(
                            query=f"{ev.sub_classification.value} риск {procurement_law}",
                            k=1,
                            doc_type="risks"
                        )
                        if kb_results:
                            kb_ref = kb_results[0].get("metadata", {}).get("source", "")
                    except Exception:
                        pass
                
                red_flags.append({
                    "sub_classification": ev.sub_classification.value,
                    "description": ev.fact,
                    "legal_basis": ev.legal_basis.value if ev.legal_basis else None,
                    "severity": "HIGH" if ev.iun_contribution and ev.iun_contribution > 15 else "MEDIUM",
                    "evidence_id": ev.evidence_id,
                    "kb_reference": kb_ref,
                })
        
        return blockers, red_flags
    
    def calculate_financial_impact(
        self,
        evidence_list: List[EvidenceExtendedModel],
        nmck: Optional[float],
        procurement_law: str
    ) -> FinancialImpact:
        """
        Рассчитывает финансовое влияние рисков.
        
        Использует матрицу из knowledge/canon/financial-impact-matrix.md
        """
        if nmck is None:
            nmck = 0.0
        
        # Собираем затраты на митигацию
        mitigation_costs = 0.0
        for ev in evidence_list:
            if ev.mitigation_cost_estimate:
                mitigation_costs += ev.mitigation_cost_estimate
        
        # Собираем риски штрафов
        penalty_risks = 0.0
        for ev in evidence_list:
            if ev.sub_classification == EvidenceSubClassification.PENALTY_RISK:
                # Штраф 10% от НМЦК для 44-ФЗ, может быть выше для 223-ФЗ
                penalty_pct = 0.10 if procurement_law == "44-ФЗ" else 0.20
                penalty_risks = nmck * penalty_pct
        
        # Упрощенный расчет (можно улучшить с учетом всех факторов)
        # Best Case: НМЦК - митигация (предполагаем маржу 20%)
        best_case = nmck * 0.20 - mitigation_costs
        
        # Worst Case: Best Case - штрафы
        worst_case = best_case - penalty_risks
        
        # Expected Value: средневзвешенное (предполагаем вероятность worst case = 20%)
        worst_case_probability = 0.20
        expected_value = best_case * (1 - worst_case_probability) + worst_case * worst_case_probability
        
        return FinancialImpact(
            best_case=max(0, best_case),  # Не может быть отрицательным
            worst_case=worst_case,
            expected_value=expected_value,
            worst_case_probability=worst_case_probability,
            mitigation_costs=mitigation_costs,
            penalty_risks=penalty_risks,
        )
    
    def generate_evidence_based_checklist(
        self,
        evidence_list: List[EvidenceExtendedModel],
        blockers: List[BlockerInfo],
        procurement_law: str
    ) -> List[Dict[str, Any]]:
        """
        Генерирует чеклист на основе evidence и блокеров.
        
        Использует шаблоны из knowledge/templates/application-checklist.md
        """
        checklist = []
        
        # Добавляем пункты для блокеров
        for blocker in blockers:
            if blocker.is_mitigable and blocker.mitigation_strategy:
                checklist.append({
                    "item": blocker.mitigation_strategy,
                    "priority": "CRITICAL",
                    "deadline_days": blocker.mitigation_time_days,
                    "cost_estimate": blocker.mitigation_cost,
                    "related_blocker": blocker.sub_classification.value,
                    "kb_reference": blocker.kb_reference,
                })
        
        # Добавляем стандартные пункты из шаблона
        checklist.extend([
            {
                "item": "Проверить соответствие документации требованиям закона",
                "priority": "HIGH",
                "deadline_days": None,
                "cost_estimate": None,
                "related_blocker": None,
                "kb_reference": f"laws/fz-{procurement_law.lower().replace(' ', '-')}.md",
            },
            {
                "item": "Подготовить все необходимые документы для заявки",
                "priority": "HIGH",
                "deadline_days": None,
                "cost_estimate": None,
                "related_blocker": None,
                "kb_reference": "templates/application-checklist.md",
            },
        ])
        
        return checklist
    
    def _make_decision(
        self,
        blockers: List[BlockerInfo],
        red_flags: List[Dict[str, Any]],
        financial_impact: FinancialImpact,
        evidence_list: List[EvidenceExtendedModel],
        procurement_law: str,
        deadline_days: Optional[int]
    ) -> Tuple[ProcurementVerdict, int, str, List[str]]:
        """
        Принимает решение на основе decision framework.
        
        Использует канонические фреймворки из knowledge/canon/
        """
        kb_references = []
        
        # ШАГ 1: Проверяем не-митигируемые блокеры
        non_mitigable_blockers = [b for b in blockers if not b.is_mitigable]
        if non_mitigable_blockers:
            blocker_desc = ", ".join([b.sub_classification.value for b in non_mitigable_blockers])
            kb_ref = f"risks/blockers-{procurement_law.lower().replace(' ', '-')}.md"
            kb_references.append(kb_ref)
            return (
                ProcurementVerdict.DO_NOT_PARTICIPATE,
                100,  # Максимальный ИУН
                f"Обнаружены не-митигируемые блокеры: {blocker_desc}. Участие невозможно.",
                kb_references
            )
        
        # ШАГ 2: Проверяем митигируемые блокеры
        mitigable_blockers = [b for b in blockers if b.is_mitigable]
        if mitigable_blockers:
            # Используем critical_parameters для оценки НМЦК если доступны
            nmck_from_params = None
            if critical_parameters:
                for param in critical_parameters:
                    if param.name == "НМЦК" and isinstance(param.value, (int, float)):
                        nmck_from_params = float(param.value)
                        break
            # Проверяем сроки митигации
            if deadline_days:
                for blocker in mitigable_blockers:
                    if blocker.mitigation_time_days and blocker.mitigation_time_days > deadline_days:
                        kb_ref = blocker.kb_reference or f"risks/blockers-{procurement_law.lower().replace(' ', '-')}.md"
                        kb_references.append(kb_ref)
                        return (
                            ProcurementVerdict.DO_NOT_PARTICIPATE,
                            90,
                            f"Блокер {blocker.sub_classification.value} требует {blocker.mitigation_time_days} дней, "
                            f"но до дедлайна осталось {deadline_days} дней.",
                            kb_references
                        )
            
            # Проверяем стоимость митигации
            total_mitigation_cost = sum(b.mitigation_cost or 0 for b in mitigable_blockers)
            
            # Если НМЦК не найдена в параметрах, пытаемся оценить из financial_impact
            if nmck_from_params:
                estimated_nmck = nmck_from_params
            elif financial_impact.best_case > 0:
                # best_case = margin - mitigation, где margin = 20% от НМЦК
                # НМЦК = (best_case + mitigation) / 0.20
                estimated_nmck = (financial_impact.best_case + financial_impact.mitigation_costs) / 0.20
            else:
                # Если best_case отрицательный, используем mitigation_costs для оценки
                estimated_nmck = financial_impact.mitigation_costs * 10  # Очень грубая оценка
            
            if estimated_nmck > 0 and total_mitigation_cost > estimated_nmck * 0.30:
                kb_ref = f"canon/financial-impact-matrix.md"
                kb_references.append(kb_ref)
                return (
                    ProcurementVerdict.DO_NOT_PARTICIPATE,
                    85,
                    f"Стоимость митигации ({total_mitigation_cost:,.0f} руб.) превышает 30% от НМЦК.",
                    kb_references
                )
        
        # ШАГ 3: Анализируем финансовое влияние
        if financial_impact.expected_value < 0:
            kb_ref = "canon/financial-impact-matrix.md"
            kb_references.append(kb_ref)
            return (
                ProcurementVerdict.DO_NOT_PARTICIPATE,
                80,
                f"Ожидаемая прибыль отрицательна: {financial_impact.expected_value:,.0f} руб.",
                kb_references
            )
        
        # ШАГ 4: Рассчитываем ИУН
        iun = self._calculate_iun(evidence_list, blockers, red_flags, procurement_law)
        
        # ШАГ 5: Принимаем финальное решение
        if mitigable_blockers:
            kb_ref = f"canon/decision-framework-{procurement_law.lower().replace(' ', '-')}.md"
            kb_references.append(kb_ref)
            return (
                ProcurementVerdict.PROCEED_WITH_CONDITIONS,
                iun,
                f"Обнаружены митигируемые блокеры. Требуется выполнить условия митигации перед подачей заявки.",
                kb_references
            )
        elif len(red_flags) > 5:
            kb_ref = f"canon/decision-framework-{procurement_law.lower().replace(' ', '-')}.md"
            kb_references.append(kb_ref)
            return (
                ProcurementVerdict.POSTPONE,
                iun,
                f"Обнаружено много red flags ({len(red_flags)}). Рекомендуется дополнительный анализ.",
                kb_references
            )
        elif financial_impact.best_case < financial_impact.mitigation_costs * 2:
            kb_ref = "canon/financial-impact-matrix.md"
            kb_references.append(kb_ref)
            return (
                ProcurementVerdict.POSTPONE,
                iun,
                f"Маржа в лучшем случае слишком низкая. Рекомендуется пересмотр условий.",
                kb_references
            )
        else:
            kb_ref = f"canon/decision-framework-{procurement_law.lower().replace(' ', '-')}.md"
            kb_references.append(kb_ref)
            return (
                ProcurementVerdict.PROCEED,
                iun,
                f"Нет критичных блокеров, финансовое влияние положительное. Можно участвовать.",
                kb_references
            )
    
    def _calculate_iun(
        self,
        evidence_list: List[EvidenceExtendedModel],
        blockers: List[BlockerInfo],
        red_flags: List[Dict[str, Any]],
        procurement_law: str
    ) -> int:
        """
        Рассчитывает ИУН (Индекс управленческой нагрузки) по формуле из canon/decision-framework-*.md
        """
        iun = 10  # Базовый риск
        
        # Добавляем вклад от блокеров
        for blocker in blockers:
            if blocker.is_mitigable:
                iun += 20
            else:
                iun += 30
        
        # Добавляем вклад от CONTROLLED RISK
        for ev in evidence_list:
            if ev.classification == EvidenceClassification.CONTROLLED_RISK:
                if ev.iun_contribution:
                    iun += ev.iun_contribution
                else:
                    iun += 5  # По умолчанию
        
        # Добавляем вклад от red flags
        for rf in red_flags:
            if rf.get("severity") == "HIGH":
                iun += 15
            else:
                iun += 10
        
        # Ограничиваем диапазон 0-100
        return min(100, max(0, iun))
    
    def _extract_nmck_from_evidence(self, evidence_list: List[EvidenceExtendedModel]) -> Optional[float]:
        """Извлекает НМЦК из evidence"""
        for ev in evidence_list:
            fact_lower = ev.fact.lower()
            if "нмцк" in fact_lower or "начальная максимальная" in fact_lower:
                return self._extract_number_from_fact(ev.fact)
        return None
    
    def _extract_number_from_fact(self, fact: str) -> Optional[float]:
        """Извлекает число из факта"""
        import re
        # Ищем числа с возможными разделителями
        numbers = re.findall(r'[\d\s,\.]+', fact)
        for num_str in numbers:
            try:
                # Убираем пробелы и заменяем запятую на точку
                cleaned = num_str.replace(' ', '').replace(',', '.')
                value = float(cleaned)
                # Если число слишком большое, это может быть НМЦК
                if value > 1000:
                    return value
            except ValueError:
                continue
        return None
    
    def search_knowledge_base(self, query: str, k: int = 5, doc_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Ищет релевантные документы в Knowledge Base через RAG.
        
        ФАЗА 4: Использует Knowledge Base MCP для улучшенного поиска.
        
        Args:
            query: Поисковый запрос
            k: Количество результатов
            doc_type: Тип документа для фильтрации (laws, standards, templates, etc.)
        
        Returns:
            Список релевантных фрагментов с метаданными
        """
        # ФАЗА 4: Пробуем использовать Knowledge Base MCP
        try:
            from services.mcp_integration import get_knowledge_base_mcp
            
            kb_mcp = get_knowledge_base_mcp()
            snippets = kb_mcp.search(query, k=k, doc_type=doc_type)
            
            if snippets:
                logger.info(f"📚 Knowledge Base MCP: найдено {len(snippets)} релевантных фрагментов")
                return snippets
        except ImportError:
            logger.debug("Knowledge Base MCP недоступен, используем RAG engine напрямую")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка Knowledge Base MCP: {e}, fallback на RAG engine")
        
        # Fallback: используем RAG engine напрямую
        if not RAG_AVAILABLE:
            return []
        
        try:
            snippets = get_law_snippets(query, k=k)
            logger.info(f"📚 Найдено {len(snippets)} релевантных фрагментов в Knowledge Base (RAG)")
            return snippets
        except Exception as e:
            logger.warning(f"⚠️ Ошибка поиска в Knowledge Base: {e}")
            return []

