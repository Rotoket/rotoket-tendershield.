"""
Reasoning & Decision Layer — ШАГ 4

Преобразует Evidence Objects в управленческие выводы и решения.

КЛЮЧЕВОЙ ПРИНЦИП:
РЕШЕНИЕ ≠ СУММА РИСКОВ
РЕШЕНИЕ = ЛОГИКА ПРОТИВОРЕЧИЙ И НАГРУЗКИ
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from evidence_types import EvidenceObject, EvidenceClassification, EvidenceConfidence
from reasoning_types import (
    RiskSignal,
    RiskType,
    Contradiction,
    DecisionNode,
    DecisionGraph,
    ManagementLoadExplanation,
    DecisionPreview,
    ReasoningResult,
)

# ФАЗА 2: Импорт расширенных типов для закупок
from core.evidence_types_extended import (
    EvidenceExtendedModel,
    classify_evidence_for_procurement,
    convert_to_extended,
    EvidenceSubClassification,
)

# ФАЗА 3: Импорт ProcurementReasoningEngine
try:
    from core.procurement_reasoner import (
        ProcurementReasoningEngine,
        ProcurementAnalysis,
        ProcurementVerdict,
    )
    PROCUREMENT_REASONER_AVAILABLE = True
except ImportError:
    PROCUREMENT_REASONER_AVAILABLE = False
    logger.warning("ProcurementReasoningEngine недоступен, используется базовый ReasoningEngine")

logger = logging.getLogger(__name__)


class DealBreakerRules:
    """
    Жёсткие правила классификации DEAL_BREAKER.
    
    LLM НЕ ИМЕЕТ ПРАВА:
    - понижать DEAL_BREAKER
    - «смягчать формулировки»
    - компенсировать его другими плюсами
    """
    
    @staticmethod
    def is_unlimited_financial_impact(evidence: EvidenceObject) -> bool:
        """Неограниченный финансовый удар."""
        if evidence.financial_impact_rub is None:
            return False
        # Если финансовое воздействие очень большое или неопределённое
        if evidence.financial_impact_rub > 1_000_000_000:  # 1 млрд руб
            return True
        # Если в факте упоминается "неограниченная" или "без ограничений"
        fact_lower = evidence.fact.lower()
        if any(phrase in fact_lower for phrase in ["неограничен", "без ограничений", "без верхнего предела"]):
            return True
        return False
    
    @staticmethod
    def is_asymmetric_responsibility(evidence: EvidenceObject) -> bool:
        """Асимметричная ответственность."""
        fact_lower = evidence.fact.lower()
        asymmetric_keywords = [
            "односторонняя ответственность",
            "ответственность только поставщика",
            "заказчик не несёт ответственности",
            "вся ответственность на поставщике",
        ]
        return any(keyword in fact_lower for keyword in asymmetric_keywords)
    
    @staticmethod
    def is_irreversible_obligation(evidence: EvidenceObject) -> bool:
        """Необратимое обязательство."""
        fact_lower = evidence.fact.lower()
        irreversible_keywords = [
            "без права отказа",
            "обязательство не может быть отменено",
            "необратимое обязательство",
            "без возможности расторжения",
        ]
        return any(keyword in fact_lower for keyword in irreversible_keywords)
    
    @staticmethod
    def is_critical_uncertainty(evidence: EvidenceObject) -> bool:
        """Критическая неопределённость без контроля."""
        if evidence.confidence == EvidenceConfidence.LOW:
            fact_lower = evidence.fact.lower()
            critical_keywords = [
                "не указано",
                "не определено",
                "требует уточнения",
                "неясно",
            ]
            if any(keyword in fact_lower for keyword in critical_keywords):
                # Проверяем, есть ли возможность контроля
                if "контроль" not in fact_lower and "уточнение" not in fact_lower:
                    return True
        return False
    
    @staticmethod
    def classify_evidence(evidence: EvidenceObject) -> EvidenceClassification:
        """
        Классифицирует Evidence по жёстким правилам DEAL_BREAKER.
        
        Если хотя бы одно правило срабатывает → DEAL_BREAKER.
        """
        if (
            DealBreakerRules.is_unlimited_financial_impact(evidence)
            or DealBreakerRules.is_asymmetric_responsibility(evidence)
            or DealBreakerRules.is_irreversible_obligation(evidence)
            or DealBreakerRules.is_critical_uncertainty(evidence)
        ):
            return EvidenceClassification.DEAL_BREAKER
        
        # Если не DEAL_BREAKER, используем исходную классификацию
        return evidence.classification


class ContradictionDetector:
    """
    Детектор противоречий между Evidence Objects.
    
    Противоречие = рост управленческой нагрузки.
    """
    
    @staticmethod
    def detect_contradictions(evidence_objects: List[EvidenceObject]) -> List[Contradiction]:
        """
        Выявляет противоречия между Evidence Objects.
        
        Примеры противоречий:
        - разные сроки оплаты
        - разные штрафы
        - разные объёмы обязательств
        - несогласованность чертежей и спецификаций
        """
        contradictions: List[Contradiction] = []
        
        # Группируем Evidence по типам фактов для поиска противоречий
        financial_evidence = [
            e for e in evidence_objects
            if "цена" in e.fact.lower() or "стоимость" in e.fact.lower() or "оплата" in e.fact.lower()
        ]
        deadline_evidence = [
            e for e in evidence_objects
            if "срок" in e.fact.lower() or "дедлайн" in e.fact.lower() or "дата" in e.fact.lower()
        ]
        penalty_evidence = [
            e for e in evidence_objects
            if "штраф" in e.fact.lower() or "неустойка" in e.fact.lower() or "пеня" in e.fact.lower()
        ]
        
        # Проверяем противоречия в финансовых данных
        if len(financial_evidence) > 1:
            # Извлекаем числовые значения
            financial_values = []
            for ev in financial_evidence:
                # Простая эвристика: ищем числа в факте
                import re
                numbers = re.findall(r'\d+[\s,.]?\d*', ev.fact)
                if numbers:
                    financial_values.append((ev.evidence_id, numbers[0]))
            
            # Если найдены разные значения → противоречие
            if len(set(v[1] for v in financial_values)) > 1:
                contradictions.append(
                    Contradiction(
                        contradiction_id=f"C-{uuid.uuid4().hex[:8].upper()}",
                        evidence_ids=[v[0] for v in financial_values],
                        description="Обнаружены противоречия в финансовых данных (разные цены/стоимости в разных документах)",
                        impact="Требуется уточнение фактической стоимости контракта. Управленческая нагрузка возрастает.",
                        resolution_hint="Необходимо сверить все документы и определить приоритетный источник данных.",
                    )
                )
        
        # Проверяем противоречия в сроках
        if len(deadline_evidence) > 1:
            # Простая эвристика: если упоминаются разные даты/сроки
            deadline_texts = [ev.fact.lower() for ev in deadline_evidence]
            if len(set(deadline_texts)) > 1:
                contradictions.append(
                    Contradiction(
                        contradiction_id=f"C-{uuid.uuid4().hex[:8].upper()}",
                        evidence_ids=[ev.evidence_id for ev in deadline_evidence],
                        description="Обнаружены противоречия в сроках (разные даты/дедлайны в разных документах)",
                        impact="Требуется уточнение фактических сроков. Риск формального отклонения заявки.",
                        resolution_hint="Необходимо определить приоритетный документ для сроков (обычно проект договора).",
                    )
                )
        
        # Проверяем противоречия в штрафах
        if len(penalty_evidence) > 1:
            penalty_texts = [ev.fact.lower() for ev in penalty_evidence]
            if len(set(penalty_texts)) > 1:
                contradictions.append(
                    Contradiction(
                        contradiction_id=f"C-{uuid.uuid4().hex[:8].upper()}",
                        evidence_ids=[ev.evidence_id for ev in penalty_evidence],
                        description="Обнаружены противоречия в штрафных санкциях (разные размеры штрафов в разных документах)",
                        impact="Требуется уточнение фактических штрафных условий. Финансовый риск неопределён.",
                        resolution_hint="Необходимо определить приоритетный документ для штрафов (обычно проект договора).",
                    )
                )
        
        return contradictions


class ReasoningEngine:
    """
    Ядро Reasoning Layer.
    
    Преобразует Evidence Objects в:
    - Risk Signals
    - Contradictions
    - Decision Graph
    - Decision Preview
    """
    
    def __init__(self):
        self.deal_breaker_rules = DealBreakerRules()
        self.contradiction_detector = ContradictionDetector()
    
    def process_evidence(
        self,
        evidence_objects: List[EvidenceObject],
        industry: Optional[str] = None,
        procurement_law: Optional[str] = None
    ) -> ReasoningResult:
        """
        Основной метод обработки Evidence Objects.
        
        ФАЗА 2: Автоматически определяет режим закупки и классифицирует evidence
        для закупок (44-ФЗ или 223-ФЗ).
        
        Преобразует Evidence → Risk Signals → Contradictions → Decision Preview.
        
        Args:
            evidence_objects: Список базовых EvidenceObject
            industry: Отрасль (для контекста)
            procurement_law: Режим закупки ("44-ФЗ" или "223-ФЗ"). Если None, определяется автоматически.
        """
        if not evidence_objects:
            logger.warning("Reasoning Engine: получен пустой список Evidence Objects")
            return self._create_empty_result()
        
        # ФАЗА 2: Определяем режим закупки из evidence (если не указан)
        if procurement_law is None:
            procurement_law = self._detect_procurement_law_from_evidence(evidence_objects)
        logger.info(f"📋 Reasoning Engine: режим закупки = {procurement_law}")
        
        # ФАЗА 2: Конвертируем базовые EvidenceObject в EvidenceExtendedModel
        extended_evidence = convert_to_extended(evidence_objects, procurement_law)
        logger.info(f"✅ Конвертировано {len(extended_evidence)} evidence в расширенный формат")
        
        # 1. Классифицируем Evidence по жёстким правилам DEAL_BREAKER
        classified_evidence = []
        for ev in extended_evidence:
            # Используем базовую классификацию из DealBreakerRules
            base_ev = EvidenceObject(
                evidence_id=ev.evidence_id,
                source_file=ev.source_file,
                fact=ev.fact,
                classification=ev.classification,
                financial_impact_rub=ev.financial_impact_rub,
                confidence=ev.confidence,
                derived_from=ev.derived_from,
                page_reference=ev.page_reference,
                section_reference=ev.section_reference,
                raw_extract=ev.raw_extract,
            )
            new_classification = self.deal_breaker_rules.classify_evidence(base_ev)
            if new_classification != ev.classification:
                logger.info(f"Evidence {ev.evidence_id} переклассифицирован: {ev.classification} → {new_classification}")
                # Обновляем классификацию в extended evidence
                ev.classification = new_classification
            classified_evidence.append(ev)
        
        # ФАЗА 2: Анализируем sub_classification для DEALBREAKER
        for ev in classified_evidence:
            if ev.classification == EvidenceClassification.DEAL_BREAKER and ev.sub_classification:
                logger.info(
                    f"🔴 DEALBREAKER обнаружен: {ev.sub_classification.value} "
                    f"(legal_basis: {ev.legal_basis.value if ev.legal_basis else 'N/A'})"
                )
        
        # 2. Выявляем противоречия (используем базовые EvidenceObject для совместимости)
        base_evidence_for_contradictions = [
            EvidenceObject(
                evidence_id=ev.evidence_id,
                source_file=ev.source_file,
                fact=ev.fact,
                classification=ev.classification,
                financial_impact_rub=ev.financial_impact_rub,
                confidence=ev.confidence,
                derived_from=ev.derived_from,
                page_reference=ev.page_reference,
                section_reference=ev.section_reference,
                raw_extract=ev.raw_extract,
            )
            for ev in classified_evidence
        ]
        contradictions = self.contradiction_detector.detect_contradictions(base_evidence_for_contradictions)
        logger.info(f"Обнаружено противоречий: {len(contradictions)}")
        
        # 3. Преобразуем Evidence → Risk Signals (используем extended evidence)
        risk_signals = self._evidence_to_risk_signals(classified_evidence, contradictions)
        logger.info(f"Сформировано Risk Signals: {len(risk_signals)}")
        
        # 4. Формируем Decision Preview (используем extended evidence)
        decision_preview = self._build_decision_preview(
            risk_signals,
            contradictions,
            classified_evidence
        )
        
        # 5. Строим Decision Graph
        decision_graph = self._build_decision_graph(
            base_evidence_for_contradictions,  # Для совместимости используем базовые
            risk_signals,
            contradictions,
            decision_preview
        )
        
        # ФАЗА 3: Если доступен ProcurementReasoningEngine, используем его для специализированного анализа
        procurement_analysis = None
        if PROCUREMENT_REASONER_AVAILABLE and procurement_law:
            try:
                procurement_engine = ProcurementReasoningEngine()
                # Используем extended evidence для специализированного анализа
                # Извлекаем НМЦК и deadline_days из evidence для более точного анализа
                nmck_from_evidence = None
                deadline_days_from_evidence = None
                for ev in classified_evidence:
                    fact_lower = ev.fact.lower()
                    # Ищем НМЦК
                    if "нмцк" in fact_lower or "начальная максимальная" in fact_lower:
                        if ev.financial_impact_rub and ev.financial_impact_rub > 1000:
                            nmck_from_evidence = ev.financial_impact_rub
                        else:
                            # Пытаемся извлечь число из факта
                            import re
                            numbers = re.findall(r'[\d\s,\.]+', ev.fact)
                            for num_str in numbers:
                                try:
                                    cleaned = num_str.replace(' ', '').replace(',', '.')
                                    value = float(cleaned)
                                    if value > 1000:
                                        nmck_from_evidence = value
                                        break
                                except ValueError:
                                    continue
                    # Ищем deadline (упрощенно, можно улучшить)
                    if "дедлайн" in fact_lower or "срок подачи" in fact_lower:
                        # Пытаемся извлечь количество дней
                        import re
                        days_match = re.search(r'(\d+)\s*(?:день|дней|дн)', fact_lower)
                        if days_match:
                            deadline_days_from_evidence = int(days_match.group(1))
                
                procurement_analysis = procurement_engine.analyze_procurement_viability(
                    classified_evidence,  # Уже extended evidence
                    procurement_law=procurement_law,
                    nmck=nmck_from_evidence,
                    deadline_days=deadline_days_from_evidence
                )
                logger.info(
                    f"✅ Procurement Analysis: verdict={procurement_analysis.verdict.value}, "
                    f"IUN={procurement_analysis.iun}, blockers={len(procurement_analysis.blockers)}"
                )
            except Exception as e:
                logger.warning(f"⚠️ Ошибка ProcurementReasoningEngine: {e}. Используем базовый анализ.")
        
        return ReasoningResult(
            risk_signals=risk_signals,
            contradictions=contradictions,
            decision_preview=decision_preview,
            decision_graph=decision_graph,
            procurement_analysis=procurement_analysis,  # ФАЗА 3: Добавляем специализированный анализ
        )
    
    def _detect_procurement_law_from_evidence(self, evidence_objects: List[EvidenceObject]) -> str:
        """
        Определяет режим закупки (44-ФЗ или 223-ФЗ) на основе evidence.
        
        Args:
            evidence_objects: Список EvidenceObject
        
        Returns:
            "44-ФЗ" или "223-ФЗ"
        """
        # Ищем упоминания законов в фактах
        fz44_count = 0
        fz223_count = 0
        
        for ev in evidence_objects:
            fact_lower = ev.fact.lower()
            if "44-фз" in fact_lower or "44 фз" in fact_lower or "контрактная система" in fact_lower:
                fz44_count += 1
            if "223-фз" in fact_lower or "223 фз" in fact_lower or "положение о закупках" in fact_lower:
                fz223_count += 1
        
        # Проверяем raw_extract для procurement_law метаданных
        for ev in evidence_objects:
            if ev.raw_extract and "procurement_law:" in ev.raw_extract:
                if "44-ФЗ" in ev.raw_extract:
                    fz44_count += 2  # Более высокий приоритет
                elif "223-ФЗ" in ev.raw_extract:
                    fz223_count += 2
        
        if fz223_count > fz44_count and fz223_count > 0:
            return "223-ФЗ"
        elif fz44_count > 0:
            return "44-ФЗ"
        else:
            # По умолчанию 44-ФЗ
            return "44-ФЗ"
    
    def _evidence_to_risk_signals(
        self,
        evidence_objects: List[Any],  # Может быть EvidenceObject или EvidenceExtendedModel
        contradictions: List[Contradiction]
    ) -> List[RiskSignal]:
        """
        Преобразует Evidence Objects в Risk Signals.
        
        ФАЗА 2: Использует extended evidence для более детальной классификации рисков.
        
        Один Evidence ≠ один Risk.
        Риск может возникать только из связки Evidence.
        """
        risk_signals: List[RiskSignal] = []
        
        # Группируем Evidence по классификации
        deal_breaker_evidence = [e for e in evidence_objects if e.classification == EvidenceClassification.DEAL_BREAKER]
        controlled_risk_evidence = [e for e in evidence_objects if e.classification == EvidenceClassification.CONTROLLED_RISK]
        market_noise_evidence = [e for e in evidence_objects if e.classification == EvidenceClassification.MARKET_NOISE]
        
        # DEAL_BREAKER → Risk Signals
        for ev in deal_breaker_evidence:
            risk_type = self._infer_risk_type(ev)
            risk_signals.append(
                RiskSignal(
                    risk_id=f"R-{uuid.uuid4().hex[:8].upper()}",
                    derived_from=[ev.evidence_id],
                    risk_type=risk_type,
                    classification=EvidenceClassification.DEAL_BREAKER,
                    description=ev.fact,
                    why_it_matters=self._explain_why_deal_breaker(ev),
                    financial_impact_rub=ev.financial_impact_rub,
                    confidence=ev.confidence,
                )
            )
        
        # CONTROLLED_RISK → Risk Signals (может быть связка Evidence)
        # Группируем связанные Evidence по типу риска
        risk_groups: Dict[RiskType, List[EvidenceObject]] = {}
        for ev in controlled_risk_evidence:
            risk_type = self._infer_risk_type(ev)
            if risk_type not in risk_groups:
                risk_groups[risk_type] = []
            risk_groups[risk_type].append(ev)
        
        for risk_type, ev_group in risk_groups.items():
            # Если несколько связанных Evidence → один Risk Signal
            if len(ev_group) > 1:
                # Объединяем связанные Evidence в один Risk
                combined_fact = " | ".join([ev.fact for ev in ev_group[:3]])  # Максимум 3 для читаемости
                risk_signals.append(
                    RiskSignal(
                        risk_id=f"R-{uuid.uuid4().hex[:8].upper()}",
                        derived_from=[ev.evidence_id for ev in ev_group],
                        risk_type=risk_type,
                        classification=EvidenceClassification.CONTROLLED_RISK,
                        description=combined_fact,
                        why_it_matters="Совокупность условий требует управленческого контроля",
                        financial_impact_rub=sum(ev.financial_impact_rub or 0 for ev in ev_group),
                        confidence=min([ev.confidence for ev in ev_group], key=lambda c: ["low", "medium", "high"].index(c.value)),
                    )
                )
            else:
                # Один Evidence → один Risk Signal
                ev = ev_group[0]
                risk_signals.append(
                    RiskSignal(
                        risk_id=f"R-{uuid.uuid4().hex[:8].upper()}",
                        derived_from=[ev.evidence_id],
                        risk_type=risk_type,
                        classification=EvidenceClassification.CONTROLLED_RISK,
                        description=ev.fact,
                        why_it_matters="Требует управленческого контроля",
                        financial_impact_rub=ev.financial_impact_rub,
                        confidence=ev.confidence,
                    )
                )
        
        return risk_signals
    
    def _infer_risk_type(self, evidence: EvidenceObject) -> RiskType:
        """Определяет тип риска по содержанию Evidence."""
        fact_lower = evidence.fact.lower()
        
        if any(kw in fact_lower for kw in ["цена", "стоимость", "оплата", "аванс", "штраф", "неустойка"]):
            return RiskType.FINANCIAL
        elif any(kw in fact_lower for kw in ["закон", "норма", "требование", "обязательство", "ответственность"]):
            return RiskType.LEGAL
        elif any(kw in fact_lower for kw in ["срок", "дедлайн", "этап", "график", "выполнение"]):
            return RiskType.OPERATIONAL
        else:
            return RiskType.TECHNICAL
    
    def _explain_why_deal_breaker(self, evidence: EvidenceObject) -> str:
        """Объясняет, почему Evidence является DEAL_BREAKER."""
        if DealBreakerRules.is_unlimited_financial_impact(evidence):
            return "Неограниченный финансовый удар делает участие экономически нецелесообразным"
        elif DealBreakerRules.is_asymmetric_responsibility(evidence):
            return "Асимметричная ответственность создаёт недопустимый правовой риск"
        elif DealBreakerRules.is_irreversible_obligation(evidence):
            return "Необратимое обязательство лишает возможности выхода из контракта"
        elif DealBreakerRules.is_critical_uncertainty(evidence):
            return "Критическая неопределённость без возможности контроля делает участие непредсказуемым"
        else:
            return "Критический стоп-фактор, делающий участие недопустимым"
    
    def _build_decision_preview(
        self,
        risk_signals: List[RiskSignal],
        contradictions: List[Contradiction],
        evidence_objects: List[EvidenceObject]
    ) -> DecisionPreview:
        """
        Формирует Decision Preview для директора (board-ready).
        
        Обязательные поля:
        - decision: УЧАСТВОВАТЬ / НЕ УЧАСТВОВАТЬ / ТОЛЬКО ПРИ УСЛОВИЯХ
        - why: 2-4 ключевых причины
        - main_risk: главный риск (если есть DEAL_BREAKER)
        - management_load: объяснение нагрузки
        - risk_mitigation: что нужно для снятия риска
        """
        deal_breakers = [r for r in risk_signals if r.classification == EvidenceClassification.DEAL_BREAKER]
        controlled_risks = [r for r in risk_signals if r.classification == EvidenceClassification.CONTROLLED_RISK]
        
        # Определяем решение
        if deal_breakers:
            decision = "DO_NOT_PARTICIPATE"
            why = [
                f"Обнаружен критический стоп-фактор: {deal_breakers[0].description[:100]}",
                "Участие создаёт недопустимый управленческий и финансовый риск",
            ]
            main_risk = deal_breakers[0].description
        elif len(controlled_risks) > 3 or contradictions:
            decision = "PARTICIPATE_WITH_CONDITIONS"
            why = [
                f"Обнаружено {len(controlled_risks)} управляемых рисков",
                f"Выявлено {len(contradictions)} противоречий между документами",
                "Требуется управленческий контроль и уточнение условий",
            ]
            main_risk = controlled_risks[0].description if controlled_risks else None
        else:
            decision = "PARTICIPATE"
            why = [
                "Критических стоп-факторов не выявлено",
                f"Обнаружено {len(controlled_risks)} управляемых рисков",
                "Условия участия стандартные",
            ]
            main_risk = None
        
        # Формируем объяснение управленческой нагрузки
        low_confidence_count = sum(1 for e in evidence_objects if e.confidence == EvidenceConfidence.LOW)
        management_load = ManagementLoadExplanation(
            sources=[
                f"Количество противоречий: {len(contradictions)}",
                f"Управляемых рисков: {len(controlled_risks)}",
                f"Evidence с низкой уверенностью: {low_confidence_count}",
            ],
            contradictions_count=len(contradictions),
            low_confidence_evidence_count=low_confidence_count,
            non_standard_conditions=[r.description for r in controlled_risks[:3]],
            manual_verification_required=[c.description for c in contradictions[:2]],
        )
        
        # Risk mitigation
        risk_mitigation = None
        if decision == "PARTICIPATE_WITH_CONDITIONS" and contradictions:
            risk_mitigation = [
                "Уточнить противоречия в документах с заказчиком",
                "Зафиксировать приоритетный источник данных (обычно проект договора)",
            ]
        
        return DecisionPreview(
            decision=decision,
            why=why,
            main_risk=main_risk,
            management_load=management_load,
            risk_mitigation=risk_mitigation,
            deal_breakers=deal_breakers,
            controlled_risks=controlled_risks,
            contradictions=contradictions,
        )
    
    def _build_decision_graph(
        self,
        evidence_objects: List[EvidenceObject],
        risk_signals: List[RiskSignal],
        contradictions: List[Contradiction],
        decision_preview: DecisionPreview
    ) -> DecisionGraph:
        """
        Строит Decision Graph для audit trail.
        
        Граф: Evidence → Risk → Contradiction → Load → Decision
        """
        nodes: List[DecisionNode] = []
        
        # Evidence nodes
        for ev in evidence_objects:
            nodes.append(
                DecisionNode(
                    node_id=ev.evidence_id,
                    node_type="evidence",
                    content={"fact": ev.fact, "classification": ev.classification.value},
                    connections=[],
                )
            )
        
        # Risk nodes
        for risk in risk_signals:
            nodes.append(
                DecisionNode(
                    node_id=risk.risk_id,
                    node_type="risk",
                    content={
                        "description": risk.description,
                        "classification": risk.classification.value,
                        "risk_type": risk.risk_type.value,
                    },
                    connections=risk.derived_from,  # Связь с Evidence
                )
            )
        
        # Contradiction nodes
        for contr in contradictions:
            nodes.append(
                DecisionNode(
                    node_id=contr.contradiction_id,
                    node_type="contradiction",
                    content={"description": contr.description, "impact": contr.impact},
                    connections=contr.evidence_ids,  # Связь с Evidence
                )
            )
        
        # Load factor node
        load_node_id = "LOAD-001"
        nodes.append(
            DecisionNode(
                node_id=load_node_id,
                node_type="load_factor",
                content={
                    "sources": decision_preview.management_load.sources,
                    "contradictions_count": decision_preview.management_load.contradictions_count,
                },
                connections=[r.risk_id for r in risk_signals] + [c.contradiction_id for c in contradictions],
            )
        )
        
        # Decision node
        decision_node_id = "DECISION-001"
        nodes.append(
            DecisionNode(
                node_id=decision_node_id,
                node_type="decision",
                content={
                    "decision": decision_preview.decision,
                    "why": decision_preview.why,
                },
                connections=[load_node_id] + [r.risk_id for r in risk_signals if r.classification == EvidenceClassification.DEAL_BREAKER],
            )
        )
        
        return DecisionGraph(
            graph_id=f"GRAPH-{uuid.uuid4().hex[:8].upper()}",
            nodes=nodes,
            root_decision=decision_node_id,
        )
    
    def _create_empty_result(self) -> ReasoningResult:
        """Создаёт пустой результат при отсутствии Evidence."""
        return ReasoningResult(
            risk_signals=[],
            contradictions=[],
            decision_preview=DecisionPreview(
                decision="DO_NOT_PARTICIPATE",
                why=["Данные для анализа отсутствуют"],
                management_load=ManagementLoadExplanation(),
            ),
            decision_graph=DecisionGraph(
                graph_id="EMPTY",
                nodes=[],
            ),
            reasoning_errors=["Evidence Objects не предоставлены"],
        )


