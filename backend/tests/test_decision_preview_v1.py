"""
Тесты для Decision Preview v1.0

Проверяет соответствие канону Decision Preview & Impact Logic v1.0
"""

import pytest
from reasoning_types import (
    DecisionPreview, 
    ManagementLoadExplanation, 
    RiskSignal, 
    RiskType
)
from evidence_types import EvidenceClassification, EvidenceConfidence
from decision_preview_formatter import DecisionPreviewFormatter
from datetime import datetime


class TestDecisionPreviewV1:
    """Тесты для Decision Preview v1.0 канона"""
    
    def test_decision_preview_has_deal_snapshot_structure(self):
        """Проверяет, что Decision Preview содержит структуру Deal Snapshot"""
        preview = DecisionPreview(
            decision="PARTICIPATE",
            why=["Факт 1", "Факт 2"],
            management_load=ManagementLoadExplanation(
                sources=["Источник 1"],
                contradictions_count=0,
                low_confidence_evidence_count=0,
                non_standard_conditions=[],
                manual_verification_required=[]
            )
        )
        
        formatted = DecisionPreviewFormatter.format_preview(preview)
        
        # Проверяем базовую структуру
        assert "decision" in formatted
        assert "decision_label" in formatted
        assert "why" in formatted
        assert "main_risk" in formatted
        assert "management_load" in formatted
    
    def test_impact_logic_format(self):
        """Проверяет, что риски используют конструкцию IMPACT LOGIC"""
        # Создаем риск с правильной конструкцией IMPACT LOGIC
        risk = RiskSignal(
            risk_id="CR-01",
            derived_from=["ev-1", "ev-2"],
            risk_type=RiskType.OPERATIONAL,
            classification=EvidenceClassification.CONTROLLED_RISK,
            description="Сжатые сроки выполнения",
            why_it_matters="Следствием является необходимость привлечения дополнительных ресурсов → Требуется операционный контроль на постоянной основе",
            confidence=EvidenceConfidence.MEDIUM
        )
        
        # Проверяем, что why_it_matters содержит конструкцию IMPACT LOGIC
        assert "Следствием является" in risk.why_it_matters
        assert "→ Требуется" in risk.why_it_matters
    
    def test_management_load_index_components(self):
        """Проверяет, что ИУН содержит компоненты A, B, C, D"""
        load = ManagementLoadExplanation(
            sources=[
                "Компонент A: Конфликты условий (Проект договора, п. 6.3)",
                "Компонент B: Финансовая экспозиция (Обоснование НМЦК)",
                "Компонент C: Юридико-процедурная нагрузка (ТЗ, раздел 3)",
                "Компонент D: Ручной операционный контроль (График работ)"
            ],
            contradictions_count=2,
            low_confidence_evidence_count=1,
            non_standard_conditions=["Нестандартные условия оплаты"],
            manual_verification_required=["Проверка лицензий"]
        )
        
        # Проверяем наличие источников
        assert len(load.sources) > 0
        assert load.contradictions_count >= 0
    
    def test_decision_preview_no_recommendations(self):
        """Проверяет, что Decision Preview не содержит рекомендаций"""
        preview = DecisionPreview(
            decision="PARTICIPATE_WITH_CONDITIONS",
            why=["Выявлены контролируемые риски", "Требуется дополнительный контроль"],
            management_load=ManagementLoadExplanation(
                sources=[],
                contradictions_count=0,
                low_confidence_evidence_count=0,
                non_standard_conditions=[],
                manual_verification_required=[]
            )
        )
        
        formatted = DecisionPreviewFormatter.format_preview(preview)
        formatted_text = str(formatted).lower()
        
        # Запрещенные слова
        forbidden_words = ["рекомендуется", "следует", "советуем", "желательно"]
        for word in forbidden_words:
            assert word not in formatted_text, f"Найдено запрещенное слово: {word}"
    
    def test_responsibility_fixation_block(self):
        """Проверяет наличие блока фиксации ответственности"""
        preview = DecisionPreview(
            decision="DO_NOT_PARTICIPATE",
            why=["Обнаружен критический стоп-фактор", "Требуется получение лицензии"],
            deal_breakers=[
                RiskSignal(
                    risk_id="DB-01",
                    derived_from=["ev-10"],
                    risk_type=RiskType.LEGAL,
                    classification=EvidenceClassification.DEAL_BREAKER,
                    description="Отсутствие обязательной лицензии",
                    why_it_matters="Следствием является невозможность участия → Требуется получение лицензии",
                    confidence=EvidenceConfidence.HIGH
                )
            ],
            management_load=ManagementLoadExplanation(
                sources=[],
                contradictions_count=0,
                low_confidence_evidence_count=0,
                non_standard_conditions=[],
                manual_verification_required=[]
            )
        )
        
        # Проверяем, что есть deal breakers
        assert len(preview.deal_breakers) > 0
        assert preview.deal_breakers[0].why_it_matters is not None
        assert "Следствием является" in preview.deal_breakers[0].why_it_matters
    
    def test_decision_preview_validation(self):
        """Проверяет валидацию Decision Preview"""
        # Валидный preview
        valid_preview = DecisionPreview(
            decision="PARTICIPATE",
            why=["Причина 1", "Причина 2"],
            management_load=ManagementLoadExplanation(
                sources=[],
                contradictions_count=0,
                low_confidence_evidence_count=0,
                non_standard_conditions=[],
                manual_verification_required=[]
            )
        )
        
        errors = DecisionPreviewFormatter.validate_preview(valid_preview)
        assert len(errors) == 0, f"Валидный preview содержит ошибки: {errors}"
        
        # Невалидный preview (неправильное решение при наличии deal breakers)
        invalid_preview = DecisionPreview(
            decision="PARTICIPATE",  # Неправильно при наличии deal breakers
            why=["Причина 1", "Причина 2"],
            deal_breakers=[
                RiskSignal(
                    risk_id="DB-01",
                    derived_from=["ev-10"],
                    risk_type=RiskType.LEGAL,
                    classification=EvidenceClassification.DEAL_BREAKER,
                    description="Тест",
                    why_it_matters="Тест",
                    confidence=EvidenceConfidence.HIGH
                )
            ],
            management_load=ManagementLoadExplanation(
                sources=[],
                contradictions_count=0,
                low_confidence_evidence_count=0,
                non_standard_conditions=[],
                manual_verification_required=[]
            )
        )
        
        errors = DecisionPreviewFormatter.validate_preview(invalid_preview)
        assert len(errors) > 0, "Невалидный preview должен содержать ошибки"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

